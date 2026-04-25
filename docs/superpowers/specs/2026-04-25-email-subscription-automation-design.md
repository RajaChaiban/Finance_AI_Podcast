# Email Subscription Automation Design

**Date:** 2026-04-25  
**Objective:** Enable Market Pulse podcast subscribers to sign up via LinkedIn comments, receive daily podcast episodes via email at 7 AM ET.

---

## Overview

Market Pulse subscribers will sign up by commenting "Send" (or similar) on a LinkedIn post. A bot replies with a Google Form link. Users fill in their email → Google Sheets auto-collects responses. Every morning at 7 AM ET, GitHub Actions runs the podcast generation pipeline and emails the episode to all subscribers.

---

## Architecture

### Components

1. **LinkedIn Bot** — Monitors post comments, replies with signup link when triggered
2. **Google Form + Google Sheets** — Collects subscriber emails, auto-syncs to Sheets
3. **GitHub Actions Scheduler** — Runs daily at 7 AM ET
4. **Subscriber Registry** — `subscribers.json` in repo (source of truth)
5. **Validation Job** — GitHub Actions pulls new emails from Sheets, validates, adds to `subscribers.json`
6. **Podcast Generation** — Existing pipeline (main.py, script generation, audio, email send)
7. **Email Sender** — Existing send_episode_email() function

### Data Flow

```
LinkedIn Comment ("Send")
    ↓
LinkedIn Bot (replies with form link)
    ↓
Google Form (user submits email)
    ↓
Google Sheets (auto-collect responses)
    ↓
GitHub Actions @ 7 AM ET (daily cron job)
    ├─ Read Google Sheets for new emails
    ├─ Validate + deduplicate
    ├─ Add to subscribers.json
    ├─ Generate podcast (main.py --stage all)
    ├─ Send to all subscribers (loop through subscribers.json, call send_episode_email for each)
    └─ Log results + notify on failure
```

---

## Components in Detail

### 1. LinkedIn Bot

**What:** Automated comment responder that detects keywords in comments and replies with signup URL.

**How:** 
- Manual monitoring OR third-party bot service (e.g., Buffer, Later, or custom Python script that polls LinkedIn API)
- Detects comment keywords: "Send", "Subscribe", "Add me", etc.
- Replies with: "Great! Sign up here: [Google Form URL] — just fill in your email and you'll get tomorrow's episode at 7 AM ET."

**Scope:** Out of scope for this design (user will handle LinkedIn bot setup). We just need to provide the Google Form URL.

---

### 2. Google Form + Google Sheets

**Form Fields:**
- Email address (required, email validation)
- Name (optional)
- Timestamp (auto)

**Form submission target:** Google Sheet named "Market Pulse Subscribers"

**Sheet structure:**
```
| Timestamp | Name | Email | Added to subscribers.json |
|-----------|------|-------|--------------------------|
| 2026-04-25 08:15 | Alice | alice@example.com | FALSE |
| 2026-04-25 09:30 | Bob | bob@example.com | FALSE |
```

**Setup:**
- Create Google Form → link to Google Sheet
- Enable Google Sheets API in Google Cloud Console
- Generate service account key (JSON) for GitHub Actions to authenticate
- Store key as GitHub Action secret

---

### 3. Subscriber Registry (`subscribers.json`)

**Location:** `subscribers.json` in repo root

**Format:**
```json
{
  "subscribers": [
    {
      "email": "alice@example.com",
      "name": "Alice",
      "added_date": "2026-04-25",
      "unsubscribed": false
    },
    {
      "email": "bob@example.com",
      "name": "Bob",
      "added_date": "2026-04-25",
      "unsubscribed": false
    }
  ]
}
```

**Source of Truth:** This file is the authoritative list. GitHub Actions uses it to determine who gets the podcast.

**Management:**
- GitHub Actions adds new validated emails
- Manual edits for unsubscribe/corrections
- Version-controlled in git

---

### 4. GitHub Actions Workflow

**Trigger:** Daily at 7 AM ET (cron: `0 7 * * *` in UTC = `0 12 * * *`)

**Steps:**
1. Checkout repo
2. Read Google Sheets (fetch new responses since last run)
3. Validate emails (format check, no duplicates)
4. Update `subscribers.json` with new subscribers
5. Commit changes to repo
6. Run podcast generation: `python main.py --stage all --categories finance_macro finance_micro crypto geopolitics ai_updates --length-preset standard`
7. Loop through `subscribers.json` and call `send_episode_email()` for each subscriber
8. Log results (success/failure counts)
9. On failure, send admin notification email

**Environment Variables Needed:**
- `GOOGLE_SHEETS_API_KEY` — Service account JSON (GitHub Secret)
- `EMAIL_ADDRESS` — Sender email (already in .env)
- `EMAIL_APP_PASSWORD` — Gmail app password (already in .env)
- `GEMINI_API_KEY` — For script generation (already in .env)
- Other API keys (FRED, GNEWS, etc.) — already in .env

---

### 5. Integration with Existing Pipeline

**No changes to existing code.** The workflow leverages:
- `main.py` — existing CLI for podcast generation
- `send_episode_email()` — existing email function
- `.env` configuration — existing API keys

**New code only:**
- GitHub Actions workflow YAML file
- Python script to read Google Sheets and update `subscribers.json`
- Unsubscribe mechanism (optional: form link or email reply handling)

---

## Success Criteria

1. ✅ LinkedIn subscribers can sign up by commenting "Send" + filling Google Form
2. ✅ New emails are pulled from Google Sheets and added to `subscribers.json` daily
3. ✅ Podcast is generated once per day with default categories
4. ✅ Email is sent to all subscribers at 7 AM ET
5. ✅ Duplicate emails are prevented
6. ✅ Failed emails are logged and reported
7. ✅ Unsubscribe mechanism works (optional MVP: manual removal from JSON)

---

## Scope & Constraints

**In Scope:**
- Daily automated podcast generation and email distribution
- Google Sheets → `subscribers.json` sync
- Email validation and deduplication
- GitHub Actions scheduler

**Out of Scope (MVP):**
- LinkedIn API integration (user handles bot setup)
- Unsubscribe links in emails (can add later)
- Subscriber preferences/customization (all get same podcast)
- Weekly digests (daily only)
- Analytics/tracking (open rates, etc.)

---

## Testing & Validation

1. **Manual test:** Add 2-3 test emails to Google Form, verify they appear in Sheets
2. **Local test:** Run GitHub Actions workflow locally (act tool) to verify logic
3. **Live test:** Run workflow on schedule, verify emails arrive at test addresses
4. **Failure test:** Disable Gemini API key, verify error handling works

---

## Rollout Plan

**Phase 1:** Set up Google Form, GitHub Actions workflow, test with 2-3 emails
**Phase 2:** Post on LinkedIn, enable LinkedIn bot, go live with real subscribers
**Phase 3:** Monitor for 1 week, adjust as needed (timing, categories, email format)

---

## Notes & Open Questions

- **LinkedIn bot:** User will choose tool/setup. We provide the Google Form URL they can link to.
- **Timezone:** Hardcoded to 7 AM ET (UTC-4 during DST, UTC-5 in winter). Adjust cron as needed.
- **Unsubscribe:** MVP doesn't include unsubscribe links. Can add later via email replies or form link.
- **Failure notifications:** Should admin receive email on failure? (Yes, recommend)
- **Categories:** MVP uses all default categories. Customization deferred to Phase 2.
