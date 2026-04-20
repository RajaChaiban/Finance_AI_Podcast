# Strategic Memo: Market Pulse Go-to-Market

_Prepared: 2026-04-18 • Based on competitor analysis (market-pulse-competitors-2026-04-18.md) and AI-podcast state-of-market (ai-generated-podcasts-state-2026-04-18.md)_

## Bottom line

**Launch as a daily podcast show first — not an app, not a SaaS.** Publish via RSS host (Buzzsprout / Transistor / Spotify for Podcasters) to Apple Podcasts + Spotify on day one; add YouTube within 60 days. Defer SaaS and mobile-app builds 12–18 months. Focus on **one category** for the first 30 episodes, not five.

The scarce resource isn't your code. It's your audience. You have shipped technology that a commercial competitor (AutomatedPodcasts.com) charges $29/mo for, and a niche (live-quant-data → two-host audio) nobody else occupies. What you don't have is distribution, listeners, or category proof. Those come from publishing, not coding.

## The three decisions, answered

| Decision | Recommendation | Why |
|---|---|---|
| **Release as content or as product?** | **Content first.** Ship a daily podcast. Productize only after ≥500 weekly listeners. | Building SaaS/app before you have audience is backward. AutomatedPodcasts.com is already at $29/mo for the closest-competing product; fighting them on UX without listeners is a losing battle. |
| **Which platforms?** | **Apple + Spotify day 1; YouTube by day 60; proprietary app never (for now).** | Apple+Spotify cover ~85% of podcast listening at zero listener-side friction. YouTube is critical — 1B+ monthly podcast viewers and the 55+ demographic (your finance audience) is the fastest-growing segment there. A proprietary app has zero pull without an audience already asking for it. |
| **What niche?** | **One category, not five. My pick: crypto.** Macro as fallback. | Macro is saturated (Bloomberg, WSJ, CNBC, Morning Brew all publish daily). Crypto is: (a) younger audience more tolerant of AI-generated content, (b) cleaner structured data from CoinGecko, (c) less competition in the "quant daily briefing" format, (d) global, not US-centric. |

## Where to focus — 90-day priority stack

### P0 · Unblock distribution (Week 1–2)
1. **RSS 2.0 feed generator.** Episodes + show notes + AI disclosure + artwork → valid podcast RSS. Host on Vercel/GitHub Pages/S3 — free. Without RSS, nothing else matters.
2. **Podcast host setup.** Buzzsprout ($0–12/mo) or Spotify for Podcasters (free) handles Apple/Spotify/Google submission. One-day task.
3. **Episode show-notes template** with mandatory AI disclosure block (Apple already requires this for "material portion"; Spotify's policy will follow within 12 months — build for it now).

### P1 · Kill the hallucination risk (Week 2–3)
This is the single biggest category killer. The Washington Post pilot died because 68–84% of scripts had fabricated quotes — not because of voice quality.
1. **Fact-grounding constraint:** every numeric claim in the Gemini output must trace to a field in that day's `snapshot.json`. Add a post-generation validator that flags unlinked numbers.
2. **Quote discipline:** blacklist "as [analyst] said" patterns unless the quote appears verbatim in a news item the pipeline actually fetched.
3. **Cite dates:** every datapoint in the script references the data date (e.g., "as of today's close" vs. vague). This is free credibility.

### P2 · Voice-quality sanity check (Week 2)
Blind A/B one episode: Kokoro-82M vs. ElevenLabs Turbo on identical script. Share with 10 listeners. If Kokoro loses badly, don't ship Kokoro publicly — integrate an ElevenLabs fallback route for published episodes even if it costs $30/mo.

Kokoro remains the right default for the pipeline; the question is whether it's listener-grade for *public* audio. Your competitive moat on TTS cost only matters if the quality floor is passed.

### P3 · Narrow to one category, one host pair, one length (Week 3–4)
- Fixed show name (e.g., "Market Pulse Crypto Daily")
- Fixed host names (not randomized per-episode)
- Fixed intro/outro music (royalty-free)
- Fixed episode length window (e.g., 8–12 min — not 20)
- Fixed publish time (e.g., 7:00 AM ET daily)

Consistency is the parasocial trust signal. Variable shows break listener habits.

### P4 · YouTube by day 60 (Week 5–8)
- Static visual: title card + waveform + chapter markers — 1 day of FFmpeg work.
- Upload same audio; YouTube's algorithm will find a different audience than Apple/Spotify (bigger, older, different discovery path).
- Crucially: YouTube titles/thumbnails carry much more traffic weight than Apple/Spotify show art. Invest here.

## Where NOT to focus

| Temptation | Cost | Why not |
|---|---|---|
| Build a mobile app | 3–6 months dev | No audience → no downloads. App stores are graveyards of pre-audience apps. |
| Build a SaaS to compete with AutomatedPodcasts | 6–12 months | They have distribution + hosting + billing infra. You'd be building what they already sold. |
| Voice cloning feature | 1–2 months | Regulatorily risky (Spotify/Apple tightening), expensive, not your differentiator. |
| NotebookLM-class document-audio | 1 month | Different category; you'd lose on UX and voice. |
| Run all 5 categories from day 1 | Ongoing attention tax | 5 thin shows = 0 audience. Pick one, compound, expand later. |
| Polish the Streamlit UI | 1 week of vanity | The customer is the listener, not the operator. |

## The positioning statement

Own this phrase publicly:

> **"The daily quant-data briefing for crypto. AI-generated. Fully transparent. Zero human cost — so it's the same time tomorrow, and the day after, forever."**

Each clause does work:
- **"Quant-data"** — separates you from the failing "AI editorial" category (Bartlett's *100 CEOs*, WaPo pilot). You're a briefing, not an opinion show.
- **"Fully transparent"** — pre-empts disclosure concerns and signals you're not pretending.
- **"Zero human cost"** — the structural reason you can publish daily where humans can't. It's the answer to "why does this show exist?"
- **"Same time tomorrow forever"** — reliability is your edge. Humans get sick, go on vacation. You don't.

## Strategic risks to watch

1. **Apple disclosure enforcement tightens.** Add the disclosure block now; don't risk a strike post-launch.
2. **Pompliano ProCap Financial's reception.** If it flops, the "fully AI finance podcast" category gets a headwind. If it succeeds, you have a proof point and should move faster. Re-check in 60 days.
3. **Gemini pricing / API changes.** Your cost structure assumes free-tier / cheap Gemini. If Google changes terms, map to a fallback (Claude Haiku, local Llama) before you have paid listeners.
4. **Kokoro voice model freeze.** Local OSS models can stagnate. Maintain an ElevenLabs escape hatch in the pipeline.

## 90-day success criteria

| Week | Milestone |
|---|---|
| 2 | RSS live, Episode #1 on Apple + Spotify |
| 4 | Disclosure + fact-grounding shipped; 5 consecutive episodes with no fabricated numbers |
| 6 | 100 weekly unique listeners |
| 8 | YouTube channel live with first 30 episodes |
| 12 | **500 weekly unique listeners** — decision point |

At 500 weekly, two paths open:
- **Scale the show** — add a second category, invest in production quality, start sponsor outreach.
- **Productize** — the audience validates the format; now building a SaaS or B2B white-label has a story to tell prospects.

Below 500 by day 90: the lesson is that either the category, format, or voice quality isn't landing. Rotate one variable and rerun. Worth the 90 days.

## One-line answer to your question

**Don't build an app. Ship the podcast. Crypto-daily, RSS-first, Apple + Spotify + YouTube. Everything else waits until 500 weekly listeners tell you to build it.**
