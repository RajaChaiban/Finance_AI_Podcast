"""
Market Pulse Telegram Bot

Send a message, get a podcast back.

Commands:
  /start          - Welcome message with usage instructions
  /podcast        - Generate with default categories (Finance Macro + Micro)
  /podcast crypto - Generate crypto-only episode
  /podcast crypto geopolitics ai_updates - Multiple categories
  /categories     - List available categories

Setup:
  1. Message @BotFather on Telegram → /newbot → get your token
  2. Add TELEGRAM_BOT_TOKEN=your_token to .env
  3. Add ALLOWED_CHAT_IDS=123456789,987654321 to .env (comma-separated Telegram
     chat/user IDs allowed to use the bot). With no value set, the bot rejects
     every request — generation is expensive (Gemini + Kokoro), don't run open.
     To find your ID: message the bot once and check the server logs for the
     refused chat ID, or use @userinfobot.
  4. Run: python telegram_bot.py
"""

import os
import asyncio
import traceback
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from src.data.categories import (
    PodcastCategory, CATEGORY_LABELS, CATEGORY_DESCRIPTIONS, DEFAULT_CATEGORIES,
)
from src.data.collector_router import CategoryCollectorRouter
from src.data.models import MarketSnapshot
from src.script.generator import ScriptGenerator
from src.audio.kokoro_engine import KokoroEngine
from src.audio.processor import AudioProcessor
from src.utils.logger import log

import yaml

# ── Config ───────────────────────────────────────────────────

load_dotenv()


def _parse_allowed_chat_ids() -> set[int]:
    raw = os.getenv("ALLOWED_CHAT_IDS", "").strip()
    if not raw:
        return set()
    ids: set[int] = set()
    for tok in raw.split(","):
        tok = tok.strip()
        if not tok:
            continue
        try:
            ids.add(int(tok))
        except ValueError:
            log.warning(f"Ignoring non-integer ALLOWED_CHAT_IDS entry: {tok!r}")
    return ids


ALLOWED_CHAT_IDS: set[int] = _parse_allowed_chat_ids()

# Single in-flight pipeline at a time. Loading Kokoro twice would OOM the box
# and overlapping Gemini calls would race the same output filename.
_pipeline_lock = asyncio.Lock()


def load_config() -> dict:
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    config["gemini_api_key"] = os.getenv("GEMINI_API_KEY", "")
    config["gnews_api_key"] = os.getenv("GNEWS_API_KEY", "")
    config["newsdata_api_key"] = os.getenv("NEWSDATA_API_KEY", "")
    config["currents_api_key"] = os.getenv("CURRENTS_API_KEY", "")
    return config


VALID_CATEGORIES = {c.value: c for c in PodcastCategory}


class InvalidCategoryError(ValueError):
    """Raised when /podcast is given an unknown category name."""

    def __init__(self, bad_arg: str):
        super().__init__(f"Unknown category: {bad_arg!r}")
        self.bad_arg = bad_arg


def parse_categories(args: list[str]) -> list[PodcastCategory]:
    """Parse category names from command arguments. Raises on invalid input."""
    if not args:
        return list(DEFAULT_CATEGORIES)

    categories = []
    for arg in args:
        arg = arg.lower().strip()
        # Support shorthand aliases
        aliases = {
            "macro": "finance_macro",
            "micro": "finance_micro",
            "finance": "finance_macro",
            "geo": "geopolitics",
            "ai": "ai_updates",
        }
        resolved = aliases.get(arg, arg)
        if resolved in VALID_CATEGORIES:
            categories.append(VALID_CATEGORIES[resolved])
        else:
            raise InvalidCategoryError(arg)

    return categories if categories else list(DEFAULT_CATEGORIES)


# ── Pipeline ─────────────────────────────────────────────────

class PipelineConfigError(RuntimeError):
    """Raised when the bot can't run because configuration is incomplete."""


def run_pipeline_sync(categories: list[PodcastCategory]) -> str:
    """Run the full podcast pipeline synchronously. Returns MP3 path.

    Raises PipelineConfigError if config is incomplete; lets pipeline runtime
    exceptions propagate so the caller can show the traceback.
    """
    config = load_config()
    date = datetime.now().strftime("%Y-%m-%d")
    output_dir = config.get("output_dir", "output")
    os.makedirs(output_dir, exist_ok=True)

    # Stage 1: Data
    log.info("Bot pipeline: collecting data...")
    router = CategoryCollectorRouter(config, categories)
    snapshot = router.collect_all()
    snapshot.save(os.path.join(output_dir, f"{date}-snapshot.json"))

    # Stage 2: Script
    log.info("Bot pipeline: generating script...")
    api_key = config["gemini_api_key"]
    if not api_key or api_key == "your_gemini_key_here":
        raise PipelineConfigError(
            "GEMINI_API_KEY is not set. Add it to .env and restart the bot."
        )

    generator = ScriptGenerator(api_key=api_key, model=config.get("gemini_model", "gemini-2.5-flash"))
    script = generator.generate(snapshot, categories)
    word_count = len(script.split())
    log.info(f"Bot pipeline: script ready ({word_count} words)")

    # Stage 3: Audio
    log.info("Bot pipeline: generating audio...")
    engine = KokoroEngine(
        voice_s1=config.get("speaker_1_voice", "am_adam"),
        voice_s2=config.get("speaker_2_voice", "af_bella"),
    )
    audio, sample_rate = engine.generate_audio(script, sample_rate=config.get("sample_rate", 24000))

    processor = AudioProcessor(output_dir=output_dir)
    mp3_path = processor.save_mp3(
        audio=audio,
        sample_rate=sample_rate,
        date=date,
        podcast_name=config.get("podcast_name", "Market Pulse"),
    )

    log.info(f"Bot pipeline: episode saved to {mp3_path}")
    return mp3_path


