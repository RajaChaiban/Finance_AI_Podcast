"""Configuration loader — merges config.yaml with .env secrets.

Mirrors the legacy Streamlit app's load_config() but exposes a dict-like
object the FastAPI routes can cache on app state.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv


ENV_TO_CONFIG = [
    ("GEMINI_API_KEY", "gemini_api_key"),
    ("FRED_API_KEY", "fred_api_key"),
    ("GNEWS_API_KEY", "gnews_api_key"),
    ("CURRENTS_API_KEY", "currents_api_key"),
    ("NEWSDATA_API_KEY", "newsdata_api_key"),
    ("EMAIL_ADDRESS", "email_address"),
    ("EMAIL_APP_PASSWORD", "email_app_password"),
    ("TELEGRAM_BOT_TOKEN", "telegram_bot_token"),
    ("TELEGRAM_CHAT_ID", "telegram_chat_id"),
]


REPO_ROOT = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def load_app_config() -> dict:
    load_dotenv(REPO_ROOT / ".env")
    with open(REPO_ROOT / "config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    for env_key, cfg_key in ENV_TO_CONFIG:
        config[cfg_key] = os.getenv(env_key, "")
    config.setdefault("output_dir", "output")
    config.setdefault("podcast_name", "Market Pulse")
    config.setdefault("gemini_model", "gemini-2.5-flash")
    config.setdefault("sample_rate", 24000)
    return config


def output_dir() -> Path:
    cfg = load_app_config()
    p = REPO_ROOT / cfg.get("output_dir", "output")
    p.mkdir(parents=True, exist_ok=True)
    return p


def data_dir() -> Path:
    p = REPO_ROOT / "data"
    p.mkdir(parents=True, exist_ok=True)
    return p
