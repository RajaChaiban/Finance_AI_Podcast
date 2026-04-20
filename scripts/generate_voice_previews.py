"""Render short preview clips for every voice in VOICE_CATALOG.

Idempotent: existing MP3s are skipped unless --force is passed. Run once
after adding a voice, or locally after cloning if the repo-committed assets
are missing. ~2-3 minutes for the full catalog on CPU.

Usage:
    python scripts/generate_voice_previews.py          # render missing only
    python scripts/generate_voice_previews.py --force  # regenerate all
"""
from __future__ import annotations

import sys
from pathlib import Path

import click
import numpy as np
import soundfile as sf
from pydub import AudioSegment

# Make the project root importable when the script is invoked directly.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kokoro import KPipeline  # noqa: E402
from src.audio.voice_blender import VOICE_CATALOG  # noqa: E402


PREVIEW_TEXT = "Welcome to Market Pulse. Here are today's top market moves."
OUT_DIR = ROOT / "assets" / "voice_previews"
SAMPLE_RATE = 24000


def _render_one(pipeline: KPipeline, voice_id: str, out_path: Path) -> bool:
    chunks = []
    for _, _, audio in pipeline(PREVIEW_TEXT, voice=voice_id, speed=1.0):
        if audio is not None:
            chunks.append(np.asarray(audio))
    if not chunks:
        return False

    combined = np.concatenate(chunks)
    wav_path = out_path.with_suffix(".wav")
    sf.write(str(wav_path), combined, SAMPLE_RATE)
    try:
        AudioSegment.from_wav(str(wav_path)).export(
            str(out_path), format="mp3", bitrate="64k",
        )
    finally:
        if wav_path.exists():
            wav_path.unlink()
    return True


@click.command()
@click.option("--force", is_flag=True, help="Regenerate clips that already exist.")
def main(force: bool):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # British voices (bf_*, bm_*) synthesize acceptably on the American
    # pipeline for a 5-second preview. Upgrade to per-region pipelines only
    # if listener feedback flags the phonemes.
    pipeline = KPipeline(lang_code="a")

    rendered = 0
    skipped = 0
    failed = 0
    for entry in VOICE_CATALOG:
        voice_id = entry["id"]
        mp3_path = OUT_DIR / f"{voice_id}.mp3"
        if mp3_path.exists() and not force:
            skipped += 1
            continue
        click.echo(f"  rendering {voice_id} ...")
        try:
            ok = _render_one(pipeline, voice_id, mp3_path)
        except Exception as e:  # noqa: BLE001 -- report per-voice but keep going
            click.echo(f"  FAIL {voice_id}: {e}")
            failed += 1
            continue
        if ok:
            rendered += 1
        else:
            click.echo(f"  FAIL {voice_id}: pipeline returned no audio")
            failed += 1

    click.echo(f"Done. Rendered={rendered}  Skipped={skipped}  Failed={failed}")
    click.echo(f"Output: {OUT_DIR}")


if __name__ == "__main__":
    main()
