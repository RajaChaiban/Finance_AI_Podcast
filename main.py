import os
import json
from datetime import datetime

import click
import yaml
from dotenv import load_dotenv

from src.data.categories import PodcastCategory, DEFAULT_CATEGORIES
from src.data.collector_router import CategoryCollectorRouter
from src.data.models import MarketSnapshot
from src.script.generator import ScriptGenerator
from src.script.length import LENGTH_PRESETS
from src.audio.kokoro_engine import KokoroEngine
from src.audio.processor import AudioProcessor
from src.utils.logger import log
from src.utils.email_sender import send_episode_email
from src.utils.telegram_sender import send_episode_telegram


def load_config() -> dict:
    load_dotenv()
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    config["gemini_api_key"] = os.getenv("GEMINI_API_KEY", "")
    config["fred_api_key"] = os.getenv("FRED_API_KEY", "")
    config["gnews_api_key"] = os.getenv("GNEWS_API_KEY", "")
    config["currents_api_key"] = os.getenv("CURRENTS_API_KEY", "")
    config["newsdata_api_key"] = os.getenv("NEWSDATA_API_KEY", "")
    # LLM provider switches (CLI uses .env; web UI overrides via DB).
    config["llm_provider"] = os.getenv("LLM_PROVIDER", config.get("llm_provider", "gemini"))
    config["ollama_model"] = os.getenv("OLLAMA_MODEL", config.get("ollama_model", "gemma4:26b"))
    config["ollama_base_url"] = os.getenv(
        "OLLAMA_BASE_URL", config.get("ollama_base_url", "http://localhost:11434")
    )
    return config


def collect_data(
    config: dict,
    categories: list[PodcastCategory],
    status_callback=None,
    cache_dir: str | None = None,
    force_refresh: bool = False,
) -> MarketSnapshot:
    log.info("=== STAGE 1: Data Collection ===")
    with CategoryCollectorRouter(config, categories) as router:
        snapshot = router.collect_all(
            status_callback=status_callback,
            cache_dir=cache_dir,
            force_refresh=force_refresh,
        )

    log.info(f"Snapshot: categories={[c.value for c in categories]}, "
             f"{len(snapshot.news)} news, {len(snapshot.top_gainers)} gainers, "
             f"{len(snapshot.top_losers)} losers, {len(snapshot.geopolitics)} geopolitics, "
             f"{len(snapshot.ai_updates)} AI updates")
    return snapshot


def generate_script(
    config: dict,
    snapshot: MarketSnapshot,
    categories: list[PodcastCategory],
    preset_key: str | None = None,
) -> str:
    from src.script.llm import build_provider

    log.info("=== STAGE 2: Script Generation ===")

    provider = build_provider(config)
    generator = ScriptGenerator(provider=provider)
    target_words = LENGTH_PRESETS[preset_key].target_words if preset_key else None
    script = generator.generate(
        snapshot,
        categories,
        target_words=target_words,
        preset_key=preset_key,
    )
    return script


def generate_audio(
    config: dict,
    script: str,
    date: str,
    voice_s1: str | None = None,
    voice_s2: str | None = None,
) -> str:
    log.info("=== STAGE 3: Audio Generation ===")

    tts_cfg = config.get("tts", {}) or {}
    engine = KokoroEngine(
        voice_s1=voice_s1 or config.get("speaker_1_voice", "am_adam"),
        voice_s2=voice_s2 or config.get("speaker_2_voice", "af_bella"),
        speed=tts_cfg.get("base_speed", 1.0),
        enable_blending=tts_cfg.get("enable_blending", True),
        enable_prosody=tts_cfg.get("enable_prosody", True),
    )
    audio, sample_rate = engine.generate_audio(script, sample_rate=config.get("sample_rate", 24000))

    processor = AudioProcessor(output_dir=config.get("output_dir", "output"))
    mp3_path = processor.save_mp3(
        audio=audio,
        sample_rate=sample_rate,
        date=date,
        podcast_name=config.get("podcast_name", "Market Pulse"),
    )
    return mp3_path


CATEGORY_CHOICES = [c.value for c in PodcastCategory]


@click.command()
@click.option("--stage", type=click.Choice(["data", "script", "audio", "all"]), default="all",
              help="Run a specific stage or the full pipeline")
