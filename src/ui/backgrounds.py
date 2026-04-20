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
  <g fill="none" stroke="rgba(245,197,24,0.22)" stroke-width="2">
    <rect x="120" y="300" width="10" height="120"/>
    <line x1="125" y1="270" x2="125" y2="450" stroke-width="1"/>
    <rect x="240" y="340" width="10" height="80" fill="rgba(15,191,143,0.28)"/>
    <line x1="245" y1="310" x2="245" y2="440" stroke-width="1"/>
    <rect x="360" y="260" width="10" height="140"/>
    <line x1="365" y1="240" x2="365" y2="430" stroke-width="1"/>
    <rect x="480" y="380" width="10" height="60" fill="rgba(15,191,143,0.25)"/>
    <line x1="485" y1="350" x2="485" y2="470" stroke-width="1"/>
    <rect x="640" y="290" width="10" height="130"/>
    <line x1="645" y1="260" x2="645" y2="450" stroke-width="1"/>
    <rect x="820" y="330" width="10" height="90" fill="rgba(15,191,143,0.28)"/>
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
          stroke="rgba(34,211,238,0.32)"/>
    <path d="M0,560 C180,540 340,500 500,460 S820,340 1000,320 1160,310 1200,300"
          stroke="rgba(43,123,255,0.28)"/>
    <path d="M0,620 C220,600 400,580 580,540 S880,440 1060,420 1180,410 1200,400"
          stroke="rgba(34,211,238,0.22)"/>
  </g>
</svg>
"""

_MOTIF_CRYPTO = """
<svg viewBox="0 0 1200 800" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">
  <defs>
    <radialGradient id="cGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="rgba(255,138,31,0.42)"/>
      <stop offset="100%" stop-color="rgba(255,62,165,0)"/>
    </radialGradient>
  </defs>
  <circle cx="600" cy="400" r="420" fill="url(#cGlow)"/>
  <g fill="rgba(255,62,165,0.32)">
    <circle cx="160" cy="180" r="3"/>
    <circle cx="320" cy="620" r="2"/>
    <circle cx="520" cy="140" r="3"/>
    <circle cx="760" cy="280" r="4"/>
    <circle cx="980" cy="520" r="2"/>
    <circle cx="1080" cy="220" r="3"/>
    <circle cx="240" cy="420" r="2"/>
    <circle cx="860" cy="680" r="3"/>
    <circle cx="420" cy="540" r="2"/>
    <circle cx="700" cy="120" r="3"/>
  </g>
</svg>
"""

_MOTIF_GEO = """
<svg viewBox="0 0 1200 800" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">
  <g fill="none" stroke="rgba(224,60,60,0.22)">
    <circle cx="600" cy="400" r="120"/>
    <circle cx="600" cy="400" r="220"/>
    <circle cx="600" cy="400" r="320"/>
    <circle cx="600" cy="400" r="420"/>
  </g>
  <g fill="none" stroke="rgba(107,43,217,0.2)">
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
  <g stroke="rgba(122,60,255,0.32)" stroke-width="1.2" fill="none">
    <line x1="180" y1="200" x2="420" y2="340"/>
    <line x1="420" y1="340" x2="640" y2="220"/>
    <line x1="420" y1="340" x2="620" y2="500"/>
    <line x1="640" y1="220" x2="880" y2="320"/>
    <line x1="620" y1="500" x2="880" y2="560"/>
    <line x1="880" y1="320" x2="880" y2="560"/>
    <line x1="880" y1="320" x2="1080" y2="260"/>
    <line x1="880" y1="560" x2="1040" y2="640"/>
    <line x1="180" y1="200" x2="320" y2="100"/>
    <line x1="1080" y1="260" x2="1140" y2="400"/>
  </g>
  <g fill="rgba(34,211,238,0.7)">
    <circle cx="180" cy="200" r="4"/>
    <circle cx="420" cy="340" r="5"/>
    <circle cx="640" cy="220" r="4"/>
    <circle cx="620" cy="500" r="4"/>
    <circle cx="880" cy="320" r="5"/>
    <circle cx="880" cy="560" r="4"/>
    <circle cx="1080" cy="260" r="3"/>
    <circle cx="1040" cy="640" r="3"/>
    <circle cx="320" cy="100" r="3"/>
    <circle cx="1140" cy="400" r="3"/>
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
    opacity: 0.75;
    mix-blend-mode: screen;
}
.mp-bg-layer .mp-motif svg { width: 100%; height: 100%; display: block; }
.mp-bg-grain {
    position: absolute; inset: 0;
    background-image: radial-gradient(rgba(255,255,255,0.04) 1px, transparent 1px);
    background-size: 3px 3px;
    opacity: 0.4;
    mix-blend-mode: overlay;
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


def _layer_html(theme: CategoryTheme, extra_style: str = "") -> str:
    return (
        f'<div class="mp-bg-layer" style="background-image:{_grad_for(theme)};{extra_style}">'
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

    n = len(selected)
    total_s = n * 10  # 10s per theme
    fade_s = 1.2
    keyframes_blocks = []
    layers_html = []
    for idx, cat in enumerate(selected):
        theme = CATEGORY_THEMES[cat]
        anim_name = f"mp-bg-cycle-{idx}"
        start_pct = (idx * 10 / total_s) * 100
        end_pct = ((idx * 10 + 10) / total_s) * 100
        fade_pct = (fade_s / total_s) * 100
        kf = (
            f"@keyframes {anim_name} {{\n"
            f"  0% {{ opacity: 0; }}\n"
            f"  {max(0.0, start_pct - fade_pct):.2f}% {{ opacity: 0; }}\n"
            f"  {start_pct:.2f}% {{ opacity: 1; }}\n"
            f"  {max(start_pct, end_pct - fade_pct):.2f}% {{ opacity: 1; }}\n"
            f"  {end_pct:.2f}% {{ opacity: 0; }}\n"
            f"  100% {{ opacity: 0; }}\n"
            f"}}"
        )
        keyframes_blocks.append(kf)
        extra = (
            f"animation: {anim_name} {total_s}s linear infinite;"
            f"opacity: 0;"
        )
        layers_html.append(_layer_html(theme, extra_style=extra))

    cycle_style = "<style>" + "\n".join(keyframes_blocks) + "</style>"
    return (
        _BASE_STYLE
        + cycle_style
        + '<div class="mp-bg-root mp-bg-cycle">'
        + "".join(layers_html)
        + '<div class="mp-bg-grain"></div>'
        + '</div>'
    )


def render_background(selected: Iterable[PodcastCategory]) -> None:
    """Inject the category background layer into the page."""
    st.markdown(build_background_html(selected), unsafe_allow_html=True)
