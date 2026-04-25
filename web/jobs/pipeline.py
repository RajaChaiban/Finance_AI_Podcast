"""Pipeline wrapper: translates existing src/ callbacks into job events.

The collectors and the Kokoro engine are sync code. To avoid blocking
the asyncio event loop (and therefore the SSE broker), each heavy stage
runs in a thread via asyncio.to_thread().
"""

from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime
from pathlib import Path

from web.db import session, dumps, loads, reindex_episode_fts
from web.jobs.runner import _append_log, _emit, _update_job, broker  # noqa: F401
from web.models import Episode, Job
from web.settings import load_app_config, output_dir


# ── Bridge sync → async for stage events ─────────────────────────

def _sync_log(job_id: str, line: str, loop: asyncio.AbstractEventLoop) -> None:
    """Append to the job's log AND publish to SSE subscribers.

    Called from the sync thread; schedules the async publish back on the
    main loop so we don't block the worker thread on asyncio machinery.
    """
    tail = _append_log(job_id, line)
    asyncio.run_coroutine_threadsafe(
        _emit(job_id, "log", line=line, tail=tail),
        loop,
    )


def _sync_stage(job_id: str, stage: str, progress: float,
                loop: asyncio.AbstractEventLoop) -> None:
    _update_job(job_id, stage=stage, progress=progress)
    asyncio.run_coroutine_threadsafe(
        _emit(job_id, "progress", stage=stage, progress=progress),
        loop,
    )


# ── Individual stages ───────────────────────────────────────────

def _stage_collect(config: dict, params: dict, loop, job_id: str):
    from src.data.categories import PodcastCategory
    from src.data.collector_router import CategoryCollectorRouter
    from src.script.length import LENGTH_PRESETS, DEFAULT_PRESET_KEY

    categories = [PodcastCategory(v) for v in params["categories"]]
    router = CategoryCollectorRouter(config, categories)
    try:
        snapshot = router.collect_all(
            status_callback=lambda msg: _sync_log(job_id, msg, loop),
            cache_dir=str(output_dir()),
            force_refresh=params.get("force_refresh", False),
        )
    finally:
        router.close()
    preset_key = params.get("length_preset", DEFAULT_PRESET_KEY)
    preset = LENGTH_PRESETS[preset_key]
    snapshot.user_voice_s1 = params.get("voice_s1", "")
    snapshot.user_voice_s2 = params.get("voice_s2", "")
    snapshot.user_length_preset = preset_key
    snapshot.user_target_words = preset.target_words
    snap_path = output_dir() / f"{snapshot.date}-snapshot.json"
    snapshot.save(str(snap_path))
    return snapshot, preset, snap_path


def _resolve_llm_config(config: dict, params: dict | None = None) -> dict:
    """Overlay DB Setting overrides — and any per-run params override — onto
    the base config dict.

    Precedence (highest wins): per-run ``params`` → DB ``Setting`` → ``config``
    (which already includes .env). The web UI persists provider choices in
    the Setting table (key prefix "default_llm_*"); the Generate form can
    further override that for a single run via ``params['llm_provider']`` +
    ``params['llm_model']``.
    """
    merged = dict(config)
    db_overrides = {
        "llm_provider": _setting("default_llm_provider"),
        "gemini_model": _setting("default_gemini_model"),
        "ollama_model": _setting("default_ollama_model"),
        "ollama_base_url": _setting("default_ollama_base_url"),
    }
    for k, v in db_overrides.items():
        if v:
            merged[k] = v

    # Per-run override from the Generate form. ``llm_model`` lands in the
    # provider-specific slot so build_provider() picks it up unchanged.
    if params:
        run_provider = params.get("llm_provider")
        run_model = params.get("llm_model")
        if run_provider:
            merged["llm_provider"] = run_provider
            if run_model:
                if run_provider == "gemini":
                    merged["gemini_model"] = run_model
                elif run_provider == "ollama":
                    merged["ollama_model"] = run_model
    return merged


def _setting(key: str):
    from web.db import session, loads
    from web.models import Setting

    with session() as s:
        row = s.get(Setting, key)
    return loads(row.value, None) if row else None


def _stage_script(snapshot, preset, config: dict, params: dict, loop, job_id: str):
    from src.data.categories import PodcastCategory
    from src.script.generator import ScriptGenerator
    from src.script.llm import build_provider

    categories = [PodcastCategory(v) for v in params["categories"]]
    llm_config = _resolve_llm_config(config, params)
    provider = build_provider(llm_config)
    generator = ScriptGenerator(provider=provider)
    _sync_log(
        job_id,
        f"Sending data to {llm_config['llm_provider']}/{provider.model}...",
        loop,
    )
    script = generator.generate(
        snapshot,
        categories,
        target_words=preset.target_words,
        preset_key=preset.key,
    )
    date_str = snapshot.date
    script_path = output_dir() / f"{date_str}-script.txt"
    script_path.write_text(script, encoding="utf-8")
    return script, script_path, provider.model


