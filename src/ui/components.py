"""Reusable UI components for Market Pulse.

All functions take primitives/config and render via st.markdown/st.button.
Selection state lives in st.session_state — components don't own it.
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
            <span>Your daily AI-generated market briefing.</span>
            <span class="mp-pill">🗓 {date_str}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_category_chips(key_prefix: str = "cat_chip") -> list[PodcastCategory]:
    """Render toggleable gradient chips. Returns current selection.

    Selection persists in st.session_state['selected_categories'] as a list
    of PodcastCategory string values. Initialize this key before first call
    if you want a default selection.
    """
    state_key = "selected_categories"
    if state_key not in st.session_state:
        st.session_state[state_key] = []

    selected_values: list[str] = list(st.session_state[state_key])

    st.markdown(
        '<div class="mp-section-title">Choose your topics</div>',
        unsafe_allow_html=True,
    )

    cats = list(PodcastCategory)
    cols = st.columns(len(cats))
    for col, cat in zip(cols, cats):
        is_active = cat.value in selected_values
        theme = CATEGORY_THEMES[cat]
        label = CATEGORY_LABELS[cat]
        btn_key = f"{key_prefix}_{cat.value}"

        if is_active:
            # Paint the gradient on this specific button via sibling selector
            active_css = (
                f"<style>"
                f"div.stButton:has(> button[kind='primary'][data-testid='stBaseButton-primary']"
                f"[aria-label='{label}']) {{ }}"
                f"</style>"
            )
            # Use primary button styling for active chips (reuses CTA gradient).
            with col:
                st.markdown(active_css, unsafe_allow_html=True)
                clicked = st.button(
                    f"✓ {label}", key=btn_key, type="primary",
                    use_container_width=True,
                )
        else:
            with col:
                # Inject a per-chip gradient-border hint on hover via data attr CSS
                chip_hover_css = (
                    f"<style>"
                    f"[data-testid='stBaseButton-secondary'][aria-label='{label}']:hover "
                    f"{{ box-shadow: 0 0 24px {theme.accent}55; "
                    f"border-color: {theme.accent} !important; }}"
                    f"</style>"
                )
                st.markdown(chip_hover_css, unsafe_allow_html=True)
                clicked = st.button(
                    label, key=btn_key, use_container_width=True,
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
        f'<div class="mp-card" style="border-left:3px solid {CATEGORY_THEMES[c].accent}">'
        f'<strong>{CATEGORY_LABELS[c]}</strong>'
        f'<div style="color: var(--mp-text-muted); font-size:0.92rem; margin-top:0.25rem">'
        f'{CATEGORY_DESCRIPTIONS[c]}</div>'
        f'</div>'
        for c in items
    )
    st.markdown(rows, unsafe_allow_html=True)


def render_api_status(required_keys, config, key_labels) -> bool:
    """Render an API-key status card and return overall ok flag."""
    ok = True
    rows = []
    for key_name in sorted(required_keys):
        label = key_labels.get(key_name, key_name)
        val = config.get(key_name, "")
        placeholder = f"your_{key_name.replace('_api_key', '')}_key_here"
        loaded = bool(val and val != placeholder)
        cls = "mp-status-dot--ok" if loaded else "mp-status-dot--miss"
        status_txt = "loaded" if loaded else "missing"
        rows.append(
            f'<div style="margin:0.25rem 0"><span class="mp-status-dot {cls}"></span>'
            f'{label}: <span style="color: var(--mp-text-muted); font-size:0.88rem">{status_txt}</span></div>'
        )
        if not loaded:
            ok = False
    html = (
        '<div class="mp-card"><strong>API status</strong>'
        '<div style="margin-top:0.5rem">'
        + "".join(rows)
        + '</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)
    return ok


def render_stage_card(
    stage_num: int,
    total: int,
    title: str,
    state: str,
    elapsed_s: float | None = None,
) -> None:
    """state: 'pending' | 'active' | 'done'."""
    cls = "mp-stage"
    if state == "done":
        cls += " mp-stage--done"
    elif state == "active":
        cls += " mp-stage--active"
    elapsed_txt = (
        f'<span style="margin-left:auto; color: var(--mp-text-muted); font-family: \'JetBrains Mono\', monospace;">{elapsed_s:.1f}s</span>'
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


def render_error_card(message: str) -> None:
    st.markdown(
        f'<div class="mp-card" style="border-color: rgba(239,68,68,0.55)">❌ {message}</div>',
        unsafe_allow_html=True,
    )
