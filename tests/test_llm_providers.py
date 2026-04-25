"""Provider abstraction for the script LLM.

The pipeline must support multiple LLM backends (Gemini cloud, Ollama local)
behind a single interface so callers don't care which one is active. These
tests pin the contract:

  - LLMProvider.complete(system, user, ...) -> str
  - GeminiProvider wraps google-genai
  - OllamaProvider wraps Ollama's HTTP /api/chat
  - build_provider(config) picks based on config["llm_provider"]
  - ScriptGenerator delegates to whichever provider it's given
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest


# ─── OllamaProvider ───────────────────────────────────────────────────────────

class TestOllamaProvider:
    def test_complete_posts_chat_request_and_returns_message_content(self):
        from src.script.llm.ollama import OllamaProvider

        captured: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["method"] = request.method
            import json as _json
            captured["body"] = _json.loads(request.content.decode("utf-8"))
            return httpx.Response(
                200,
                json={"message": {"role": "assistant", "content": "hello from qwen"}},
            )

        transport = httpx.MockTransport(handler)
        client = httpx.Client(transport=transport)
        provider = OllamaProvider(
            model="qwen2.5:14b",
            base_url="http://localhost:11434",
            client=client,
        )

        out = provider.complete(
            system="be terse",
            user="say hi",
            temperature=0.5,
            max_tokens=128,
        )

        assert out == "hello from qwen"
        assert captured["method"] == "POST"
        assert captured["url"].endswith("/api/chat")
        assert captured["body"]["model"] == "qwen2.5:14b"
        assert captured["body"]["stream"] is False
        msgs = captured["body"]["messages"]
        assert msgs[0] == {"role": "system", "content": "be terse"}
        assert msgs[1] == {"role": "user", "content": "say hi"}
        # Ollama uses num_predict, not max_tokens
        assert captured["body"]["options"]["num_predict"] == 128
        assert captured["body"]["options"]["temperature"] == 0.5

    def test_complete_raises_on_http_error(self):
        from src.script.llm.ollama import OllamaProvider

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="boom")

        client = httpx.Client(transport=httpx.MockTransport(handler))
        provider = OllamaProvider(
            model="qwen2.5:14b",
            base_url="http://localhost:11434",
            client=client,
        )

        with pytest.raises(httpx.HTTPStatusError):
            provider.complete(system="s", user="u", temperature=0.7, max_tokens=64)


# ─── GeminiProvider ───────────────────────────────────────────────────────────

class TestGeminiProvider:
    def test_complete_calls_generate_content_with_system_instruction(self):
        from src.script.llm.gemini import GeminiProvider

        with patch("src.script.llm.gemini.genai.Client") as MockClient:
            mock = MagicMock()
            mock.models.generate_content.return_value.text = "gemini reply"
            MockClient.return_value = mock

            provider = GeminiProvider(api_key="k", model="gemini-3.1-flash-lite-preview")
            out = provider.complete(
                system="sys",
                user="usr",
                temperature=0.7,
                max_tokens=4096,
            )

        assert out == "gemini reply"
        call = mock.models.generate_content.call_args
        assert call.kwargs["model"] == "gemini-3.1-flash-lite-preview"
        assert call.kwargs["contents"] == "usr"
        cfg = call.kwargs["config"]
        # GenerateContentConfig is opaque; inspect attrs.
        assert cfg.system_instruction == "sys"
        assert cfg.temperature == 0.7
        assert cfg.max_output_tokens == 4096


# ─── Factory ──────────────────────────────────────────────────────────────────

class TestBuildProvider:
    def test_default_returns_gemini(self):
        from src.script.llm.factory import build_provider
        from src.script.llm.gemini import GeminiProvider

        with patch("src.script.llm.gemini.genai.Client"):
            p = build_provider({"gemini_api_key": "k", "gemini_model": "gemini-2.5-flash"})
        assert isinstance(p, GeminiProvider)

    def test_gemini_when_provider_is_gemini(self):
        from src.script.llm.factory import build_provider
        from src.script.llm.gemini import GeminiProvider

        with patch("src.script.llm.gemini.genai.Client"):
            p = build_provider({
                "llm_provider": "gemini",
                "gemini_api_key": "k",
                "gemini_model": "gemini-2.5-flash",
            })
        assert isinstance(p, GeminiProvider)

    def test_ollama_when_provider_is_ollama(self):
        from src.script.llm.factory import build_provider
        from src.script.llm.ollama import OllamaProvider

        p = build_provider({
            "llm_provider": "ollama",
            "ollama_model": "qwen2.5:14b",
            "ollama_base_url": "http://localhost:11434",
        })
        assert isinstance(p, OllamaProvider)
        assert p.model == "qwen2.5:14b"
        assert p.base_url == "http://localhost:11434"

    def test_unknown_provider_raises(self):
        from src.script.llm.factory import build_provider

        with pytest.raises(ValueError):
            build_provider({"llm_provider": "claude-secret"})

    def test_gemini_missing_key_raises(self):
        from src.script.llm.factory import build_provider

        with pytest.raises(ValueError):
            build_provider({"llm_provider": "gemini", "gemini_api_key": ""})

    def test_gemini_placeholder_key_raises(self):
        from src.script.llm.factory import build_provider

        with pytest.raises(ValueError):
            build_provider({
                "llm_provider": "gemini",
                "gemini_api_key": "your_gemini_key_here",
            })


# ─── ScriptGenerator delegates to provider ───────────────────────────────────

class TestScriptGeneratorDelegates:
    def test_generate_calls_provider_complete_with_prompts(self):
        from src.data.categories import DEFAULT_CATEGORIES
        from src.data.models import MarketSnapshot
        from src.script.generator import ScriptGenerator

        # Minimal valid script — two speaker lines so validators don't fail.
        provider = MagicMock()
        provider.model = "fake-model"
        provider.complete.return_value = (
            "[S1] Welcome to the show.\n[S2] Glad to be here.\n"
        )

        gen = ScriptGenerator(provider=provider)
        snap = MarketSnapshot(date="2026-04-25")
        script = gen.generate(snap, list(DEFAULT_CATEGORIES))

        assert provider.complete.called
        call = provider.complete.call_args
        # System and user prompt threaded through.
        assert isinstance(call.kwargs.get("system") or call.args[0], str)
        sys_arg = call.kwargs.get("system", call.args[0] if call.args else None)
        usr_arg = call.kwargs.get("user", call.args[1] if len(call.args) > 1 else None)
        assert "TARGET LENGTH" in sys_arg
        assert "2026-04-25" in usr_arg
        # Returned script is the cleaned output.
        assert "[S1] Welcome to the show." in script
        assert "[S2] Glad to be here." in script

    def test_legacy_constructor_still_works(self):
        """Backward-compat: old call sites pass api_key + model directly."""
        from src.script.generator import ScriptGenerator

        with patch("src.script.llm.gemini.genai.Client"):
            gen = ScriptGenerator(api_key="k", model="gemini-3.1-flash-lite-preview")

        # _clean_script does not need a real provider.
        cleaned = gen._clean_script("[S1] Hi.\nstray\n[S2] Bye.\n")
        assert cleaned.splitlines() == ["[S1] Hi.", "[S2] Bye."]
