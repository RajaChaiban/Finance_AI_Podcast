# Voice Previews

Short MP3 clips used by the Market Pulse sidebar so users can hear each voice before picking. The UI (`app.py`) renders an `st.audio` widget under each voice dropdown when a matching `{voice_id}.mp3` exists in this directory.

## Regenerate

From the repo root:

```bash
python scripts/generate_voice_previews.py          # render missing clips only
python scripts/generate_voice_previews.py --force  # regenerate everything
```

Takes ~2–3 minutes for the full `VOICE_CATALOG` on CPU. Each clip is ~5 seconds at 64 kbps (≈ 40 KB).

Run this after adding or removing a voice in `src/audio/voice_blender.py`.
