import os
import json
from datetime import datetime

import click
import yaml
from dotenv import load_dotenv

from src.data.finnhub_collector import FinnhubCollector
from src.data.marketaux_collector import MarketAuxCollector
from src.data.models import MarketSnapshot
from src.script.generator import ScriptGenerator
from src.audio.kokoro_engine import KokoroEngine
from src.audio.processor import AudioProcessor
from src.utils.logger import log


def load_config() -> dict:
    load_dotenv()
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    config["finnhub_api_key"] = os.getenv("FINNHUB_API_KEY", "")
    config["marketaux_api_key"] = os.getenv("MARKETAUX_API_KEY", "")
    config["gemini_api_key"] = os.getenv("GEMINI_API_KEY", "")
    return config


def collect_data(config: dict, status_callback=None) -> MarketSnapshot:
    log.info("=== STAGE 1: Data Collection ===")

    finnhub = FinnhubCollector(api_key=config["finnhub_api_key"])
    marketaux = MarketAuxCollector(api_key=config["marketaux_api_key"])

    if status_callback:
        status_callback("Collecting Finnhub data...")
    finnhub_data = finnhub.collect_all()

    if status_callback:
        status_callback("Collecting MarketAux news...")
    marketaux_data = marketaux.collect_all()

    snapshot = MarketSnapshot(
        date=datetime.now().strftime("%Y-%m-%d"),
        indices=finnhub_data.get("indices", {}),
        top_gainers=finnhub_data.get("top_gainers", []),
        top_losers=finnhub_data.get("top_losers", []),
        earnings=finnhub_data.get("earnings", []),
        economic_events=finnhub_data.get("economic_events", []),
        crypto=finnhub_data.get("crypto", {}),
        forex=finnhub_data.get("forex", {}),
        commodities=finnhub_data.get("commodities", {}),
        news=marketaux_data.get("news", []),
        market_sentiment=marketaux_data.get("market_sentiment", "neutral"),
    )

    log.info(f"Snapshot: {len(snapshot.news)} news, {len(snapshot.top_gainers)} gainers, "
             f"{len(snapshot.top_losers)} losers, sentiment={snapshot.market_sentiment}")
    return snapshot


def generate_script(config: dict, snapshot: MarketSnapshot) -> str:
    log.info("=== STAGE 2: Script Generation ===")

    api_key = config["gemini_api_key"]
    if not api_key or api_key == "your_gemini_key_here":
        raise ValueError("Gemini API key not set. Edit your .env file with a valid GEMINI_API_KEY.")

    generator = ScriptGenerator(
        api_key=api_key,
        model=config.get("gemini_model", "gemini-2.5-flash"),
    )
    script = generator.generate(snapshot)
    return script


def generate_audio(config: dict, script: str, date: str) -> str:
    log.info("=== STAGE 3: Audio Generation ===")

    engine = KokoroEngine(
        voice_s1=config.get("speaker_1_voice", "am_adam"),
        voice_s2=config.get("speaker_2_voice", "af_bella"),
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


@click.command()
@click.option("--stage", type=click.Choice(["data", "script", "audio", "all"]), default="all",
              help="Run a specific stage or the full pipeline")
@click.option("--date", default=None, help="Date override (YYYY-MM-DD)")
def main(stage: str, date: str | None):
    """Market Pulse -- Automated Finance Podcast Generator"""
    config = load_config()
    date = date or datetime.now().strftime("%Y-%m-%d")
    output_dir = config.get("output_dir", "output")
    os.makedirs(output_dir, exist_ok=True)

    snapshot_path = os.path.join(output_dir, f"{date}-snapshot.json")
    script_path = os.path.join(output_dir, f"{date}-script.txt")

    log.info(f"Market Pulse pipeline -- {date}")

    if stage in ("data", "all"):
        snapshot = collect_data(config)
        snapshot.save(snapshot_path)
        log.info(f"Snapshot saved: {snapshot_path}")
        if stage == "data":
            return

    if stage in ("script", "all"):
        if stage == "script":
            snapshot = MarketSnapshot.load(snapshot_path)
        script = generate_script(config, snapshot)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        log.info(f"Script saved: {script_path}")
        if stage == "script":
            return

    if stage in ("audio", "all"):
        if stage == "audio":
            with open(script_path, "r", encoding="utf-8") as f:
                script = f.read()
        mp3_path = generate_audio(config, script, date)
        log.info(f"=== DONE === Episode saved: {mp3_path}")


if __name__ == "__main__":
    main()
