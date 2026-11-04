"""
Outgoing email (password reset links) over plain SMTP.

Works with any SMTP provider, including free ones such as a Gmail account with an
app password. If SMTP_HOST is not configured, the reset link is written to the
server log instead so the feature still works during development.
"""

import logging
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import quote

from ..core.config import settings

logger = logging.getLogger(__name__)


def is_email_configured() -> bool:
    return bool(settings.SMTP_HOST)


def build_reset_link(raw_token: str) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={quote(raw_token, safe='')}"


def send_password_reset_email(to_email: str, display_name: str, reset_link: str) -> None:
    """Sends the reset email. Never raises: failures are logged so the request still succeeds."""
    if not is_email_configured():
        logger.warning(
            "SMTP is not configured, so no email was sent. Password reset link for %s: %s",
            to_email,
            reset_link,
        )
        return

    sender = settings.SMTP_FROM or settings.SMTP_USER or "no-reply@pledge-fighter.local"
    message = EmailMessage()
    message["Subject"] = "Reset your Pledge Fighter password"
    message["From"] = sender
    message["To"] = to_email
    message.set_content(
        f"Hi {display_name},\n\n"
        "We received a request to reset your Pledge Fighter password.\n"
        f"Open this link to choose a new password (valid for {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes):\n\n"
        f"{reset_link}\n\n"
        "If you did not ask for this, you can ignore this email. Your password will not change.\n"
    )

    try:
        context = ssl.create_default_context()
        if settings.SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15, context=context)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            if settings.SMTP_USE_TLS:
                server.starttls(context=context)
        with server:
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
    except Exception:
        logger.exception("Failed to send password reset email to %s", to_email)
