"""Job endpoints: SSE live stream + JSON status for the floating pill."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from web.jobs.runner import active_job, broker, get_job
from web.routes._common import job_view


router = APIRouter(prefix="/jobs")


_PARTIAL = Path(__file__).resolve().parent.parent / "templates" / "partials" / "live_progress.html"


def _render_partial(request: Request, job: dict) -> str:
    templates = request.app.state.templates
    return templates.get_template("partials/live_progress.html").render(
        request=request, job=job
    )


@router.get("/active.json")
def active_json():
    job = active_job()
    return JSONResponse({"job": job_view(job) if job else None})


@router.get("/{job_id}/stream")
async def stream(request: Request, job_id: str):
    """Server-sent events for a single job.

    Emits initial state, then re-renders the `live_progress.html` partial
    on every runner event. Closes when the job reaches a terminal state.
    """

    async def gen():
        # Initial snapshot
        job = get_job(job_id)
        if job is None:
            yield "event: error\ndata: unknown job\n\n"
            return

        view = job_view(job)
        html = _render_partial(request, view).replace("\n", "")
        yield f"data: {html}\n\n"

        if view["status"] in {"done", "failed", "cancelled"}:
            return

        q = broker.subscribe(job_id)
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(q.get(), timeout=15)
                except asyncio.TimeoutError:
                    # Heartbeat keeps the connection alive through proxies.
                    yield ": keepalive\n\n"
                    continue

                job = get_job(job_id)
                if job is None:
                    break
                view = job_view(job)
                html = _render_partial(request, view).replace("\n", "")
                yield f"data: {html}\n\n"

                if event.get("type") == "status" and event.get("status") in {
                    "done", "failed", "cancelled"
                }:
                    break
        finally:
            broker.unsubscribe(job_id, q)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
