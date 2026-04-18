"""Measure objective prosody metrics on a rendered podcast audio file.

Usage:
    python scripts/tts_prosody_metrics.py output/2026-04-18-market-pulse.mp3
    python scripts/tts_prosody_metrics.py output/sample.wav --json out.json

Metrics:
    f0_mean_hz / f0_std_hz / f0_range_hz   -- pitch variation (monotone ↓)
    speaking_rate_wps / rate_variance      -- syllables-per-second + variance
    pause_count / pause_mean_ms            -- silences above a threshold
    rms_mean_db / rms_std_db / dynamic_range_db
    flatness_score                         -- 0..1 composite; >0.7 flags monotone
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np


@dataclass
class ProsodyMetrics:
    duration_s: float
    f0_mean_hz: float
    f0_std_hz: float
    f0_range_hz: float
    voiced_ratio: float
    speaking_rate_wps: float
    rate_variance: float
    pause_count: int
    pause_mean_ms: float
    pause_total_ms: float
    rms_mean_db: float
    rms_std_db: float
    dynamic_range_db: float
    flatness_score: float


def _load_audio(path: Path):
    import librosa
    # librosa.load auto-handles mp3, wav, etc. Force mono at 22.05kHz (plenty for F0).
    y, sr = librosa.load(str(path), sr=22050, mono=True)
    return y, sr


def _pitch_stats(y, sr):
    import librosa
    # pyin gives voiced/unvoiced decisions per frame plus F0.
    f0, voiced_flag, _ = librosa.pyin(
        y, fmin=65.0, fmax=400.0, sr=sr,
        frame_length=2048, hop_length=256,
    )
    voiced = f0[voiced_flag & ~np.isnan(f0)]
    if voiced.size == 0:
        return 0.0, 0.0, 0.0, 0.0
    f0_mean = float(np.mean(voiced))
    f0_std = float(np.std(voiced))
    f0_range = float(np.percentile(voiced, 95) - np.percentile(voiced, 5))
    voiced_ratio = float(voiced.size / f0.size)
    return f0_mean, f0_std, f0_range, voiced_ratio


def _rate_stats(y, sr, window_s: float = 3.0):
    """Approximate syllable rate via onset-envelope peaks.

    Breaks the signal into `window_s` windows and computes per-window syllable
    rate; returns mean rate and variance across windows.
    """
    import librosa
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=256)
    peaks = librosa.util.peak_pick(
        onset_env, pre_max=5, post_max=5, pre_avg=5, post_avg=5, delta=0.2, wait=5
    )
    peak_times = librosa.frames_to_time(peaks, sr=sr, hop_length=256)
    duration = len(y) / sr
    if duration <= 0:
        return 0.0, 0.0
    # Window-wise rate
    n_windows = max(1, int(duration // window_s))
    rates = []
    for w in range(n_windows):
        t0 = w * window_s
        t1 = (w + 1) * window_s
        count = int(np.sum((peak_times >= t0) & (peak_times < t1)))
        rates.append(count / window_s)
    mean_rate = float(np.mean(rates)) if rates else 0.0
    var_rate = float(np.var(rates)) if rates else 0.0
    return mean_rate, var_rate


def _pause_stats(y, sr, min_pause_ms: int = 200, db_floor: float = -40.0):
    import librosa
    # Frame RMS, convert to dBFS, find contiguous runs below threshold.
    rms = librosa.feature.rms(y=y, hop_length=256)[0]
    rms_db = 20.0 * np.log10(np.maximum(rms, 1e-6))
    frame_time = 256 / sr
    min_frames = int((min_pause_ms / 1000.0) / frame_time)

    below = rms_db < db_floor
    runs = []
    i = 0
    n = len(below)
    while i < n:
        if below[i]:
            j = i
            while j < n and below[j]:
                j += 1
            if (j - i) >= min_frames:
                runs.append((j - i) * frame_time * 1000.0)
            i = j
        else:
            i += 1
    pause_mean = float(np.mean(runs)) if runs else 0.0
    pause_total = float(np.sum(runs)) if runs else 0.0
    return len(runs), pause_mean, pause_total, rms_db


def _dynamics(rms_db: np.ndarray):
    voiced = rms_db[rms_db > -60.0]  # ignore deep silence
    if voiced.size == 0:
        return 0.0, 0.0, 0.0
    return (
        float(np.mean(voiced)),
        float(np.std(voiced)),
        float(np.percentile(voiced, 95) - np.percentile(voiced, 5)),
    )


def _flatness(f0_range_hz: float, rate_variance: float, rms_dynamic_db: float) -> float:
    """0..1 composite; higher = flatter/more monotone.

    Targets: healthy podcasts sit around f0_range 80-140 Hz, rate_variance > 0.3,
    rms_dynamic_range > 8 dB. Anything well below those floors contributes.
    """
    f0_pen = max(0.0, 1.0 - f0_range_hz / 100.0)
    rate_pen = max(0.0, 1.0 - rate_variance / 0.4)
    rms_pen = max(0.0, 1.0 - rms_dynamic_db / 10.0)
    return float(np.clip((f0_pen + rate_pen + rms_pen) / 3.0, 0.0, 1.0))


def analyze(audio_path: str | Path) -> ProsodyMetrics:
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(path)

    y, sr = _load_audio(path)
    duration = len(y) / sr

    f0_mean, f0_std, f0_range, voiced_ratio = _pitch_stats(y, sr)
    rate_mean, rate_var = _rate_stats(y, sr)
    pause_count, pause_mean, pause_total, rms_db = _pause_stats(y, sr)
    rms_mean_db, rms_std_db, rms_range_db = _dynamics(rms_db)
    flat = _flatness(f0_range, rate_var, rms_range_db)

    return ProsodyMetrics(
        duration_s=duration,
        f0_mean_hz=f0_mean,
        f0_std_hz=f0_std,
        f0_range_hz=f0_range,
        voiced_ratio=voiced_ratio,
        speaking_rate_wps=rate_mean,
        rate_variance=rate_var,
        pause_count=pause_count,
        pause_mean_ms=pause_mean,
        pause_total_ms=pause_total,
        rms_mean_db=rms_mean_db,
        rms_std_db=rms_std_db,
        dynamic_range_db=rms_range_db,
        flatness_score=flat,
    )


def _print(metrics: ProsodyMetrics) -> None:
    print(f"  duration          : {metrics.duration_s:.1f} s")
    print(f"  f0 mean / std     : {metrics.f0_mean_hz:6.1f} / {metrics.f0_std_hz:5.1f} Hz")
    print(f"  f0 range (p5-p95) : {metrics.f0_range_hz:6.1f} Hz")
    print(f"  voiced ratio      : {metrics.voiced_ratio:5.1%}")
    print(f"  speaking rate     : {metrics.speaking_rate_wps:.2f} syl/s  (variance {metrics.rate_variance:.3f})")
    print(f"  pauses            : {metrics.pause_count} runs, mean {metrics.pause_mean_ms:.0f} ms, total {metrics.pause_total_ms/1000:.1f} s")
    print(f"  rms mean / std    : {metrics.rms_mean_db:5.1f} / {metrics.rms_std_db:4.1f} dB")
    print(f"  dynamic range     : {metrics.dynamic_range_db:5.1f} dB")
    flag = "  <-- MONOTONE" if metrics.flatness_score > 0.7 else ""
    print(f"  flatness score    : {metrics.flatness_score:.2f}{flag}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Kokoro TTS prosody metrics")
    ap.add_argument("audio", help="Path to .wav or .mp3 to analyze")
    ap.add_argument("--json", dest="json_out", default=None, help="Write metrics JSON here")
    args = ap.parse_args()

    try:
        metrics = analyze(args.audio)
    except FileNotFoundError as e:
        print(f"Not found: {e}", file=sys.stderr)
        return 2

    print(f"Prosody metrics for {args.audio}:")
    _print(metrics)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(asdict(metrics), indent=2))
        print(f"\nWrote JSON: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
