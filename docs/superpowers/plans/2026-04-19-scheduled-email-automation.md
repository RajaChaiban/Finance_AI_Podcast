# Scheduled Daily Podcast Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automate the Market Pulse pipeline so a daily pre-market episode is generated on GitHub Actions and delivered to the operator via both email and Telegram, with failure notifications on the same channels.

**Architecture:** A new GitHub Actions workflow runs the existing `main.py` pipeline on a UTC cron schedule (~6:30 AM ET pre-market). Delivery is fanned out to email (existing `send_episode_email`) and Telegram (new `send_episode_telegram`, parallel module). Each channel is best-effort — `main.py` exits 0 if at least one succeeds. A failure-path step notifies both channels with the error tail and Actions run URL. Kokoro model weights are cached between runs; MP3s are uploaded as 7-day GH Actions artifacts as a safety net.

**Tech Stack:** Python 3.11+, `click`, `python-telegram-bot` (already installed), `smtplib` (stdlib), GitHub Actions (`schedule:` + `workflow_dispatch:`), `actions/cache`, `actions/upload-artifact`.

**Spec:** `docs/superpowers/specs/2026-04-19-scheduled-email-automation-design.md`

---

## File Structure

| Path | Create/Modify | Responsibility |
|---|---|---|
| `src/utils/telegram_sender.py` | Create | `send_episode_telegram()` — push MP3 via Bot API, returns bool, mirrors `email_sender.py`. |
| `src/utils/notify_failure.py` | Create | `notify_failure()` — short failure message sent to both channels. |
| `main.py` | Modify L92, L133–143 | Add `--telegram-chat-id` flag; refactor Stage 4 to fan out email + Telegram with per-channel success tracking. |
| `tests/test_telegram_sender.py` | Create | Unit tests: chat-id validation, missing-file guard, happy-path (Bot mocked). |
| `tests/test_notify_failure.py` | Create | Unit test: both senders invoked, failure of one doesn't abort the other. |
| `.env.example` | Modify | Document new `TELEGRAM_CHAT_ID` env var. |
| `.github/workflows/daily-podcast.yml` | Create | Cron `30 10 * * *` UTC, pipeline invocation, fan-out, failure notify, artifact upload, Kokoro cache. |
| `README.md` | Modify | New "Scheduled runs (GitHub Actions)" section with secrets list + first-run checklist. |

---

## Task 1: Telegram sender utility

**Files:**
- Create: `src/utils/telegram_sender.py`
- Test: `tests/test_telegram_sender.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_telegram_sender.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_telegram_sender.py -v`
Expected: FAIL — module `src.utils.telegram_sender` not importable.

- [ ] **Step 3: Implement `src/utils/telegram_sender.py`**

Create `src/utils/telegram_sender.py`:

```python
"""Push a podcast MP3 to a single Telegram chat via the Bot API.

Mirrors `src/utils/email_sender.py` in posture: returns a bool, logs a
warning on failure, never raises. Intended for the scheduled/automated
pipeline; the reactive `telegram_bot.py` stays untouched.
"""

from __future__ import annotations

import asyncio
import os
from typing import Optional

from telegram import Bot

from src.utils.logger import log


def _is_valid_chat_id(val) -> bool:
    """Chat IDs are integers (positive for users, negative for groups/channels).

    Accept int or a string that parses cleanly to a non-zero int. Reject
    empty strings, non-numeric text, whitespace, and zero (not a valid chat).
    """
    if val is None:
        return False
    if isinstance(val, bool):
        return False
    if isinstance(val, int):
        return val != 0
    if isinstance(val, str):
        s = val.strip()
        if not s or any(c.isspace() for c in s):
            return False
        try:
            return int(s) != 0
        except ValueError:
            return False
    return False


async def _send_audio_async(bot_token: str, chat_id: int, mp3_path: str,
                            title: str, caption: str) -> None:
    bot = Bot(token=bot_token)
    with open(mp3_path, "rb") as f:
        await bot.send_audio(
            chat_id=chat_id,
            audio=f,
            title=title,
            performer="Market Pulse AI",
            caption=caption,
        )


def send_episode_telegram(
    mp3_path: str,
    chat_id,
    bot_token: Optional[str] = None,
    categories: Optional[list[str]] = None,
) -> bool:
    """Send an MP3 episode to a Telegram chat. Returns True on success."""
    bot_token = bot_token if bot_token is not None else os.getenv("TELEGRAM_BOT_TOKEN", "")

    if not bot_token:
        log.warning("Telegram not configured: set TELEGRAM_BOT_TOKEN in .env")
        return False
    if not _is_valid_chat_id(chat_id):
        log.warning(f"Rejected invalid Telegram chat_id: {chat_id!r}")
        return False
    if not os.path.exists(mp3_path):
        log.warning(f"MP3 file not found: {mp3_path}")
        return False

    chat_id_int = int(str(chat_id).strip())
    filename = os.path.basename(mp3_path)
    file_size_mb = os.path.getsize(mp3_path) / (1024 * 1024)

    # Telegram bots cap uploads at 50 MB. Bail early so we don't eat a
    # confusing 413 from the API mid-run.
    if file_size_mb > 50:
        log.warning(
            f"MP3 exceeds Telegram bot upload limit: {file_size_mb:.1f} MB > 50 MB ({filename})"
        )
        return False

    cat_text = ", ".join(categories) if categories else "all topics"
    title = f"Market Pulse - {filename.replace('.mp3', '').replace('-', ' ').title()}"
    caption = f"Categories: {cat_text}"

    try:
        log.info(f"Sending episode to Telegram chat {chat_id_int} ({file_size_mb:.1f} MB)...")
        asyncio.run(_send_audio_async(bot_token, chat_id_int, mp3_path, title, caption))
        log.info(f"Episode sent to Telegram chat {chat_id_int}")
        return True
    except Exception as e:
        log.warning(f"Failed to send Telegram: {type(e).__name__}: {e}")
        return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_telegram_sender.py -v`
