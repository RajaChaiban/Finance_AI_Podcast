"""Shared helpers for route handlers — template globals, episode row unpacking."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Iterable

from fastapi import Request
from sqlmodel import select

from web.db import loads, session
from web.models import Episode, Job


def ctx(request: Request, **extra) -> dict:
    """Jinja context with common globals every page uses."""
    today = datetime.now()
    base = {
        "request": request,
        "today": today.strftime("%Y-%m-%d"),
        "today_long": today.strftime("%A, %B %d, %Y"),
    }
    base.update(extra)
    return base


def episode_to_view(ep: Episode) -> dict:
    """Unpack an Episode row into a template-friendly dict."""
    categories = loads(ep.categories_json, [])
    stage_times = loads(ep.stage_times_json, {})
    mp3_url = _rel_url(ep.mp3_path)
    return {
        "id": ep.id,
        "date": ep.date,
        "date_long": _date_long(ep.date),
        "podcast_name": ep.podcast_name,
        "categories": categories,
        "category_labels": [_cat_label(c) for c in categories],
        "length_preset": ep.length_preset,
        "target_words": ep.target_words,
        "word_count": ep.word_count,
        "duration_seconds": ep.duration_seconds,
        "duration_pretty": _duration_pretty(ep.duration_seconds),
        "mp3_path": ep.mp3_path,
        "mp3_url": mp3_url,
        "script_path": ep.script_path,
        "snapshot_path": ep.snapshot_path,
        "voice_s1": ep.voice_s1,
        "voice_s2": ep.voice_s2,
        "gemini_model": ep.gemini_model,
        "stage_times": stage_times,
        "total_time": sum(stage_times.values()) if stage_times else 0,
        "created_at": ep.created_at,
    }


def _rel_url(path: str) -> str | None:
    """Map an on-disk output/ path to the /output/... URL the app mounts."""
    if not path:
        return None
    p = path.replace("\\", "/")
    idx = p.rfind("/output/")
    if idx != -1:
        return p[idx:]
    # Already starts with output/ or is a bare filename
    if p.startswith("output/"):
        return "/" + p
    return "/output/" + p.rsplit("/", 1)[-1]


def _cat_label(value: str) -> str:
    try:
        from src.data.categories import PodcastCategory, CATEGORY_LABELS
        return CATEGORY_LABELS.get(PodcastCategory(value), value)
    except Exception:
        return value.replace("_", " ").title()


def _duration_pretty(seconds: float) -> str:
    if not seconds:
        return "—"
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}"


def _date_long(date_str: str) -> str:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%A, %B %d, %Y")
    except Exception:
        return date_str


STAGE_ORDER = ["data", "script", "audio"]
STAGE_LABELS = {
    "data":   ("Data Collection",   "Pulling markets, news, and signals from every selected category."),
    "script": ("Script Generation", "Gemini drafts the dialogue between Alex and Sam."),
    "audio":  ("Audio Synthesis",   "Kokoro voices the script segment by segment."),
}


def job_view(job) -> dict:
    """Template-ready dict for a Job row (covers both SQLModel rows and dicts)."""
    if job is None:
        return {}
    if isinstance(job, dict):
        get = lambda k, default=None: job.get(k, default)
    else:
        get = lambda k, default=None: getattr(job, k, default)

    status = get("status") or "queued"
    stage = get("stage") or "data"
    try:
        cur_idx = STAGE_ORDER.index(stage)
    except ValueError:
        cur_idx = 0

    stages = []
    for idx, key in enumerate(STAGE_ORDER):
        label, desc = STAGE_LABELS[key]
        if status == "done":
            state = "done"
        elif status == "failed":
            state = "done" if idx < cur_idx else ("failed" if idx == cur_idx else "pending")
        elif status == "running":
            state = "done" if idx < cur_idx else ("active" if idx == cur_idx else "pending")
        else:
            state = "pending"
        stages.append({"key": key, "label": label, "desc": desc, "state": state, "index": idx + 1})

    return {
        "id": get("id"),
        "status": status,
        "stage": stage,
        "progress": float(get("progress") or 0.0),
        "log_tail": loads(get("log_tail_json", "[]"), []),
        "error_message": get("error_message"),
        "episode_id": get("episode_id"),
        "stages": stages,
    }


def recent_episodes(limit: int = 3) -> list[dict]:
    with session() as s:
        rows = s.exec(
            select(Episode).order_by(Episode.created_at.desc()).limit(limit)
        ).all()
    return [episode_to_view(r) for r in rows]


def episode_for_date(date_str: str) -> dict | None:
    with session() as s:
        row = s.exec(
            select(Episode).where(Episode.date == date_str)
            .order_by(Episode.created_at.desc())
        ).first()
    return episode_to_view(row) if row else None


def cadence_streak(days: int = 14) -> list[dict]:
    """Return up to `days` days ending today, each flagged if an episode exists."""
    with session() as s:
        rows = s.exec(
            select(Episode.date).order_by(Episode.date.desc()).limit(days * 3)
        ).all()
    published = {r for r in rows}
    out = []
    today = datetime.now()
    for i in range(days - 1, -1, -1):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        out.append({"date": d, "published": d in published, "short": d[-2:]})
    return out
