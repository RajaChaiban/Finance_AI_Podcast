"""Generate route — pipeline form + live progress view."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from src.audio.voice_blender import VOICE_CATALOG, voice_label
from src.data.categories import (
    CATEGORY_API_KEYS, CATEGORY_DESCRIPTIONS, CATEGORY_LABELS,
    DEFAULT_CATEGORIES, PodcastCategory,
)
from src.script.length import DEFAULT_PRESET_KEY, LENGTH_PRESETS
from src.script.llm import LLM_CATALOG, default_option_id, get_option

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
    saved_provider = rows.get("default_llm_provider") or config.get("llm_provider")
    saved_model = (
        rows.get("default_ollama_model") if saved_provider == "ollama"
        else rows.get("default_gemini_model")
    )
    if saved_model is None:
        saved_model = (
            config.get("ollama_model") if saved_provider == "ollama"
            else config.get("gemini_model")
        )
    return {
        "categories": rows.get("default_categories") or [c.value for c in DEFAULT_CATEGORIES],
        "length_preset": rows.get("default_length_preset") or DEFAULT_PRESET_KEY,
        "voice_s1": rows.get("default_voice_s1") or config.get("speaker_1_voice", "am_adam"),
        "voice_s2": rows.get("default_voice_s2") or config.get("speaker_2_voice", "af_bella"),
        "ollama_base_url": (
            rows.get("default_ollama_base_url")
            or config.get("ollama_base_url", "http://localhost:11434")
        ),
        "llm_choice": default_option_id(saved_provider, saved_model),
    }


def _installed_ollama_models(base_url: str) -> set[str]:
    """Ping Ollama once at page render to mark which catalog tags are pulled.

    Returns an empty set on any failure — the UI just shows every Ollama
    option as "not installed" rather than blocking page load on a slow
    or down Ollama server.
    """
    url = f"{base_url.rstrip('/')}/api/tags"
    try:
        resp = httpx.get(url, timeout=2.0)
        resp.raise_for_status()
    except (httpx.HTTPError, httpx.InvalidURL):
        return set()
    try:
        return {m.get("name", "") for m in resp.json().get("models", [])}
    except ValueError:
        return set()


def _llm_options_view(installed: set[str]) -> list[dict]:
    """Render-ready dicts for the Generate template's LLM dropdown."""
    out = []
    for opt in LLM_CATALOG:
        installed_flag = (not opt.is_local) or (opt.model in installed)
        out.append({
            "id": opt.id,
            "label": opt.label,
            "note": opt.note,
            "is_local": opt.is_local,
            "model": opt.model,
            "installed": installed_flag,
        })
    return out


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

    installed = _installed_ollama_models(defaults["ollama_base_url"])
    llm_options = _llm_options_view(installed)
    ollama_reachable = bool(installed)

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
            llm_options=llm_options,
            ollama_reachable=ollama_reachable,
            ollama_base_url=defaults["ollama_base_url"],
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
    llm_choice: str = Form(""),
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

    # Per-run LLM override. Unknown choice falls back to whatever Settings
    # has saved — same behaviour as if the field weren't sent.
    chosen = get_option(llm_choice) if llm_choice else None
    if chosen is not None:
        params["llm_provider"] = chosen.provider
        params["llm_model"] = chosen.model

    job_id = enqueue_job(params)
    return RedirectResponse(f"/generate?job={job_id}", status_code=303)
