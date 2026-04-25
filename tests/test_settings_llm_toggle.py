"""Toggle the LLM provider from the Settings page.

Pins the round-trip: POST /settings/llm persists the choice; GET /settings
shows it; the pipeline picks up the override the next time it runs.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


# ─── _resolve_llm_config: DB overrides win over base config ──────────────────

class TestResolveLlmConfig:
    def _resolver(self):
        from web.jobs.pipeline import _resolve_llm_config
        return _resolve_llm_config

    def test_no_overrides_returns_base_config(self):
        resolve = self._resolver()
        with patch("web.jobs.pipeline._setting", return_value=None):
            out = resolve({"llm_provider": "gemini", "gemini_api_key": "k"})
        assert out["llm_provider"] == "gemini"
        assert out["gemini_api_key"] == "k"

    def test_db_provider_override_wins(self):
        resolve = self._resolver()

        def fake_setting(key):
            return {
                "default_llm_provider": "ollama",
                "default_ollama_model": "qwen2.5:32b",
                "default_ollama_base_url": "http://192.168.1.50:11434",
                "default_gemini_model": None,
            }.get(key)

        with patch("web.jobs.pipeline._setting", side_effect=fake_setting):
            out = resolve({
                "llm_provider": "gemini",  # base says gemini
                "gemini_api_key": "k",
                "ollama_model": "qwen2.5:14b",
                "ollama_base_url": "http://localhost:11434",
            })
        assert out["llm_provider"] == "ollama"
        assert out["ollama_model"] == "qwen2.5:32b"
        assert out["ollama_base_url"] == "http://192.168.1.50:11434"

    def test_partial_override_only_replaces_set_keys(self):
        resolve = self._resolver()

        def fake_setting(key):
            return {"default_llm_provider": "ollama"}.get(key)

        with patch("web.jobs.pipeline._setting", side_effect=fake_setting):
            out = resolve({
                "llm_provider": "gemini",
                "gemini_api_key": "k",
                "ollama_model": "qwen2.5:14b",
                "ollama_base_url": "http://localhost:11434",
            })
        # Provider switched, but the rest of the config falls back to base.
        assert out["llm_provider"] == "ollama"
        assert out["ollama_model"] == "qwen2.5:14b"
        assert out["gemini_api_key"] == "k"


# ─── End-to-end: settings round-trip via TestClient + tmp DB ─────────────────

@pytest.fixture
def isolated_app(tmp_path, monkeypatch):
    """Spin up the FastAPI app against an isolated SQLite DB.

    The web.db module wires up its engine at import time using
    web.settings.data_dir(). We swap data_dir to a tmp path BEFORE importing
    so each test starts with a clean DB and never touches the user's data.
    """
    import importlib
    import sys

    # Force a fresh data dir for this test run.
    monkeypatch.setattr(
        "web.settings.data_dir",
        lambda: tmp_path,
        raising=False,
    )

    # Drop cached web.db / web.main / web.routes.* so they re-import against
    # the patched data_dir.
    for mod in list(sys.modules):
        if mod == "web.db" or mod.startswith("web.main") or mod.startswith("web.routes") or mod.startswith("web.jobs"):
            sys.modules.pop(mod, None)

    from fastapi.testclient import TestClient
    web_main = importlib.import_module("web.main")
    with TestClient(web_main.app) as client:
        yield client


class TestSettingsLlmRoute:
    def test_post_llm_persists_provider_and_redirects(self, isolated_app):
        client = isolated_app

        resp = client.post(
            "/settings/llm",
            data={
                "llm_provider": "ollama",
                "gemini_model": "gemini-2.5-flash",
                "ollama_model": "qwen2.5:14b",
                "ollama_base_url": "http://localhost:11434",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 303

        # Confirm the toggle persisted: subsequent _resolve_llm_config picks it.
        from web.jobs.pipeline import _resolve_llm_config
        merged = _resolve_llm_config({"llm_provider": "gemini", "gemini_api_key": "k"})
        assert merged["llm_provider"] == "ollama"
        assert merged["ollama_model"] == "qwen2.5:14b"

    def test_get_settings_reflects_persisted_choice(self, isolated_app):
        client = isolated_app

        client.post(
            "/settings/llm",
            data={
                "llm_provider": "ollama",
                "gemini_model": "gemini-2.5-flash",
                "ollama_model": "qwen2.5:32b",
                "ollama_base_url": "http://localhost:11434",
            },
            follow_redirects=False,
        )

        resp = client.get("/settings")
        assert resp.status_code == 200
        body = resp.text
        # The UI must show that ollama is the active selection.
        assert 'value="ollama"' in body
        # The Ollama model the user picked must be in the rendered form.
        assert "qwen2.5:32b" in body

    def test_post_rejects_unknown_provider(self, isolated_app):
        client = isolated_app

        resp = client.post(
            "/settings/llm",
            data={
                "llm_provider": "bogus",
                "gemini_model": "gemini-2.5-flash",
                "ollama_model": "qwen2.5:14b",
                "ollama_base_url": "http://localhost:11434",
            },
            follow_redirects=False,
        )
        # Either a 4xx, or a redirect with a falsy persisted value — but the
        # next pipeline build_provider call must not silently use "bogus".
        from web.jobs.pipeline import _resolve_llm_config
        merged = _resolve_llm_config({"llm_provider": "gemini", "gemini_api_key": "k"})
        assert merged["llm_provider"] in {"gemini", "ollama"}

    def test_round_trip_drives_build_provider_to_ollama(self, isolated_app):
        client = isolated_app
        from src.script.llm.ollama import OllamaProvider
        from src.script.llm import build_provider
        from web.jobs.pipeline import _resolve_llm_config

        client.post(
            "/settings/llm",
            data={
                "llm_provider": "ollama",
                "gemini_model": "gemini-2.5-flash",
                "ollama_model": "qwen2.5:14b",
                "ollama_base_url": "http://localhost:11434",
            },
            follow_redirects=False,
        )

        merged = _resolve_llm_config({
            "llm_provider": "gemini",
            "gemini_api_key": "k",
            "ollama_model": "qwen2.5:14b",
            "ollama_base_url": "http://localhost:11434",
        })
        provider = build_provider(merged)
        assert isinstance(provider, OllamaProvider)
