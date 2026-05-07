"""Main FastAPI application — chat endpoint and request routing."""

import asyncio
import logging
import os
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.admin_routes import router as admin_router, login_router as admin_login_router, set_session_store, _public_typing_router
from app.catalog_handler import handle_catalog_query
from app.config import Settings, load_settings
from app.groq_client import GroqClient, is_llm_available
from app.library_info_handler import handle_library_info_query
from app.models import ChatRequest, ChatResponse, ErrorResponse, LibraryInfo
from app.models import FeedbackRequest
from app.ai_settings import AiSettings, load_ai_settings
from pydantic import BaseModel
from app.query_classifier import classify_query
from app.session_manager import SessionManager
from app.session_store import SessionStore
from app.staff_routes import router as staff_router, set_staff_store
from app.staff_store import StaffStore

app = FastAPI(title="Library AI Chatbot")

# CORS middleware for iframe embedding from any Koha instance.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount admin API routers.
app.include_router(admin_login_router)
app.include_router(admin_router)
app.include_router(staff_router)
app.include_router(_public_typing_router)

# Module-level variables initialised during the startup event.
settings: Settings | None = None
groq_client: GroqClient | None = None
session_manager: SessionManager | None = None
session_store: SessionStore | None = None
library_info: LibraryInfo | None = None
ai_settings: AiSettings = AiSettings()

CLARIFYING_MESSAGE = (
    "Hmm, I'm not quite sure what you mean! 🤔 "
    "I'm your library assistant — I can help you with:\n"
    "📚 Finding books in the catalog\n"
    "🕐 Library hours and locations\n"
    "📋 Policies, fines, and membership info\n\n"
    "What would you like to know?"
)

GREETING_MESSAGE = (
    "Hello! 👋 How can I help you today? "
    "I can assist with finding books, library hours, borrowing info, printing services, and more."
)

# Varied greeting responses to feel more natural (picked randomly)
_GREETING_RESPONSES = [
    "Hello! 👋 How can I help you today? I can find books, answer questions about library hours, policies, and more.",
    "Hi there! 😊 What can I help you with? I'm here for book searches, library info, and anything else library-related.",
    "Hey! 👋 I'm LLORA, your library assistant. Looking for a book, or do you have a question about the library?",
    "Hello! 📚 Ready to help — need a book recommendation, library hours, or something else?",
]

OFF_TOPIC_MESSAGE = (
    "I'm only able to help with library and school-related topics! 😊 "
    "I can assist you with:\n"
    "📚 Finding books in the catalog\n"
    "🕐 Library hours and locations\n"
    "📋 Borrowing policies, fines, and membership info\n"
    "🖨️ Printing services\n\n"
    "Is there anything library-related I can help you with?"
)

HANDOFF_ACTIVATED_MESSAGE = (
    "I've notified a librarian — they'll join this chat shortly! 📨"
)

HANDOFF_ACTIVE_NOTE = (
    "A librarian has been notified and will respond here soon. "
    "Your message has been saved. 💬"
)

# Cleanup interval for expired sessions (seconds).
_CLEANUP_INTERVAL = 300