Expected: 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/utils/telegram_sender.py tests/test_telegram_sender.py
git commit -m "feat(utils): add send_episode_telegram for scheduled delivery"
```

---

## Task 2: Failure notification utility

**Files:**
- Create: `src/utils/notify_failure.py`
- Test: `tests/test_notify_failure.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_notify_failure.py`:

```python
"""Tests for src/utils/notify_failure.py."""

from __future__ import annotations

from unittest.mock import patch

from src.utils.notify_failure import notify_failure


class TestNotifyFailure:
    def test_invokes_both_channels(self):
        with patch("src.utils.notify_failure.send_episode_email", return_value=True) as m_email, \
             patch("src.utils.notify_failure.send_episode_telegram", return_value=True) as m_tg:
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
        m_tg.assert_called_once()
        # Failure messages never carry the MP3 attachment — they're alerts, not deliveries.
        assert m_email.call_args.kwargs.get("mp3_path") is None or \
               m_email.call_args.kwargs.get("mp3_path") == ""

    def test_continues_when_email_raises(self):
        with patch("src.utils.notify_failure.send_episode_email", side_effect=RuntimeError("smtp down")), \
             patch("src.utils.notify_failure.send_episode_telegram", return_value=True) as m_tg:
            # Must not raise
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
            m_tg.assert_called_once()

    def test_continues_when_telegram_raises(self):
        with patch("src.utils.notify_failure.send_episode_email", return_value=True) as m_email, \
             patch("src.utils.notify_failure.send_episode_telegram", side_effect=RuntimeError("tg down")):
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
             patch("src.utils.notify_failure.send_episode_telegram", return_value=True):
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_notify_failure.py -v`
Expected: FAIL — module not importable.

- [ ] **Step 3: Implement `src/utils/notify_failure.py`**

Create `src/utils/notify_failure.py`:

```python
"""Send a short failure alert via email and Telegram.

Called from the GitHub Actions failure path. Best-effort on both channels:
a crash in one sender must not block the other, and the function itself
never raises — the workflow run status is the last line of defense.
"""

from __future__ import annotations

from typing import Optional

from src.utils.email_sender import send_episode_email
from src.utils.telegram_sender import send_episode_telegram
from src.utils.logger import log


