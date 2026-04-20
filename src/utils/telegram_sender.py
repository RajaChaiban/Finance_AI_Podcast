"""Push a podcast MP3 to a single Telegram chat via the Bot API.

Mirrors `src/utils/email_sender.py` in posture: returns a bool, logs a
warning on failure, never raises. Intended for the scheduled/automated
pipeline; the reactive `telegram_bot.py` stays untouched.
"""

from __future__ import annotations

import asyncio
import os
from typing import Optional

from telegram import Bot

from src.utils.logger import log


def _is_valid_chat_id(val) -> bool:
    """Chat IDs are integers (positive for users, negative for groups/channels).

    Accept int or a string that parses cleanly to a non-zero int. Reject
    empty strings, non-numeric text, whitespace, and zero (not a valid chat).
    """
    if val is None:
        return False
    if isinstance(val, bool):
        return False
    if isinstance(val, int):
        return val != 0
    if isinstance(val, str):
        if "\r" in val or "\n" in val:
            return False
        s = val.strip()
        if not s or any(c.isspace() for c in s):
            return False
        try:
            return int(s) != 0
        except ValueError:
            return False
    return False


async def _send_audio_async(bot_token: str, chat_id: int, mp3_path: str,
                            title: str, caption: str) -> None:
    bot = Bot(token=bot_token)
    with open(mp3_path, "rb") as f:
        await bot.send_audio(
            chat_id=chat_id,
            audio=f,
            title=title,
            performer="Market Pulse AI",
            caption=caption,
        )


def send_episode_telegram(
    mp3_path: str,
    chat_id,
    bot_token: Optional[str] = None,
    categories: Optional[list[str]] = None,
) -> bool:
    """Send an MP3 episode to a Telegram chat. Returns True on success."""
    bot_token = bot_token if bot_token is not None else os.getenv("TELEGRAM_BOT_TOKEN", "")

    if not bot_token:
        log.warning("Telegram not configured: set TELEGRAM_BOT_TOKEN in .env")
        return False
    if not _is_valid_chat_id(chat_id):
        log.warning(f"Rejected invalid Telegram chat_id: {chat_id!r}")
        return False
    if not os.path.exists(mp3_path):
        log.warning(f"MP3 file not found: {mp3_path}")
        return False

    chat_id_int = int(str(chat_id).strip())
    filename = os.path.basename(mp3_path)
    file_size_mb = os.path.getsize(mp3_path) / (1024 * 1024)

    if file_size_mb > 50:
        log.warning(
            f"MP3 exceeds Telegram bot upload limit: {file_size_mb:.1f} MB > 50 MB ({filename})"
        )
        return False

    cat_text = ", ".join(categories) if categories else "all topics"
    title = f"Market Pulse - {filename.replace('.mp3', '').replace('-', ' ').title()}"
    caption = f"Categories: {cat_text}"

    try:
        log.info(f"Sending episode to Telegram chat {chat_id_int} ({file_size_mb:.1f} MB)...")
        asyncio.run(_send_audio_async(bot_token, chat_id_int, mp3_path, title, caption))
        log.info(f"Episode sent to Telegram chat {chat_id_int}")
        return True
    except Exception as e:
        log.warning(f"Failed to send Telegram: {type(e).__name__}: {e}")
        return False