@app.on_event("startup")
async def startup() -> None:
    """Initialise application state on startup.

    DB-heavy work (schema init/migration) runs in a thread executor so it
    doesn't block the async event loop while waiting on Turso HTTP round-trips.
    """
    global settings, groq_client, session_manager, session_store, library_info, ai_settings
    import asyncio
    import json as _json

    loop = asyncio.get_event_loop()

    try:
        settings = load_settings()
    except Exception:
        logger.warning("Failed to load settings — using defaults")
        settings = None

    # GroqClient instantiation is cheap now (openai imported lazily on first use)
    if settings:
        groq_client = GroqClient(base_url=settings.ollama_url, model=settings.ollama_model)
    else:
        groq_client = GroqClient(
            base_url=os.environ.get("OLLAMA_URL", "https://openrouter.ai/api/v1"),
            model=os.environ.get("OLLAMA_MODEL", "meta-llama/llama-3.2-3b-instruct:free"),
        )

    session_manager = SessionManager()
    library_info = LibraryInfo()

    db_path = os.environ.get("SESSION_DB_PATH", "/tmp/sessions.db")

    # Run DB init in a thread so Turso HTTP calls don't block the event loop
    def _init_stores():
        ss = SessionStore(db_path=db_path)
        sf = StaffStore(db_path=db_path)
        return ss, sf

    try:
        _ss_inst, _sf_inst = await loop.run_in_executor(None, _init_stores)
        session_store = _ss_inst
        set_session_store(session_store)
        set_staff_store(_sf_inst)
    except Exception:
        logger.warning("Failed to initialise stores at %s", db_path)
        session_store = None

    # Load library info and AI settings from DB (also in executor)
    def _load_config():
        from app.staff_routes import staff_store as _ss
        if _ss is None:
            return None, None
        lib_json = _ss.get_setting("library_info_json")
        ai_json = _ss.get_setting("ai_settings_json")
        return lib_json, ai_json

    try:
        lib_json, ai_json = await loop.run_in_executor(None, _load_config)
        if lib_json:
            library_info = LibraryInfo(**_json.loads(lib_json))
            logger.info("Loaded library info (%d FAQs)", len(library_info.faqs))
        if ai_json or True:  # always load AI settings (uses defaults if not set)
            from app.staff_routes import staff_store as _ss2
            ai_settings = load_ai_settings(_ss2)
            import app.groq_client as _gc
            _gc.SYSTEM_PROMPT = ai_settings.build_system_prompt()
            logger.info("Loaded AI settings: name=%s", ai_settings.name)
    except Exception:
        logger.warning("Failed to load config from database")

    _sync_faq_questions()
    # Note: _periodic_cleanup background task removed — Vercel serverless instances
    # are killed after each request, so the task never runs. Use a Vercel Cron Job
    # for periodic cleanup if needed.


@app.get("/debug/koha-test")
async def debug_koha_test():
    """Debug endpoint — test if we can reach the Koha catalog."""
    import httpx
    koha_url = os.environ.get("KOHA_API_URL", "not set")
    url = f"{koha_url.rstrip('/')}/cgi-bin/koha/opac-search.pl"
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as http:
            resp = await http.get(
                url,
                params={"q": "java", "format": "rss"},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
            )
            return {
                "koha_api_url": koha_url,
                "search_url": url,
                "status_code": resp.status_code,
                "response_length": len(resp.text),
                "first_200_chars": resp.text[:200],
            }
    except Exception as exc:
        return {
            "koha_api_url": koha_url,
            "search_url": url,
            "error": str(exc),
            "error_type": type(exc).__name__,
        }


@app.post("/api/format-results")
async def format_results(request: dict):
    """Format raw catalog search results from client-side Koha search."""
    results = request.get("results", [])
    session_id = request.get("session_id", "")
    message = request.get("message", "")

    if not results:
        from app.catalog_handler import NO_RESULTS_MESSAGE
        reply = NO_RESULTS_MESSAGE
    else:
        lines = []
        for i, rec in enumerate(results[:20], start=1):
            parts = [f"{i}. {rec.get('title', 'Unknown')} by {rec.get('author', 'Unknown Author')}"]
            if rec.get("url"):
                parts.append(f"   View in catalog: {rec['url']}")
            lines.append("\n".join(parts))
        reply = "Here's what I found in the catalog 📚:\n\n" + "\n".join(lines)

    # Store in session
    if session_manager and session_id:
        session_manager.add_message(session_id, "assistant", reply)

    # Persist
    if session_store and session_id:
        try:
            session_store.save_message(session_id, "assistant", reply)
        except Exception:
            pass

    return ChatResponse(reply=reply, session_id=session_id, timestamp=time.time())


@app.get("/health")
async def health():
    """Simple health-check endpoint."""
    has_key = bool(os.environ.get("OPENROUTER_API_KEY"))
    llm_url = os.environ.get("OLLAMA_URL", "not set")
    llm_model = os.environ.get("OLLAMA_MODEL", "not set")
    return {
        "status": "ok",
        "llm_enabled": has_key,
        "llm_url": llm_url,
        "llm_model": llm_model,
    }


@app.get("/api/session-status/{session_id}")
async def session_status(session_id: str):
    """Check if a session is still active or has expired."""
    if session_store is None:
        return {"status": "unknown"}
    try:
        detail = session_store.get_session(session_id)
        if detail is None:
            return {"status": "not_found"}
        return {"status": detail.status}
    except Exception:
        return {"status": "unknown"}


