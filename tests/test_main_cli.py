"""Tests for main.py CLI flag wiring around delivery fan-out."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

from click.testing import CliRunner

import main


def _write_minimal_config(tmp_path):
    (tmp_path / "config.yaml").write_text(
        "podcast_name: Market Pulse\noutput_dir: output\ngemini_model: x\n"
    )
    (tmp_path / "output").mkdir()
    mp3 = tmp_path / "output" / "Market_Pulse_2099-01-01.mp3"
    mp3.write_bytes(b"id3")
    return mp3


def test_both_delivery_flags_invoke_both_senders(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mp3 = _write_minimal_config(tmp_path)

    with patch("main.collect_data") as m_data, \
         patch("main.generate_script", return_value="[S1] hi"), \
         patch("main.generate_audio", return_value=str(mp3)), \
         patch("main.send_episode_email", return_value=True) as m_email, \
         patch("main.send_episode_telegram", return_value=True) as m_tg:
        snap = MagicMock()
        snap.save = MagicMock()
        m_data.return_value = snap

        result = CliRunner().invoke(main.main, [
            "--date", "2099-01-01",
            "-e", "me@example.com",
            "--telegram-chat-id", "123456789",
        ])

    assert result.exit_code == 0, result.output
    m_email.assert_called_once()
    m_tg.assert_called_once()


def test_only_telegram_flag_skips_email(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mp3 = _write_minimal_config(tmp_path)

    with patch("main.collect_data") as m_data, \
         patch("main.generate_script", return_value="[S1] hi"), \
         patch("main.generate_audio", return_value=str(mp3)), \
         patch("main.send_episode_email", return_value=True) as m_email, \
         patch("main.send_episode_telegram", return_value=True) as m_tg:
        snap = MagicMock()
        snap.save = MagicMock()
        m_data.return_value = snap

        result = CliRunner().invoke(main.main, [
            "--date", "2099-01-01",
            "--telegram-chat-id", "123456789",
        ])

    assert result.exit_code == 0, result.output
    m_email.assert_not_called()
    m_tg.assert_called_once()


def test_exit_nonzero_when_both_channels_fail(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mp3 = _write_minimal_config(tmp_path)

    with patch("main.collect_data") as m_data, \
         patch("main.generate_script", return_value="[S1] hi"), \
         patch("main.generate_audio", return_value=str(mp3)), \
         patch("main.send_episode_email", return_value=False), \
         patch("main.send_episode_telegram", return_value=False):
        snap = MagicMock()
        snap.save = MagicMock()
        m_data.return_value = snap

        result = CliRunner().invoke(main.main, [
            "--date", "2099-01-01",
            "-e", "me@example.com",
            "--telegram-chat-id", "123456789",
        ])

    assert result.exit_code != 0, result.output
