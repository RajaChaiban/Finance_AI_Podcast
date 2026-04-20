"""Generate route — pipeline form + live progress view."""

from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from src.audio.voice_blender import VOICE_CATALOG, voice_label
from src.data.categories import (
    CATEGORY_API_KEYS, CATEGORY_DESCRIPTIONS, CATEGORY_LABELS,
    DEFAULT_CATEGORIES, PodcastCategory,
)
from src.script.length import DEFAULT_PRESET_KEY, LENGTH_PRESETS

from web.db import loads, session
from web.jobs.runner import active_job, enqueue_job, get_job
from web.models import Setting
from web.routes._common import ctx, job_view
from web.settings import load_app_config


router = APIRouter(prefix="/generate")


def _settings_defaults() -> dict:
    from sqlmodel import select
    with session() as s:
        rows = {r.key: loads(r.value, None) for r in s.exec(select(Setting)).all()}
    config = load_app_config()
    return {
        "categories": rows.get("default_categories") or [c.value for c in DEFAULT_CATEGORIES],
        "length_preset": rows.get("default_length_preset") or DEFAULT_PRESET_KEY,
        "voice_s1": rows.get("default_voice_s1") or config.get("speaker_1_voice", "am_adam"),
        "voice_s2": rows.get("default_voice_s2") or config.get("speaker_2_voice", "af_bella"),
    }


def _all_categories() -> list[dict]:
    return [
        {
            "value": c.value,
            "label": CATEGORY_LABELS[c],
            "description": CATEGORY_DESCRIPTIONS[c],
        }
        for c in PodcastCategory
    ]


def _voices_by_gender() -> dict:
    male = [v for v in VOICE_CATALOG if v["gender"] == "male"]
    female = [v for v in VOICE_CATALOG if v["gender"] == "female"]
    return {"male": male, "female": female}


@router.get("")
def generate_page(request: Request):
    templates = request.app.state.templates
    defaults = _settings_defaults()
    config = load_app_config()
    job = active_job()

    required_keys = {"gemini_api_key"}
    for cat_value in defaults["categories"]:
        try:
            cat = PodcastCategory(cat_value)
        except ValueError:
            continue
        for key_name in CATEGORY_API_KEYS.get(cat, []):
            required_keys.add(key_name)
    missing = [k for k in required_keys if not (config.get(k) and "your_" not in config.get(k, ""))]

    return templates.TemplateResponse(
        "pages/generate.html",
        ctx(
            request,
            all_categories=_all_categories(),
            defaults=defaults,
            voices=_voices_by_gender(),
            voice_label_fn=voice_label,
            length_presets=LENGTH_PRESETS,
            active_job=job,
            job=job_view(job) if job else None,
            missing_keys=missing,
            config=config,
        ),
    )


@router.post("/start")
def start(
    request: Request,
    categories: list[str] = Form(default_factory=list),
    length_preset: str = Form(DEFAULT_PRESET_KEY),
    voice_s1: str = Form(...),
    voice_s2: str = Form(...),
    force_refresh: bool = Form(False),
):
    # Refuse if a job is already queued/running
    existing = active_job()
    if existing is not None:
        return RedirectResponse("/generate", status_code=303)

    # Validate categories — drop any the enum doesn't know
    safe_cats: list[str] = []
    for c in categories:
        try:
            PodcastCategory(c)
            safe_cats.append(c)
        except ValueError:
            continue
    if not safe_cats:
        safe_cats = [c.value for c in DEFAULT_CATEGORIES]

    params = {
        "categories": safe_cats,
        "length_preset": length_preset if length_preset in LENGTH_PRESETS else DEFAULT_PRESET_KEY,
        "voice_s1": voice_s1,
        "voice_s2": voice_s2,
        "force_refresh": bool(force_refresh),
    }
    job_id = enqueue_job(params)
    return RedirectResponse(f"/generate?job={job_id}", status_code=303)