def _stage_audio(script: str, config: dict, params: dict, loop, job_id: str, date_str: str):
    from src.audio.kokoro_engine import KokoroEngine
    from src.audio.processor import AudioProcessor

    tts_cfg = config.get("tts", {}) or {}
    engine = KokoroEngine(
        voice_s1=params["voice_s1"],
        voice_s2=params["voice_s2"],
        speed=tts_cfg.get("base_speed", 1.0),
        enable_blending=tts_cfg.get("enable_blending", True),
        enable_prosody=tts_cfg.get("enable_prosody", True),
    )

    def on_progress(i, total, speaker, preview):
        pct = 2 / 3 + (1 / 3) * (i + 1) / max(total, 1)  # audio = last third
        _sync_stage(job_id, "audio", pct, loop)
        _sync_log(job_id, f"Segment {i+1}/{total} [{speaker}] \"{preview[:60]}...\"", loop)

    audio, sr = engine.generate_audio(
        script,
        sample_rate=config.get("sample_rate", 24000),
        on_progress=on_progress,
    )
    _sync_log(job_id, "Encoding MP3...", loop)
    processor = AudioProcessor(output_dir=str(output_dir()))
    mp3_path = processor.save_mp3(
        audio=audio,
        sample_rate=sr,
        date=date_str,
        podcast_name=config.get("podcast_name", "Market Pulse"),
    )
    duration = len(audio) / sr
    return Path(mp3_path), duration


# ── Orchestrator ────────────────────────────────────────────────

def _run_sync(job_id: str, params: dict, loop) -> int:
    """Runs in a thread. Returns the new episode's id."""
    config = load_app_config()
    stage_times: dict[str, float] = {}

    # STAGE 1: data
    _sync_stage(job_id, "data", 0.02, loop)
    _sync_log(job_id, "Collecting market data...", loop)
    t0 = time.time()
    snapshot, preset, snap_path = _stage_collect(config, params, loop, job_id)
    stage_times["data"] = time.time() - t0
    _sync_stage(job_id, "data", 1 / 3, loop)
    _sync_log(job_id, f"Data collected in {stage_times['data']:.1f}s", loop)

    # STAGE 2: script
    _sync_stage(job_id, "script", 0.34, loop)
    _sync_log(job_id, "Generating script...", loop)
    t0 = time.time()
    script, script_path, llm_model = _stage_script(snapshot, preset, config, params, loop, job_id)
    stage_times["script"] = time.time() - t0
    word_count = len(script.split())
    _sync_stage(job_id, "script", 2 / 3, loop)
    _sync_log(job_id,
              f"Script generated in {stage_times['script']:.1f}s ({word_count} words)",
              loop)

    # STAGE 3: audio
    _sync_stage(job_id, "audio", 0.67, loop)
    _sync_log(job_id, "Synthesizing audio with Kokoro...", loop)
    t0 = time.time()
    mp3_path, duration = _stage_audio(script, config, params, loop, job_id, snapshot.date)
    stage_times["audio"] = time.time() - t0
    _sync_stage(job_id, "audio", 1.0, loop)
    _sync_log(job_id,
              f"Audio generated in {stage_times['audio']:.1f}s ({duration/60:.1f} min)",
              loop)

    # Persist episode
    ep = Episode(
        date=snapshot.date,
        podcast_name=config.get("podcast_name", "Market Pulse"),
        categories_json=dumps(params["categories"]),
        length_preset=preset.key,
        target_words=preset.target_words,
        word_count=word_count,
        duration_seconds=duration,
        mp3_path=str(mp3_path),
        script_path=str(script_path),
        snapshot_path=str(snap_path),
        voice_s1=params["voice_s1"],
        voice_s2=params["voice_s2"],
        gemini_model=llm_model,
        stage_times_json=dumps(stage_times),
        created_at=datetime.utcnow(),
    )
    with session() as s:
        s.add(ep)
        s.commit()
        s.refresh(ep)
        ep_id = ep.id
    reindex_episode_fts(ep_id, snapshot.date, script)
    return ep_id


async def run_pipeline(job_id: str) -> int:
    """Async entry point called from the worker."""
    job = None
    with session() as s:
        job = s.get(Job, job_id)
        if job is None:
            raise RuntimeError(f"Job {job_id} not found")
        params = loads(job.params_json, {})
    loop = asyncio.get_running_loop()
    episode_id = await asyncio.to_thread(_run_sync, job_id, params, loop)
    return episode_id
