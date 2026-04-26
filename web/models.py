"""SQLModel tables for the Market Pulse web app.

Three entities:
- Episode: completed podcast episodes (metadata + paths to artefacts)
- Job: pipeline runs (queued, running, done, failed, cancelled)
- Setting: arbitrary UI preferences (JSON-encoded values)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Episode(SQLModel, table=True):
    __tablename__ = "episodes"

    id: Optional[int] = Field(default=None, primary_key=True)
    date: str = Field(index=True)
    podcast_name: str
    categories_json: str
    length_preset: str
    target_words: int
    word_count: int
    duration_seconds: float
    mp3_path: str
    script_path: str
    snapshot_path: str
    voice_s1: str
    voice_s2: str
    gemini_model: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    stage_times_json: str = "{}"


class Job(SQLModel, table=True):
    __tablename__ = "jobs"

    id: str = Field(primary_key=True)
    status: str = Field(index=True)
    stage: Optional[str] = None
    progress: float = 0.0
    log_tail_json: str = "[]"
    episode_id: Optional[int] = Field(default=None, foreign_key="episodes.id")
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    params_json: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class Setting(SQLModel, table=True):
    __tablename__ = "settings"

    key: str = Field(primary_key=True)
    value: str


class PodcastConfig(SQLModel, table=True):
    __tablename__ = "podcast_config"

    date: str = Field(primary_key=True)  # YYYY-MM-DD format
    length_preset: str = Field(default="standard")  # brief, standard, deep
    voice_s1: str = Field(default="am_adam")  # speaker 1 voice id
    voice_s2: str = Field(default="af_bella")  # speaker 2 voice id
    updated_at: datetime = Field(default_factory=datetime.utcnow)