def notify_failure(
    error_summary: str,
    log_tail: str,
    run_url: str,
    recipient_email: Optional[str] = None,
    telegram_chat_id: Optional[str] = None,
    telegram_bot_token: Optional[str] = None,
    email_sender: Optional[str] = None,
    email_password: Optional[str] = None,
) -> None:
    """Send a failure alert on both channels. Never raises."""
    subject = f"[Market Pulse FAILED] {error_summary}"
    body = (
        f"The scheduled Market Pulse run failed.\n\n"
        f"Error: {error_summary}\n\n"
        f"Run: {run_url}\n\n"
        f"Last log lines:\n"
        f"{'-' * 60}\n"
        f"{log_tail}\n"
        f"{'-' * 60}\n"
    )

    if recipient_email:
        try:
            send_episode_email(
                mp3_path="",  # No attachment for alerts.
                recipient=recipient_email,
                subject=subject,
                body=body,
                sender_email=email_sender,
                sender_password=email_password,
            )
        except Exception as e:
            log.warning(f"notify_failure: email channel raised: {type(e).__name__}: {e}")

    if telegram_chat_id and telegram_bot_token:
        try:
            # Send as plain text message, not audio. We reuse send_episode_telegram
            # only for its bot wiring; the alert is a message, so we inline it here.
            import asyncio
            from telegram import Bot

            async def _send_alert():
                bot = Bot(token=telegram_bot_token)
                text = f"{subject}\n\n{body}"
                if len(text) > 4000:
                    text = text[:3997] + "..."
                await bot.send_message(chat_id=int(str(telegram_chat_id).strip()), text=text)

            asyncio.run(_send_alert())
            log.info(f"Failure alert sent to Telegram chat {telegram_chat_id}")
        except Exception as e:
            log.warning(f"notify_failure: telegram channel raised: {type(e).__name__}: {e}")


if __name__ == "__main__":
    # CLI entry so GH Actions can invoke: python -m src.utils.notify_failure
    import os
    import sys

    run_url = os.getenv("GITHUB_RUN_URL", "(no run url)")
    error_summary = os.getenv("FAILURE_SUMMARY", "Scheduled run failed")
    log_tail = sys.stdin.read() if not sys.stdin.isatty() else "(no log tail piped)"

    notify_failure(
        error_summary=error_summary,
        log_tail=log_tail,
        run_url=run_url,
        recipient_email=os.getenv("EMAIL_ADDRESS"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        email_sender=os.getenv("EMAIL_ADDRESS"),
        email_password=os.getenv("EMAIL_APP_PASSWORD"),
    )
```

Note: the test `test_invokes_both_channels` checks `mp3_path` kwarg on the email call. `send_episode_email` treats an empty path as a missing file and returns `False`. That's a known limitation — email failure notifications without attachment would be rejected by the existing validator. Fix this in the next step.

- [ ] **Step 4: Allow email sender to send bodies without attachments**

Open `src/utils/email_sender.py`. Modify the MP3 existence check (around L62–64) so empty `mp3_path` means "no attachment" rather than error:

Replace:

```python
    if not os.path.exists(mp3_path):
        log.warning(f"MP3 file not found: {mp3_path}")
        return False
```

With:

```python
    has_attachment = bool(mp3_path) and os.path.exists(mp3_path)
    if mp3_path and not has_attachment:
        log.warning(f"MP3 file not found: {mp3_path}")
        return False
```

Then modify the attachment-building block (around L82–93) so it only attaches when `has_attachment` is True:

Replace:

```python
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with open(mp3_path, "rb") as f:
            part = MIMEBase("audio", "mpeg")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)
```

With:

```python
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        if has_attachment:
            with open(mp3_path, "rb") as f:
                part = MIMEBase("audio", "mpeg")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={filename}")
                msg.attach(part)
```

Also guard the filename/size computation (lines 66–67) so it only runs when there's an attachment. Move those two lines inside an `if has_attachment:` block, defaulting to placeholders otherwise:

Replace:

```python
    filename = os.path.basename(mp3_path)
    file_size_mb = os.path.getsize(mp3_path) / (1024 * 1024)
