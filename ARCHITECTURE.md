# Market Pulse — Architecture

A three-stage pipeline that turns live market data into a two-host MP3 episode. The same pipeline backs three entry points (Streamlit UI, CLI, Telegram bot).

---

## High-level pipeline

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Stage 1: DATA  │ ──▶ │ Stage 2: SCRIPT │ ──▶ │ Stage 3: AUDIO   │ ──▶ │ MP3 + email  │
│ collector_router│     │   ScriptGen     │     │  KokoroEngine +  │     │  delivery    │
│   (8+ sources)  │     │   (Gemini)      │     │  AudioProcessor  │     │              │
└─────────────────┘     └─────────────────┘     └──────────────────┘     └──────────────┘
   MarketSnapshot           script.txt              numpy audio                MP3
```

Each stage writes its artifact to `output/`, so individual stages can be re-run via `python main.py --stage {data,script,audio}` without re-doing earlier work.

---

## Entry points

| File              | Surface          | Notes                                                              |
| ----------------- | ---------------- | ------------------------------------------------------------------ |
| `app.py`          | Streamlit web UI | Sidebar for category + voice selection; live progress per stage    |
| `main.py`         | Click CLI        | Stage selection, date override, email flag                         |
| `telegram_bot.py` | Telegram bot     | `/podcast [categories]`; gated by `ALLOWED_CHAT_IDS` allow-list    |

All three call into the same `src/` modules.

---

## Module map

```
src/
├── data/        Stage 1 — collectors, routing, snapshot model
├── script/      Stage 2 — Gemini prompt assembly + generation
├── audio/       Stage 3 — Kokoro TTS, voice blending, prosody, MP3 encode
└── utils/       Cross-cutting — logger + email sender
```

### `src/data/` — Stage 1: Data Collection

| File                       | Role                                                                 |
| -------------------------- | -------------------------------------------------------------------- |
| `categories.py`            | `PodcastCategory` enum + per-category metadata and required API keys |
| `models.py`                | All dataclasses, including the central `MarketSnapshot`              |
| `collector_router.py`      | `CategoryCollectorRouter` — picks collectors per selected category   |
| `worldmonitor_collector.py`| **Primary source** for all categories (no API key needed)            |
| `fred_collector.py`        | Treasury yields — supplements Finance Macro                          |
| `coingecko_collector.py`   | DeFi / trending — supplements Crypto                                 |
| `gnews_collector.py`       | Headlines — supplements Geopolitics + AI Updates                     |
| `currents_collector.py`    | World news — supplements Geopolitics + AI Updates                    |
| `newsdata_collector.py`    | AI/tech news — supplements AI Updates                                |
| `classifiers.py`           | Sentiment / topic classification helpers                             |

**Routing rule** (`collector_router.py:19`): World Monitor always runs; supplemental collectors run only if the relevant category is selected *and* its API key is present (`_has_key`). Missing optional keys are skipped silently — the pipeline still produces an episode.

### `src/script/` — Stage 2: Script Generation

| File          | Role                                                                          |
| ------------- | ----------------------------------------------------------------------------- |
| `prompts.py`  | `build_system_prompt`, `build_user_prompt` — category-aware Gemini prompts    |
| `generator.py`| `ScriptGenerator` — Gemini call, output cleanup (`_clean_script`), validation |

`generator.py:45` strips orphan lines that don't start with `[S1]`/`[S2]`, preventing the TTS from reading stage directions or section headers aloud.

### `src/audio/` — Stage 3: Audio Generation

| File              | Role                                                                            |
| ----------------- | ------------------------------------------------------------------------------- |
| `kokoro_engine.py`| `KokoroEngine` — parses `[S1:emotion]` segments, generates audio per turn       |
| `voice_blender.py`| `VoiceBlender`, `BlendRecipe`, `VOICE_CATALOG` — multi-voice timbre blending    |
| `prosody.py`      | Emotion → pitch/rate adjustments                                                |
| `processor.py`    | `AudioProcessor.save_mp3` — concatenation + MP3 encode via `pydub`              |

The script format is `[S1] dialogue` or `[S1:excited] dialogue`. The engine maps each tag to the configured anchor voice (S1 = Alex, S2 = Sam) and optionally blends in an emotion recipe.

### `src/utils/`

- `logger.py` — shared structured logger
- `email_sender.py` — `send_episode_email` (SMTP via Gmail app password)

---

## Data contract: `MarketSnapshot`

`src/data/models.py:83` defines the single object that flows from Stage 1 → Stage 2. Every collector mutates fields on it; the script generator only reads from it.

Core fields:

- `date`, `categories` — run metadata
- `indices`, `commodities`, `forex`, `crypto` — raw market dicts
- `top_gainers`, `top_losers`, `earnings` — typed dataclass lists
- `news`, `geopolitics`, `ai_updates` — typed item lists per category
- `macro_indicators` — FRED supplements (Finance Macro)
- `crypto_global`, `crypto_trending` — CoinGecko supplements (Crypto)
- World Monitor enrichments: `fear_greed`, `macro_signals`, `sectors`, `etf_flows`, `predictions`, `forecasts`, `sanctions`, `unrest_events`, `conflict_events`, `cross_signals`, `gdelt_intel`

Persisted as JSON via `MarketSnapshot.save()` / `MarketSnapshot.load()`, which lets `--stage script` and `--stage audio` resume from a saved snapshot.

---

## Output layout

```
output/
├── 2026-04-18-snapshot.json     # Stage 1 artifact
├── 2026-04-18-script.txt        # Stage 2 artifact
└── Market_Pulse_2026-04-18.mp3  # Stage 3 artifact
```

---

## Configuration sources

1. `config.yaml` — non-secret defaults (voices, model, output dir, target length)
2. `.env` — secrets (API keys, email creds, Telegram token + allow-list)

`load_config()` (in both `app.py:26` and `main.py:19`) merges them: YAML for behavior, env for credentials.

---

## Auxiliary tooling (`scripts/`)

- `tts_ab_render.py` — render the same script through multiple voice/prosody variants for A/B comparison
- `tts_prosody_metrics.py` — measure pitch/duration metrics on rendered audio
- `variants.yaml` — variant definitions consumed by the above

These are dev-only and not part of the production pipeline.
