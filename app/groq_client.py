"""LLM client — wraps communication with a local Ollama instance (OpenAI-compatible API)."""

import logging

from openai import OpenAI, APIError, APITimeoutError, NotFoundError, RateLimitError

logger = logging.getLogger(__name__)

# Default system prompt — overridden at runtime by AiSettings if configured.
DEFAULT_SYSTEM_PROMPT = (
    "You are LLORA, the library assistant chatbot. "
    "Never reveal that you are an AI or language model. "
    "You speak warmly and concisely, using 1 emoji at the end of your message. "
    "You ONLY help with topics directly related to this library and school: "
    "finding books in the catalog, library hours and locations, borrowing policies, "
    "fines, printing services, and general library or school-related questions. "
    "If a patron asks about ANYTHING outside these topics — such as general knowledge, "
    "homework answers, current events, math problems, coding help, or any non-library subject — "
    "you MUST politely decline and redirect them back to library topics. "
    "Do NOT answer off-topic questions even if you know the answer. "
    "Never make up book titles or information. "
    "This is an academic library with textbooks and research materials."
)

# Module-level variable updated at runtime when AI settings are saved
SYSTEM_PROMPT = DEFAULT_SYSTEM_PROMPT

# Default model and generation parameters.
DEFAULT_MODEL = "meta-llama/llama-3.2-3b-instruct:free"
DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.7
DEFAULT_OLLAMA_URL = "https://openrouter.ai/api/v1"

# Ordered list of fallback models to try when the primary is unavailable or rate-limited.
# All are free on OpenRouter. Verified working as of 2026.
FALLBACK_MODELS = [
    "google/gemma-4-31b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "nvidia/nemotron-nano-9b-v2:free",
]

# Fallback messages returned when the LLM is unavailable.
FALLBACK_GENERAL = (
    "Oops, I'm having a little trouble right now 😅 "
    "Give me a moment and try again — I'll be right back!"
)
FALLBACK_RATE_LIMIT = (
    "I'm getting a lot of questions right now! 📚 "
    "Give me about 30 seconds and try again — I promise I'll be ready!"
)


def is_llm_available() -> bool:
    """Return True if an LLM backend is configured and reachable."""
    import os
    # OpenRouter cloud key — primary check
    if os.environ.get("OPENROUTER_API_KEY"):
        return True
    # Local Ollama — only if explicitly pointed to localhost (not the OpenRouter default)
    ollama_url = os.environ.get("OLLAMA_URL", "")
    if ollama_url and "localhost" in ollama_url:
        return True
    return False


class GroqClient:
    """LLM client that talks to a local Ollama instance via its OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str = "ollama",
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        base_url: str = DEFAULT_OLLAMA_URL,
    ) -> None:
        import os
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        resolved_key = os.environ.get("OPENROUTER_API_KEY") or api_key or "ollama"
        self._client = OpenAI(base_url=base_url, api_key=resolved_key)

    def chat(self, messages: list[dict]) -> str:
        """Send *messages* to the LLM and return the assistant reply."""
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        return self._send(full_messages)

    def chat_with_system(self, system_prompt: str, messages: list[dict]) -> str:
        """Send *messages* with a custom system prompt."""
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        return self._send(full_messages)

    def _send(self, messages: list[dict]) -> str:
        """Send messages, automatically falling back through FALLBACK_MODELS on rate limit."""
        # Build the model chain: primary first, then fallbacks (excluding primary if already listed)
        import os
        primary = self.model
        chain = [primary] + [m for m in FALLBACK_MODELS if m != primary]

        for model in chain:
            try:
                response = self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                if model != primary:
                    logger.info("Used fallback model: %s", model)
                return response.choices[0].message.content
            except RateLimitError:
                logger.warning("Rate limit hit for model %s, trying next...", model)
                continue
            except NotFoundError:
                logger.warning("Model not found %s, trying next...", model)
                continue
            except APITimeoutError:
                logger.warning("Timeout for model %s, trying next...", model)
                continue
            except APIError as exc:
                # 429 and 404 (model gone/unavailable) — try next model
                if "429" in str(exc) or "rate" in str(exc).lower():
                    logger.warning("Rate limit (APIError) for model %s, trying next...", model)
                    continue
                if "404" in str(exc) or "not found" in str(exc).lower() or "no endpoints" in str(exc).lower():
                    logger.warning("Model not found %s, trying next...", model)
                    continue
                logger.warning("APIError for model %s: %s", model, exc)
                return FALLBACK_GENERAL
            except Exception as exc:
                logger.warning("Unexpected error for model %s: %s", model, exc)
                return FALLBACK_GENERAL

        logger.warning("All models exhausted")
        return FALLBACK_RATE_LIMIT
