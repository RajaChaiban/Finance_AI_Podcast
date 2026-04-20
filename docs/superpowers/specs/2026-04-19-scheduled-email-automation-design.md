# Scheduled Daily Podcast Automation — Design

**Date:** 2026-04-19
**Status:** Draft
**Owner:** RajaChaiban

## Goal

Run the Market Pulse pipeline automatically every day and deliver the finished MP3 episode to the operator by **both email and Telegram**, with no human in the loop. Failed runs must notify via the same two channels so missing episodes are never silent.

## Non-goals

- Delivery to third parties (subscribers, Spotify). That is the long-term product; this spec is internal daily delivery.
- Web hosting, RSS, or public distribution of MP3s.
- Multi-recipient mailing lists.
- Changing pipeline internals (data, script, audio).

## Requirements

| # | Requirement |
|---|---|
| R1 | Pipeline runs daily on a cron schedule, unattended, with no local machine required. |
| R2 | Target run time: **6:30 AM ET pre-market** (runs before US market open at 9:30 ET). |
| R3 | Uses **default categories** from `config.yaml` (currently `finance_macro` + `finance_micro`). |
| R4 | On success, MP3 is sent to operator via email (`send_episode_email`) **and** Telegram (`sendAudio` API). |
| R5 | On failure, a short notification is sent via email + Telegram with error summary and link to logs. |
| R6 | All secrets (API keys, bot token, app password, recipient IDs) stored as GitHub repo secrets — never committed. |
| R7 | Kokoro model weights cached between runs so cold-start doesn't stretch every run to 10+ min. |
| R8 | Generated MP3 is also retained as a GitHub Actions artifact (7-day retention) as a safety net if both delivery channels fail. |

## Architecture

### Where the pieces live

```
.github/workflows/daily-podcast.yml   NEW — cron schedule + pipeline + delivery + failure handling
src/utils/telegram_sender.py          NEW — push MP3 via Bot API sendAudio (parallel to email_sender.py)
src/utils/notify_failure.py           NEW — short failure notification via email + telegram
main.py                               CHANGED — add --telegram-chat-id flag (parallel to -e)
.env.example                          CHANGED — document TELEGRAM_CHAT_ID var for scheduled pusher
```

### Runtime flow

1. **Cron triggers** GitHub Actions workflow at `30 10 * * *` UTC (= 6:30 AM EDT in summer, 5:30 AM EST in winter; acceptable drift — see "DST" below).
2. Workflow **checks out** the repo, sets up Python, restores Kokoro model cache, installs `requirements.txt`.
3. Workflow **injects secrets** as env vars: `GEMINI_API_KEY`, `EMAIL_ADDRESS`, `EMAIL_APP_PASSWORD`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, plus optional `FRED_API_KEY`, `GNEWS_API_KEY`, etc.
4. Workflow **invokes**:
   ```
   python main.py -e "$EMAIL_ADDRESS" --telegram-chat-id "$TELEGRAM_CHAT_ID"
   ```
   - `main.py` runs the existing 3-stage pipeline (data → script → audio).
   - Stage 4 (delivery) now fans out to both `send_episode_email()` and `send_episode_telegram()`. Each reports success/failure independently. Email failure must not prevent Telegram delivery and vice-versa.
5. Workflow **uploads MP3** from `output/` as an `actions/upload-artifact` step (retention: 7 days).
6. On **any step failure**, workflow runs `python -m src.utils.notify_failure` with the tail of the log and the Actions run URL. This uses the same sender utilities but with a short "run failed" body.

### Module boundaries

- `email_sender.send_episode_email()` — **unchanged** (already exists and works).
- `telegram_sender.send_episode_telegram(mp3_path, chat_id, bot_token, categories) -> bool` — new. Uses `python-telegram-bot`'s `Bot.send_audio()` to push the file to a specific chat. Mirrors the signature of `email_sender`. Returns `True/False`, logs warnings on failure; never raises.
- `notify_failure.notify(error_summary, log_tail, run_url)` — new. Builds a short subject + body, calls both senders with no attachment. Best-effort — both sender failures are logged but don't propagate.
- `main.py` — gains `--telegram-chat-id CHAT_ID` CLI flag. When set, after the existing email send (if any), also calls `send_episode_telegram()`. Both are independent; failure of one doesn't abort the other.

### Delivery fan-out policy

