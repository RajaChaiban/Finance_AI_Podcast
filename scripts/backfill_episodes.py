"""One-shot: scan output/ for existing episodes and register them in SQLite.

Matches MP3 files to their corresponding script + snapshot JSON by date
(filename convention: YYYY-MM-DD-*). Idempotent — running twice won't
duplicate entries.

Usage:
    python -m scripts.backfill_episodes
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from sqlmodel import select

# Make repo importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from web.db import dumps, init_db, reindex_episode_fts, session
from web.models import Episode
from web.settings import load_app_config, output_dir


DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def _estimate_duration(mp3_path: Path) -> float:
    """Try soundfile/pydub; fall back to 0 on failure."""
    try:
        import soundfile as sf
        info = sf.info(str(mp3_path))
        if info.duration:
            return float(info.duration)
    except Exception:
        pass
    try:
        from pydub.utils import mediainfo
        info = mediainfo(str(mp3_path))
        if info.get("duration"):
            return float(info["duration"])
    except Exception:
        pass
    return 0.0


def _preset_for_words(word_count: int) -> tuple[str, int]:
    from src.script.length import LENGTH_PRESETS
    # Closest preset by target word count
    best = min(LENGTH_PRESETS.values(), key=lambda p: abs(p.target_words - word_count))
    return best.key, best.target_words


def main() -> None:
    init_db()
    config = load_app_config()
    out = output_dir()

    mp3s = sorted(out.glob("*.mp3"))
    registered = 0
    skipped = 0

    with session() as s:
        known_paths = {
            e.mp3_path for e in s.exec(select(Episode)).all()
        }

    for mp3 in mp3s:
        # Must match YYYY-MM-DD prefix
        m = DATE_RE.match(mp3.name)
        if not m:
            continue
        date = m.group(1)

        # Skip test files
        if "test" in mp3.stem.lower() or mp3.stem.startswith("ab_"):
            continue

        if str(mp3) in known_paths:
            skipped += 1
            continue

        script_path = out / f"{date}-script.txt"
        snapshot_path = out / f"{date}-snapshot.json"

        if not script_path.exists():
            print(f"[skip] {mp3.name}: no matching script")
            skipped += 1
            continue

        script_text = script_path.read_text(encoding="utf-8")
        word_count = len(script_text.split())

        # Snapshot — tolerate missing fields
        snap_data: dict = {}
        if snapshot_path.exists():
            try:
                snap_data = json.loads(snapshot_path.read_text(encoding="utf-8"))
            except Exception:
                snap_data = {}

        categories = snap_data.get("categories") or ["finance_macro", "finance_micro"]
        voice_s1 = snap_data.get("user_voice_s1") or config.get("speaker_1_voice", "am_adam")
        voice_s2 = snap_data.get("user_voice_s2") or config.get("speaker_2_voice", "af_bella")
        preset_key = snap_data.get("user_length_preset")
        target_words = snap_data.get("user_target_words")
        if not preset_key or not target_words:
            preset_key, target_words = _preset_for_words(word_count)

        duration = _estimate_duration(mp3)
        created_at = datetime.fromtimestamp(mp3.stat().st_mtime)

        ep = Episode(
            date=date,
            podcast_name=config.get("podcast_name", "Market Pulse"),
            categories_json=dumps(categories),
            length_preset=preset_key,
            target_words=int(target_words),
            word_count=word_count,
            duration_seconds=duration,
            mp3_path=str(mp3),
            script_path=str(script_path),
            snapshot_path=str(snapshot_path) if snapshot_path.exists() else "",
            voice_s1=voice_s1,
            voice_s2=voice_s2,
            gemini_model=config.get("gemini_model", "gemini-2.5-flash"),
            stage_times_json=dumps({}),
            created_at=created_at,
        )
        with session() as s:
            s.add(ep)
            s.commit()
            s.refresh(ep)
            ep_id = ep.id
        reindex_episode_fts(ep_id, date, script_text)
        registered += 1
        print(f"[add] {date} — {word_count} words, {duration:.1f}s")

    print(f"\nDone. Registered: {registered}, skipped: {skipped}.")


if __name__ == "__main__":
    main()