# ── Telegram Handlers ────────────────────────────────────────

def _is_authorized(update: Update) -> bool:
    """Allow-list check. With ALLOWED_CHAT_IDS empty, deny all."""
    chat = update.effective_chat
    user = update.effective_user
    chat_id = chat.id if chat else None
    user_id = user.id if user else None
    if chat_id in ALLOWED_CHAT_IDS or user_id in ALLOWED_CHAT_IDS:
        return True
    log.warning(
        f"Refused unauthorized request — chat_id={chat_id}, user_id={user_id}. "
        f"Add to ALLOWED_CHAT_IDS in .env to allow."
    )
    return False


async def _reject(update: Update) -> None:
    if update.message:
        await update.message.reply_text(
            "Sorry, this bot is private. Ask the operator to add your Telegram "
            "ID to ALLOWED_CHAT_IDS."
        )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    if not _is_authorized(update):
        await _reject(update)
        return
    cat_list = "\n".join(
        f"  `{c.value}` — {CATEGORY_DESCRIPTIONS[c]}"
        for c in PodcastCategory
    )
    await update.message.reply_text(
        f"*Market Pulse Podcast Bot*\n\n"
        f"Generate a podcast episode on demand\\.\n\n"
        f"*Usage:*\n"
        f"`/podcast` — Default \\(Finance Macro \\+ Micro\\)\n"
        f"`/podcast crypto` — Single category\n"
        f"`/podcast crypto geopolitics` — Multiple categories\n\n"
        f"*Shortcuts:* `macro`, `micro`, `crypto`, `geo`, `ai`\n\n"
        f"`/categories` — List all categories",
        parse_mode="MarkdownV2",
    )


async def cmd_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /categories command."""
    if not _is_authorized(update):
        await _reject(update)
        return
    lines = []
    for c in PodcastCategory:
        lines.append(f"  {CATEGORY_LABELS[c]}: {CATEGORY_DESCRIPTIONS[c]}")
    await update.message.reply_text(
        "Available categories:\n\n" + "\n".join(lines)
    )


async def cmd_podcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /podcast command — generate and send episode."""
    if not _is_authorized(update):
        await _reject(update)
        return

    try:
        categories = parse_categories(context.args)
    except InvalidCategoryError as e:
        valid = ", ".join(VALID_CATEGORIES.keys())
        await update.message.reply_text(
            f"Invalid category {e.bad_arg!r}. Valid options: {valid}\n\n"
            f"Shortcuts: macro, micro, crypto, geo, ai"
        )
        return

    if _pipeline_lock.locked():
        await update.message.reply_text(
            "A podcast is already being generated. Wait for it to finish, then try again."
        )
        return

    cat_names = ", ".join(CATEGORY_LABELS[c] for c in categories)
    status_msg = await update.message.reply_text(
        f"Generating podcast for: {cat_names}\n\n"
        f"Stage 1/3: Collecting data...\n"
        f"This takes a few minutes. I'll send the audio when it's ready."
    )

    async with _pipeline_lock:
        loop = asyncio.get_event_loop()
        try:
            mp3_path = await loop.run_in_executor(None, run_pipeline_sync, categories)
        except PipelineConfigError as e:
            log.warning(f"Pipeline config error: {e}")
            await status_msg.edit_text(f"Configuration error: {e}")
            return
        except Exception as e:
            log.warning(f"Pipeline failed: {e}\n{traceback.format_exc()}")
            # Keep the user message short; full traceback stays in server logs.
            await status_msg.edit_text(
                f"Failed to generate episode: {type(e).__name__}: {e}\n"
                "Full traceback is in the server logs."
            )
            return

    if mp3_path and os.path.exists(mp3_path):
        file_size_mb = os.path.getsize(mp3_path) / (1024 * 1024)
        await status_msg.edit_text(f"Done! Sending {file_size_mb:.1f} MB episode...")
        with open(mp3_path, "rb") as f:
            await update.message.reply_audio(
                audio=f,
                title=f"Market Pulse — {cat_names}",
                performer="Market Pulse AI",
                caption=f"Categories: {cat_names}",
            )
        await status_msg.delete()
    else:
        await status_msg.edit_text(
            "Pipeline finished but no MP3 was produced. Check server logs."
        )


# ── Main ─────────────────────────────────────────────────────

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("Error: Set TELEGRAM_BOT_TOKEN in your .env file.")
        print("Get a token from @BotFather on Telegram: https://t.me/BotFather")
        return

    if not ALLOWED_CHAT_IDS:
        log.warning(
            "ALLOWED_CHAT_IDS is empty — every request will be refused. "
            "Set it in .env to allow specific Telegram chat/user IDs."
        )

    log.info("Starting Market Pulse Telegram bot...")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("categories", cmd_categories))
    app.add_handler(CommandHandler("podcast", cmd_podcast))

    log.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
