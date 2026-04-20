# Market Pulse UI Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh the Market Pulse Streamlit UI to a bold Gen-Z fintech aesthetic with category-reactive cycling backgrounds, without touching backend code.

**Architecture:** All new presentation code lives in a new `src/ui/` package (theme, backgrounds, components). `app.py` is rewritten as a thin composition layer around the unchanged pipeline calls. Zero new dependencies — pure CSS + inline SVG injected via `st.markdown(..., unsafe_allow_html=True)`.

**Tech Stack:** Streamlit, Python 3, HTML/CSS3 (animations via keyframes), inline SVG, pytest.

---

## File Structure

**Create:**
- `src/ui/__init__.py` — package marker + re-exports
- `src/ui/theme.py` — global CSS injection (`inject_theme()`)
- `src/ui/backgrounds.py` — `render_background(selected_categories)` + palette/motif data
- `src/ui/components.py` — hero, chips, control-deck, CTA, stage cards, metric cards, speaker bubbles
- `tests/test_ui_theme.py` — theme CSS sanity
- `tests/test_ui_backgrounds.py` — background rendering logic

**Modify:**
- `app.py` — replace inline UI code with calls to `src/ui/`

**Leave untouched:**
- `src/data/`, `src/script/`, `src/audio/`, `src/utils/`, `config.yaml`, every test in `tests/` except the new ones.

---

## Task 1: Scaffold `src/ui/` package

**Files:**
- Create: `src/ui/__init__.py`

- [ ] **Step 1: Create the package file**

```python
"""Market Pulse presentation layer.

All UI-only code (CSS injection, background rendering, component helpers)
lives here. Backend modules do not import from `src.ui`.
"""

from src.ui.theme import inject_theme
from src.ui.backgrounds import render_background
from src.ui import components

__all__ = ["inject_theme", "render_background", "components"]
```

- [ ] **Step 2: Verify import**

