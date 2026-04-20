"""Send a short failure alert via email and Telegram.

Called from the GitHub Actions failure path. Best-effort on both channels:
a crash in one sender must not block the other, and the function itself
never raises — the workflow run status is the last line of defense.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from telegram import Bot

from src.utils.email_sender import send_episode_email
from src.utils.logger import log


def notify_failure(
    error_summary: str,
    log_tail: str,
    run_url: str,
    recipient_email: Optional[str] = None,
    telegram_chat_id: Optional[str] = None,
    telegram_bot_token: Optional[str] = None,
    email_sender: Optional[str] = None,
    email_password: Optional[str] = None,
) -> None:
    """Send a failure alert on both channels. Never raises."""
    subject = f"[Market Pulse FAILED] {error_summary}"
    body = (
        f"The scheduled Market Pulse run failed.\n\n"
        f"Error: {error_summary}\n\n"
        f"Run: {run_url}\n\n"
        f"Last log lines:\n"
        f"{'-' * 60}\n"
        f"{log_tail}\n"
        f"{'-' * 60}\n"
    )

    if recipient_email:
        try:
            send_episode_email(
                mp3_path="",
                recipient=recipient_email,
                subject=subject,
                body=body,
                sender_email=email_sender,
                sender_password=email_password,
            )
        except Exception as e:
            log.warning(f"notify_failure: email channel raised: {type(e).__name__}: {e}")

    if telegram_chat_id and telegram_bot_token:
        try:
            async def _send_alert():
                bot = Bot(token=telegram_bot_token)
                text = f"{subject}\n\n{body}"
                if len(text) > 4000:
                    text = text[:3997] + "..."
                await bot.send_message(chat_id=int(str(telegram_chat_id).strip()), text=text)

            asyncio.run(_send_alert())
            log.info(f"Failure alert sent to Telegram chat {telegram_chat_id}")
        except Exception as e:
            log.warning(f"notify_failure: telegram channel raised: {type(e).__name__}: {e}")


if __name__ == "__main__":
    import os
    import sys

    run_url = os.getenv("GITHUB_RUN_URL", "(no run url)")
    error_summary = os.getenv("FAILURE_SUMMARY", "Scheduled run failed")
    log_tail = sys.stdin.read() if not sys.stdin.isatty() else "(no log tail piped)"

    notify_failure(
        error_summary=error_summary,
        log_tail=log_tail,
        run_url=run_url,
        recipient_email=os.getenv("EMAIL_ADDRESS"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        email_sender=os.getenv("EMAIL_ADDRESS"),
        email_password=os.getenv("EMAIL_APP_PASSWORD"),
    )
