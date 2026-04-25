"""GET /settings/llm/test pings Ollama's /api/tags so the user can verify
connectivity before kicking off a 5-minute podcast run.

Connectivity errors (server down, wrong port, model not pulled) are the most
common Ollama footgun, and surfacing them on the Settings page beats discovering
them via a stack trace in the script stage.
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest


@pytest.fixture
def isolated_app(tmp_path, monkeypatch):
    """Reuse the same isolation pattern as test_settings_llm_toggle.py."""
    import importlib
    import sys

    monkeypatch.setattr("web.settings.data_dir", lambda: tmp_path, raising=False)
    for mod in list(sys.modules):
        if mod == "web.db" or mod.startswith("web.main") or mod.startswith("web.routes") or mod.startswith("web.jobs"):
            sys.modules.pop(mod, None)

    from fastapi.testclient import TestClient
    web_main = importlib.import_module("web.main")
    with TestClient(web_main.app) as client:
        yield client


class TestOllamaTestConnection:
    def test_returns_ok_with_model_list_when_ollama_responds(self, isolated_app):
        client = isolated_app

        def fake_get(url, timeout):
            return httpx.Response(
                200,
                json={
                    "models": [
                        {"name": "gemma4:26b", "size": 16_000_000_000},
                        {"name": "qwen3.5:27b", "size": 17_000_000_000},
                    ]
                },
                request=httpx.Request("GET", url),
            )

        with patch("httpx.get", side_effect=fake_get):
            resp = client.get("/settings/llm/test?base_url=http://localhost:11434")

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert "gemma4:26b" in body["models"]
        assert "qwen3.5:27b" in body["models"]
        assert body["tested_url"] == "http://localhost:11434/api/tags"

    def test_returns_ok_false_when_ollama_unreachable(self, isolated_app):
        client = isolated_app

        def fake_get(url, timeout):
            raise httpx.ConnectError("Connection refused")

        with patch("httpx.get", side_effect=fake_get):
            resp = client.get("/settings/llm/test?base_url=http://localhost:11434")

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is False
        assert "ollama serve" in body["error"].lower() or "connect" in body["error"].lower()

    def test_returns_ok_false_on_http_error(self, isolated_app):
        client = isolated_app

        def fake_get(url, timeout):
            return httpx.Response(500, text="Internal Server Error",
                                  request=httpx.Request("GET", url))

        with patch("httpx.get", side_effect=fake_get):
            resp = client.get("/settings/llm/test?base_url=http://localhost:11434")

        body = resp.json()
        assert body["ok"] is False
        assert "500" in body["error"]

    def test_falls_back_to_saved_setting_when_no_query_param(self, isolated_app):
        client = isolated_app

        # Persist a saved base_url first.
        client.post(
            "/settings/llm",
            data={
                "llm_provider": "ollama",
                "gemini_model": "",
                "ollama_model": "gemma4:26b",
                "ollama_base_url": "http://192.168.1.50:11434",
            },
            follow_redirects=False,
        )

        captured = {}

        def fake_get(url, timeout):
            captured["url"] = url
            return httpx.Response(
                200,
                json={"models": []},
                request=httpx.Request("GET", url),
            )

        with patch("httpx.get", side_effect=fake_get):
            resp = client.get("/settings/llm/test")

        assert resp.status_code == 200
        assert "192.168.1.50" in captured["url"]
        assert resp.json()["ok"] is True

    def test_strips_trailing_slash_from_base_url(self, isolated_app):
        client = isolated_app

        captured = {}

        def fake_get(url, timeout):
            captured["url"] = url
            return httpx.Response(200, json={"models": []},
                                  request=httpx.Request("GET", url))

        with patch("httpx.get", side_effect=fake_get):
            client.get("/settings/llm/test?base_url=http://localhost:11434/")

        # No double slash before /api/tags.
        assert captured["url"] == "http://localhost:11434/api/tags"
