"""Global theme CSS for Market Pulse.

Exposes `build_theme_css()` (testable, returns the raw CSS string) and
`inject_theme()` (wraps it in <style> and injects via st.markdown).
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
.mp-section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 1.1rem;
    color: var(--mp-text);
    letter-spacing: -0.01em;
    margin: 1.2rem 0 0.5rem;
}
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
    background-size: 200% 200%;
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    animation: mp-hero-shift 10s ease-in-out infinite alternate;
}
@keyframes mp-hero-shift {
    0%   { background-position: 0% 50%; }
    100% { background-position: 100% 50%; }
}
.mp-hero .mp-subtitle {
    color: var(--mp-text-muted);
    font-size: 1.05rem;
    margin-top: 0.35rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    flex-wrap: wrap;
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
    padding: 1rem 1.15rem;
    backdrop-filter: blur(14px);
    box-shadow: var(--mp-shadow-soft);
    transition: transform 220ms var(--mp-ease), border-color 220ms var(--mp-ease);
    margin-bottom: 0.5rem;
}
.mp-card:hover { transform: translateY(-2px); border-color: rgba(255,255,255,0.22); }

.mp-chip {
    /* Marker class for category chips, styled via div.stButton override below */
}
div.stButton > button {
    border-radius: 999px;
    font-weight: 600;
    transition: transform 180ms var(--mp-ease), box-shadow 180ms var(--mp-ease), background 200ms var(--mp-ease);
    background: var(--mp-surface);
    color: var(--mp-text);
    border: 1px solid var(--mp-border);
}
div.stButton > button:hover:not(:disabled) {
    transform: scale(1.02);
    border-color: rgba(255,255,255,0.28);
}

/* Gradient CTA (primary button) */
div.stButton > button[kind="primary"] {
    border: none !important;
    border-radius: 999px !important;
    padding: 0.85rem 1.2rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.01em;
    color: #0b0c16 !important;
    background: var(--mp-hero-grad) !important;
    background-size: 200% 200% !important;
    box-shadow: var(--mp-shadow-glow);
    animation: mp-cta-shift 8s ease-in-out infinite alternate;
}
@keyframes mp-cta-shift {
    0%   { background-position: 0% 50%; }
    100% { background-position: 100% 50%; }
}
div.stButton > button[kind="primary"]:hover:not(:disabled) {
    transform: translateY(-1px) scale(1.01);
    box-shadow: 0 0 42px rgba(255, 62, 165, 0.45);
}
div.stButton > button[kind="primary"]:disabled {
    filter: grayscale(40%) opacity(0.5);
    box-shadow: none;
    animation: none;
}

.mp-cta {
    /* Marker kept for completeness; real styling is on stButton[kind=primary] */
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
    backdrop-filter: blur(12px);
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
    margin-bottom: 0.6rem;
    backdrop-filter: blur(12px);
}
.mp-metric .mp-metric-label {
    font-size: 0.76rem;
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
    backdrop-filter: blur(12px);
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

/* Streamlit tab pills */
div[data-baseweb="tab-list"] {
    gap: 0.4rem;
    background: transparent;
}
button[data-baseweb="tab"] {
    border-radius: 999px !important;
    background: var(--mp-surface) !important;
    border: 1px solid var(--mp-border) !important;
    padding: 0.35rem 0.9rem !important;
    color: var(--mp-text) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: var(--mp-hero-grad) !important;
    color: #0b0c16 !important;
    border-color: transparent !important;
}

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