```

With:

```python
    if has_attachment:
        filename = os.path.basename(mp3_path)
        file_size_mb = os.path.getsize(mp3_path) / (1024 * 1024)
    else:
        filename = ""
        file_size_mb = 0.0
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_notify_failure.py tests/test_telegram_sender.py -v`
Expected: all tests PASS (3 new + 5 telegram + 3 chat-id = 11 PASS).

Also run the full suite to verify email_sender changes didn't regress:

Run: `pytest -q`
Expected: all prior tests still PASS.

- [ ] **Step 6: Commit**

```bash
git add src/utils/notify_failure.py src/utils/email_sender.py tests/test_notify_failure.py
git commit -m "feat(utils): notify_failure alerter + allow attachment-less email"
```

---

## Task 3: Fan-out Stage 4 in main.py

**Files:**
- Modify: `main.py` (L92 CLI flag, L133–143 Stage 4)

- [ ] **Step 1: Add a test for main's fan-out logic**

Existing `tests/test_pipeline_wiring.py` is pure-logic. Fan-out behavior is best covered by invoking the CLI in isolation. Create one small test in `tests/test_main_cli.py`:

```python
"""Tests for main.py CLI flag wiring around delivery fan-out."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

from click.testing import CliRunner

import main


def test_both_delivery_flags_invoke_both_senders(tmp_path, monkeypatch):
    """--email and --telegram-chat-id both set → both senders called."""
    monkeypatch.chdir(tmp_path)

    # Minimal config.yaml so load_config() works.
    (tmp_path / "config.yaml").write_text(
        "podcast_name: Market Pulse\noutput_dir: output\ngemini_model: x\n"
    )
    (tmp_path / "output").mkdir()
    mp3 = tmp_path / "output" / "Market_Pulse_2099-01-01.mp3"
    mp3.write_bytes(b"id3")

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
    (tmp_path / "config.yaml").write_text(
        "podcast_name: Market Pulse\noutput_dir: output\ngemini_model: x\n"
    )
    (tmp_path / "output").mkdir()
    mp3 = tmp_path / "output" / "Market_Pulse_2099-01-01.mp3"
    mp3.write_bytes(b"id3")

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
    (tmp_path / "config.yaml").write_text(
        "podcast_name: Market Pulse\noutput_dir: output\ngemini_model: x\n"
    )
    (tmp_path / "output").mkdir()
    mp3 = tmp_path / "output" / "Market_Pulse_2099-01-01.mp3"
    mp3.write_bytes(b"id3")

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_main_cli.py -v`
Expected: FAIL — `--telegram-chat-id` is not a recognized option yet.

- [ ] **Step 3: Add the flag and fan-out in `main.py`**

In `main.py`, update the imports block (L16) to add the Telegram sender:

Replace line 16:

```python
from src.utils.email_sender import send_episode_email
```

With:

```python
from src.utils.email_sender import send_episode_email
from src.utils.telegram_sender import send_episode_telegram
```

Then update the Click command signature (L85–93). Replace:

```python
@click.command()
@click.option("--stage", type=click.Choice(["data", "script", "audio", "all"]), default="all",
              help="Run a specific stage or the full pipeline")
@click.option("--date", default=None, help="Date override (YYYY-MM-DD)")
@click.option("--categories", "-c", multiple=True, type=click.Choice(CATEGORY_CHOICES),
              default=["finance_macro", "finance_micro"],
              help="Categories to include (repeatable, e.g. -c crypto -c geopolitics)")
@click.option("--email", "-e", default=None, help="Send episode to this email address after generation")
def main(stage: str, date: str | None, categories: tuple[str], email: str | None):
```

With:

```python
@click.command()
@click.option("--stage", type=click.Choice(["data", "script", "audio", "all"]), default="all",
              help="Run a specific stage or the full pipeline")
@click.option("--date", default=None, help="Date override (YYYY-MM-DD)")
@click.option("--categories", "-c", multiple=True, type=click.Choice(CATEGORY_CHOICES),
              default=["finance_macro", "finance_micro"],
              help="Categories to include (repeatable, e.g. -c crypto -c geopolitics)")
@click.option("--email", "-e", default=None, help="Send episode to this email address after generation")
@click.option("--telegram-chat-id", default=None,
              help="Push episode to this Telegram chat ID after generation")
def main(stage: str, date: str | None, categories: tuple[str],
         email: str | None, telegram_chat_id: str | None):
```

Then replace the Stage 4 block (L133–143):

```python
        # ── STAGE 4: Email Delivery ─────────────────────────
        if email:
            log.info("=== STAGE 4: Email Delivery ===")
            cat_names = [c.value.replace("_", " ").title() for c in cat_list]
            sent = send_episode_email(
                mp3_path=mp3_path,
                recipient=email,
                categories=cat_names,
            )
            if not sent:
                log.warning("Email delivery failed. Check EMAIL_ADDRESS and EMAIL_APP_PASSWORD in .env")
```

With:

```python
        # ── STAGE 4: Delivery Fan-out ───────────────────────
        if email or telegram_chat_id:
            log.info("=== STAGE 4: Delivery ===")
            cat_names = [c.value.replace("_", " ").title() for c in cat_list]

            email_ok = True  # Default True so "not requested" doesn't count as failure.
            tg_ok = True
            attempted = 0

            if email:
                attempted += 1
                email_ok = send_episode_email(
                    mp3_path=mp3_path,
                    recipient=email,
                    categories=cat_names,
                )
                if not email_ok:
                    log.warning("Email delivery failed. Check EMAIL_ADDRESS / EMAIL_APP_PASSWORD.")

            if telegram_chat_id:
                attempted += 1
                tg_ok = send_episode_telegram(
                    mp3_path=mp3_path,
                    chat_id=telegram_chat_id,
                    categories=cat_names,
                )
                if not tg_ok:
                    log.warning("Telegram delivery failed. Check TELEGRAM_BOT_TOKEN / chat id.")

            # Exit non-zero only if every attempted channel failed.
            # This lets GitHub Actions' if: failure() fire on true total failure.
            if attempted > 0 and not (email_ok or tg_ok):
                import sys
                sys.exit(1)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_main_cli.py -v`
Expected: 3 tests PASS.

Also run the full suite:

Run: `pytest -q`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main_cli.py
git commit -m "feat(cli): --telegram-chat-id flag + delivery fan-out with partial-success semantics"
```

---

## Task 4: Document TELEGRAM_CHAT_ID in .env.example

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Add the new env var**

Replace the current `.env.example` contents with:

```
GEMINI_API_KEY=your_gemini_key_here
FRED_API_KEY=your_fred_key_here
GNEWS_API_KEY=your_gnews_key_here
CURRENTS_API_KEY=your_currents_key_here
NEWSDATA_API_KEY=your_newsdata_key_here
EMAIL_ADDRESS=your_gmail@gmail.com
EMAIL_APP_PASSWORD=your_app_password_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
# Comma-separated Telegram chat/user IDs allowed to use /podcast (reactive bot).
# Empty = refuse all requests. Find your ID with @userinfobot on Telegram.
ALLOWED_CHAT_IDS=
# Single chat ID the scheduled/automated pipeline pushes to (typically your own).
# Distinct from ALLOWED_CHAT_IDS: that is a security allow-list; this is a target.
TELEGRAM_CHAT_ID=
```

- [ ] **Step 2: Commit**

```bash
git add .env.example
git commit -m "docs(env): add TELEGRAM_CHAT_ID for scheduled pusher target"
```

---

## Task 5: GitHub Actions workflow

**Files:**
- Create: `.github/workflows/daily-podcast.yml`

- [ ] **Step 1: Create the workflow file**

Create `.github/workflows/daily-podcast.yml`:

```yaml
name: Daily Podcast

on:
  schedule:
    # 10:30 UTC = 6:30 AM ET during EDT (summer) / 5:30 AM ET during EST (winter).
    # Single cron; DST drift is documented in docs/superpowers/specs/2026-04-19-scheduled-email-automation-design.md.
    - cron: "30 10 * * *"
  workflow_dispatch:  # Allow manual runs from the Actions tab.

# Only one daily run at a time. If a run is already in progress when cron fires
# again, skip — we never want two Kokoro instances fighting for memory.
concurrency:
  group: daily-podcast
  cancel-in-progress: false

jobs:
  generate-and-deliver:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    env:
      GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      FRED_API_KEY: ${{ secrets.FRED_API_KEY }}
      GNEWS_API_KEY: ${{ secrets.GNEWS_API_KEY }}
      CURRENTS_API_KEY: ${{ secrets.CURRENTS_API_KEY }}
      NEWSDATA_API_KEY: ${{ secrets.NEWSDATA_API_KEY }}
      EMAIL_ADDRESS: ${{ secrets.EMAIL_ADDRESS }}
      EMAIL_APP_PASSWORD: ${{ secrets.EMAIL_APP_PASSWORD }}
      TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
      TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install system deps (ffmpeg for pydub)
        run: sudo apt-get update && sudo apt-get install -y ffmpeg

      - name: Install Python deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Restore Kokoro model cache
        uses: actions/cache@v4
        with:
          path: |
            ~/.cache/huggingface
            ~/.cache/kokoro
          key: kokoro-model-${{ hashFiles('requirements.txt') }}
          restore-keys: |
            kokoro-model-

      - name: Run pipeline with fan-out delivery
        id: run_pipeline
        run: |
          set -o pipefail
          python main.py \
            -e "$EMAIL_ADDRESS" \
            --telegram-chat-id "$TELEGRAM_CHAT_ID" \
            2>&1 | tee pipeline.log

      - name: Upload MP3 artifact (safety net)
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: market-pulse-${{ github.run_id }}
          path: output/Market_Pulse_*.mp3
          retention-days: 7
          if-no-files-found: warn

      - name: Upload pipeline log
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: pipeline-log-${{ github.run_id }}
          path: pipeline.log
          retention-days: 7
          if-no-files-found: ignore

      - name: Notify failure on both channels
        if: failure()
        env:
          GITHUB_RUN_URL: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
          FAILURE_SUMMARY: "Daily podcast run failed"
        run: |
          # Tail the pipeline log (last 50 lines) and pipe it to the notifier.
          if [ -f pipeline.log ]; then
            tail -n 50 pipeline.log | python -m src.utils.notify_failure
          else
            echo "(no pipeline log captured)" | python -m src.utils.notify_failure
          fi
```

- [ ] **Step 2: Sanity-check the YAML syntax**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/daily-podcast.yml'))"`
Expected: no output (parses cleanly).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/daily-podcast.yml
git commit -m "ci: daily podcast workflow with fan-out delivery and failure alerts"
```

---

## Task 6: README section for scheduled runs

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add the new section**

Open `README.md`. Add a new section between the existing "Telegram bot" section and "Configuration (config.yaml)" section (after the current L80 `ALLOWED_CHAT_IDS...` paragraph, before the `---` and `## Configuration`):

```markdown
---

## Scheduled runs (GitHub Actions)

Generate and deliver a daily episode with zero local machine required. See
[`.github/workflows/daily-podcast.yml`](.github/workflows/daily-podcast.yml).

**Schedule:** Every day at 10:30 UTC (6:30 AM ET during EDT / 5:30 AM ET during EST).
Also runnable manually from the Actions tab via `workflow_dispatch`.

**First-time setup:**

1. Push this repo to GitHub.
2. Go to **Settings → Secrets and variables → Actions → New repository secret** and
   add each of the following (mirrors your local `.env`):

   | Secret | Required | Purpose |
   |---|---|---|
   | `GEMINI_API_KEY`     | yes | Script generation |
   | `EMAIL_ADDRESS`      | yes | Gmail sender + self-recipient |
   | `EMAIL_APP_PASSWORD` | yes | Gmail App Password (not regular password) |
   | `TELEGRAM_BOT_TOKEN` | yes | From `@BotFather` |
   | `TELEGRAM_CHAT_ID`   | yes | Your own chat ID (one of the IDs in `ALLOWED_CHAT_IDS`) |
   | `FRED_API_KEY`       | no  | Treasury yields enrichment |
   | `GNEWS_API_KEY`      | no  | Geopolitics / AI news |
   | `CURRENTS_API_KEY`   | no  | World news supplement |
   | `NEWSDATA_API_KEY`   | no  | AI news supplement |

3. Trigger the first run manually: **Actions → Daily Podcast → Run workflow**.
   Confirm the MP3 arrives by email and Telegram.

**What the workflow does:** runs the full pipeline, then delivers the MP3 to both
your email and your Telegram chat. Best-effort per channel — if Gmail is flaky the
Telegram push still fires, and vice versa. On hard failure (both channels down, or
pipeline crash), a short alert is sent on the same two channels with the log tail
and a link to the Actions run.

**Cost / limits:** fits comfortably in the free GitHub Actions tier for public repos.
For private repos, each run uses ~15 minutes of included compute. MP3s are uploaded
as workflow artifacts with 7-day retention as a safety net.

---
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs(readme): GitHub Actions scheduled runs + secrets checklist"
```

---

## Final verification

- [ ] **Step 1: Run the full test suite**

Run: `pytest -q`
Expected: all tests PASS.

- [ ] **Step 2: Dry-run `main.py` locally with both flags**

Requires `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` + `EMAIL_ADDRESS` + `EMAIL_APP_PASSWORD` set in `.env`.

Run:
```bash
python main.py -e "$EMAIL_ADDRESS" --telegram-chat-id "$TELEGRAM_CHAT_ID"
```

Expected: MP3 generated in `output/`, received by email and in Telegram chat within a few minutes. Logs show both `Episode sent to <email>` and `Episode sent to Telegram chat <id>`.

- [ ] **Step 3: Workflow dry-run (after push)**

Push the branch to GitHub. Set all required secrets. Trigger the workflow via **Actions → Daily Podcast → Run workflow**.

Expected: job completes green; MP3 arrives via both channels; artifact is downloadable from the Actions run.

- [ ] **Step 4: Failure-path verification**

Create a short-lived test branch. Temporarily blank `GEMINI_API_KEY` secret (or set it to a bogus value). Trigger `workflow_dispatch`. Confirm the `Notify failure` step fires and a "[Market Pulse FAILED]" alert arrives on both channels with the log tail and the run URL. Restore the secret afterwards.