def _sync_faq_questions() -> None:
    """Sync FAQ question strings into the classifier for fast intent matching."""
    try:
        import app.query_classifier as _qc
        if library_info and library_info.faqs:
            _qc.FAQ_QUESTIONS = {f.question.strip().lower() for f in library_info.faqs}
        else:
            _qc.FAQ_QUESTIONS = set()
    except Exception:
        pass


@app.get("/api/faqs")
async def get_faqs():
    """Return the configured FAQ buttons for the chat widget (no-cache)."""
    faqs = []
    if library_info is not None:
        faqs = [f.model_dump() for f in library_info.faqs]
    return JSONResponse(
        content={"faqs": faqs},
        headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"},
    )


@app.get("/api/ai-config")
async def get_ai_config():
    """Return public AI config for the widget (name, welcome message)."""
    return JSONResponse(
        content={
            "name": ai_settings.name,
            "welcome_message": ai_settings.get_welcome_text(),
        },
        headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"},
    )


@app.get("/api/image/{img_key}")
async def get_image(img_key: str):
    """Serve a stored FAQ image by its DB key."""
    try:
        from app.staff_routes import staff_store as _ss
        if _ss is None:
            return JSONResponse(status_code=404, content={"error": "Not found"})
        data_url = _ss.get_setting(img_key)
        if not data_url or not data_url.startswith("data:image/"):
            return JSONResponse(status_code=404, content={"error": "Image not found"})
        # Parse data URL: data:<mime>;base64,<data>
        import base64
        header, b64data = data_url.split(",", 1)
        mime = header.split(":")[1].split(";")[0]
        img_bytes = base64.b64decode(b64data)
        from fastapi.responses import Response as _Resp
        return _Resp(
            content=img_bytes,
            media_type=mime,
            headers={"Cache-Control": "public, max-age=86400"},
        )
    except Exception:
        logger.exception("Failed to serve image %s", img_key)
        return JSONResponse(status_code=500, content={"error": "Failed to serve image"})


@app.get("/debug/faq-images")
async def debug_faq_images():
    """Debug: show what image_url values are stored in the current FAQ list."""
    result = []
    if library_info:
        for faq in library_info.faqs:
            result.append({
                "label": faq.label,
                "question": faq.question,
                "image_url_length": len(faq.image_url) if faq.image_url else 0,
                "image_url_preview": faq.image_url[:120] if faq.image_url else "",
            })
    return {"faqs": result, "total": len(result)}


@app.get("/")
async def root():
    """Root endpoint — confirms the API is running."""
    return {"status": "ok", "app": "Library AI Chatbot"}


