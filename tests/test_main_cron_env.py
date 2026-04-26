"""Cron uses env vars, not CLI flags, to drive its run config.

These tests pin the contract the GitHub workflow relies on:

  - GEMINI_MODEL is honoured by load_config()
  - CATEGORIES env var splits into the right tuple, with fallback
  - LENGTH_PRESET / VOICE_S1 / VOICE_S2 land on the click options via
    Click's envvar mechanism

If any of these break, the daily-podcast workflow silently falls back
to the previous defaults — which is what we just stopped doing.
"""

from __future__ import annotations

import os
from unittest.mock import patch

from click.testing import CliRunner


def _isolated_env(**env_vars):
    """Replace os.environ with a clean dict containing only what we set."""
    return patch.dict(os.environ, env_vars, clear=False)


# ── load_config() reads GEMINI_MODEL from env ───────────────────────────────

def test_load_config_reads_gemini_model_from_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.yaml").write_text("podcast_name: Test\n")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    monkeypatch.setenv("GEMINI_API_KEY", "x")

    from main import load_config

    config = load_config()
    assert config["gemini_model"] == "gemini-2.5-flash-lite"


def test_load_config_gemini_model_falls_back_when_env_unset(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.yaml").write_text("podcast_name: Test\n")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "x")

    from main import load_config

    config = load_config()
    assert config["gemini_model"] == "gemini-2.5-flash"


# ── CATEGORIES env var ──────────────────────────────────────────────────────

def test_env_categories_splits_comma_separated(monkeypatch):
    monkeypatch.setenv(
        "CATEGORIES",
        "finance_macro,finance_micro,crypto,geopolitics,ai_updates",
    )
    from main import _env_categories

    assert _env_categories() == (
        "finance_macro",
        "finance_micro",
        "crypto",
        "geopolitics",
        "ai_updates",
    )


def test_env_categories_strips_whitespace_and_drops_blanks(monkeypatch):
    monkeypatch.setenv("CATEGORIES", "  crypto , , finance_macro  ")
    from main import _env_categories

    assert _env_categories() == ("crypto", "finance_macro")


def test_env_categories_falls_back_when_unset(monkeypatch):
    monkeypatch.delenv("CATEGORIES", raising=False)
    from main import _env_categories

    assert _env_categories() == ("finance_macro", "finance_micro")


def test_env_categories_falls_back_on_empty_string(monkeypatch):
    monkeypatch.setenv("CATEGORIES", "   ")
    from main import _env_categories

    assert _env_categories() == ("finance_macro", "finance_micro")


# ── click envvar wiring ─────────────────────────────────────────────────────

def test_cli_respects_voice_s1_voice_s2_length_preset_env(monkeypatch, tmp_path):
    """We don't run the full pipeline — we shim collect/generate/synthesize so
    the test runs in milliseconds. The point is to confirm Click sees the env
    vars and the chosen voices/preset land on the captured params."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.yaml").write_text(
        "podcast_name: Test\n"
        "speaker_1_voice: am_adam\n"
        "speaker_2_voice: af_bella\n"
    )
    (tmp_path / "output").mkdir()
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    monkeypatch.setenv("VOICE_S1", "am_michael")
    monkeypatch.setenv("VOICE_S2", "af_jessica")
    monkeypatch.setenv("LENGTH_PRESET", "standard")

    captured: dict = {}

    import main as main_module

    class _StubSnapshot:
        date = "2026-04-26"
        categories: list[str] = []
        user_voice_s1 = ""
        user_voice_s2 = ""
        user_length_preset = ""
        user_target_words = 0

        def save(self, path: str) -> None:
            captured["snapshot_voice_s1"] = self.user_voice_s1
            captured["snapshot_voice_s2"] = self.user_voice_s2
            captured["snapshot_length_preset"] = self.user_length_preset

        @classmethod
        def load(cls, path: str):
            return cls()

    def fake_collect(config, categories, **kwargs):
        return _StubSnapshot()

    def fake_generate(config, snapshot, categories, preset_key=None):
        captured["preset_key"] = preset_key
        return "[S1] hi\n[S2] hi\n"

    def fake_audio(config, script, output_dir, date, voice_s1, voice_s2):
        captured["audio_voice_s1"] = voice_s1
        captured["audio_voice_s2"] = voice_s2
        return "/tmp/fake.mp3"

    monkeypatch.setattr(main_module, "collect_data", fake_collect)
    monkeypatch.setattr(main_module, "generate_script", fake_generate)
    monkeypatch.setattr(main_module, "generate_audio", fake_audio, raising=False)
    monkeypatch.setattr(main_module, "MarketSnapshot", _StubSnapshot)

    runner = CliRunner()
    result = runner.invoke(main_module.main, ["--stage", "data"])

    # We only need to confirm Click read the env vars before invocation.
    # The "data" stage exits early, but voice/preset env vars are bound to
    # CLI params at click parse time — captured via the snapshot.save shim.
    assert result.exit_code == 0, result.output
    assert captured["snapshot_voice_s1"] == "am_michael"
    assert captured["snapshot_voice_s2"] == "af_jessica"
    assert captured["snapshot_length_preset"] == "standard"
