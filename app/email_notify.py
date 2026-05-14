"""Notification for librarian handoff — supports Gmail service account, SMTP, and ntfy.sh."""

import base64
import json
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gmail API via service account (domain-wide delegation)
# ---------------------------------------------------------------------------

_gmail_service = None


def _get_gmail_service():
    """Build and cache a Gmail API service using a service account."""
    global _gmail_service
    if _gmail_service is not None:
        return _gmail_service

    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    creds_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "")
    delegate_email = os.environ.get("SMTP_EMAIL", "")

    if not delegate_email:
        return None

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

        if creds_json:
            info = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        elif creds_file and os.path.exists(creds_file):
            credentials = service_account.Credentials.from_service_account_file(creds_file, scopes=SCOPES)
        else:
            return None

        # Delegate to the actual sender email (must be in the same Google Workspace)
        delegated = credentials.with_subject(delegate_email)
        _gmail_service = build("gmail", "v1", credentials=delegated, cache_discovery=False)
        logger.info("Gmail API service account initialised (delegating to %s)", delegate_email)
        return _gmail_service
    except Exception:
        logger.exception("Failed to initialise Gmail service account")
        return None


def _use_service_account() -> bool:
    """Check if service account credentials are configured."""
    return bool(
        os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
        or os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    )


def _send_via_service_account(msg: MIMEMultipart) -> bool:
    """Send an email using the Gmail API with service account credentials."""
    service = _get_gmail_service()
    if service is None:
        return False
    try:
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
        return True
    except Exception:
        logger.exception("Failed to send email via Gmail API service account")
        return False


def _send_via_smtp(smtp_email: str, smtp_password: str, msg: MIMEMultipart) -> bool:
    """Send an email using Gmail SMTP with app password."""
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
        return True
    except Exception:
        logger.exception("Failed to send email via SMTP")
        return False


def _send_email(smtp_email: str, smtp_password: str, msg: MIMEMultipart) -> bool:
    """Send email — tries service account first, falls back to SMTP."""
    if _use_service_account():
        return _send_via_service_account(msg)
    if smtp_email and smtp_password:
        return _send_via_smtp(smtp_email, smtp_password, msg)
    logger.warning("No email credentials configured (neither service account nor SMTP)")
    return False


def _build_chat_link(admin_url: str, session_id: str, staff_name: str = "") -> str:
    """Build a live chat queue URL so librarians see all waiting sessions first.

    The session_id is no longer used to jump directly into a specific chat —
    librarians should pick from the queue so they can see what is already
    being handled by colleagues.
    """
    from urllib.parse import quote
    link = f"{admin_url}/chat/"
    if staff_name:
        link += f"?name={quote(staff_name)}"
    return link


# ---------------------------------------------------------------------------
# Email builders
# ---------------------------------------------------------------------------