def _llm_reply(
    client: GroqClient | None,
    message: str,
    history: list[dict],
    max_history: int = 6,
    max_tokens: int | None = None,
) -> str | None:
    """Call the LLM with conversation history. Returns None if LLM is not configured."""
    if not client or not is_llm_available():
        return None
    try:
        messages_for_llm = list(history[-max_history:]) if history else []
        messages_for_llm.append({"role": "user", "content": message})
        # Temporarily override max_tokens if specified
        if max_tokens is not None:
            original = client.max_tokens
            client.max_tokens = max_tokens
        reply = client.chat(messages_for_llm)
        if max_tokens is not None:
            client.max_tokens = original
        if isinstance(reply, str) and reply.strip():
            return reply
    except Exception as exc:
        logger.warning("LLM call failed: %s", exc)
    return None


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Process a patron chat message and return a response.

    Validates the request, classifies the query intent, routes to the
    appropriate handler, and stores the conversation in the session.
    """
    global session_manager, groq_client, settings, library_info

    # --- Validate message ---
    if not request.message or not request.message.strip():
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="Message field is required and must be non-empty"
            ).model_dump(),
        )

    # --- Validate session_id ---
    if not request.session_id or not request.session_id.strip():
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="Session identifier is required"
            ).model_dump(),
        )

    # --- Session & history ---
    session_mgr = session_manager or SessionManager()
    history = session_mgr.get_history(request.session_id)

    # --- Ensure session store is available (handles cold-start where startup hasn't fired yet) ---
    global session_store
    if session_store is None:
        try:
            db_path = os.environ.get("SESSION_DB_PATH", "/tmp/sessions.db")
            session_store = SessionStore(db_path=db_path)
            from app.admin_routes import set_session_store as _set_ss
            _set_ss(session_store)
        except Exception:
            logger.warning("Failed to init session store on-demand in /api/chat")

    # --- Check if handoff is active (librarian takeover) ---
    _active_live_chat = session_store.get_active_live_chat(request.session_id) if session_store else None
    _handoff_active = _active_live_chat is not None or (
        session_store is not None and session_store.is_handoff_active(request.session_id)
    )
    if _handoff_active:
        # Patron is in handoff mode — save their message to the live chat session
        session_mgr.add_message(request.session_id, "user", request.message)
        _store = session_store
        _sid = request.session_id
        _msg = request.message
        _lc = _active_live_chat
        async def _persist_handoff():
            try:
                live_chat = _lc
                # Retry up to 3 times to handle race conditions / cold-start DB lag
                for _attempt in range(3):
                    if live_chat:
                        break
                    live_chat = _store.get_active_live_chat(_sid)
                    if not live_chat:
                        await asyncio.sleep(0.5)
                if live_chat:
                    _store.save_live_chat_message(live_chat["id"], "user", _msg)
                else:
                    # Last resort: save to regular messages table so the message
                    # is at least recorded, but log a warning.
                    logger.warning(
                        "Could not find active live chat for session %s — "
                        "saving patron message to regular messages table", _sid
                    )
                    _store.save_message(_sid, "user", _msg, intent="handoff")
            except Exception:
                logger.exception("Failed to persist handoff message for session %s", _sid)
        asyncio.create_task(_persist_handoff())
        return ChatResponse(reply="", session_id=request.session_id, timestamp=time.time())

    # --- Classify intent ---
    client = groq_client  # may be None before startup wiring
    classification = classify_query(client, request.message, history)

    # --- Route to handler ---
    reply: str
    if classification.intent == "talk_to_librarian":
        # Check if handoff is already active — don't re-notify
        already_active = session_store is not None and session_store.is_handoff_active(request.session_id)
        if already_active:
            # Already in handoff — just save the message silently
            session_mgr.add_message(request.session_id, "user", request.message)
            if session_store is not None:
                _store = session_store
                _sid = request.session_id
                _msg = request.message
                async def _persist_dup():
                    try:
                        _store.save_message(_sid, "user", _msg, intent="handoff")
                    except Exception:
                        logger.exception("Failed to persist duplicate handoff msg for session %s", _sid)
                asyncio.create_task(_persist_dup())
            return ChatResponse(reply="", session_id=request.session_id, timestamp=time.time())

        # First time — activate handoff and notify
        reply = HANDOFF_ACTIVATED_MESSAGE
        if session_store is not None:
            try:
                # Save messages first (creates session row), then activate handoff
                session_store.save_message(request.session_id, "user", request.message, intent="talk_to_librarian")
                session_store.save_message(request.session_id, "assistant", reply)
                session_store.activate_handoff(request.session_id)
                # Create a separate live chat session
                live_chat_id = session_store.create_live_chat(request.session_id)
                logger.info("Created live chat %s for session %s", live_chat_id, request.session_id)
            except Exception:
                logger.exception("Failed to activate handoff for session %s", request.session_id)
        # Send notification in background (ntfy push or email)
        if settings:
            _cfg = settings
            _sid = request.session_id
            async def _send_notification():
                import json as _json
                from app.email_notify import send_ntfy_notification, send_handoff_email, send_staff_notify_email
                if _cfg.ntfy_topic:
                    send_ntfy_notification(_cfg.ntfy_topic, _sid, _cfg.chatbot_public_url)
                from app.email_notify import _use_service_account
                _has_email = (_cfg.smtp_email and _cfg.smtp_password) or _use_service_account()
                if _has_email:
                    # Email all active staff contacts (personalized by name)
                    try:
                        from app.staff_routes import staff_store as _ss
                        if _ss:
                            contacts = _ss.get_active_contacts()
                            logger.info("Notifying %d staff contacts for session %s", len(contacts), _sid)
                            for c in contacts:
                                try:
                                    send_staff_notify_email(
                                        _cfg.smtp_email, _cfg.smtp_password,
                                        c["email"], c["name"], _sid, _cfg.chatbot_public_url,
                                    )
                                except Exception:
                                    logger.exception("Failed to notify contact %s", c["email"])
                    except Exception:
                        logger.exception("Failed to fetch staff contacts")
            asyncio.create_task(_send_notification())
        session_mgr.add_message(request.session_id, "user", request.message)
        session_mgr.add_message(request.session_id, "assistant", reply)
        return ChatResponse(reply=reply, session_id=request.session_id, timestamp=time.time())
    elif classification.intent == "catalog_search":
        koha_url = settings.koha_api_url if settings else ""
        # First try server-side search
        reply = await handle_catalog_query(
            client, request.message, koha_url, history
        )
        # If server-side search failed (likely 403 from WAF), fall back to client-side
        if reply == CLARIFYING_MESSAGE or "couldn't find" in reply:
            from app.catalog_handler import _extract_keywords, _is_vague_query
            raw_kw = _extract_keywords(request.message)
            if not _is_vague_query(raw_kw):
                # Always use raw keywords — most reliable for client-side search
                session_mgr.add_message(request.session_id, "user", request.message)
                return ChatResponse(
                    reply="",
                    session_id=request.session_id,
                    timestamp=time.time(),
                    client_search=raw_kw,
                )
    elif classification.intent == "library_info":
        reply, _img_url = handle_library_info_query(
            client, request.message, library_info, history
        )
        # Pass image_url as-is — the widget resolves relative /api/image/ paths
        # using its own CHATBOT_API base, which is always correct regardless of deployment.
        # Store conversation and return with image if present
        session_mgr.add_message(request.session_id, "user", request.message)
        session_mgr.add_message(request.session_id, "assistant", reply)
        if session_store is not None:
            _store = session_store
            _sid = request.session_id
            _msg = request.message
            _reply = reply
            _intent = classification.intent
            async def _persist_info():
                try:
                    _store.save_message(_sid, "user", _msg, intent=_intent)
                    _store.save_message(_sid, "assistant", _reply)
                except Exception:
                    logger.exception("Failed to persist messages for session %s", _sid)
            asyncio.create_task(_persist_info())
        return ChatResponse(
            reply=reply,
            session_id=request.session_id,
            timestamp=time.time(),
            image_url=_img_url if _img_url else None,
        )
    elif classification.intent == "greeting":
        # Use a fast static response — no LLM needed for greetings
        import random
        reply = random.choice(_GREETING_RESPONSES)
    elif classification.intent == "conversational":
        # Follow-up or clarifying message — use LLM with full history, short response
        reply = _llm_reply(client, request.message, history, max_history=8, max_tokens=150) or CLARIFYING_MESSAGE
    else:
        # "unclear" / off-topic — LLM will redirect per system prompt, short response
        reply = _llm_reply(client, request.message, history, max_history=6, max_tokens=120) or OFF_TOPIC_MESSAGE

    # --- Store conversation turn ---
    session_mgr.add_message(request.session_id, "user", request.message)
    session_mgr.add_message(request.session_id, "assistant", reply)

    # --- Persist to SQLite session store (non-blocking) ---
    if session_store is not None:
        _store = session_store
        _sid = request.session_id
        _msg = request.message
        _reply = reply
        _intent = classification.intent

        async def _persist():
            try:
                _store.save_message(_sid, "user", _msg, intent=_intent)
                _store.save_message(_sid, "assistant", _reply)
            except Exception:
                logger.exception("Failed to persist messages for session %s", _sid)

        asyncio.create_task(_persist())

    return ChatResponse(reply=reply, session_id=request.session_id, timestamp=time.time())


@app.post("/api/close-session")
async def close_session(request: ChatRequest):
    """Mark a chat session as expired when the patron closes the page."""
    if not request.session_id or not request.session_id.strip():
        return JSONResponse(status_code=400, content={"error": "Session identifier is required"})
    if session_store is not None:
        try:
            live_chat = session_store.get_active_live_chat(request.session_id)
            if live_chat:
                # Only auto-end the live chat if it hasn't been claimed by a librarian yet.
                # If a librarian is actively handling it, only they can end it.
                if not live_chat.get("staff_username"):
                    session_store.end_live_chat(live_chat["id"])
                # If claimed, leave the live chat running — librarian will end it explicitly.
            # Deactivate handoff flag only if no active live chat remains
            remaining = session_store.get_active_live_chat(request.session_id)
            if not remaining and session_store.is_handoff_active(request.session_id):
                session_store.deactivate_handoff(request.session_id)
            session_store.close_session(request.session_id)
        except Exception:
            logger.exception("Failed to close session %s", request.session_id)
    return {"status": "ok"}


@app.post("/api/cancel-handoff")
async def cancel_handoff(request: ChatRequest):
    """Allow a patron to cancel their librarian handoff request."""
    if not request.session_id or not request.session_id.strip():
        return JSONResponse(status_code=400, content={"error": "Session identifier is required"})
    if session_store is None:
        return JSONResponse(status_code=500, content={"error": "Store not available"})
    try:
        live_chat = session_store.get_active_live_chat(request.session_id)
        if not live_chat:
            return JSONResponse(status_code=404, content={"error": "No active handoff"})
        if live_chat["staff_username"]:
            return JSONResponse(status_code=409, content={"error": "A librarian has already joined. Cannot cancel."})
        session_store.cancel_live_chat(live_chat["id"])
        session_store.save_message(
            request.session_id, "assistant",
            "Librarian request cancelled. 👋 I'm LLORA, your AI assistant — what can I help you with?"
        )
        return {"status": "ok"}
    except Exception:
        logger.exception("Failed to cancel handoff for session %s", request.session_id)
        return JSONResponse(status_code=500, content={"error": "Failed to cancel handoff"})


@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Accept patron feedback (thumbs up/down) on a bot response."""
    if not request.session_id or not request.session_id.strip():
        return JSONResponse(status_code=400, content={"error": "Session identifier is required"})
    if request.rating not in (1, -1):
        return JSONResponse(status_code=400, content={"error": "Rating must be 1 or -1"})
    if session_store is not None:
        try:
            session_store.save_feedback(
                request.session_id, request.message_timestamp, request.rating,
            )
        except Exception:
            logger.exception("Failed to save feedback for session %s", request.session_id)
            return JSONResponse(status_code=500, content={"error": "Failed to save feedback"})
    return {"status": "ok"}


