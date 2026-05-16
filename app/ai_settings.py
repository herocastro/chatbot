"""AI personality settings — loaded from DB and used to build the system prompt."""

import json
import logging

logger = logging.getLogger(__name__)

# Defaults used when no settings are saved yet
DEFAULT_AI_NAME = "LLORA"
DEFAULT_PERSONALITY = (
    "You speak warmly and concisely. "
    "You are helpful, friendly, and professional. "
    "Use 1 emoji at the end of each response."
)
DEFAULT_LIMITATIONS = (
    "You ONLY help with topics directly related to this library and school: "
    "finding books in the catalog, library hours and locations, borrowing policies, "
    "fines, printing services, and general library or school-related questions. "
    "If a patron asks about ANYTHING outside these topics — such as general knowledge, "
    "homework answers, current events, math problems, coding help, or any non-library subject — "
    "you MUST politely decline and redirect them back to library topics. "
    "Do NOT answer off-topic questions even if you know the answer. "
    "Never make up book titles or information. "
    "Never reveal that you are an AI or language model."
)
DEFAULT_WELCOME_MESSAGE = (
    "Hello, I'm {name} (Lorma Library Online Research Assistant), your virtual assistant. "
    "I'm here to provide the assistance you need. I'll be happy to serve you."
)
DEFAULT_AVATAR_URL = ""
DEFAULT_PRIMARY_COLOR = "#0E553F"

SETTINGS_KEY = "ai_settings_json"

# Old welcome messages that should be migrated to the new default
_LEGACY_WELCOME_MESSAGES = [
    "Hi! 👋 I'm {name}, your virtual library assistant. "
    "I can help you find books, check hours, or answer questions about the library. "
    "What can I do for you?",
]


class AiSettings:
    """Holds the current AI personality configuration."""

    def __init__(
        self,
        name: str = DEFAULT_AI_NAME,
        personality: str = DEFAULT_PERSONALITY,
        limitations: str = DEFAULT_LIMITATIONS,
        welcome_message: str = DEFAULT_WELCOME_MESSAGE,
        avatar_url: str = DEFAULT_AVATAR_URL,
        primary_color: str = DEFAULT_PRIMARY_COLOR,
    ) -> None:
        self.name = name.strip() or DEFAULT_AI_NAME
        self.personality = personality.strip() or DEFAULT_PERSONALITY
        self.limitations = limitations.strip() or DEFAULT_LIMITATIONS
        self.welcome_message = welcome_message.strip() or DEFAULT_WELCOME_MESSAGE
        self.avatar_url = avatar_url.strip()
        self.primary_color = primary_color.strip() or DEFAULT_PRIMARY_COLOR

    def build_system_prompt(self) -> str:
        """Build the full system prompt from the current settings."""
        return (
            f"You are {self.name}, the library assistant chatbot. "
            f"{self.personality} "
            f"{self.limitations} "
            "This is an academic library with textbooks and research materials."
        )

    def get_welcome_text(self) -> str:
        """Return the welcome message with the AI name substituted."""
        return self.welcome_message.replace("{name}", self.name)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "personality": self.personality,
            "limitations": self.limitations,
            "welcome_message": self.welcome_message,
            "avatar_url": self.avatar_url,
            "primary_color": self.primary_color,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AiSettings":
        return cls(
            name=data.get("name", DEFAULT_AI_NAME),
            personality=data.get("personality", DEFAULT_PERSONALITY),
            limitations=data.get("limitations", DEFAULT_LIMITATIONS),
            welcome_message=data.get("welcome_message", DEFAULT_WELCOME_MESSAGE),
            avatar_url=data.get("avatar_url", DEFAULT_AVATAR_URL),
            primary_color=data.get("primary_color", DEFAULT_PRIMARY_COLOR),
        )


def load_ai_settings(staff_store) -> AiSettings:
    """Load AI settings from the database, falling back to defaults."""
    if staff_store is None:
        return AiSettings()
    try:
        raw = staff_store.get_setting(SETTINGS_KEY)
        if raw:
            data = json.loads(raw)
            # Migrate legacy welcome messages to the new default
            saved_welcome = data.get("welcome_message", "").strip()
            if saved_welcome in [m.strip() for m in _LEGACY_WELCOME_MESSAGES]:
                data["welcome_message"] = DEFAULT_WELCOME_MESSAGE
                save_ai_settings(staff_store, AiSettings.from_dict(data))
            return AiSettings.from_dict(data)
    except Exception:
        logger.warning("Failed to load AI settings from DB, using defaults")
    return AiSettings()


def save_ai_settings(staff_store, settings: AiSettings) -> None:
    """Persist AI settings to the database."""
    if staff_store is None:
        return
    staff_store.update_settings({SETTINGS_KEY: json.dumps(settings.to_dict(), ensure_ascii=False)})