@click.option("--date", default=None, help="Date override (YYYY-MM-DD)")
@click.option("--categories", "-c", multiple=True, type=click.Choice(CATEGORY_CHOICES),
              default=["finance_macro", "finance_micro"],
              help="Categories to include (repeatable, e.g. -c crypto -c geopolitics)")
@click.option("--email", "-e", default=None, help="Send episode to this email address after generation")
@click.option("--telegram-chat-id", default=None,
              help="Push episode to this Telegram chat ID after generation")
@click.option("--length-preset", type=click.Choice(list(LENGTH_PRESETS.keys())), default=None,
              help="Episode length preset (brief / standard / deep). Overrides default target length.")
@click.option("--no-cache", is_flag=True,
              help="Force re-fetch of data even if today's snapshot cache exists.")
@click.option("--voice-s1", default=None, help="Override speaker 1 (Alex) voice id.")
@click.option("--voice-s2", default=None, help="Override speaker 2 (Sam) voice id.")
def main(stage: str, date: str | None, categories: tuple[str],
         email: str | None, telegram_chat_id: str | None,
         length_preset: str | None, no_cache: bool,
         voice_s1: str | None, voice_s2: str | None):
    """Market Pulse -- Automated Finance Podcast Generator"""
    config = load_config()
    date = date or datetime.now().strftime("%Y-%m-%d")
    output_dir = config.get("output_dir", "output")
    os.makedirs(output_dir, exist_ok=True)

    cat_list = [PodcastCategory(c) for c in categories]

    snapshot_path = os.path.join(output_dir, f"{date}-snapshot.json")
    script_path = os.path.join(output_dir, f"{date}-script.txt")

    log.info(f"Market Pulse pipeline -- {date} -- categories: {[c.value for c in cat_list]}")

    if stage in ("data", "all"):
        snapshot = collect_data(
            config, cat_list,
            cache_dir=output_dir,
            force_refresh=no_cache,
        )
        # Record user selections on the canonical snapshot (audit trail).
        snapshot.user_voice_s1 = voice_s1 or config.get("speaker_1_voice", "")
        snapshot.user_voice_s2 = voice_s2 or config.get("speaker_2_voice", "")
        snapshot.user_length_preset = length_preset or ""
        snapshot.user_target_words = (
            LENGTH_PRESETS[length_preset].target_words if length_preset else 0
        )
        snapshot.save(snapshot_path)
        log.info(f"Snapshot saved: {snapshot_path}")
        if stage == "data":
            return

    if stage in ("script", "all"):
        if stage == "script":
            snapshot = MarketSnapshot.load(snapshot_path)
            if snapshot.categories:
                cat_list = [PodcastCategory(c) for c in snapshot.categories]
            # Prefer the preset recorded on the snapshot if the user didn't
            # override it on the re-run, so stage=script rehydrates cleanly.
            if length_preset is None and snapshot.user_length_preset:
                length_preset = snapshot.user_length_preset
        script = generate_script(config, snapshot, cat_list, preset_key=length_preset)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        log.info(f"Script saved: {script_path}")
        if stage == "script":
            return

    if stage in ("audio", "all"):
        if stage == "audio":
            with open(script_path, "r", encoding="utf-8") as f:
                script = f.read()
        mp3_path = generate_audio(config, script, date, voice_s1=voice_s1, voice_s2=voice_s2)
        log.info(f"=== DONE === Episode saved: {mp3_path}")

        # ── STAGE 4: Delivery Fan-out ───────────────────────
        if email or telegram_chat_id:
            log.info("=== STAGE 4: Delivery ===")
            cat_names = [c.value.replace("_", " ").title() for c in cat_list]

            email_ok = True
            tg_ok = True
            attempted = 0

            if email:
                attempted += 1
                email_ok = send_episode_email(
                    mp3_path=mp3_path,
                    recipient=email,
                    categories=cat_names,
                )
                if not email_ok:
                    log.warning("Email delivery failed. Check EMAIL_ADDRESS / EMAIL_APP_PASSWORD.")

            if telegram_chat_id:
                attempted += 1
                tg_ok = send_episode_telegram(
                    mp3_path=mp3_path,
                    chat_id=telegram_chat_id,
                    categories=cat_names,
                )
                if not tg_ok:
                    log.warning("Telegram delivery failed. Check TELEGRAM_BOT_TOKEN / chat id.")

            if attempted > 0 and not (email_ok or tg_ok):
                import sys
                sys.exit(1)


if __name__ == "__main__":
    main()
