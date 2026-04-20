# Market Pulse — UI Refresh Design

**Date:** 2026-04-19
**Status:** Approved (pending user spec review)
**Scope:** Visual overhaul of `app.py` Streamlit UI. Zero backend changes.

## Goal

Transform the current plain Streamlit UI into a bold, Gen-Z fintech aesthetic
(Robinhood-meets-Linear) with category-reactive cycling backgrounds. The
visual identity should make Market Pulse feel like a product a 20-something
would open daily and show a friend — not a data-science demo.

## Non-goals

- No framework change — still Streamlit.
- No changes to `src/data/`, `src/script/`, `src/audio/`, `src/utils/`,
  `config.yaml`, or the pipeline contract.
- No new dependencies (pure CSS + inline SVG).
- No session-state key renames (keeps existing flow intact).

## Architecture

All presentation code lives in a new `src/ui/` package. `app.py` imports from
it and its body becomes a thin composition of UI components around the
unchanged pipeline calls.

```
src/ui/
├── __init__.py
├── theme.py          # global CSS injection (fonts, resets, tokens)
├── backgrounds.py    # category palettes, SVG motifs, cycling layer
└── components.py     # hero, category chips, CTA, stage cards, result cards
```

Each module exposes small functions that return HTML strings and call
`st.markdown(html, unsafe_allow_html=True)` — no custom Streamlit
components, no iframes, no extra processes.

## Components

### 1. Theme (`src/ui/theme.py`)

`inject_theme()` — called once at the top of `app.py`. Injects:

- Google Fonts: Space Grotesk (display) + Inter (body) + JetBrains Mono
  (numerics).
- CSS custom properties (design tokens): palette per category, radii, shadow
  scale, motion curves.
- Global resets: remove the Streamlit hamburger/footer, make the main block
  transparent so backgrounds show through, tighten default spacing.
- Reusable classes: `.mp-card`, `.mp-chip`, `.mp-chip--active`, `.mp-cta`,
  `.mp-stage`, `.mp-metric`, `.mp-pill`, `.mp-speaker-alex`,
  `.mp-speaker-sam`.

### 2. Backgrounds (`src/ui/backgrounds.py`)

`render_background(selected_categories: list[PodcastCategory])` — emits a
fixed full-viewport layer behind all content (`z-index: -1`).

Per-category config:

| Category | Palette | Motif |
|---|---|---|
| Finance Macro | Deep emerald → gold | Candlestick silhouettes drifting up |
| Finance Micro | Electric blue → cyan | Looping sparkline curves |
| Crypto | Neon orange → magenta | Hex-dot particles + radial glow |
| Geopolitics | Crimson → deep purple | Radar rings + meridian lines |
| AI Updates | Electric violet → cyan | Pulsing neural-net nodes |

Rules:

- If `selected_categories` is empty → neutral dark-slate mesh, no motif.
- If one category selected → static background for that category.
- If 2+ selected → cycle: each theme visible for 10s with a 1.2s
  cross-fade. Implemented via keyframed `opacity` on stacked layers (no
  JavaScript).
- All motifs are inline SVG strings or pure CSS. No external assets.

### 3. Components (`src/ui/components.py`)

- `render_hero(date_str)` — big gradient wordmark + date pill. Replaces
  `st.title` / `st.caption`.
- `render_category_chips(selected: list[PodcastCategory])` — **replaces the
  sidebar multiselect**. Renders tappable gradient chips in the main column.
  Click toggles selection with a scale-pulse animation. Returns the updated
  selection list. Internally uses Streamlit buttons styled via CSS, with
  selection state held in `st.session_state.selected_categories`.
- `render_control_deck(config, voice_options)` — the existing sidebar
  content (API status dots, podcast settings, voice pickers, reset) in a
  cleaner, tighter style.
- `render_cta(disabled, label)` — pill-shaped gradient button. Wraps
  `st.button` with a CSS class.
- `render_stage_card(stage_num, title, state, elapsed)` — replaces
  `st.status` visuals with a horizontal card that fills with gradient on
  completion.
- `render_metric_card(label, value, delta=None)` — replaces `st.metric` with
  bigger, gradient-numeric styling.
- `render_speaker_bubble(speaker, emotion, text)` — upgraded script-tab
  bubbles (bigger padding, rounder corners, speaker avatar dot).

## Data flow

Unchanged. `app.py` still:

1. Loads config (`load_config`).
2. Builds `CategoryCollectorRouter`, calls `collect_all()`.
3. Instantiates `ScriptGenerator`, calls `generate()`.
4. Instantiates `KokoroEngine`, calls `generate_audio()`.
5. Saves MP3 via `AudioProcessor`.
6. Optional email via `send_episode_email`.

The UI layer wraps these calls but passes the same arguments. Every
session-state key (`snapshot`, `script`, `mp3_path`, `stage_times`,
`has_run`, `selected_voice_s1`, `selected_voice_s2`) is preserved.

One new session-state key: `selected_categories` (list[str]) — replaces the
transient multiselect value but holds the same data type the downstream code
expects.

## Error handling

- Missing API key: red glowing dot next to the key label in the control deck
  (same keys_ok gate as today).
- No categories selected: CTA disabled + a glassy warning card with a soft
  pulse.
- Pipeline exception: existing Streamlit error surface is kept; we just wrap
  it in the new `mp-card` class so it matches the style.
- Background SVG must never block clicks (`pointer-events: none`).

## Testing

Priority is functional regression — the pipeline must still generate an
episode end-to-end after the redesign.

1. **Unit:** `tests/test_ui_theme.py` — `inject_theme()` returns/streams
   valid non-empty CSS; no Streamlit runtime required.
2. **Unit:** `tests/test_ui_backgrounds.py` — `render_background([])`,
   single-category, and multi-category paths each produce an HTML string
   containing the expected palette custom properties.
3. **Wiring regression:** `tests/test_pipeline_wiring.py` (already exists)
   must still pass — confirms collector/generator/engine contracts.
4. **Manual smoke:** `streamlit run app.py` — run a real Finance Macro +
   Crypto episode; verify backgrounds cycle, chips toggle, CTA generates,
   audio plays, email sends.
5. **Browser check:** screenshot the UI in Chrome at 1440px and 1024px; no
   overlap, no horizontal scroll, backgrounds don't intercept clicks.

## Risks

- **Streamlit CSS fragility:** class names inside Streamlit can change
  between versions. Mitigation: target stable semantic selectors
  (`[data-testid]`) and our own `.mp-*` classes; document pinning concerns
  in `ARCHITECTURE.md`.
- **Performance:** animated backgrounds on every frame cost GPU. Mitigation:
  `transform`/`opacity` only (no layout thrash), `will-change: opacity`,
  respect `prefers-reduced-motion` (freeze cycling, keep palette).
- **Chip-vs-multiselect parity:** the custom chip selector must produce the
  same list the downstream code consumes. Covered by wiring test.

## Open questions

None — creative direction confirmed by user 2026-04-19.