class HandoffRatingRequest(BaseModel):
    session_id: str
    rating: int  # 1 = Not Satisfied, 2 = Moderately Satisfied, 3 = Satisfied, 4 = Very Satisfied


@app.post("/api/rate-handoff")
async def rate_handoff(request: HandoffRatingRequest):
    """Accept patron rating (1–4 scale) for the staff member who handled their live chat."""
    if not request.session_id or not request.session_id.strip():
        return JSONResponse(status_code=400, content={"error": "Session identifier is required"})
    if request.rating not in (1, 2, 3, 4):
        return JSONResponse(status_code=400, content={"error": "Rating must be 1, 2, 3, or 4"})
    if session_store is None:
        return JSONResponse(status_code=500, content={"error": "Store not available"})
    # Look up who handled this session — check live chat first, fall back to old claim
    claimed_by = session_store.get_handoff_claim(request.session_id)
    if not claimed_by:
        return JSONResponse(status_code=400, content={"error": "No staff handler found for this session"})
    try:
        session_store.save_staff_rating(request.session_id, claimed_by, request.rating)
        return {"status": "ok"}
    except Exception:
        logger.exception("Failed to save handoff rating for session %s", request.session_id)
        return JSONResponse(status_code=500, content={"error": "Failed to save rating"})


@app.get("/api/messenger-link")
async def get_messenger_link():
    """Return the configured Messenger link for the Talk to a Librarian feature."""
    link = settings.messenger_link if settings else "https://m.me/your-library-page"
    return {"messenger_link": link}


