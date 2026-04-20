"""Unit tests for src.ui.backgrounds — HTML builder for the fixed layer."""

from src.data.categories import PodcastCategory
from src.ui.backgrounds import build_background_html, CATEGORY_THEMES


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
    assert "mp-bg-cycle" not in html


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
