import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings
from app.services.notifications.email_sender import EmailSender

logger = logging.getLogger(__name__)


def deliver(sender: EmailSender, *, to: str, subject: str, text: str, html: str) -> bool:
    """Send one email; returns False instead of raising when the SMTP server fails."""
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = get_settings().mail_from
    message["To"] = to
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    try:
        sender.send(message)
    except (smtplib.SMTPException, OSError):
        logger.warning("Could not send '%s' to %s", subject, to, exc_info=True)
        return False
    return True