def send_handoff_email(
    smtp_email: str,
    smtp_password: str,
    librarian_email: str,
    session_id: str,
    admin_url: str,
) -> bool:
    """Send a handoff notification email."""
    chat_link = _build_chat_link(admin_url, session_id)
    subject = "📚 A patron wants to ask a librarian"

    html_body = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:480px;margin:0 auto;padding:20px">
      <div style="background:#2c3e50;color:#fff;padding:16px 20px;border-radius:8px 8px 0 0;text-align:center">
        <h2 style="margin:0;font-size:1.1rem">📚 Librarian Needed</h2>
      </div>
      <div style="background:#fff;border:1px solid #ecf0f1;border-top:none;padding:24px 20px;border-radius:0 0 8px 8px">
        <p style="color:#333;font-size:0.95rem;margin:0 0 16px">A patron is waiting to chat with a librarian.</p>
        <p style="color:#555;font-size:0.88rem;margin:0 0 20px">Open the live chat queue to see all waiting patrons and pick up the ones that haven't been claimed yet.</p>
        <div style="text-align:center;margin:20px 0">
          <a href="{chat_link}" style="display:inline-block;background:#2c3e50;color:#fff;text-decoration:none;padding:12px 28px;border-radius:6px;font-size:0.95rem;font-weight:600">
            📋 View Live Chat Queue
          </a>
        </div>
        <p style="color:#bdc3c7;font-size:0.78rem;text-align:center;margin:16px 0 0">— Lorma Library Chatbot</p>
      </div>
    </div>
    """

    plain_body = (
        f"A patron has requested to speak with a librarian.\n\n"
        f"Open the live chat queue to see all waiting patrons and pick up unclaimed sessions:\n{chat_link}\n\n"
        f"— Lorma Library Chatbot"
    )

    sender = smtp_email or os.environ.get("SMTP_EMAIL", "noreply@example.com")
    msg = MIMEMultipart("alternative")
    msg["From"] = f"Lorma Library Chatbot <{sender}>"
    msg["To"] = librarian_email
    msg["Subject"] = subject
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    ok = _send_email(smtp_email, smtp_password, msg)
    if ok:
        logger.info("Handoff email sent for session %s", session_id)
    return ok


def send_staff_notify_email(
    smtp_email: str,
    smtp_password: str,
    recipient_email: str,
    staff_name: str,
    session_id: str,
    admin_url: str,
) -> bool:
    """Send a personalized notification email to a specific librarian."""
    chat_link = _build_chat_link(admin_url, session_id, staff_name) if session_id else f"{admin_url}/chat/"
    subject = f"📚 {staff_name}, a patron needs your help"

    html_body = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:480px;margin:0 auto;padding:20px">
      <div style="background:#2c3e50;color:#fff;padding:16px 20px;border-radius:8px 8px 0 0;text-align:center">
        <h2 style="margin:0;font-size:1.1rem">📚 Librarian Needed</h2>
      </div>
      <div style="background:#fff;border:1px solid #ecf0f1;border-top:none;padding:24px 20px;border-radius:0 0 8px 8px">
        <p style="color:#333;font-size:0.95rem;margin:0 0 16px">Hi <strong>{staff_name}</strong>, a patron is waiting to chat with a librarian.</p>
        <p style="color:#555;font-size:0.88rem;margin:0 0 20px">Open the live chat queue to see all waiting patrons and pick up the ones that haven't been claimed yet.</p>
        <div style="text-align:center;margin:20px 0">
          <a href="{chat_link}" style="display:inline-block;background:#2c3e50;color:#fff;text-decoration:none;padding:12px 28px;border-radius:6px;font-size:0.95rem;font-weight:600">
            📋 View Live Chat Queue
          </a>
        </div>
        <p style="color:#bdc3c7;font-size:0.78rem;text-align:center;margin:16px 0 0">— Lorma Library Chatbot</p>
      </div>
    </div>
    """

    plain_body = f"Hi {staff_name},\n\nA patron is waiting to chat with a librarian.\n"
    plain_body += f"\nOpen the live chat queue to see all waiting patrons and pick up unclaimed sessions:\n{chat_link}\n\n— Lorma Library Chatbot"

    sender = smtp_email or os.environ.get("SMTP_EMAIL", "noreply@example.com")
    msg = MIMEMultipart("alternative")
    msg["From"] = f"Lorma Library Chatbot <{sender}>"
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    ok = _send_email(smtp_email, smtp_password, msg)
    if ok:
        logger.info("Staff notification sent to %s (%s)", staff_name, recipient_email)
    return ok