# Default library hours (Philippines — Lorma Colleges libraries).
# Each day maps to a list of {open, close} windows in 24-h "HH:MM" format.
# An empty list means the library is closed that day.
_DEFAULT_LIBRARY_HOURS: dict = {
    "monday":    [{"open": "07:00", "close": "19:00"}],
    "tuesday":   [{"open": "07:00", "close": "19:00"}],
    "wednesday": [{"open": "07:00", "close": "19:00"}],
    "thursday":  [{"open": "07:00", "close": "19:00"}],
    "friday":    [{"open": "07:00", "close": "19:00"}],
    "saturday":  [{"open": "08:30", "close": "16:30"}],
    "sunday":    [],
}

# How many minutes before closing the librarian button is disabled.
_LIBRARIAN_CUTOFF_MINUTES = 30


def _get_library_hours() -> dict:
    """Return the configured library hours from DB, falling back to defaults."""
    try:
        from app.staff_routes import staff_store as _ss
        if _ss is not None:
            raw = _ss.get_setting("library_hours_json")
            if raw:
                import json as _json
                return _json.loads(raw)
    except Exception:
        pass
    return _DEFAULT_LIBRARY_HOURS


def _check_librarian_available(hours: dict, cutoff_minutes: int = 30) -> dict:
    """Check whether the librarian button should be enabled right now.

    Uses Asia/Manila timezone (UTC+8, no DST).
    Returns {"available": bool, "reason": str, "closes_at": str|None}.
    """
    import datetime

    # Philippines is UTC+8 with no DST.
    ph_tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(ph_tz)
    day_name = now.strftime("%A").lower()  # e.g. "monday"

    windows = hours.get(day_name, [])
    if not windows:
        return {
            "available": False,
            "reason": "The library is closed today.",
            "closes_at": None,
        }

    now_time = now.time().replace(second=0, microsecond=0)

    for window in windows:
        try:
            open_h, open_m = map(int, window["open"].split(":"))
            close_h, close_m = map(int, window["close"].split(":"))
        except (KeyError, ValueError):
            continue

        open_time = datetime.time(open_h, open_m)
        close_time = datetime.time(close_h, close_m)
        cutoff_dt = (
            datetime.datetime.combine(now.date(), close_time, tzinfo=ph_tz)
            - datetime.timedelta(minutes=cutoff_minutes)
        )
        cutoff_time = cutoff_dt.time()

        if open_time <= now_time < cutoff_time:
            # Within hours and before cutoff — available
            close_str = window["close"]
            return {
                "available": True,
                "reason": f"Librarians are available until {close_str}.",
                "closes_at": close_str,
            }
        elif cutoff_time <= now_time < close_time:
            # Within the 30-min cutoff window
            close_str = window["close"]
            return {
                "available": False,
                "reason": (
                    f"The library closes at {close_str}. "
                    f"The librarian chat is disabled {cutoff_minutes} minutes before closing."
                ),
                "closes_at": close_str,
            }

    # Outside all windows for today
    return {
        "available": False,
        "reason": "The library is currently closed.",
        "closes_at": None,
    }


