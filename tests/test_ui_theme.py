"""Unit tests for src.ui.theme — CSS string builder.

These tests never call into Streamlit runtime. They only exercise
`build_theme_css()`, the pure-string function.
"""

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
    for cls in (
        ".mp-card", ".mp-chip", ".mp-cta", ".mp-stage",
        ".mp-metric", ".mp-pill", ".mp-speaker-alex",
        ".mp-speaker-sam", ".mp-hero",
    ):
        assert cls in css


def test_build_theme_css_imports_fonts():
    css = build_theme_css()
    assert "fonts.googleapis.com" in css
    assert "Space Grotesk" in css
    assert "Inter" in css


def test_build_theme_css_respects_reduced_motion():
    css = build_theme_css()
    assert "prefers-reduced-motion" in css
