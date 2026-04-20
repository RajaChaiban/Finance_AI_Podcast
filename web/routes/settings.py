"""Settings route — API key status + default preferences."""

from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from src.audio.voice_blender import VOICE_CATALOG, voice_label
from src.data.categories import (
    API_KEY_LABELS, CATEGORY_LABELS, DEFAULT_CATEGORIES, PodcastCategory,
)
from src.script.length import DEFAULT_PRESET_KEY, LENGTH_PRESETS

from web.db import dumps, loads, session
from web.models import Setting
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

    all_categories = [(c.value, CATEGORY_LABELS[c]) for c in PodcastCategory]
    male = [v for v in VOICE_CATALOG if v["gender"] == "male"]
    female = [v for v in VOICE_CATALOG if v["gender"] == "female"]

    return templates.TemplateResponse(
        "pages/settings.html",
        ctx(
            request,
            api_keys=api_keys,
            defaults=defaults,
            all_categories=all_categories,
            voices_male=male,
            voices_female=female,
            voice_label_fn=voice_label,
            length_presets=LENGTH_PRESETS,
            podcast_name=config.get("podcast_name", "Market Pulse"),
            gemini_model=config.get("gemini_model", "gemini-2.5-flash"),
        ),
    )


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
