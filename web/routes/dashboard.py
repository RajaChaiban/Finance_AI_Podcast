"""Dashboard route — daily cockpit."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Request

from web.jobs.runner import active_job
from web.routes._common import (
    cadence_streak, ctx, episode_for_date, recent_episodes,
)


router = APIRouter()


@router.get("/")
def dashboard(request: Request):
    templates = request.app.state.templates
    today = datetime.now().strftime("%Y-%m-%d")
    today_episode = episode_for_date(today)
    recent = recent_episodes(3)
    streak = cadence_streak(14)
    published = sum(1 for d in streak if d["published"])
    job = active_job()
    return templates.TemplateResponse(
        "pages/dashboard.html",
        ctx(
            request,
            today_episode=today_episode,
            recent=recent,
            streak=streak,
            streak_count=published,
            streak_total=len(streak),
            active_job=job,
        ),
    )
