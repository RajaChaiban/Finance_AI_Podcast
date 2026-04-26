"""Catalog → form-handling round trip for the Generate UI's LLM picker.

These tests pin the small contract the rest of the system relies on:

  - Every catalog entry has a stable id, a known provider, and a model tag.
  - get_option(id) returns the right entry, None for unknown ids.
  - default_option_id maps a saved (provider, model) back to a catalog id
    when there's a match, and falls back to the first cloud entry when not.
"""

from __future__ import annotations


def test_catalog_has_at_least_one_cloud_and_one_local_entry():
    from src.script.llm.catalog import LLM_CATALOG

    cloud = [opt for opt in LLM_CATALOG if not opt.is_local]
    local = [opt for opt in LLM_CATALOG if opt.is_local]

    assert cloud, "expected at least one cloud option"
    assert local, "expected at least one local option"


def test_catalog_ids_are_unique():
    from src.script.llm.catalog import LLM_CATALOG

    ids = [opt.id for opt in LLM_CATALOG]
    assert len(ids) == len(set(ids)), f"duplicate catalog ids: {ids}"


def test_catalog_providers_are_known():
    from src.script.llm.catalog import LLM_CATALOG

    for opt in LLM_CATALOG:
        assert opt.provider in {"gemini", "ollama"}, (
            f"{opt.id} has unknown provider {opt.provider!r}"
        )


def test_get_option_returns_entry_for_known_id():
    from src.script.llm.catalog import get_option

    opt = get_option("gemini-flash")
    assert opt is not None
    assert opt.provider == "gemini"
    assert opt.model == "gemini-2.5-flash"


def test_get_option_returns_none_for_unknown_id():
    from src.script.llm.catalog import get_option

    assert get_option("does-not-exist") is None
    assert get_option("") is None


def test_default_option_id_matches_saved_provider_and_model():
    from src.script.llm.catalog import default_option_id

    chosen = default_option_id("ollama", "gemma4:26b")
    assert chosen == "gemma4-26b"


def test_gemini_3_series_present():
    """The newest Gemini 3 preview models must be selectable from the
    Generate UI. Pinning the API model IDs here so a wrong rename in
    the catalog (e.g. dropping the `-preview` suffix) trips a test
    instead of returning 404 from the live API."""
    from src.script.llm.catalog import get_option

    pro = get_option("gemini-31-pro")
    flash = get_option("gemini-3-flash")
    lite = get_option("gemini-31-flash-lite")

    assert pro is not None and pro.model == "gemini-3.1-pro-preview"
    assert flash is not None and flash.model == "gemini-3-flash-preview"
    assert lite is not None and lite.model == "gemini-3.1-flash-lite-preview"
    assert all(opt.provider == "gemini" for opt in (pro, flash, lite))


def test_default_option_id_resolves_gemini_3_pro():
    from src.script.llm.catalog import default_option_id

    assert default_option_id("gemini", "gemini-3.1-pro-preview") == "gemini-31-pro"


def test_existing_gemini_25_flash_default_still_resolves():
    """Adding Gemini 3 at the top of the catalog must not silently
    promote a preview model to the new default for existing users —
    saved (gemini, gemini-2.5-flash) still maps to gemini-flash."""
    from src.script.llm.catalog import default_option_id

    assert default_option_id("gemini", "gemini-2.5-flash") == "gemini-flash"


def test_default_option_id_falls_back_when_no_match():
    from src.script.llm.catalog import LLM_CATALOG, default_option_id

    # Off-catalog tag (e.g. user typed something custom in Settings) should
    # not crash the UI — fall back to the first catalog entry.
    chosen = default_option_id("ollama", "made-up:99b")
    assert chosen == LLM_CATALOG[0].id


def test_default_option_id_falls_back_on_missing_input():
    from src.script.llm.catalog import LLM_CATALOG, default_option_id

    assert default_option_id(None, None) == LLM_CATALOG[0].id
    assert default_option_id("gemini", None) == LLM_CATALOG[0].id


def test_resolve_llm_config_lets_per_run_params_override_db_settings():
    """When the Generate form sends llm_provider + llm_model, that wins
    over both .env and the DB Setting default — for that one run."""
    from web.jobs.pipeline import _resolve_llm_config

    base = {
        "llm_provider": "gemini",
        "gemini_model": "gemini-2.5-flash",
        "ollama_model": "gemma4:26b",
        "ollama_base_url": "http://localhost:11434",
    }
    params = {"llm_provider": "ollama", "llm_model": "qwen3.5:27b"}

    merged = _resolve_llm_config(base, params)

    assert merged["llm_provider"] == "ollama"
    assert merged["ollama_model"] == "qwen3.5:27b"


def test_resolve_llm_config_no_params_means_db_or_env_wins():
    from web.jobs.pipeline import _resolve_llm_config

    base = {
        "llm_provider": "gemini",
        "gemini_model": "gemini-2.5-flash",
        "ollama_model": "gemma4:26b",
        "ollama_base_url": "http://localhost:11434",
    }
    merged = _resolve_llm_config(base, None)
    # No params, no DB setting in this test → base passes through.
    assert merged["llm_provider"] == "gemini"
    assert merged["gemini_model"] == "gemini-2.5-flash"


def test_resolve_llm_config_gemini_override_lands_in_gemini_model_slot():
    from web.jobs.pipeline import _resolve_llm_config

    base = {
        "llm_provider": "gemini",
        "gemini_model": "gemini-2.5-flash",
    }
    params = {"llm_provider": "gemini", "llm_model": "gemini-2.5-pro"}

    merged = _resolve_llm_config(base, params)
    assert merged["gemini_model"] == "gemini-2.5-pro"
