# Market Pulse

Automated multi-category finance podcast generator. Pulls live market data, drafts a two-host script with Gemini, and synthesizes an MP3 episode with Kokoro-82M TTS. Runs from a FastAPI web UI, a CLI, or a Telegram bot.

---

## Quick start

### 1. Install

```bash
git clone <repo-url> Finance_Podcast
cd Finance_Podcast
python -m venv .venv
.venv\Scripts\activate           # Windows
# source .venv/bin/activate      # macOS / Linux
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in keys:

```bash
cp .env.example .env
```

| Variable             | Required for                       | Where to get it                                  |
| -------------------- | ---------------------------------- | ------------------------------------------------ |
| `GEMINI_API_KEY`     | Script generation (always)         | https://aistudio.google.com/apikey               |
| `FRED_API_KEY`       | Treasury yields (optional)         | https://fred.stlouisfed.org/docs/api/api_key.html |
| `GNEWS_API_KEY`      | Geopolitics / AI headlines (opt.)  | https://gnews.io                                 |
| `CURRENTS_API_KEY`   | World news supplement (optional)   | https://currentsapi.services                     |
| `NEWSDATA_API_KEY`   | AI news supplement (optional)      | https://newsdata.io                              |
| `EMAIL_ADDRESS`      | Send episode by email (optional)   | A Gmail account                                  |
| `EMAIL_APP_PASSWORD` | Gmail app password (optional)      | https://myaccount.google.com/apppasswords        |
| `TELEGRAM_BOT_TOKEN` | Telegram bot (optional)            | Message `@BotFather` → `/newbot`                 |
| `ALLOWED_CHAT_IDS`   | Telegram bot allow-list (required if bot used) | Find via `@userinfobot`              |

Only `GEMINI_API_KEY` is required. World Monitor (the primary data source) needs no key, so the pipeline runs end-to-end with just Gemini configured.

### 3. Run the UI

```bash
uvicorn web.main:app --reload
```

Opens at http://127.0.0.1:8000. Four views accessed via the sidebar:

- **Dashboard** — today's episode, recent three, 14-day cadence streak
- **Generate** — pick categories / length / voices, watch the three-stage pipeline live (server-sent events)
- **Library** — every episode with inline player, full-text script search, category/date filters
- **Settings** — API-key status (read from `.env`), default preferences

First-time setup: once you've generated a few episodes with the CLI, register them with:

```bash
python -m scripts.backfill_episodes
```

Data lives in `data/market_pulse.db` (SQLite). Back it up or delete it to reset.

---

## Other entry points

### CLI (`main.py`)

```bash
python main.py                                           # default categories
python main.py -c crypto -c geopolitics                  # multiple categories
python main.py --stage data                              # just collect data
python main.py --stage script --date 2026-04-18          # regen script from saved snapshot
python main.py --stage audio --date 2026-04-18           # regen audio from saved script
python main.py -e you@example.com                        # email when done
```

Categories: `finance_macro`, `finance_micro`, `crypto`, `geopolitics`, `ai_updates`.

### Telegram bot (`telegram_bot.py`)

```bash
python telegram_bot.py
```

Then in Telegram:

- `/podcast` — default categories
- `/podcast crypto geopolitics` — pick categories
- `/categories` — list available categories

`ALLOWED_CHAT_IDS` must contain your chat ID, otherwise every request is refused (generation costs API credits).

---

## Scheduled runs (GitHub Actions)

Generate and deliver a daily episode with zero local machine required. See
[`.github/workflows/daily-podcast.yml`](.github/workflows/daily-podcast.yml).

**Schedule:** Every day at 10:30 UTC (6:30 AM ET during EDT / 5:30 AM ET during EST).
Also runnable manually from the Actions tab via `workflow_dispatch`.

**First-time setup:**

1. Push this repo to GitHub.
2. Go to **Settings → Secrets and variables → Actions → New repository secret** and
   add each of the following (mirrors your local `.env`):

   | Secret               | Required | Purpose                                            |
   | -------------------- | -------- | -------------------------------------------------- |
   | `GEMINI_API_KEY`     | yes      | Script generation                                  |
   | `EMAIL_ADDRESS`      | yes      | Gmail sender + self-recipient                      |
   | `EMAIL_APP_PASSWORD` | yes      | Gmail App Password (not regular password)          |
   | `TELEGRAM_BOT_TOKEN` | yes      | From `@BotFather`                                  |
   | `TELEGRAM_CHAT_ID`   | yes      | Your own chat ID (one of the IDs in `ALLOWED_CHAT_IDS`) |
   | `FRED_API_KEY`       | no       | Treasury yields enrichment                         |
   | `GNEWS_API_KEY`      | no       | Geopolitics / AI news                              |
   | `CURRENTS_API_KEY`   | no       | World news supplement                              |
   | `NEWSDATA_API_KEY`   | no       | AI news supplement                                 |

3. Trigger the first run manually: **Actions → Daily Podcast → Run workflow**.
   Confirm the MP3 arrives by email and Telegram.

**What the workflow does:** runs the full pipeline, then delivers the MP3 to both
your email and your Telegram chat. Best-effort per channel — if Gmail is flaky the
Telegram push still fires, and vice versa. On hard failure (both channels down, or
pipeline crash), a short alert is sent on the same two channels with the log tail
and a link to the Actions run.

**Cost / limits:** fits comfortably in the free GitHub Actions tier for public repos.
For private repos, each run uses ~15 minutes of included compute. MP3s are uploaded
as workflow artifacts with 7-day retention as a safety net.

---

## Configuration (`config.yaml`)

| Key                    | Default                | Purpose                                      |
| ---------------------- | ---------------------- | -------------------------------------------- |
| `podcast_name`         | `Market Pulse`         | Used in MP3 filename and email subject       |
| `target_length_words`  | `3000`                 | Target script length (~20 min audio)         |
| `speaker_1_voice`      | `am_adam`              | Default Kokoro voice ID for Alex             |
| `speaker_2_voice`      | `af_bella`             | Default Kokoro voice ID for Sam              |
| `tts.base_speed`       | `1.0`                  | Speech rate multiplier                       |
| `tts.enable_blending`  | `true`                 | Multi-voice timbre blending                  |
| `tts.enable_prosody`   | `true`                 | Emotion-based pitch/rate adjustments         |
| `gemini_model`         | `gemini-2.5-flash`     | Gemini model used by `ScriptGenerator`       |
| `output_dir`           | `output`               | Where snapshots / scripts / MP3s land        |
| `sample_rate`          | `24000`                | Audio sample rate (Hz)                       |
| `default_categories`   | macro + micro          | Fallback when no categories selected         |

---

## Output artifacts

For each run on date `YYYY-MM-DD` you get three files in `output/`:

- `YYYY-MM-DD-snapshot.json` — raw market data
- `YYYY-MM-DD-script.txt` — final two-host script with `[S1]` / `[S2]` tags
- `Market_Pulse_YYYY-MM-DD.mp3` — the episode

---

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Test fixtures live in `tests/fixtures/`.

---

## Architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for module layout and pipeline flow.
