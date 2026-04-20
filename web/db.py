"""SQLite engine, schema bootstrap, FTS5 virtual table for script search."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from web.models import Episode, Job, Setting  # noqa: F401 — register tables
from web.settings import data_dir


DB_PATH = data_dir() / "market_pulse.db"

engine = create_engine(
    f"sqlite:///{DB_PATH.as_posix()}",
    connect_args={"check_same_thread": False},
    echo=False,
)


def init_db() -> None:
    """Create tables + FTS5 virtual table + triggers. Idempotent."""
    SQLModel.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE VIRTUAL TABLE IF NOT EXISTS episodes_fts "
            "USING fts5(episode_id UNINDEXED, date, script_text, content='')"
        ))
        # Crash-safety: any row still marked 'running' at startup was
        # interrupted by a crash/restart — flip to failed so the UI and
        # the job runner don't spin on ghost work.
        conn.execute(text(
            "UPDATE jobs SET status='failed', "
            "error_message=COALESCE(error_message,'interrupted by restart'), "
            "finished_at=CURRENT_TIMESTAMP "
            "WHERE status='running'"
        ))


@contextmanager
def session() -> Iterator[Session]:
    with Session(engine) as s:
        yield s


def reindex_episode_fts(episode_id: int, date: str, script_text: str) -> None:
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM episodes_fts WHERE episode_id = :eid"),
                     {"eid": episode_id})
        conn.execute(text(
            "INSERT INTO episodes_fts (episode_id, date, script_text) "
            "VALUES (:eid, :date, :text)"
        ), {"eid": episode_id, "date": date, "text": script_text})


def fts_search_episode_ids(query: str, limit: int = 50) -> list[int]:
    """Return episode ids whose scripts match the FTS query, most-recent first."""
    if not query.strip():
        return []
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT episode_id FROM episodes_fts WHERE episodes_fts MATCH :q "
            "ORDER BY date DESC LIMIT :lim"
        ), {"q": query, "lim": limit}).fetchall()
    return [r[0] for r in rows]


# ── Tiny JSON helpers ───────────────────────────────────────────

def dumps(value) -> str:
    return json.dumps(value, default=str, ensure_ascii=False)


def loads(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default