Both channels fire independently. Order: email first, Telegram second (matches user's stated priority order). Exit code of `main.py` is `0` if **at least one** channel succeeds; non-zero only if both fail. This ensures the `if: failure()` path triggers only for actual total-failure cases, not for "telegram delivered but email server was flaky."

### Secrets mapping

Every secret needed mirrors the local `.env` format. Added to repo via GitHub Settings → Secrets and variables → Actions:

| GitHub Secret          | Mirrors local `.env` var | Required for |
|------------------------|--------------------------|--------------|
| `GEMINI_API_KEY`       | `GEMINI_API_KEY`         | Script generation |
| `EMAIL_ADDRESS`        | `EMAIL_ADDRESS`          | Email sender + recipient |
| `EMAIL_APP_PASSWORD`   | `EMAIL_APP_PASSWORD`     | Gmail SMTP auth |
| `TELEGRAM_BOT_TOKEN`   | `TELEGRAM_BOT_TOKEN`     | Telegram push |
| `TELEGRAM_CHAT_ID`     | *(new)* single chat ID   | Telegram push target |
| `FRED_API_KEY`         | `FRED_API_KEY`           | Optional — Treasury yields |
| `GNEWS_API_KEY`        | `GNEWS_API_KEY`          | Optional — geo/AI headlines |
| `CURRENTS_API_KEY`     | `CURRENTS_API_KEY`       | Optional |
| `NEWSDATA_API_KEY`     | `NEWSDATA_API_KEY`       | Optional |

`TELEGRAM_CHAT_ID` is new — the operator's own chat ID (one of the values already in local `ALLOWED_CHAT_IDS`). The scheduled job pushes to a single chat; we don't reuse `ALLOWED_CHAT_IDS` because that list is a security gate for the reactive bot, not a broadcast list.

## Key decisions

### DST drift (acceptable)
GitHub Actions cron is UTC-only with no DST handling. Single cron `30 10 * * *` fires at 6:30 AM during EDT (~8 months/year) and 5:30 AM during EST (~4 months/year). The target is "pre-market" — both times qualify. Dual-cron workarounds (two entries with date-conditional skip logic) add complexity that isn't worth it for a 1-hour drift. If the drift ever matters, the fix is a one-line cron change per season.

### Kokoro model caching
Kokoro-82M weights are ~300 MB. Downloaded on first run, cached thereafter via `actions/cache` keyed on `requirements.txt` hash + Kokoro version. Cold run ~8 min; warm run ~3 min (matching local behavior). Cache eviction happens automatically after 7 days of non-use; next run re-downloads.

### Not committing MP3s to repo
Daily audio files would balloon repo size (20–30 MB × 365 = ~10 GB/yr). GH Actions artifacts (7-day retention) give short-term fallback access without touching the repo. Long-term archival is a future feature (S3/GCS or Spotify RSS host).

### Single entry point (`main.py`) vs new `scheduled_run.py`
Chose to extend `main.py` with a `--telegram-chat-id` flag rather than create a parallel runner. Reasons: (1) pipeline logic stays in one place; (2) the same command works for manual CLI testing and the scheduler; (3) matches the existing `-e` flag pattern. A separate runner would duplicate data/script/audio orchestration — needless drift.

### Telegram delivery is best-effort per channel
A flaky SMTP server should not prevent Telegram delivery (or vice-versa). Each sender returns `bool`; `main.py` logs a warning for the failed one and still exits 0 if the other succeeded. Only both-failing triggers the workflow's `if: failure()` path.

## Error handling

| Failure mode | Behavior |
|---|---|
| Gemini API error | Pipeline raises; workflow fails; `notify_failure` fires with error summary. |
| World Monitor / news 5xx | Collectors already degrade gracefully (see `ARCHITECTURE.md`); pipeline proceeds with partial snapshot. |
| Kokoro OOM / crash | Pipeline raises; workflow fails; `notify_failure` fires. |
| Email SMTP auth fails | Logged warning; Telegram still attempted; overall exit 0 if TG succeeds. |
| Telegram file too large (>50 MB) | `send_episode_telegram` catches and logs; email still attempted. Extremely rare for ~20-min episodes. |
| Bot token revoked / chat blocked | Logged warning; non-fatal if email succeeds. |
| Both deliveries fail | `main.py` exits non-zero → workflow fails → `notify_failure` fires (itself best-effort; if notification also fails, the GH Actions run status is the last line of defense). |

## Testing plan

Manual testing prior to enabling the schedule:

1. **Local dry-run:** `python main.py -e $EMAIL_ADDRESS --telegram-chat-id $CHAT_ID` — verify both channels receive the current day's episode. Already tested channels work; only validates the new CLI flag + telegram_sender.
2. **Workflow dry-run:** add `workflow_dispatch:` trigger alongside `schedule:` so the job can be kicked manually from the Actions tab. Run it once; confirm MP3 arrives by email + Telegram.
3. **Failure-path test:** temporarily unset `GEMINI_API_KEY` in a test branch workflow run; confirm `notify_failure` fires and the message arrives on both channels with a useful log tail.
4. **Cache hit:** run workflow twice and confirm the second run skips Kokoro model download (check Actions log for cache-hit line).

No unit tests required for `telegram_sender` — it's a thin wrapper around a vetted library, same posture as the existing `email_sender`. Integration test is the dry-run above.

## Open items (explicit, not TBD)

- **None.** All prior open questions (schedule, timezone, categories, delivery channels, failure behavior, artifact retention) are resolved in this spec.

## Future work (out of scope for this spec)

- Long-term MP3 archival (S3 / GCS / Spotify RSS host).
- Multiple recipients / mailing list.
- Retry-on-failure (user chose notify-only for now).
- Pause-on-market-holidays (Labor Day episodes have no market context — can add a holiday check later).
