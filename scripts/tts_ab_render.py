"""A/B render a fixture under several KokoroEngine configs.

Renders each variant, prepends a narrated label, concatenates into a single
comparison MP3, and writes per-variant prosody metrics to CSV so subjective
and objective judgments can be compared side-by-side.

Usage:
    python scripts/tts_ab_render.py \
        --fixture tests/fixtures/ab_sample.txt \
        --variants scripts/variants.yaml \
        --out output/ab_comparison.mp3
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml
from pydub import AudioSegment

# Make `src` imports work whether run from repo root or elsewhere.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.audio.kokoro_engine import KokoroEngine  # noqa: E402
from src.audio.processor import AudioProcessor  # noqa: E402
from src.utils.logger import log  # noqa: E402

# Import metrics via relative path since scripts/ isn't a package.
sys.path.insert(0, str(_REPO_ROOT / "scripts"))
from tts_prosody_metrics import analyze  # noqa: E402


SAMPLE_RATE = 24000


def _build_label_audio(engine: KokoroEngine, label: str) -> np.ndarray:
    """Synthesize a short spoken label using the engine's S1 neutral voice."""
    script = f"[S1] Variant: {label}."
    audio, _ = engine.generate_audio(script, sample_rate=SAMPLE_RATE)
    return audio


def _silence(duration_s: float) -> np.ndarray:
    return np.zeros(int(SAMPLE_RATE * duration_s), dtype=np.float32)


def _render_variant(variant: dict, fixture_text: str) -> tuple[np.ndarray, str]:
    name = variant["name"]
    log.info(f"--- Rendering variant '{name}' ---")
    engine = KokoroEngine(
        voice_s1=variant.get("voice_s1", "am_adam"),
        voice_s2=variant.get("voice_s2", "af_bella"),
        speed=variant.get("base_speed", 1.0),
        enable_blending=variant.get("enable_blending", True),
        enable_prosody=variant.get("enable_prosody", True),
    )
    label_audio = _build_label_audio(engine, name)
    body_audio, _ = engine.generate_audio(fixture_text, sample_rate=SAMPLE_RATE)
    combined = np.concatenate([label_audio, _silence(0.6), body_audio])
    return combined, name


def _write_wav(audio: np.ndarray, path: Path) -> None:
    sf.write(str(path), audio, SAMPLE_RATE)


def _render_all(variants: list[dict], fixture_text: str, tmpdir: Path) -> list[tuple[str, Path]]:
    rendered = []
    for v in variants:
        audio, name = _render_variant(v, fixture_text)
        wav_path = tmpdir / f"{name}.wav"
        _write_wav(audio, wav_path)
        rendered.append((name, wav_path))
    return rendered


def _concat_to_mp3(rendered: list[tuple[str, Path]], out_path: Path, gap_s: float = 1.0) -> None:
    gap = AudioSegment.silent(duration=int(gap_s * 1000))
    combined = AudioSegment.empty()
    for i, (_, wav_path) in enumerate(rendered):
        seg = AudioSegment.from_wav(str(wav_path))
        combined += seg
        if i < len(rendered) - 1:
            combined += gap

    processor = AudioProcessor(output_dir=str(out_path.parent))
    # Reuse the existing normalize helper for consistent levels.
    normalized = processor.normalize(combined)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    normalized.export(str(out_path), format="mp3", bitrate="192k",
                      tags={"title": "TTS A/B Comparison", "artist": "Market Pulse"})


def _metrics_csv(rendered: list[tuple[str, Path]], csv_path: Path) -> None:
    rows = []
    for name, wav_path in rendered:
        m = analyze(wav_path)
        rows.append({"variant": name, **asdict(m)})
    if not rows:
        return
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    log.info(f"Wrote metrics: {csv_path}")


def main() -> int:
    ap = argparse.ArgumentParser(description="A/B render a fixture under multiple KokoroEngine configs")
    ap.add_argument("--fixture", default="tests/fixtures/ab_sample.txt")
    ap.add_argument("--variants", default="scripts/variants.yaml")
    ap.add_argument("--out", default="output/ab_comparison.mp3")
    ap.add_argument("--metrics-csv", default="output/ab_metrics.csv")
    args = ap.parse_args()

    fixture_path = Path(args.fixture)
    variants_path = Path(args.variants)
    out_path = Path(args.out)
    metrics_path = Path(args.metrics_csv)

    if not fixture_path.exists():
        print(f"Fixture not found: {fixture_path}", file=sys.stderr)
        return 2
    if not variants_path.exists():
        print(f"Variants not found: {variants_path}", file=sys.stderr)
        return 2

    fixture_text = fixture_path.read_text(encoding="utf-8")
    variants = yaml.safe_load(variants_path.read_text(encoding="utf-8"))
    if not isinstance(variants, list) or not variants:
        print("variants.yaml must be a non-empty list", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory() as td:
        tmpdir = Path(td)
        rendered = _render_all(variants, fixture_text, tmpdir)
        _concat_to_mp3(rendered, out_path)
        _metrics_csv(rendered, metrics_path)

    log.info(f"Done. A/B MP3: {out_path} | metrics: {metrics_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