def send_claimed_email(
    smtp_email: str,
    smtp_password: str,
    recipient_email: str,
    staff_name: str,
    claimed_by: str,
    session_id: str,
    display_name: str = "",
    waiting_sessions: list | None = None,
    admin_url: str = "",
) -> bool:
    """Notify a librarian that another librarian has already claimed the session."""
    patron_label = display_name or (session_id[:16] + "…" if session_id else "Unknown")
    subject = f"📚 {patron_label} is already being helped by {claimed_by}"

    # Build waiting sessions block
    waiting_html = ""
    waiting_plain = ""
    if waiting_sessions:
        rows_html = "".join(
            f'<tr><td style="padding:6px 10px;border-bottom:1px solid #ecf0f1">{w["display_name"] or w["session_id"][:16] + "…"}</td>'
            f'<td style="padding:6px 10px;border-bottom:1px solid #ecf0f1;text-align:center">{w["message_count"]} msgs</td>'
            f'<td style="padding:6px 10px;border-bottom:1px solid #ecf0f1;text-align:center">'
            f'{"<span style=\'color:#e67e22\'>Waiting</span>" if not w["staff_username"] else "<span style=\'color:#27ae60\'>" + w["staff_username"] + "</span>"}'
            f'</td></tr>'
            for w in waiting_sessions
        )
        waiting_html = f"""
        <div style="margin-top:20px;border-top:1px solid #ecf0f1;padding-top:16px">
          <p style="color:#555;font-size:0.88rem;margin:0 0 10px;font-weight:600">Other sessions still in queue:</p>
          <table style="width:100%;border-collapse:collapse;font-size:0.85rem">
            <thead>
              <tr style="background:#f4f6f9">
                <th style="padding:6px 10px;text-align:left;color:#7f8c8d;font-weight:600">Patron</th>
                <th style="padding:6px 10px;text-align:center;color:#7f8c8d;font-weight:600">Msgs</th>
                <th style="padding:6px 10px;text-align:center;color:#7f8c8d;font-weight:600">Status</th>
              </tr>
            </thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>"""
        waiting_plain = "\n\nOther sessions still in queue:\n" + "\n".join(
            f"  • {w['display_name'] or w['session_id'][:16] + '…'} — "
            f"{'Waiting' if not w['staff_username'] else 'With ' + w['staff_username']}"
            for w in waiting_sessions
        )

    # Include staff name in the queue link so they auto-join without typing
    # No session param — this opens the queue picker, not a specific session
    from urllib.parse import quote as _quote
    if admin_url and staff_name:
        chat_link = f"{admin_url}/chat/?name={_quote(staff_name)}"
    elif admin_url:
        chat_link = f"{admin_url}/chat/"
    else:
        chat_link = ""

    join_btn = ""
    if chat_link:
        join_btn = f"""
        <div style="text-align:center;margin:20px 0">
          <a href="{chat_link}" style="display:inline-block;background:#2c3e50;color:#fff;text-decoration:none;padding:12px 28px;border-radius:6px;font-size:0.95rem;font-weight:600">
            💬 View Live Chat Queue
          </a>
        </div>"""

    html_body = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:520px;margin:0 auto;padding:20px">
      <div style="background:#27ae60;color:#fff;padding:16px 20px;border-radius:8px 8px 0 0;text-align:center">
        <h2 style="margin:0;font-size:1.1rem">✅ Patron Being Helped</h2>
      </div>
      <div style="background:#fff;border:1px solid #ecf0f1;border-top:none;padding:24px 20px;border-radius:0 0 8px 8px">
        <p style="color:#333;font-size:0.95rem;margin:0 0 12px">Hi <strong>{staff_name}</strong>,</p>
        <p style="color:#333;font-size:0.95rem;margin:0 0 16px">
          <strong>{claimed_by}</strong> has already joined the chat with <strong>{patron_label}</strong> — no action needed for this session.
        </p>
        {waiting_html}
        {join_btn}
        <p style="color:#bdc3c7;font-size:0.78rem;text-align:center;margin:16px 0 0">— Lorma Library Chatbot</p>
      </div>
    </div>
    """

    plain_body = (
        f"Hi {staff_name},\n\n"
        f"{claimed_by} has already joined the chat with {patron_label} — no action needed for this session."
        f"{waiting_plain}\n\n— Lorma Library Chatbot"
    )

    sender = smtp_email or os.environ.get("SMTP_EMAIL", "noreply@example.com")
    msg = MIMEMultipart("alternative")
    msg["From"] = f"Lorma Library Chatbot <{sender}>"
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    ok = _send_email(smtp_email, smtp_password, msg)
    if ok:
        logger.info("Claimed notification sent to %s (%s) — claimed by %s", staff_name, recipient_email, claimed_by)
    return ok


def send_ntfy_notification(
    ntfy_topic: str,
    session_id: str,
    admin_url: str,
) -> bool:
    """Send a push notification via ntfy.sh."""
    chat_link = _build_chat_link(admin_url, session_id)
    try:
        httpx.post(
            f"https://ntfy.sh/{ntfy_topic}",
            headers={
                "Title": "📚 Patron wants to talk to a librarian",
                "Click": chat_link,
                "Tags": "books,speech_balloon",
            },
            content="A patron is waiting for help. Tap to open the live chat queue and pick up unclaimed sessions.",
            timeout=10.0,
        )
        logger.info("ntfy notification sent for session %s", session_id)
        return True
    except Exception:
        logger.exception("Failed to send ntfy notification for session %s", session_id)
        return False
