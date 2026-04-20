"""Tests for src/utils/notify_failure.py."""

from __future__ import annotations

from unittest.mock import patch

from src.utils.notify_failure import notify_failure


class TestNotifyFailure:
    def test_invokes_both_channels(self):
        with patch("src.utils.notify_failure.send_episode_email", return_value=True) as m_email, \
             patch("src.utils.notify_failure.Bot") as m_bot:
            notify_failure(
                error_summary="Pipeline crashed",
                log_tail="Traceback...",
                run_url="https://github.com/foo/bar/actions/runs/123",
                recipient_email="ops@example.com",
                telegram_chat_id="123456789",
                telegram_bot_token="tok",
                email_sender="from@example.com",
                email_password="pw",
            )
        m_email.assert_called_once()
        m_bot.assert_called_once_with(token="tok")
        assert m_email.call_args.kwargs.get("mp3_path", "") == ""

    def test_continues_when_email_raises(self):
        with patch("src.utils.notify_failure.send_episode_email", side_effect=RuntimeError("smtp down")), \
             patch("src.utils.notify_failure.Bot") as m_bot:
            notify_failure(
                error_summary="x",
                log_tail="y",
                run_url="z",
                recipient_email="a@b.com",
                telegram_chat_id="123",
                telegram_bot_token="t",
                email_sender="f@b.com",
                email_password="p",
            )
            m_bot.assert_called_once()

    def test_continues_when_telegram_raises(self):
        with patch("src.utils.notify_failure.send_episode_email", return_value=True) as m_email, \
             patch("src.utils.notify_failure.Bot", side_effect=RuntimeError("tg down")):
            notify_failure(
                error_summary="x",
                log_tail="y",
                run_url="z",
                recipient_email="a@b.com",
                telegram_chat_id="123",
                telegram_bot_token="t",
                email_sender="f@b.com",
                email_password="p",
            )
            m_email.assert_called_once()

    def test_body_contains_run_url_and_log_tail(self):
        captured = {}

        def capture_email(**kwargs):
            captured["email_body"] = kwargs.get("body")
            captured["email_subject"] = kwargs.get("subject")
            return True

        with patch("src.utils.notify_failure.send_episode_email", side_effect=capture_email), \
             patch("src.utils.notify_failure.Bot"):
            notify_failure(
                error_summary="Gemini 429",
                log_tail="RateLimitError: too many requests",
                run_url="https://github.com/foo/bar/actions/runs/42",
                recipient_email="a@b.com",
                telegram_chat_id="123",
                telegram_bot_token="t",
                email_sender="f@b.com",
                email_password="p",
            )

        assert "Gemini 429" in captured["email_subject"] or "Gemini 429" in captured["email_body"]
        assert "https://github.com/foo/bar/actions/runs/42" in captured["email_body"]
        assert "RateLimitError" in captured["email_body"]