Run: `python -c "from src.ui import inject_theme, render_background, components; print('ok')"`
Expected: `ok` (will briefly fail until Tasks 2-3 land; OK — we'll re-check then)

---

## Task 2: Theme module with CSS injection

**Files:**
- Create: `src/ui/theme.py`
- Test: `tests/test_ui_theme.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ui_theme.py
import pytest
from src.ui.theme import build_theme_css


def test_build_theme_css_returns_non_empty_string():
    css = build_theme_css()
    assert isinstance(css, str)
    assert len(css) > 500


def test_build_theme_css_defines_category_palettes():
    css = build_theme_css()
    for cat in ("macro", "micro", "crypto", "geo", "ai"):
        assert f"--mp-{cat}-grad-start" in css
        assert f"--mp-{cat}-grad-end" in css


def test_build_theme_css_defines_component_classes():
    css = build_theme_css()
    for cls in (".mp-card", ".mp-chip", ".mp-cta", ".mp-stage",
                ".mp-metric", ".mp-pill", ".mp-speaker-alex",
                ".mp-speaker-sam", ".mp-hero"):
        assert cls in css


def test_build_theme_css_imports_fonts():
    css = build_theme_css()
    assert "fonts.googleapis.com" in css
    assert "Space Grotesk" in css
    assert "Inter" in css


def test_build_theme_css_respects_reduced_motion():
    css = build_theme_css()
    assert "prefers-reduced-motion" in css
```

- [ ] **Step 2: Run to confirm failure**

Run: `pytest tests/test_ui_theme.py -v`
Expected: ModuleNotFoundError on `src.ui.theme`.

- [ ] **Step 3: Implement `src/ui/theme.py`**

```python
"""Global theme CSS for Market Pulse.

Exposes `build_theme_css()` (testable, returns the CSS string) and
`inject_theme()` (calls st.markdown with the CSS wrapped in <style>).
"""

import streamlit as st


_FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;500;600;700&"
    "family=Space+Grotesk:wght@500;600;700&"
    "family=JetBrains+Mono:wght@500;600&display=swap');"
)


_TOKENS = """
:root {
    --mp-bg-base: #0b0c16;
    --mp-surface: rgba(255, 255, 255, 0.06);
    --mp-surface-strong: rgba(255, 255, 255, 0.10);
    --mp-border: rgba(255, 255, 255, 0.12);
    --mp-text: #f2f4ff;
    --mp-text-muted: rgba(242, 244, 255, 0.62);
    --mp-radius-sm: 10px;
    --mp-radius-md: 16px;
    --mp-radius-lg: 24px;
    --mp-shadow-soft: 0 8px 30px rgba(0, 0, 0, 0.35);
    --mp-shadow-glow: 0 0 32px rgba(150, 80, 255, 0.35);
    --mp-ease: cubic-bezier(0.2, 0.8, 0.2, 1);

    --mp-macro-grad-start: #0fbf8f;
    --mp-macro-grad-end:   #f5c518;
    --mp-micro-grad-start: #2b7bff;
    --mp-micro-grad-end:   #22d3ee;
    --mp-crypto-grad-start: #ff8a1f;
    --mp-crypto-grad-end:   #ff3ea5;
    --mp-geo-grad-start: #e03c3c;
    --mp-geo-grad-end:   #6b2bd9;
    --mp-ai-grad-start: #7a3cff;
    --mp-ai-grad-end:   #22d3ee;

    --mp-hero-grad: linear-gradient(120deg, #22d3ee, #7a3cff 40%, #ff3ea5 80%, #f5c518);
}
"""


_RESET = """
html, body, [data-testid="stAppViewContainer"] {
    background: transparent !important;
    color: var(--mp-text);
    font-family: 'Inter', system-ui, sans-serif;
}
[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stAppViewContainer"] > .main { padding-top: 1.2rem; }
section[data-testid="stSidebar"] > div {
    background: rgba(11, 12, 22, 0.72);
    backdrop-filter: blur(14px);
    border-right: 1px solid var(--mp-border);
}
[data-testid="stMarkdownContainer"] p { color: var(--mp-text); }
h1, h2, h3, h4 { font-family: 'Space Grotesk', 'Inter', sans-serif; }
code, .mp-numeric { font-family: 'JetBrains Mono', ui-monospace, monospace; }
"""


_COMPONENTS = """
.mp-hero {
    padding: 2.2rem 1rem 1.4rem;
    margin-bottom: 0.8rem;
}
.mp-hero h1 {
    font-size: clamp(2.6rem, 6vw, 4.4rem);
    font-weight: 700;
    line-height: 1.02;
    letter-spacing: -0.02em;
    margin: 0;
    background: var(--mp-hero-grad);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.mp-hero .mp-subtitle {
    color: var(--mp-text-muted);
    font-size: 1.05rem;
    margin-top: 0.3rem;
}
.mp-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.32rem 0.8rem;
    border-radius: 999px;
    background: var(--mp-surface);
    border: 1px solid var(--mp-border);
    color: var(--mp-text);
    font-size: 0.85rem;
    font-weight: 500;
}

.mp-card {
    background: var(--mp-surface);
    border: 1px solid var(--mp-border);
    border-radius: var(--mp-radius-md);
    padding: 1.1rem 1.2rem;
    backdrop-filter: blur(14px);
    box-shadow: var(--mp-shadow-soft);
    transition: transform 220ms var(--mp-ease), border-color 220ms var(--mp-ease);
}
.mp-card:hover { transform: translateY(-2px); border-color: rgba(255,255,255,0.22); }

.mp-chip-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.6rem;
    margin: 0.6rem 0 1.1rem;
}
/* Streamlit button override used by render_category_chips */
div.stButton > button.mp-chip, div.stButton > button[kind="secondary"].mp-chip {
    width: 100%;
    border-radius: 999px;
    padding: 0.55rem 0.9rem;
    font-weight: 600;
    letter-spacing: 0.01em;
    background: var(--mp-surface);
    color: var(--mp-text);
    border: 1px solid var(--mp-border);
    transition: transform 180ms var(--mp-ease), box-shadow 180ms var(--mp-ease);
}
div.stButton > button.mp-chip:hover { transform: scale(1.02); }
div.stButton > button.mp-chip--active {
    color: #0b0c16;
    border-color: transparent;
    box-shadow: 0 6px 20px rgba(122, 60, 255, 0.35);
}

/* Gradient CTA */
div.stButton > button[kind="primary"] {
    border: none !important;
    border-radius: 999px !important;
    padding: 0.85rem 1.2rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.01em;
    color: #0b0c16 !important;
    background: var(--mp-hero-grad) !important;
    box-shadow: var(--mp-shadow-glow);
    transition: transform 200ms var(--mp-ease), box-shadow 200ms var(--mp-ease);
}
div.stButton > button[kind="primary"]:hover:not(:disabled) {
    transform: translateY(-1px) scale(1.01);
    box-shadow: 0 0 42px rgba(255, 62, 165, 0.45);
}
div.stButton > button[kind="primary"]:disabled {
    filter: grayscale(40%) opacity(0.5);
    box-shadow: none;
}

.mp-stage {
    display: flex;
    align-items: center;
    gap: 0.9rem;
    padding: 0.85rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: var(--mp-radius-md);
    border: 1px solid var(--mp-border);
    background: var(--mp-surface);
    position: relative;
    overflow: hidden;
}
.mp-stage .mp-stage-num {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    color: var(--mp-text-muted);
}
.mp-stage.mp-stage--done {
    border-color: transparent;
    background: linear-gradient(110deg, rgba(34, 211, 238, 0.22), rgba(122, 60, 255, 0.22));
}
.mp-stage.mp-stage--active::before {
    content: "";
    position: absolute; inset: 0;
    background: linear-gradient(110deg, transparent, rgba(122, 60, 255, 0.25), transparent);
    animation: mp-sweep 1.6s linear infinite;
}
@keyframes mp-sweep { 0%{transform:translateX(-60%);} 100%{transform:translateX(60%);} }

.mp-metric {
    background: var(--mp-surface);
    border: 1px solid var(--mp-border);
    border-radius: var(--mp-radius-md);
    padding: 0.9rem 1.1rem;
}
.mp-metric .mp-metric-label {
    font-size: 0.78rem;
    color: var(--mp-text-muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.mp-metric .mp-metric-value {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 2rem;
    background: var(--mp-hero-grad);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    margin-top: 0.1rem;
}
.mp-metric .mp-metric-delta {
    font-size: 0.85rem;
    color: var(--mp-text-muted);
}

.mp-speaker-alex, .mp-speaker-sam {
    margin: 0.45rem 0;
    padding: 0.85rem 1.1rem;
    border-radius: 18px;
    border: 1px solid var(--mp-border);
    background: var(--mp-surface);
    max-width: 92%;
}
.mp-speaker-alex { border-left: 3px solid #22d3ee; }
.mp-speaker-sam  { border-left: 3px solid #ff3ea5; margin-left: 8%; }
.mp-speaker-alex strong { color: #22d3ee; }
.mp-speaker-sam  strong { color: #ff3ea5; }
.mp-emotion { opacity: 0.55; font-size: 0.85em; margin-left: 0.35rem; }

.mp-status-dot {
    display: inline-block; width: 8px; height: 8px; border-radius: 50%;
    margin-right: 0.4rem; vertical-align: middle;
}
.mp-status-dot--ok { background: #22c55e; box-shadow: 0 0 10px #22c55e; }
.mp-status-dot--miss { background: #ef4444; box-shadow: 0 0 10px #ef4444; animation: mp-pulse 1.6s ease-in-out infinite; }
@keyframes mp-pulse { 0%,100%{opacity:1;} 50%{opacity:0.35;} }

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.001ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.001ms !important;
    }
}
"""


def build_theme_css() -> str:
    """Return the full theme CSS string (without <style> tags)."""
    return "\n".join([_FONT_IMPORT, _TOKENS, _RESET, _COMPONENTS])


def inject_theme() -> None:
    """Inject the theme CSS into the current Streamlit page."""
    st.markdown(f"<style>{build_theme_css()}</style>", unsafe_allow_html=True)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_ui_theme.py -v`
Expected: 5 passed.

---

## Task 3: Backgrounds module

**Files:**
- Create: `src/ui/backgrounds.py`
- Test: `tests/test_ui_backgrounds.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ui_backgrounds.py
import pytest

from src.data.categories import PodcastCategory
from src.ui.backgrounds import (
    build_background_html,
    CATEGORY_THEMES,
)


def test_all_categories_have_themes():
    for cat in PodcastCategory:
        assert cat in CATEGORY_THEMES
        theme = CATEGORY_THEMES[cat]
        assert theme.grad_start.startswith("#")
        assert theme.grad_end.startswith("#")
        assert "<svg" in theme.motif_svg


def test_empty_selection_renders_neutral_layer():
    html = build_background_html([])
    assert "mp-bg-root" in html
    assert "mp-bg-neutral" in html


def test_single_category_renders_static_layer():
    html = build_background_html([PodcastCategory.CRYPTO])
    theme = CATEGORY_THEMES[PodcastCategory.CRYPTO]
    assert theme.grad_start in html
    assert "mp-bg-cycle" not in html  # no cycle keyframes needed for single


def test_multi_category_renders_cycle_layers():
    html = build_background_html(
        [PodcastCategory.CRYPTO, PodcastCategory.AI_UPDATES]
    )
    assert "mp-bg-cycle" in html
    assert CATEGORY_THEMES[PodcastCategory.CRYPTO].grad_start in html
    assert CATEGORY_THEMES[PodcastCategory.AI_UPDATES].grad_start in html


def test_background_layer_is_behind_content_and_non_interactive():
    html = build_background_html([PodcastCategory.FINANCE_MACRO])
    assert "pointer-events: none" in html
    assert "z-index: -1" in html or "z-index:-1" in html
```

- [ ] **Step 2: Run to confirm failure**

Run: `pytest tests/test_ui_backgrounds.py -v`
Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement `src/ui/backgrounds.py`**

```python
"""Category-reactive cycling background for Market Pulse.

`build_background_html(selected)` returns a self-contained HTML string
(with <style>) that renders a fixed full-viewport layer behind all
content. Multiple selections cycle through themes with crossfades.
"""

from dataclasses import dataclass
from typing import Iterable
import streamlit as st

from src.data.categories import PodcastCategory


@dataclass(frozen=True)
class CategoryTheme:
    grad_start: str
    grad_end: str
    accent: str
    motif_svg: str


# ── Motif SVGs ──────────────────────────────────────────────────
_MOTIF_MACRO = """
<svg viewBox="0 0 1200 800" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">
  <g fill="none" stroke="rgba(245,197,24,0.18)" stroke-width="2">
    <rect x="120" y="300" width="10" height="120"/>
    <line x1="125" y1="270" x2="125" y2="450" stroke-width="1"/>
    <rect x="240" y="340" width="10" height="80" fill="rgba(15,191,143,0.25)"/>
    <line x1="245" y1="310" x2="245" y2="440" stroke-width="1"/>
    <rect x="360" y="260" width="10" height="140"/>
    <line x1="365" y1="240" x2="365" y2="430" stroke-width="1"/>
    <rect x="480" y="380" width="10" height="60" fill="rgba(15,191,143,0.22)"/>
    <line x1="485" y1="350" x2="485" y2="470" stroke-width="1"/>
    <rect x="640" y="290" width="10" height="130"/>
    <line x1="645" y1="260" x2="645" y2="450" stroke-width="1"/>
    <rect x="820" y="330" width="10" height="90" fill="rgba(15,191,143,0.25)"/>
    <line x1="825" y1="300" x2="825" y2="450" stroke-width="1"/>
    <rect x="980" y="270" width="10" height="150"/>
    <line x1="985" y1="240" x2="985" y2="450" stroke-width="1"/>
  </g>
</svg>
"""

_MOTIF_MICRO = """
<svg viewBox="0 0 1200 800" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">
  <g fill="none" stroke-width="2">
    <path d="M0,500 C200,460 280,420 400,380 S700,260 900,220 1100,180 1200,160"
          stroke="rgba(34,211,238,0.25)"/>
    <path d="M0,560 C180,540 340,500 500,460 S820,340 1000,320 1160,310 1200,300"
          stroke="rgba(43,123,255,0.22)"/>
    <path d="M0,620 C220,600 400,580 580,540 S880,440 1060,420 1180,410 1200,400"
          stroke="rgba(34,211,238,0.18)"/>
  </g>
</svg>
"""

_MOTIF_CRYPTO = """
<svg viewBox="0 0 1200 800" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">
  <defs>
    <radialGradient id="cGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="rgba(255,138,31,0.35)"/>
      <stop offset="100%" stop-color="rgba(255,62,165,0)"/>
    </radialGradient>
  </defs>
  <circle cx="600" cy="400" r="420" fill="url(#cGlow)"/>
  <g fill="rgba(255,62,165,0.22)">
    <circle cx="160" cy="180" r="3"/>
    <circle cx="320" cy="620" r="2"/>
    <circle cx="520" cy="140" r="3"/>
    <circle cx="760" cy="280" r="4"/>
    <circle cx="980" cy="520" r="2"/>
    <circle cx="1080" cy="220" r="3"/>
    <circle cx="240" cy="420" r="2"/>
    <circle cx="860" cy="680" r="3"/>
  </g>
</svg>
"""

_MOTIF_GEO = """
<svg viewBox="0 0 1200 800" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">
  <g fill="none" stroke="rgba(224,60,60,0.18)">
    <circle cx="600" cy="400" r="120"/>
    <circle cx="600" cy="400" r="220"/>
    <circle cx="600" cy="400" r="320"/>
    <circle cx="600" cy="400" r="420"/>
  </g>
  <g fill="none" stroke="rgba(107,43,217,0.16)">
    <path d="M200,0 Q200,400 200,800"/>
    <path d="M400,0 Q400,400 400,800"/>
    <path d="M800,0 Q800,400 800,800"/>
    <path d="M1000,0 Q1000,400 1000,800"/>
    <path d="M0,200 Q600,200 1200,200"/>
    <path d="M0,600 Q600,600 1200,600"/>
  </g>
</svg>
"""

_MOTIF_AI = """
<svg viewBox="0 0 1200 800" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">
  <g stroke="rgba(122,60,255,0.25)" stroke-width="1.2" fill="none">
    <line x1="180" y1="200" x2="420" y2="340"/>
    <line x1="420" y1="340" x2="640" y2="220"/>
    <line x1="420" y1="340" x2="620" y2="500"/>
    <line x1="640" y1="220" x2="880" y2="320"/>
    <line x1="620" y1="500" x2="880" y2="560"/>
    <line x1="880" y1="320" x2="880" y2="560"/>
    <line x1="880" y1="320" x2="1080" y2="260"/>
    <line x1="880" y1="560" x2="1040" y2="640"/>
  </g>
  <g fill="rgba(34,211,238,0.55)">
    <circle cx="180" cy="200" r="4"/>
    <circle cx="420" cy="340" r="5"/>
    <circle cx="640" cy="220" r="4"/>
    <circle cx="620" cy="500" r="4"/>
    <circle cx="880" cy="320" r="5"/>
    <circle cx="880" cy="560" r="4"/>
    <circle cx="1080" cy="260" r="3"/>
    <circle cx="1040" cy="640" r="3"/>
  </g>
</svg>
"""

CATEGORY_THEMES: dict[PodcastCategory, CategoryTheme] = {
    PodcastCategory.FINANCE_MACRO: CategoryTheme(
        grad_start="#0fbf8f", grad_end="#f5c518",
        accent="#f5c518", motif_svg=_MOTIF_MACRO,
    ),
    PodcastCategory.FINANCE_MICRO: CategoryTheme(
        grad_start="#2b7bff", grad_end="#22d3ee",
        accent="#22d3ee", motif_svg=_MOTIF_MICRO,
    ),
    PodcastCategory.CRYPTO: CategoryTheme(
        grad_start="#ff8a1f", grad_end="#ff3ea5",
        accent="#ff3ea5", motif_svg=_MOTIF_CRYPTO,
    ),
    PodcastCategory.GEOPOLITICS: CategoryTheme(
        grad_start="#e03c3c", grad_end="#6b2bd9",
        accent="#e03c3c", motif_svg=_MOTIF_GEO,
    ),
    PodcastCategory.AI_UPDATES: CategoryTheme(
        grad_start="#7a3cff", grad_end="#22d3ee",
        accent="#7a3cff", motif_svg=_MOTIF_AI,
    ),
}


_NEUTRAL_GRAD = "linear-gradient(135deg, #0b0c16 0%, #141a2e 60%, #1b1640 100%)"


_BASE_STYLE = """
<style>
.mp-bg-root {
    position: fixed;
    inset: 0;
    z-index: -1;
    pointer-events: none;
    overflow: hidden;
    background: #0b0c16;
}
.mp-bg-layer {
    position: absolute;
    inset: 0;
    background-size: 200% 200%;
    animation: mp-bg-drift 18s ease-in-out infinite alternate;
}
.mp-bg-layer .mp-motif {
    position: absolute;
    inset: 0;
    opacity: 0.7;
    mix-blend-mode: screen;
}
.mp-bg-layer .mp-motif svg { width: 100%; height: 100%; display: block; }
.mp-bg-grain {
    position: absolute; inset: 0;
    background-image:
        radial-gradient(rgba(255,255,255,0.04) 1px, transparent 1px);
    background-size: 3px 3px;
    opacity: 0.45;
}
.mp-bg-neutral { background: """ + _NEUTRAL_GRAD + """; }
@keyframes mp-bg-drift {
    0%   { background-position: 0% 0%; }
    100% { background-position: 100% 100%; }
}
@media (prefers-reduced-motion: reduce) {
    .mp-bg-layer { animation: none; }
}
</style>
"""


def _grad_for(theme: CategoryTheme) -> str:
    return f"linear-gradient(135deg, {theme.grad_start} 0%, {theme.grad_end} 100%)"


def _layer_html(theme: CategoryTheme, style: str = "") -> str:
    return (
        f'<div class="mp-bg-layer" style="background-image:{_grad_for(theme)};{style}">'
        f'<div class="mp-motif">{theme.motif_svg}</div>'
        f'</div>'
    )


def build_background_html(selected: Iterable[PodcastCategory]) -> str:
    """Return the full <style>+<div> HTML for the background layer."""
    selected = list(selected)
    if not selected:
        return (
            _BASE_STYLE
            + '<div class="mp-bg-root">'
            + '<div class="mp-bg-layer mp-bg-neutral"></div>'
            + '<div class="mp-bg-grain"></div>'
            + '</div>'
        )

    if len(selected) == 1:
        theme = CATEGORY_THEMES[selected[0]]
        return (
            _BASE_STYLE
            + '<div class="mp-bg-root">'
            + _layer_html(theme)
            + '<div class="mp-bg-grain"></div>'
            + '</div>'
        )

    # Multi: build per-layer keyframes that cycle through opacity windows.
    n = len(selected)
    total_s = n * 10  # 10s per theme
    fade_s = 1.2
    # Each layer is visible for (10s - fade) fully, fades in/out at the edges.
    keyframes = []
    layers = []
    for idx, cat in enumerate(selected):
        theme = CATEGORY_THEMES[cat]
        anim_name = f"mp-bg-cycle-{idx}"
        start_pct = (idx * 10 / total_s) * 100
        end_pct = ((idx * 10 + 10) / total_s) * 100
        fade_pct = (fade_s / total_s) * 100
        kf = f"""
@keyframes {anim_name} {{
    0% {{ opacity: 0; }}
    {max(0.0, start_pct - fade_pct):.2f}% {{ opacity: 0; }}
    {start_pct:.2f}% {{ opacity: 1; }}
    {max(start_pct, end_pct - fade_pct):.2f}% {{ opacity: 1; }}
    {end_pct:.2f}% {{ opacity: 0; }}
    100% {{ opacity: 0; }}
}}
"""
        keyframes.append(kf)
        style = (
            f"animation: {anim_name} {total_s}s linear infinite;"
            f"opacity: 0;"
        )
        layers.append(_layer_html(theme, style=style))

    cycle_style = "<style>" + "\n".join(keyframes) + "</style>"
    # Keep the first layer also visible immediately so the page isn't blank
    # during the first keyframe cycle setup: mark the root with mp-bg-cycle.
    return (
        _BASE_STYLE
        + cycle_style
        + '<div class="mp-bg-root mp-bg-cycle">'
        + "".join(layers)
        + '<div class="mp-bg-grain"></div>'
        + '</div>'
    )


def render_background(selected: Iterable[PodcastCategory]) -> None:
    """Inject the category background layer into the page."""
    st.markdown(build_background_html(selected), unsafe_allow_html=True)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_ui_backgrounds.py -v`
Expected: 5 passed.

---

## Task 4: Components module

**Files:**
- Create: `src/ui/components.py`

- [ ] **Step 1: Implement components**

```python
"""Reusable UI components for Market Pulse.

All functions take primitives/config and render via st.markdown/st.button.
No component owns global state — selection lives in st.session_state.
"""

from __future__ import annotations

from typing import Iterable
import streamlit as st

from src.data.categories import (
    PodcastCategory, CATEGORY_LABELS, CATEGORY_DESCRIPTIONS,
)
from src.ui.backgrounds import CATEGORY_THEMES


def render_hero(date_str: str) -> None:
    st.markdown(
        f"""
        <div class="mp-hero">
          <h1>Market Pulse</h1>
          <div class="mp-subtitle">
            Your daily AI-generated market briefing.
            <span class="mp-pill">📅 {date_str}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_category_chips(
    key_prefix: str = "cat_chip",
) -> list[PodcastCategory]:
    """Render toggleable gradient chips. Returns current selection.

    Selection is persisted in st.session_state['selected_categories'] as a
    list of PodcastCategory values (strings). Caller should pass the initial
    default in via session_state before first render.
    """
    state_key = "selected_categories"
    if state_key not in st.session_state:
        st.session_state[state_key] = []

    selected_values: list[str] = list(st.session_state[state_key])

    st.markdown(
        '<div class="mp-section-title">Choose your topics</div>',
        unsafe_allow_html=True,
    )

    # Grid of buttons — we rely on CSS class injection via the `help` arg
    # isn't an option; instead we wrap each button in a styled container and
    # style all stButton > button inside via our global CSS.
    cols = st.columns(len(PodcastCategory))
    for col, cat in zip(cols, list(PodcastCategory)):
        is_active = cat.value in selected_values
        theme = CATEGORY_THEMES[cat]
        label = CATEGORY_LABELS[cat]
        with col:
            # Inline style so each chip can paint its own gradient when active.
            active_style = (
                f"<style>div[data-testid='stButton'] > button#{key_prefix}_{cat.value} "
                f"{{ background: linear-gradient(135deg, {theme.grad_start}, {theme.grad_end}) !important; "
                f"color: #0b0c16 !important; border: none !important; }}</style>"
                if is_active else ""
            )
            st.markdown(active_style, unsafe_allow_html=True)
            clicked = st.button(
                ("✓ " if is_active else "") + label,
                key=f"{key_prefix}_{cat.value}",
                use_container_width=True,
            )
            if clicked:
                if is_active:
                    selected_values.remove(cat.value)
                else:
                    selected_values.append(cat.value)
                st.session_state[state_key] = selected_values
                st.rerun()

    return [PodcastCategory(v) for v in selected_values]


def render_category_descriptions(selected: Iterable[PodcastCategory]) -> None:
    items = list(selected)
    if not items:
        return
    rows = "".join(
        f'<div class="mp-card" style="margin-bottom:0.5rem">'
        f'<strong>{CATEGORY_LABELS[c]}</strong>'
        f'<div class="mp-subtitle" style="font-size:0.9rem">{CATEGORY_DESCRIPTIONS[c]}</div>'
        f'</div>'
        for c in items
    )
    st.markdown(rows, unsafe_allow_html=True)


def render_api_status(required_keys, config, key_labels) -> bool:
    ok = True
    html_parts = ['<div class="mp-card"><strong>API status</strong><div style="margin-top:0.5rem">']
    for key_name in sorted(required_keys):
        label = key_labels.get(key_name, key_name)
        val = config.get(key_name, "")
        placeholder = f"your_{key_name.replace('_api_key', '')}_key_here"
        loaded = bool(val and val != placeholder)
        cls = "mp-status-dot--ok" if loaded else "mp-status-dot--miss"
        status_txt = "loaded" if loaded else "missing"
        html_parts.append(
            f'<div style="margin:0.2rem 0"><span class="mp-status-dot {cls}"></span>'
            f'{label}: <span class="mp-subtitle" style="font-size:0.9rem">{status_txt}</span></div>'
        )
        if not loaded:
            ok = False
    html_parts.append('</div></div>')
    st.markdown("".join(html_parts), unsafe_allow_html=True)
    return ok


def render_stage_card(stage_num: int, total: int, title: str,
                      state: str, elapsed_s: float | None = None) -> None:
    """state: 'pending' | 'active' | 'done'."""
    cls = "mp-stage"
    if state == "done":
        cls += " mp-stage--done"
    elif state == "active":
        cls += " mp-stage--active"
    elapsed_txt = (
        f'<span class="mp-subtitle" style="margin-left:auto">{elapsed_s:.1f}s</span>'
        if elapsed_s is not None else ""
    )
    st.markdown(
        f'<div class="{cls}">'
        f'<span class="mp-stage-num">{stage_num}/{total}</span>'
        f'<span><strong>{title}</strong></span>'
        f'{elapsed_txt}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_metric(label: str, value: str, delta: str | None = None) -> None:
    delta_html = f'<div class="mp-metric-delta">{delta}</div>' if delta else ""
    st.markdown(
        f'<div class="mp-metric">'
        f'<div class="mp-metric-label">{label}</div>'
        f'<div class="mp-metric-value">{value}</div>'
        f'{delta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_speaker_line(speaker: str, emotion: str | None, text: str) -> None:
    cls = "mp-speaker-alex" if speaker == "S1" else "mp-speaker-sam"
    name = "Alex" if speaker == "S1" else "Sam"
    emo = f'<span class="mp-emotion">[{emotion}]</span>' if emotion else ""
    st.markdown(
        f'<div class="{cls}"><strong>{name}:</strong>{emo} {text}</div>',
        unsafe_allow_html=True,
    )


def render_warning_card(message: str) -> None:
    st.markdown(
        f'<div class="mp-card" style="border-color: rgba(255,165,0,0.5)">⚠️ {message}</div>',
        unsafe_allow_html=True,
    )


def render_success_card(message: str) -> None:
    st.markdown(
        f'<div class="mp-card" style="border-color: rgba(34,197,94,0.55)">✅ {message}</div>',
        unsafe_allow_html=True,
    )
```

- [ ] **Step 2: Verify import**

Run: `python -c "from src.ui import inject_theme, render_background, components; print('ok')"`
Expected: `ok`

---

## Task 5: Rewrite `app.py`

**Files:**
- Modify: `app.py` (full rewrite of presentation; keep pipeline calls identical)

- [ ] **Step 1: Replace app.py**

Rewrite `app.py` so it:
1. `inject_theme()` before anything else
2. `render_background(selected)` once the categories are known (but before the body, so it renders behind)
3. `render_hero(date)` instead of `st.title/caption`
4. `render_category_chips()` in the main column (replaces `st.multiselect`)
5. Sidebar: keeps API key status (via `render_api_status`), voice pickers, podcast settings, reset
6. CTA: a single `st.button(type="primary", ...)` (picks up our CSS)
7. Stage cards: after each pipeline stage completes, append a `render_stage_card(..., state='done')`
8. Results tabs: wrap contents in `mp-card` divs; use `render_metric` + `render_speaker_line`
9. **Preserve** every pipeline call verbatim (CategoryCollectorRouter, ScriptGenerator, KokoroEngine, AudioProcessor, send_episode_email), every session-state key, and the cache.

Full code in the implementation step below. Key invariants:
- Default selection seeded from `DEFAULT_CATEGORIES` if `selected_categories` session key absent.
- `selected_categories` in session state is a list of category `.value` strings, converted to enum via `PodcastCategory(v)` for pipeline calls.
- Generate button's `disabled` gate keeps same three conditions: keys_ok, not has_run, selected non-empty.

- [ ] **Step 2: Implement**

```python
# app.py
import os
import time
from datetime import datetime

import streamlit as st
import yaml
from dotenv import load_dotenv

from src.data.categories import (
    PodcastCategory, CATEGORY_LABELS,
    CATEGORY_API_KEYS, API_KEY_LABELS, DEFAULT_CATEGORIES,
)
from src.data.collector_router import CategoryCollectorRouter
from src.script.generator import ScriptGenerator
from src.audio.kokoro_engine import KokoroEngine
from src.audio.processor import AudioProcessor
from src.audio.voice_blender import VOICE_CATALOG, voice_label
from src.utils.email_sender import send_episode_email

from src.ui import inject_theme, render_background
from src.ui.components import (
    render_hero, render_category_chips, render_category_descriptions,
    render_api_status, render_stage_card, render_metric,
    render_speaker_line, render_warning_card, render_success_card,
)


st.set_page_config(page_title="Market Pulse", page_icon="🎙️", layout="wide")
inject_theme()


@st.cache_resource
def load_config():
    load_dotenv()
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    for env_key, cfg_key in [
        ("GEMINI_API_KEY", "gemini_api_key"),
        ("FRED_API_KEY", "fred_api_key"),
        ("GNEWS_API_KEY", "gnews_api_key"),
        ("CURRENTS_API_KEY", "currents_api_key"),
        ("NEWSDATA_API_KEY", "newsdata_api_key"),
        ("EMAIL_ADDRESS", "email_address"),
        ("EMAIL_APP_PASSWORD", "email_app_password"),
    ]:
        config[cfg_key] = os.getenv(env_key, "")
    return config


# Session state defaults
for key, val in [
    ("snapshot", None), ("script", None), ("mp3_path", None),
    ("stage_times", {}), ("has_run", False),
]:
    if key not in st.session_state:
        st.session_state[key] = val

if "selected_categories" not in st.session_state:
    st.session_state["selected_categories"] = [c.value for c in DEFAULT_CATEGORIES]

config = load_config()
date = datetime.now().strftime("%Y-%m-%d")

# Render background first (reads current selection from session_state)
current_selection_enums = [
    PodcastCategory(v) for v in st.session_state["selected_categories"]
]
render_background(current_selection_enums)

# Hero
render_hero(date)

# Main body: category chips
selected_categories = render_category_chips()

# Selected category descriptions as cards
render_category_descriptions(selected_categories)

# Sidebar: control deck
with st.sidebar:
    st.markdown("### Control Deck")

    required_keys = {"gemini_api_key"}
    for cat in selected_categories:
        for key_name in CATEGORY_API_KEYS.get(cat, []):
            required_keys.add(key_name)
    keys_ok = render_api_status(required_keys, config, API_KEY_LABELS)

    st.markdown("### Podcast")
    st.markdown(
        f'<div class="mp-card">'
        f'<div><strong>Name</strong> {config.get("podcast_name", "Market Pulse")}</div>'
        f'<div><strong>LLM</strong> {config.get("gemini_model", "gemini-2.5-flash")}</div>'
        f'<div><strong>Date</strong> {date}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Host Voices")
    male_voice_ids = [v["id"] for v in VOICE_CATALOG if v["gender"] == "male"]
    female_voice_ids = [v["id"] for v in VOICE_CATALOG if v["gender"] == "female"]
    configured_s1 = config.get("speaker_1_voice", "am_adam")
    configured_s2 = config.get("speaker_2_voice", "af_bella")
    s1_default_idx = male_voice_ids.index(configured_s1) if configured_s1 in male_voice_ids else 0
    s2_default_idx = female_voice_ids.index(configured_s2) if configured_s2 in female_voice_ids else 0
    selected_voice_s1 = st.selectbox(
        "Alex (Speaker 1)", options=male_voice_ids, index=s1_default_idx,
        format_func=voice_label,
    )
    selected_voice_s2 = st.selectbox(
        "Sam (Speaker 2)", options=female_voice_ids, index=s2_default_idx,
        format_func=voice_label,
    )
    st.session_state.selected_voice_s1 = selected_voice_s1
    st.session_state.selected_voice_s2 = selected_voice_s2

    if st.button("Reset", use_container_width=True):
        for k in ["snapshot", "script", "mp3_path", "stage_times", "has_run"]:
            st.session_state[k] = None if k != "stage_times" else {}
        st.session_state.has_run = False
        st.rerun()

# CTA
if not selected_categories:
    render_warning_card("Select at least one category to generate a podcast.")

run_pipeline = st.button(
    "⚡ Generate Episode",
    type="primary",
    use_container_width=True,
    disabled=(not keys_ok) or st.session_state.has_run or (not selected_categories),
)

# Pipeline
if run_pipeline:
    output_dir = config.get("output_dir", "output")
    os.makedirs(output_dir, exist_ok=True)
    cat_names = ", ".join(CATEGORY_LABELS[c] for c in selected_categories)

    # Stage 1: Data
    with st.status(f"Stage 1/3 — Collecting data for: {cat_names}...", expanded=True) as status:
        t0 = time.time()
        router = CategoryCollectorRouter(config, selected_categories)

        def on_status(msg):
            st.write(msg)

        snapshot = router.collect_all(status_callback=on_status)
        snapshot.save(os.path.join(output_dir, f"{date}-snapshot.json"))
        st.session_state.snapshot = snapshot
        elapsed = time.time() - t0
        st.session_state.stage_times["data"] = elapsed
        status.update(label=f"Stage 1/3 — Data collected ({elapsed:.1f}s)",
                      state="complete", expanded=False)

    # Stage 2: Script
    with st.status("Stage 2/3 — Generating podcast script...", expanded=True) as status:
        t0 = time.time()
        st.write(f"Sending data to Gemini ({config.get('gemini_model', 'gemini-2.5-flash')})...")
        generator = ScriptGenerator(
            api_key=config["gemini_api_key"],
            model=config.get("gemini_model", "gemini-2.5-flash"),
        )
        script = generator.generate(snapshot, selected_categories)
        word_count = len(script.split())
        st.write(f"Script generated: {word_count} words (~{word_count // 150} min episode)")
        script_path = os.path.join(output_dir, f"{date}-script.txt")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        st.session_state.script = script
        elapsed = time.time() - t0
        st.session_state.stage_times["script"] = elapsed
        status.update(label=f"Stage 2/3 — Script generated ({elapsed:.1f}s, {word_count} words)",
                      state="complete", expanded=False)

    # Stage 3: Audio
    with st.status("Stage 3/3 — Generating audio...", expanded=True) as status:
        t0 = time.time()
        st.write("Loading Kokoro-82M TTS model...")
        tts_cfg = config.get("tts", {}) or {}
        voice_s1 = st.session_state.get("selected_voice_s1", config.get("speaker_1_voice", "am_adam"))
        voice_s2 = st.session_state.get("selected_voice_s2", config.get("speaker_2_voice", "af_bella"))
        st.write(f"Voices: Alex = {voice_label(voice_s1)}  |  Sam = {voice_label(voice_s2)}")
        engine = KokoroEngine(
            voice_s1=voice_s1, voice_s2=voice_s2,
            speed=tts_cfg.get("base_speed", 1.0),
            enable_blending=tts_cfg.get("enable_blending", True),
            enable_prosody=tts_cfg.get("enable_prosody", True),
        )
        progress_bar = st.progress(0, text="Starting synthesis...")
        segment_log = st.empty()

        def on_progress(i, total, speaker, preview):
            pct = (i + 1) / total
            voice_name = "Alex" if speaker == "S1" else "Sam"
            progress_bar.progress(pct, text=f"Segment {i+1}/{total} ({voice_name})")
            segment_log.caption(f'"{preview}..."')

        audio, sample_rate = engine.generate_audio(
            script, sample_rate=config.get("sample_rate", 24000),
            on_progress=on_progress,
        )
        progress_bar.progress(1.0, text="Synthesis complete!")
        st.write("Encoding MP3...")
        processor = AudioProcessor(output_dir=output_dir)
        mp3_path = processor.save_mp3(
            audio=audio, sample_rate=sample_rate, date=date,
            podcast_name=config.get("podcast_name", "Market Pulse"),
        )
        st.session_state.mp3_path = mp3_path
        duration = len(audio) / sample_rate
        elapsed = time.time() - t0
        st.session_state.stage_times["audio"] = elapsed
        status.update(label=f"Stage 3/3 — Audio generated ({elapsed:.1f}s, {duration/60:.1f} min episode)",
                      state="complete", expanded=False)

    st.session_state.has_run = True
    st.balloons()
    st.rerun()

# Results
if st.session_state.has_run:
    render_success_card("Episode ready — listen, download, or send below.")

    # Stage summary cards
    times = st.session_state.stage_times
    labels = {"data": "Data Collection", "script": "Script Generation", "audio": "Audio Generation"}
    for i, key in enumerate(["data", "script", "audio"], start=1):
        elapsed = times.get(key)
        if elapsed is not None:
            render_stage_card(i, 3, labels[key], state="done", elapsed_s=elapsed)
    total = sum(times.values()) if times else 0
    if total:
        render_metric("Total Pipeline Time", f"{total/60:.1f} min")

    tab_audio, tab_data, tab_script = st.tabs(["🎧 Audio", "📊 Data", "📝 Script"])

    # Audio tab
    with tab_audio:
        mp3_path = st.session_state.mp3_path
        if mp3_path and os.path.exists(mp3_path):
            file_size = os.path.getsize(mp3_path) / (1024 * 1024)
            st.markdown(
                f'<div class="mp-card"><strong>{os.path.basename(mp3_path)}</strong>'
                f' <span class="mp-subtitle">({file_size:.1f} MB)</span></div>',
                unsafe_allow_html=True,
            )
            st.audio(mp3_path, format="audio/mp3")
            with open(mp3_path, "rb") as f:
                st.download_button(
                    "Download MP3", data=f, file_name=os.path.basename(mp3_path),
                    mime="audio/mpeg", use_container_width=True,
                )
            st.divider()
            st.markdown("### Send via Email")
            email_configured = (config.get("email_address", "") and
                                config.get("email_app_password", ""))
            if not email_configured:
                st.caption("Set EMAIL_ADDRESS and EMAIL_APP_PASSWORD in .env to enable.")
            email_col1, email_col2 = st.columns([3, 1])
            with email_col1:
                recipient = st.text_input(
                    "Recipient email", placeholder="recipient@example.com",
                    disabled=not email_configured,
                )
            with email_col2:
                st.markdown("<br>", unsafe_allow_html=True)
                send_clicked = st.button(
                    "Send", type="primary", use_container_width=True,
                    disabled=not email_configured or not recipient,
                )
            if send_clicked and recipient:
                with st.spinner("Sending email..."):
                    snapshot = st.session_state.snapshot
                    cat_names = snapshot.categories if snapshot else []
                    cat_labels = [c.replace("_", " ").title() for c in cat_names]
                    sent = send_episode_email(
                        mp3_path=mp3_path, recipient=recipient,
                        categories=cat_labels,
                        sender_email=config.get("email_address"),
                        sender_password=config.get("email_app_password"),
                    )
                if sent:
                    render_success_card(f"Episode sent to {recipient}!")
                else:
                    render_warning_card("Failed to send. Check EMAIL_ADDRESS and EMAIL_APP_PASSWORD in .env.")

    # Data tab — keep existing per-category rendering but wrap in a card
    with tab_data:
        snapshot = st.session_state.snapshot
        if snapshot:
            active_cats = ([PodcastCategory(c) for c in snapshot.categories]
                           if snapshot.categories else DEFAULT_CATEGORIES)
            _render_data_sections(snapshot, active_cats)

    # Script tab
    with tab_script:
        script = st.session_state.script
        if script:
            import re as _re
            word_count = len(script.split())
            render_metric("Word Count", f"{word_count:,}", delta=f"~{word_count // 150} min episode")
            st.divider()
            tag_re = _re.compile(r"^\[(S[12])(?::([a-z_]+))?\]\s*(.*)")
            for line in script.split("\n"):
                line = line.strip()
                if not line:
                    continue
                m = tag_re.match(line)
                if not m:
                    continue
                render_speaker_line(m.group(1), m.group(2), m.group(3))
```

The `_render_data_sections` helper is the existing data-tab content from the old `app.py`, extracted verbatim into a local function to keep app.py tidy. Include it in the file at module scope. (It uses `st.subheader`, `st.markdown(..., unsafe_allow_html=True)`, and the existing snapshot fields — no logic change.)

- [ ] **Step 3: Syntax check**

Run: `python -c "import ast; ast.parse(open('app.py').read())"`
Expected: no output (success).

- [ ] **Step 4: Streamlit import smoke**

Run: `python -c "import streamlit; exec(open('app.py').read())"`
Expected: may complain about `st.set_page_config` being called outside Streamlit — that's fine. No ImportError, no SyntaxError, no AttributeError from our modules.

A safer smoke test: `python -c "from src.ui import inject_theme, render_background; from src.ui.components import render_hero; print('ok')"`
Expected: `ok`.

---

## Task 6: Pipeline wiring regression

**Files:**
- Run: `tests/test_pipeline_wiring.py` (already exists in the repo)

- [ ] **Step 1: Run existing wiring tests**

Run: `pytest tests/test_pipeline_wiring.py -v`
Expected: all pass. If any fail, fix app.py.

- [ ] **Step 2: Run full test suite**

Run: `pytest -q`
Expected: all pass.

---

## Task 7: Manual smoke run

- [ ] **Step 1: Start Streamlit**

Run: `streamlit run app.py --server.headless true --server.port 8501 &`
Expected: server starts.

- [ ] **Step 2: Curl the page**

Run: `curl -sS http://localhost:8501/healthz` (Streamlit exposes `/healthz`)
Expected: `ok`.

Then GET `http://localhost:8501/` and confirm HTTP 200 with "Market Pulse" in the body. (Full interactive smoke is a manual step — the user should open the browser.)

- [ ] **Step 3: Stop server**

Kill the background process.

---

## Task 8: Final commit

- [ ] **Step 1: Ask user whether to commit**

Per user preference, do NOT auto-commit. Ask:
> "Implementation complete and tests pass. Commit now?"

If yes:

```bash
git add src/ui/ tests/test_ui_theme.py tests/test_ui_backgrounds.py app.py docs/superpowers/
git commit -m "feat: Gen-Z UI refresh with category-reactive backgrounds"
```
