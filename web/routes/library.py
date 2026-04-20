"""Library route — filterable timeline of past episodes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query, Request
from sqlmodel import select

from src.data.categories import CATEGORY_LABELS, PodcastCategory

from web.db import fts_search_episode_ids, loads, session
from web.models import Episode
from web.routes._common import ctx, episode_to_view


router = APIRouter(prefix="/library")


def _script_preview(script_path: str, n_lines: int = 10) -> list[str]:
    p = Path(script_path)
    if not p.exists():
        return []
    try:
        lines = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        return lines[:n_lines]
    except Exception:
        return []


@router.get("")
def library(
    request: Request,
    q: str | None = Query(None),
    category: str | None = Query(None),
    since: str | None = Query(None),
    until: str | None = Query(None),
):
    templates = request.app.state.templates

    stmt = select(Episode).order_by(Episode.date.desc(), Episode.created_at.desc())

    # Date bounds
    if since:
        stmt = stmt.where(Episode.date >= since)
    if until:
        stmt = stmt.where(Episode.date <= until)

    # Script full-text search → narrow by ids
    if q:
        ids = fts_search_episode_ids(q, limit=200)
        if ids:
            stmt = stmt.where(Episode.id.in_(ids))
        else:
            stmt = stmt.where(Episode.id == -1)  # force empty

    with session() as s:
        rows = s.exec(stmt.limit(200)).all()

    items = []
    for r in rows:
        view = episode_to_view(r)
        if category and category not in view["categories"]:
            continue
        items.append(view)

    categories = [(c.value, CATEGORY_LABELS[c]) for c in PodcastCategory]

    return templates.TemplateResponse(
        "pages/library.html",
        ctx(
            request,
            items=items,
            count=len(items),
            q=q or "",
            category=category or "",
            since=since or "",
            until=until or "",
            categories=categories,
        ),
    )


@router.get("/{episode_id}/script")
def episode_script(request: Request, episode_id: int):
    templates = request.app.state.templates
    with session() as s:
        ep = s.get(Episode, episode_id)
    if ep is None:
        return templates.TemplateResponse(
            "partials/empty.html", {"request": request, "message": "Episode not found"}, status_code=404
        )
    view = episode_to_view(ep)
    p = Path(ep.script_path)
    lines = p.read_text(encoding="utf-8").splitlines() if p.exists() else []

    import re
    tag_re = re.compile(r"^\[(S[12])(?::([a-z_]+))?\]\s*(.*)")
    parsed = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = tag_re.match(line)
        if m:
            parsed.append({
                "speaker": m.group(1),
                "speaker_name": "Alex" if m.group(1) == "S1" else "Sam",
                "emotion": m.group(2) or "",
                "text": m.group(3),
            })
    return templates.TemplateResponse(
        "partials/script_view.html",
        {"request": request, "ep": view, "lines": parsed},
    )