class PatronInfoRequest(BaseModel):
    session_id: str
    patron_type: str   # e.g. "Student (Higher Ed)"
    patron_details: str  # e.g. "BSIT 3rd Year"


@app.post("/api/patron-info")
async def save_patron_info(request: PatronInfoRequest):
    """Save patron identity info collected before a librarian handoff."""
    if not request.session_id or not request.session_id.strip():
        return JSONResponse(status_code=400, content={"error": "Session identifier is required"})
    if not request.patron_type or not request.patron_type.strip():
        return JSONResponse(status_code=400, content={"error": "Patron type is required"})
    if session_store is None:
        return JSONResponse(status_code=500, content={"error": "Store not available"})
    try:
        session_store.save_patron_info(
            request.session_id,
            request.patron_type.strip(),
            request.patron_details.strip(),
        )
        return {"status": "ok"}
    except Exception:
        logger.exception("Failed to save patron info for session %s", request.session_id)
        return JSONResponse(status_code=500, content={"error": "Failed to save patron info"})


@app.get("/api/patron-info/{session_id}")
async def get_patron_info(session_id: str):
    """Return patron identity info for a session (used by librarian dashboard)."""
    if session_store is None:
        return {"patron_type": None, "patron_details": None}
    info = session_store.get_patron_info(session_id)
    if info:
        return info
    return {"patron_type": None, "patron_details": None}


