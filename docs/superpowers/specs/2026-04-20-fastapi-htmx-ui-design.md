# Market Pulse — FastAPI + HTMX UI

**Date:** 2026-04-20
**Scope:** Replace the Streamlit `app.py` with a FastAPI + Jinja2 + HTMX + Tailwind + Alpine.js web app. Owner-operator tool only — no auth, no public pages.

## Goals

- A modern, editorial-aesthetic, "real app" interface for generating, browsing, and managing daily Market Pulse episodes
- Survives restarts (durable job + episode state in SQLite)
- Keeps existing `src/` modules untouched as the service layer
- Keeps `main.py` CLI untouched (GitHub Actions cron still uses it)

## Non-goals

- Public access / multi-user / auth
- Realtime multi-device sync (Supabase, etc.)
- Scheduled job UI (stays on GitHub Actions cron)
- Mobile-first (desktop-first; responsive fallback only)

## Stack

- **FastAPI** + Uvicorn
- **Jinja2** server-rendered templates
- **HTMX** for partial swaps, out-of-band updates, SSE
- **Alpine.js** for small client-side islands
- **Tailwind CSS v4** (CDN build initially)
- **SQLModel + SQLite** for data layer (with SQLite FTS5 for script search)
- **Existing `src/`** reused as the service layer

## Folder layout

```
web/
  main.py              # FastAPI app + lifespan
  settings.py          # pydantic-settings for env/config
  db.py                # SQLite engine, session helpers, FTS setup
  models.py            # SQLModel tables: Episode, Job, Setting
  routes/
    dashboard.py
    generate.py
    library.py
    settings.py
    jobs.py            # SSE stream + job control
  jobs/
    runner.py          # asyncio job loop, SSE broker
    pipeline.py        # wraps existing src/ modules
  templates/
    base.html
    pages/
    partials/
  static/
    app.css            # Tailwind (or CDN)
    app.js             # Alpine init
    images/
```

## Information Architecture

Four top-level views via sidebar nav, HTMX-swapped so nav doesn't flash:

| View | Route | Purpose |
|---|---|---|
| Dashboard | `/` | Today's episode card, Generate CTA, recent 3 episodes, weekly cadence streak, active job status |
| Generate | `/generate` | Category chips, voices, length preset, refresh toggle, Run. When a job is running → becomes live "Now Generating" screen |
| Library | `/library` | Timeline + filter rail (categories, date range, FTS search across scripts) |
| Settings | `/settings` | API key status (masked), default voices, default length, default categories, Kokoro TTS options |

**Persistent chrome:** sidebar (collapsible), top bar with ⌘K command palette, floating job pill (bottom-right, only when a job is running).

## Data Model

```python
class Episode(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    date: str                 # "2026-04-20"
    podcast_name: str
    categories: str           # JSON array
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
    created_at: datetime
    stage_times_json: str

class Job(SQLModel, table=True):
    id: str                   # uuid4
    status: str               # queued | running | done | failed | cancelled
    stage: str | None         # data | script | audio
    progress: float           # 0..1
    log_tail_json: str        # last 50 log lines
    episode_id: int | None
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    params_json: str          # full request

class Setting(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str                # JSON-encoded
```

Virtual FTS5 table: `episodes_fts(date, script_text)`.

## Job Runner

One in-process asyncio worker polls `Job` rows in `queued` status, runs them serially (single-user, one TTS at a time). Pipeline wrapper translates existing `src/` callbacks into progress events. SSE broker fan-outs events to subscribers. On app startup, any `running` job left over from a crash is marked `failed` with "interrupted by restart" — no auto-resume.

## Frontend

**HTMX (90% of interactivity):**
- `hx-get` + `hx-target` + `hx-push-url` for nav swaps
- `hx-post` returning component partials for form interactions (category toggle)
- SSE extension for `/jobs/{id}/stream`; OOB swaps keep pill in sync across views

**Alpine.js islands:**
- `sidebar` — collapse state + active-route
- `audioPlayer` — play/pause, scrub, lite visualizer
- `jobPill` — expand/collapse, drag
- `commandPalette` — ⌘K modal, fuzzy action search
- `toast` — flyouts for success/error

**Reusable partials:** `episode_card`, `stage_card`, `category_chip`, `voice_row`, `log_line`, `metric_tile`, `filter_rail`.

## Visual Design (editorial-modern)

**Palette:**
- BG: `#FAF7F2` cream / `#141210` ink (dark mode)
- Text: `#1A1714` on cream / `#F4EEE4` on dark
- Accent primary: `#B8522C` burnt sienna
- Accent secondary: `#3F5B4E` deep forest
- Grid: `#E8DFD2` / `#2A2522`
- Deltas: `#3A7D44` positive / `#C03B2E` negative (desaturated, editorial)

**Type:** Fraunces (serif display), Inter (UI body), JetBrains Mono (numerics/tickers).

**Spacing/corners:** `rounded-2xl` on cards, generous padding (min `p-6`), `max-w-5xl` readable columns.

**Motion:** 150ms ease-out on hover, 300ms on layout, no bounce. Respects `prefers-reduced-motion`.

**Texture:** subtle 3% SVG noise overlay.

**Dark mode:** supported, toggle in sidebar footer, defaults to system.

## Error Handling

- API key missing → Settings view flags + Generate disabled with inline explanation
- Collector failures → individual-source, non-fatal; warnings in live log + tagged on episode
- Script/TTS failure → job `failed` with error message; retry clones params
- DB missing → auto-create schema on startup; migration error shows a clear error page
- SSE disconnect → client auto-reconnect; server re-emits current state (not full history)

## Testing

- Unit: data layer (insert/query/FTS), job state transitions, pipeline wrapper
- Integration: end-to-end job with a stubbed pipeline (no Gemini/Kokoro)
- Smoke: Playwright test boots app, navigates each view, runs a stub job
- Existing `tests/test_pipeline_wiring.py` stays valid

## Migration

- Delete `app.py` (Streamlit)
- Delete `src/ui/` (Streamlit-specific components)
- Keep `main.py` CLI
- Add `web/` as above
- Add `web/` + `data/` (for SQLite file) to `.gitignore` where appropriate
- README updated with new run instructions (`uvicorn web.main:app --reload`)
