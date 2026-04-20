"""Tests for src/utils/telegram_sender.py.

Mirrors the posture of email_sender: a thin library wrapper. We verify
input guards (so bad args don't hit the network) and confirm the happy
path calls Bot.send_audio with the expected arguments.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.telegram_sender import send_episode_telegram, _is_valid_chat_id


class TestChatIdValidation:
    @pytest.mark.parametrize("val", [123456789, -1001234567890, "123456789", "-1001234567890"])
    def test_accepts_valid_ids(self, val):
        assert _is_valid_chat_id(val) is True

    @pytest.mark.parametrize("val", [None, "", "   ", "abc", "12.3", 0, "\n123", "1 2"])
    def test_rejects_invalid_ids(self, val):
        assert _is_valid_chat_id(val) is False


class TestSendEpisodeTelegram:
    def test_returns_false_when_mp3_missing(self, tmp_path):
        missing = tmp_path / "nope.mp3"
        result = send_episode_telegram(
            mp3_path=str(missing),
            chat_id="123456789",
            bot_token="fake-token",
        )
        assert result is False

    def test_returns_false_when_bot_token_empty(self, tmp_path):
        mp3 = tmp_path / "a.mp3"
        mp3.write_bytes(b"id3")
        result = send_episode_telegram(
            mp3_path=str(mp3),
            chat_id="123456789",
            bot_token="",
        )
        assert result is False

    def test_returns_false_when_chat_id_invalid(self, tmp_path):
        mp3 = tmp_path / "a.mp3"
        mp3.write_bytes(b"id3")
        result = send_episode_telegram(
            mp3_path=str(mp3),
            chat_id="not-a-number",
            bot_token="fake-token",
        )
        assert result is False

    def test_happy_path_calls_send_audio(self, tmp_path):
        mp3 = tmp_path / "Market_Pulse_2026-04-19.mp3"
        mp3.write_bytes(b"id3-fake-audio")

        fake_bot = MagicMock()
        fake_bot.send_audio = AsyncMock(return_value=MagicMock())

        with patch("src.utils.telegram_sender.Bot", return_value=fake_bot):
            ok = send_episode_telegram(
                mp3_path=str(mp3),
                chat_id="123456789",
                bot_token="fake-token",
                categories=["Finance Macro", "Finance Micro"],
            )

        assert ok is True
        fake_bot.send_audio.assert_awaited_once()
        kwargs = fake_bot.send_audio.await_args.kwargs
        assert kwargs["chat_id"] == 123456789
        assert "Market Pulse" in kwargs["title"]
        assert "Finance Macro" in kwargs["caption"]

    def test_returns_false_when_send_audio_raises(self, tmp_path):
        mp3 = tmp_path / "a.mp3"
        mp3.write_bytes(b"id3")

        fake_bot = MagicMock()
        fake_bot.send_audio = AsyncMock(side_effect=RuntimeError("telegram 500"))

        with patch("src.utils.telegram_sender.Bot", return_value=fake_bot):
            ok = send_episode_telegram(
                mp3_path=str(mp3),
                chat_id="123456789",
                bot_token="fake-token",
            )

        assert ok is False
