"""In-process asyncio job runner + SSE broker.

One worker task polls the `jobs` table for queued rows and executes them
serially. All state transitions are persisted to SQLite so the UI can poll
if SSE fails. Progress events are fanned-out via an asyncio queue-per-
subscriber pattern.
"""

from __future__ import annotations

import asyncio
import json
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlmodel import select

from web.db import session, dumps, loads
from web.models import Job


# ── SSE Broker ──────────────────────────────────────────────────

@dataclass
class _Broker:
    subscribers: dict[str, set[asyncio.Queue]] = field(default_factory=dict)

    def subscribe(self, job_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        self.subscribers.setdefault(job_id, set()).add(q)
        return q

    def unsubscribe(self, job_id: str, q: asyncio.Queue) -> None:
        subs = self.subscribers.get(job_id)
        if subs and q in subs:
            subs.discard(q)
            if not subs:
                self.subscribers.pop(job_id, None)

    async def publish(self, job_id: str, event: dict) -> None:
        for q in list(self.subscribers.get(job_id, set())):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # Slow consumer — drop the event rather than block the worker.
                pass


broker = _Broker()


# ── Job helpers ─────────────────────────────────────────────────

MAX_LOG_LINES = 80


def _append_log(job_id: str, line: str) -> list[str]:
    with session() as s:
        job = s.get(Job, job_id)
        if job is None:
            return []
        tail: list[str] = loads(job.log_tail_json, [])
        tail.append(line)
        if len(tail) > MAX_LOG_LINES:
            tail = tail[-MAX_LOG_LINES:]
        job.log_tail_json = dumps(tail)
        s.add(job)
        s.commit()
        return tail


def _update_job(job_id: str, **fields) -> None:
    with session() as s:
        job = s.get(Job, job_id)
        if job is None:
            return
        for k, v in fields.items():
            setattr(job, k, v)
        s.add(job)
        s.commit()


async def _emit(job_id: str, event_type: str, **data) -> None:
    await broker.publish(job_id, {"type": event_type, "job_id": job_id, **data})


# ── Main worker loop ────────────────────────────────────────────

_worker_task: asyncio.Task | None = None
_stop_event: asyncio.Event | None = None


async def _run_one(job_id: str) -> None:
    """Execute a single queued job to completion (or failure)."""
    from web.jobs.pipeline import run_pipeline  # local import to avoid cycles

    _update_job(job_id, status="running", started_at=datetime.utcnow())
    await _emit(job_id, "status", status="running", stage="starting", progress=0.0)

    try:
        episode_id = await run_pipeline(job_id)
        _update_job(
            job_id,
            status="done",
            stage=None,
            progress=1.0,
            finished_at=datetime.utcnow(),
            episode_id=episode_id,
        )
        await _emit(job_id, "status", status="done", stage=None, progress=1.0,
                    episode_id=episode_id)
    except Exception as exc:  # noqa: BLE001 — last-resort safety
        msg = f"{exc.__class__.__name__}: {exc}"
        tb = traceback.format_exc()
        _append_log(job_id, f"ERROR: {msg}")
        _append_log(job_id, tb.splitlines()[-1] if tb else "")
        _update_job(
            job_id,
            status="failed",
            finished_at=datetime.utcnow(),
            error_message=msg,
        )
        await _emit(job_id, "status", status="failed", error=msg)


async def _worker_loop() -> None:
    assert _stop_event is not None
    while not _stop_event.is_set():
        job_id: str | None = None
        with session() as s:
            row = s.exec(
                select(Job).where(Job.status == "queued").order_by(Job.created_at)
            ).first()
            if row is not None:
                job_id = row.id
        if job_id is None:
            try:
                await asyncio.wait_for(_stop_event.wait(), timeout=1.5)
            except asyncio.TimeoutError:
                pass
            continue
        await _run_one(job_id)


def start_worker() -> None:
    global _worker_task, _stop_event
    if _worker_task is not None and not _worker_task.done():
        return
    _stop_event = asyncio.Event()
    _worker_task = asyncio.create_task(_worker_loop(), name="mp-job-worker")


async def stop_worker() -> None:
    global _worker_task, _stop_event
    if _stop_event is not None:
        _stop_event.set()
    if _worker_task is not None:
        try:
            await asyncio.wait_for(_worker_task, timeout=5)
        except asyncio.TimeoutError:
            _worker_task.cancel()
    _worker_task = None


# ── Public API used by routes ──────────────────────────────────

def active_job() -> Job | None:
    with session() as s:
        row = s.exec(
            select(Job).where(Job.status.in_(["queued", "running"]))
            .order_by(Job.created_at)
        ).first()
        if row is None:
            return None
        # Detach for cross-request use
        s.expunge(row)
        return row


def get_job(job_id: str) -> Job | None:
    with session() as s:
        row = s.get(Job, job_id)
        if row is not None:
            s.expunge(row)
        return row


def enqueue_job(params: dict[str, Any]) -> str:
    import uuid
    job_id = uuid.uuid4().hex
    with session() as s:
        s.add(Job(
            id=job_id,
            status="queued",
            params_json=dumps(params),
        ))
        s.commit()
    return job_id
