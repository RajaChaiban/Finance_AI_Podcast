"""Settings route — API key status + default preferences."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse

from src.audio.voice_blender import VOICE_CATALOG, voice_label
from src.data.categories import (
    API_KEY_LABELS, CATEGORY_LABELS, DEFAULT_CATEGORIES, PodcastCategory,
)
from src.script.length import DEFAULT_PRESET_KEY, LENGTH_PRESETS

from datetime import datetime, timedelta
from web.db import dumps, loads, session
from web.models import Setting, PodcastConfig
from web.routes._common import ctx
from web.settings import load_app_config


router = APIRouter(prefix="/settings")


def _get(key: str, default):
    with session() as s:
        row = s.get(Setting, key)
    return loads(row.value, default) if row else default


def _set(key: str, value) -> None:
    with session() as s:
        row = s.get(Setting, key)
        if row is None:
            s.add(Setting(key=key, value=dumps(value)))
        else:
            row.value = dumps(value)
            s.add(row)
        s.commit()


def _mask(key: str) -> str:
    if not key:
        return ""
    if len(key) < 10:
        return "•" * len(key)
    return f"{key[:4]}…{key[-4:]}"


VALID_LLM_PROVIDERS = {"gemini", "ollama"}


@router.get("")
def settings_page(request: Request):
    templates = request.app.state.templates
    config = load_app_config()

    api_keys = []
    for key, label in API_KEY_LABELS.items():
        val = config.get(key, "")
        is_set = bool(val) and "your_" not in val
        api_keys.append({
            "key": key,
            "label": label,
            "is_set": is_set,
            "masked": _mask(val) if is_set else "— not set —",
        })

    defaults = {
        "categories": _get("default_categories", [c.value for c in DEFAULT_CATEGORIES]),
        "length_preset": _get("default_length_preset", DEFAULT_PRESET_KEY),
        "voice_s1": _get("default_voice_s1", config.get("speaker_1_voice", "am_adam")),
        "voice_s2": _get("default_voice_s2", config.get("speaker_2_voice", "af_bella")),
    }

    llm = {
        "provider": _get("default_llm_provider", config.get("llm_provider", "gemini")),
        "gemini_model": _get("default_gemini_model", config.get("gemini_model", "gemini-2.5-flash")),
        "ollama_model": _get("default_ollama_model", config.get("ollama_model", "gemma4:26b")),
        "ollama_base_url": _get("default_ollama_base_url", config.get("ollama_base_url", "http://localhost:11434")),
    }

    all_categories = [(c.value, CATEGORY_LABELS[c]) for c in PodcastCategory]
    male = [v for v in VOICE_CATALOG if v["gender"] == "male"]
    female = [v for v in VOICE_CATALOG if v["gender"] == "female"]

    return templates.TemplateResponse(
        "pages/settings.html",
        ctx(
            request,
            api_keys=api_keys,
            defaults=defaults,
            llm=llm,
            all_categories=all_categories,
            voices_male=male,
            voices_female=female,
            voice_label_fn=voice_label,
            length_presets=LENGTH_PRESETS,
            podcast_name=config.get("podcast_name", "Market Pulse"),
            gemini_model=config.get("gemini_model", "gemini-2.5-flash"),
        ),
    )


@router.get("/llm/test")
def test_ollama_connection(
    request: Request,  # noqa: ARG001
    base_url: str = Query(default=""),
):
    """Ping Ollama's /api/tags so the user can confirm connectivity.

    Always returns HTTP 200 with a JSON body — the UI distinguishes success
    from failure by reading the `ok` field. Returning 500 on Ollama errors
    would just trigger the global error page, which is not the UX we want
    here.
    """
    url = (base_url or _get("default_ollama_base_url",
                            load_app_config().get("ollama_base_url", "http://localhost:11434")))
    url = url.rstrip("/")
    tags_url = f"{url}/api/tags"

    try:
        resp = httpx.get(tags_url, timeout=5.0)
    except httpx.ConnectError as e:
        return JSONResponse({
            "ok": False,
            "tested_url": tags_url,
            "error": (
                f"Could not connect to Ollama at {url}. "
                "Is `ollama serve` running? "
                f"({e.__class__.__name__}: {e})"
            ),
        })
    except httpx.HTTPError as e:
        return JSONResponse({
            "ok": False,
            "tested_url": tags_url,
            "error": f"{e.__class__.__name__}: {e}",
        })

    if resp.status_code != 200:
        return JSONResponse({
            "ok": False,
            "tested_url": tags_url,
            "error": f"Ollama returned HTTP {resp.status_code}",
        })

    try:
        models = [m.get("name", "") for m in resp.json().get("models", [])]
    except ValueError:
        models = []

    return JSONResponse({
        "ok": True,
        "tested_url": tags_url,
        "models": models,
    })


@router.post("/llm")
def save_llm(
    request: Request,  # noqa: ARG001
    llm_provider: str = Form(...),
    gemini_model: str = Form(""),
    ollama_model: str = Form(""),
    ollama_base_url: str = Form(""),
):
    # Reject unknown providers — silently accepting "bogus" would let the next
    # pipeline run blow up at build_provider() with no UI breadcrumb.
    if llm_provider not in VALID_LLM_PROVIDERS:
        return RedirectResponse("/settings?llm_error=invalid_provider", status_code=303)

    _set("default_llm_provider", llm_provider)
    if gemini_model.strip():
        _set("default_gemini_model", gemini_model.strip())
    if ollama_model.strip():
        _set("default_ollama_model", ollama_model.strip())
    if ollama_base_url.strip():
        _set("default_ollama_base_url", ollama_base_url.strip())
    return RedirectResponse("/settings?saved=1", status_code=303)


@router.post("/defaults")
def save_defaults(
    request: Request,
    categories: list[str] = Form(default_factory=list),
    length_preset: str = Form(DEFAULT_PRESET_KEY),
    voice_s1: str = Form(...),
    voice_s2: str = Form(...),
):
    safe_cats = [c for c in categories if c in {pc.value for pc in PodcastCategory}]
    if not safe_cats:
        safe_cats = [c.value for c in DEFAULT_CATEGORIES]
    _set("default_categories", safe_cats)
    _set("default_length_preset",
         length_preset if length_preset in LENGTH_PRESETS else DEFAULT_PRESET_KEY)
    _set("default_voice_s1", voice_s1)
    _set("default_voice_s2", voice_s2)
    return RedirectResponse("/settings?saved=1", status_code=303)


@router.get("/podcast-config")
def get_podcast_config(date: str = Query(default=None)):
    """Get podcast config for a specific date (defaults to tomorrow)."""
    if not date:
        date = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")

    with session() as s:
        config = s.get(PodcastConfig, date)

    if config:
        return {
            "date": config.date,
            "length_preset": config.length_preset,
            "voice_s1": config.voice_s1,
            "voice_s2": config.voice_s2,
        }

    # Return defaults if no config exists
    defaults = {
        "date": date,
        "length_preset": _get("default_length_preset", DEFAULT_PRESET_KEY),
        "voice_s1": _get("default_voice_s1", "am_adam"),
        "voice_s2": _get("default_voice_s2", "af_bella"),
    }
    return defaults


@router.post("/podcast-config")
def save_podcast_config(
    date: str = Form(...),
    length_preset: str = Form(DEFAULT_PRESET_KEY),
    voice_s1: str = Form(...),
    voice_s2: str = Form(...),
):
    """Save podcast config for a specific date."""
    if length_preset not in LENGTH_PRESETS:
        length_preset = DEFAULT_PRESET_KEY

    with session() as s:
        config = s.get(PodcastConfig, date)
        if config is None:
            config = PodcastConfig(
                date=date,
                length_preset=length_preset,
                voice_s1=voice_s1,
                voice_s2=voice_s2,
            )
            s.add(config)
        else:
            config.length_preset = length_preset
            config.voice_s1 = voice_s1
            config.voice_s2 = voice_s2
            config.updated_at = datetime.utcnow()
            s.add(config)
        s.commit()

    return RedirectResponse(f"/settings?podcast_config_date={date}&saved=1", status_code=303)
