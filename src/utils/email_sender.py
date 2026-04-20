import re
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from src.utils.logger import log


# Plain email regex — enough to block header-injection via CR/LF and catch
# the common malformed inputs. The MIME library isn't strict about these, so
# a recipient like "x@y.com\r\nBcc: evil@x.com" would otherwise slip through.
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _is_valid_email(addr: str) -> bool:
    if not addr or not isinstance(addr, str):
        return False
    if "\r" in addr or "\n" in addr:
        return False
    return bool(_EMAIL_RE.match(addr))


def send_episode_email(
    mp3_path: str,
    recipient: str,
    subject: str = None,
    body: str = None,
    sender_email: str = None,
    sender_password: str = None,
    categories: list[str] = None,
) -> bool:
    """Send a podcast episode MP3 via Gmail.

    Args:
        mp3_path: Path to the MP3 file.
        recipient: Recipient email address.
        subject: Email subject (auto-generated if None).
        body: Email body text (auto-generated if None).
        sender_email: Gmail address (reads EMAIL_ADDRESS env if None).
        sender_password: Gmail App Password (reads EMAIL_APP_PASSWORD env if None).
        categories: List of category names for the auto-generated body.

    Returns:
        True if sent successfully, False otherwise.
    """
    sender_email = sender_email or os.getenv("EMAIL_ADDRESS", "")
    sender_password = sender_password or os.getenv("EMAIL_APP_PASSWORD", "")

    if not sender_email or not sender_password:
        log.warning("Email not configured: set EMAIL_ADDRESS and EMAIL_APP_PASSWORD in .env")
        return False

    if not _is_valid_email(recipient):
        log.warning(f"Rejected invalid recipient address: {recipient!r}")
        return False
    if not _is_valid_email(sender_email):
        log.warning(f"Rejected invalid sender address: {sender_email!r}")
        return False

    has_attachment = bool(mp3_path) and os.path.exists(mp3_path)
    if mp3_path and not has_attachment:
        log.warning(f"MP3 file not found: {mp3_path}")
        return False

    if has_attachment:
        filename = os.path.basename(mp3_path)
        file_size_mb = os.path.getsize(mp3_path) / (1024 * 1024)
    else:
        filename = ""
        file_size_mb = 0.0

    if subject is None:
        subject = f"Market Pulse - {filename.replace('.mp3', '').replace('-', ' ').title()}"

    if body is None:
        cat_text = ", ".join(categories) if categories else "all topics"
        body = (
            f"Your Market Pulse podcast episode is ready!\n\n"
            f"Categories: {cat_text}\n"
            f"File: {filename} ({file_size_mb:.1f} MB)\n\n"
            f"-- Market Pulse Podcast Generator"
        )

    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        if has_attachment:
            with open(mp3_path, "rb") as f:
                part = MIMEBase("audio", "mpeg")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={filename}")
                msg.attach(part)

        log.info(f"Sending episode to {recipient} ({file_size_mb:.1f} MB)...")

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        log.info(f"Episode sent to {recipient}")
        return True

    except smtplib.SMTPAuthenticationError:
        log.warning("Email auth failed. Check EMAIL_ADDRESS and EMAIL_APP_PASSWORD in .env. "
                     "Use a Gmail App Password, not your regular password: "
                     "https://myaccount.google.com/apppasswords")
        return False
    except Exception as e:
        log.warning(f"Failed to send email: {e}")
        return False
