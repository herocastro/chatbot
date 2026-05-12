"""Library info handler — loads library data and answers patron questions."""

import json
import logging

from app.groq_client import GroqClient
from app.models import LibraryInfo

logger = logging.getLogger(__name__)

CONTACT_STAFF_MESSAGE = (
    "I'm sorry, I don't have that information available. "
    "Please contact library staff for further assistance."
)

FAQ_RESPONSE_PROMPT = (
    "A patron asked: \"{message}\"\n\n"
    "Here is the relevant library information:\n"
    "{data}\n\n"
    "Rules:\n"
    "- Answer in a friendly, conversational way using ONLY the data above.\n"
    "- Do NOT introduce yourself — just answer the question directly.\n"
    "- Write in natural flowing sentences. Do NOT use bullet points, dashes, or lists.\n"
    "- Use 1 emoji at the end."
)


def _resolve_library_info_path(file_path: str) -> str:
    """Resolve the library info path, trying the project root as a fallback."""
    import os
    if os.path.isfile(file_path):
        return file_path
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidate = os.path.join(base, file_path)
    if os.path.isfile(candidate):
        return candidate
    return file_path


def load_library_info(file_path: str) -> LibraryInfo:
    """Load and validate library information from a JSON file."""
    resolved = _resolve_library_info_path(file_path)
    try:
        with open(resolved, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error("Library info file not found at '%s' (resolved: '%s')", file_path, resolved)
        return LibraryInfo()
    except json.JSONDecodeError as exc:
        logger.error("Library info file at '%s' is malformed: %s", resolved, exc)
        return LibraryInfo()

    try:
        return LibraryInfo(**data)
    except Exception as exc:
        logger.error("Library info file at '%s' has invalid structure: %s", resolved, exc)
        return LibraryInfo()


def _is_llm_available(client: GroqClient) -> bool:
    """Check if the LLM client is configured with a real API."""
    from app.groq_client import is_llm_available
    return client is not None and is_llm_available()


def _find_matching_faqs(message: str, library_info: LibraryInfo) -> list:
    """Return FAQ items whose question or label is relevant to the message."""
    if not library_info.faqs:
        return []
    msg_lower = message.strip().lower()
    words = set(msg_lower.replace("?", " ").replace("!", " ").split())

    # 1. Exact question match — highest priority
    for faq in library_info.faqs:
        if faq.question.strip().lower() == msg_lower:
            return [faq]

    # 2. Keyword match against question and label
    scored = []
    for faq in library_info.faqs:
        faq_words = set((faq.question + " " + faq.label).lower().replace("?", " ").split())
        overlap = len(words & faq_words)
        if overlap > 0:
            scored.append((overlap, faq))
    if scored:
        scored.sort(key=lambda x: x[0], reverse=True)
        return [faq for score, faq in scored[:3] if score >= 1]

    return []


def handle_library_info_query(
    client: GroqClient,
    message: str,
    library_info: LibraryInfo,
    conversation_history: list[dict],
) -> tuple[str, str, str]:
    """Handle a library information query from a patron.

    Returns (reply_text, image_url, pdf_url) — image_url and pdf_url are
    empty strings if not present.
    """
    if not library_info or not library_info.faqs:
        return CONTACT_STAFF_MESSAGE, "", ""

    matches = _find_matching_faqs(message, library_info)

    if not matches:
        return CONTACT_STAFF_MESSAGE, "", ""

    # Exact match — return content and image directly, bypassing LLM
    import re as _re
    _url_pattern = _re.compile(r'https?://\S+|data:image/[^\s]+')
    msg_lower = message.strip().lower()
    exact_image_url = ""
    exact_pdf_url = ""
    if len(matches) == 1 and matches[0].question.strip().lower() == msg_lower:
        faq = matches[0]
        exact_image_url = faq.image_url.strip() if faq.image_url else ""
        exact_pdf_url = faq.pdf_url.strip() if faq.pdf_url else ""

        # If image_url is empty, check if a URL was embedded in the content field
        # (happens when admin pasted a URL into the reply box instead of the image field)
        if not exact_image_url:
            embedded = _url_pattern.search(faq.content)
            if embedded:
                exact_image_url = embedded.group(0)

        # Strip all URLs from content before returning — image is sent separately
        clean_content = _url_pattern.sub("", faq.content).strip()

        if clean_content:
            return clean_content, exact_image_url, exact_pdf_url
        # No text content but has image or PDF — return a minimal reply so the bubble is never blank
        if exact_image_url or exact_pdf_url:
            return "Here's the information you requested. 📋", exact_image_url, exact_pdf_url

    # Collect image and pdf from best match (first one with a value)
    image_url = exact_image_url
    pdf_url = exact_pdf_url
    if not image_url:
        for faq in matches:
            if faq.image_url and faq.image_url.strip():
                image_url = faq.image_url.strip()
                break
        if not image_url:
            for faq in matches:
                embedded = _url_pattern.search(faq.content)
                if embedded:
                    image_url = embedded.group(0)
                    break
    if not pdf_url:
        for faq in matches:
            if faq.pdf_url and faq.pdf_url.strip():
                pdf_url = faq.pdf_url.strip()
                break

    # Build data string from matched FAQ content — strip URLs so LLM never repeats them
    data_parts = []
    for faq in matches:
        clean_content = _url_pattern.sub("", faq.content).strip()
        if clean_content:
            data_parts.append(f"[{faq.question}]\n{clean_content}")

    if not data_parts:
        # No content at all — if we have an image or PDF, return a minimal reply
        if image_url or pdf_url:
            logger.info("FAQ image/pdf-only reply, image_url length=%d, pdf_url length=%d", len(image_url), len(pdf_url))
            return "Here's the information you requested. 📋", image_url, pdf_url
        return CONTACT_STAFF_MESSAGE, "", ""

    data_str = "\n\n".join(data_parts)

    # Try LLM for a conversational reply
    if client and _is_llm_available(client):
        try:
            prompt = FAQ_RESPONSE_PROMPT.format(message=message, data=data_str)
            messages: list[dict] = []
            if conversation_history:
                messages.extend(conversation_history[-4:])
            messages.append({"role": "user", "content": prompt})
            reply = client.chat(messages)
            if isinstance(reply, str) and reply and "trouble" not in reply.lower() and "moment" not in reply.lower():
                return reply, image_url, pdf_url
        except Exception:
            logger.info("LLM unavailable for library info, using raw FAQ content")

    return f"{data_str} 📚", image_url, pdf_url