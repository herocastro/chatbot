"""Ably real-time publish helper.

Publishes messages to Ably channels so browsers receive them instantly
via WebSocket instead of waiting for the next poll interval.

Channel naming:
  live-chat:{live_chat_id}  — messages for a specific live chat session
  handoff-queue             — new handoff requests (for librarian dashboard)
"""

import logging
import os

import httpx

logger = logging.getLogger(__name__)

_ABLY_API_KEY = os.environ.get("ABLY_API_KEY", "")
_ABLY_REST_URL = "https://rest.ably.io/channels/{channel}/messages"


def _get_key() -> str:
    return os.environ.get("ABLY_API_KEY", _ABLY_API_KEY)


def publish(channel: str, event: str, data: dict) -> bool:
    """Publish a single event to an Ably channel via the REST API.

    Returns True on success, False on failure (non-fatal — polling is the fallback).
    """
    key = _get_key()
    if not key:
        return False
    try:
        url = _ABLY_REST_URL.format(channel=channel)
        resp = httpx.post(
            url,
            json={"name": event, "data": data},
            auth=tuple(key.split(":", 1)),  # key_id:key_secret
            timeout=5.0,
        )
        if resp.status_code not in (200, 201):
            logger.warning("Ably publish failed: %s %s", resp.status_code, resp.text[:200])
            return False
        return True
    except Exception:
        logger.warning("Ably publish error (non-fatal)", exc_info=True)
        return False


def publish_live_chat_message(live_chat_id: str, role: str, content: str,
                               timestamp: float, msg_id: int | None = None) -> bool:
    """Publish a new live chat message to the channel for that session."""
    return publish(
        channel=f"live-chat:{live_chat_id}",
        event="message",
        data={
            "id": msg_id,
            "role": role,
            "content": content,
            "timestamp": timestamp,
        },
    )


def publish_handoff_status(live_chat_id: str, parent_session_id: str, status: str,
                            staff_username: str | None = None) -> bool:
    """Publish a handoff status change (claimed, ended, etc.)."""
    return publish(
        channel=f"live-chat:{live_chat_id}",
        event="status",
        data={
            "live_chat_id": live_chat_id,
            "parent_session_id": parent_session_id,
            "status": status,
            "staff_username": staff_username,
        },
    )


def publish_new_handoff(live_chat_id: str, parent_session_id: str,
                         display_name: str = "") -> bool:
    """Notify the librarian dashboard that a new patron is waiting."""
    return publish(
        channel="handoff-queue",
        event="new-request",
        data={
            "live_chat_id": live_chat_id,
            "parent_session_id": parent_session_id,
            "display_name": display_name,
        },
    )