@app.get("/api/librarian-available")
async def librarian_available():
    """Return whether the Talk-to-a-Librarian button should be enabled.

    Checks current Philippines time (Asia/Manila, UTC+8) against the
    configured library hours. The button is disabled 30 minutes before
    closing time.
    """
    hours = _get_library_hours()
    result = _check_librarian_available(hours, _LIBRARIAN_CUTOFF_MINUTES)
    return JSONResponse(
        content=result,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@app.get("/api/poll/{session_id}")
async def poll_messages(session_id: str, since: float = 0):
    """Patron polls for new messages (librarian replies) since a timestamp."""
    global session_store
    if session_store is None:
        try:
            db_path = os.environ.get("SESSION_DB_PATH", "/tmp/sessions.db")
            session_store = SessionStore(db_path=db_path)
            from app.admin_routes import set_session_store as _set_ss
            _set_ss(session_store)
        except Exception:
            pass
    if session_store is None:
        return {"messages": [], "handoff_active": False, "handled_by": None,
                "live_chat_id": None, "live_chat_status": None}
    try:
        # Use get_active_live_chat as the single source of truth.
        # is_handoff_active() already checks for active live chats internally,
        # so we query the live chat directly and derive handoff_active from it.
        live_chat = session_store.get_active_live_chat(session_id)
        if live_chat:
            live_chat_id = live_chat["id"]
            handled_by = live_chat["staff_username"]
            live_chat_status = live_chat["status"]   # "waiting" | "active"
            handoff = True
            msgs = session_store.get_live_chat_messages(live_chat_id, since)
        else:
            # No active live chat — check if there's a recently-ended one
            ended_chat = session_store.get_recently_ended_live_chat(session_id)
            live_chat_id = ended_chat["id"] if ended_chat else None
            handled_by = ended_chat["staff_username"] if ended_chat else None
            # Only signal "ended" if we have a concrete ended row in the DB.
            # Never infer "ended" from missing data — that's indistinguishable
            # from a Vercel cold-start instance with an empty DB.
            if ended_chat:
                live_chat_status = "ended"
                handoff = False
            else:
                # Secondary fallback: check sessions table directly.
                # If handoff_active=0 AND handoff_count>0 AND message_count>0,
                # the librarian ended the chat but the ended live_chat row isn't
                # visible on this Vercel instance yet (cold-start DB lag).
                # message_count>0 guard prevents false positives on empty-DB instances.
                hs = session_store.get_session_handoff_state(session_id)
                if (
                    hs is not None
                    and hs["handoff_active"] == 0
                    and hs["handoff_count"] > 0
                    and hs["message_count"] > 0
                ):
                    live_chat_status = "ended"
                    handoff = False
                else:
                    live_chat_status = None
                    handoff = session_store.is_handoff_active(session_id)
            msgs = session_store.get_new_messages_since(session_id, since)
        return {
            "messages": msgs,
            "handoff_active": handoff,
            "handled_by": handled_by,
            "live_chat_id": live_chat_id,
            "live_chat_status": live_chat_status,
        }
    except Exception:
        logger.exception("Failed to poll messages for session %s", session_id)
        return {"messages": [], "handoff_active": False, "handled_by": None,
                "live_chat_id": None, "live_chat_status": None}


# Serve admin dashboard HTML at /admin/.
_admin_html = os.path.join(os.path.dirname(__file__), "static", "admin.html")
_live_chat_html = os.path.join(os.path.dirname(__file__), "static", "live-chat.html")


@app.get("/admin/")
async def admin_dashboard():
    """Serve the admin monitoring dashboard with no-cache headers."""
    return HTMLResponse(
        content=open(_admin_html, "r", encoding="utf-8").read(),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/chat/")
async def live_chat_page():
    """Serve the standalone live chat page with API key injected."""
    api_key = os.environ.get("ADMIN_API_KEY", "")
    with open(_live_chat_html, "r", encoding="utf-8") as f:
        html = f.read()
    # Inject the API key so the page can auto-connect
    html = html.replace("__INJECTED_API_KEY__", api_key)
    return HTMLResponse(html)


@app.get("/admin/chat/")
async def live_chat_page_alt():
    """Serve the live chat page at /admin/chat/ too."""
    return await live_chat_page()


# Serve the inline widget JS with no-cache headers so updates are always picked up.
_widget_js = os.path.join(os.path.dirname(__file__), "static", "koha-chatbot-inline.js")

@app.get("/static/koha-chatbot-inline.js")
async def serve_widget_js():
    """Serve the inline widget JS with no-cache headers."""
    return FileResponse(
        _widget_js,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


# Mount static files for the chat widget.
_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")
