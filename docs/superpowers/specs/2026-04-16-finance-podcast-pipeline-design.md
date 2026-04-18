# Finance Podcast Pipeline -- Design Spec

## Context

**Problem:** Staying informed about daily financial markets requires consuming multiple sources (news sites, data feeds, social sentiment). This is time-consuming and fragmented.

**Solution:** An automated pipeline that collects financial market data (macro + micro + crypto + commodities + forex), uses Gemini to transform it into a casual two-speaker podcast script, and generates audio using Kokoro-82M TTS. The output is a ~10-15 minute daily podcast episode saved locally as MP3.

**Why now:** Open-source TTS models (Kokoro-82M) have reached podcast-quality output at minimal compute cost (runs on CPU). Financial data APIs offer generous free tiers. The pipeline is feasible without any paid infrastructure.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Pipeline Orchestrator                     │
│                        (main.py)                            │
└──────────┬──────────────┬──────────────┬────────────────────┘
           │              │              │
           v              v              v
   ┌──────────────┐ ┌──────────┐ ┌──────────────┐
   │ Data Collection│ │  Script  │ │    Audio     │
   │   (parallel)  │ │Generation│ │  Generation  │
   │               │ │ (Gemini) │ │ (Kokoro-82M) │
   │ - Finnhub     │ │          │ │              │
   │ - MarketAux   │ │          │ │              │
   └──────────────┘ └──────────┘ └──────────────┘
           │              │              │
           v              v              v
     MarketSnapshot    Script text     MP3 file
     (dataclass)       ([S1]/[S2])     (output/)
```

**Flow:** Collect data → Generate script → Generate audio → Save MP3

---

## Module 1: Data Collection

### 1.1 FinnhubCollector (`src/data/finnhub_collector.py`)

Uses the Finnhub API (free tier: 60 requests/min).

**Data collected:**
- **Market indices:** S&P 500, NASDAQ, DOW -- daily open/close/change %
- **Top movers:** Biggest gainers and losers of the day
- **Earnings calendar:** Companies reporting today, EPS beat/miss
- **Economic calendar:** Fed decisions, CPI, GDP, employment data releases
- **Crypto:** BTC, ETH prices and 24h change
- **Forex:** Major pairs (EUR/USD, GBP/USD, USD/JPY) daily moves

**Returns:** Dict of categorized market data

### 1.2 MarketAuxCollector (`src/data/marketaux_collector.py`)

Uses the MarketAux API (free tier: 100 requests/day).

**Data collected:**
- **Top financial news:** Headline, summary, source, published time
- **Entity sentiment:** Per-entity sentiment scores (bullish/bearish/neutral)
- **Market narratives:** What themes are driving markets today

**Returns:** Dict of news items with sentiment annotations

### 1.3 MarketSnapshot (`src/data/models.py`)

A dataclass that merges all collected data into a unified structure:

```python
@dataclass
class MarketSnapshot:
    date: str
    indices: dict          # S&P, NASDAQ, DOW performance
    top_gainers: list      # Top 5 gaining stocks
    top_losers: list       # Top 5 losing stocks
    earnings: list         # Earnings reports today
    economic_events: list  # Macro events (Fed, CPI, etc.)
    crypto: dict           # BTC, ETH prices + changes
    forex: dict            # Major currency pairs
    commodities: dict      # Oil, gold prices + changes
    news: list             # Top news with sentiment
    market_sentiment: str  # Overall market mood
```

---

## Module 2: Script Generation (Gemini)

### 2.1 ScriptGenerator (`src/script/generator.py`)

Uses the Google Gemini API to transform MarketSnapshot into a podcast script.

**Process:**
1. Serialize `MarketSnapshot` into a structured data block
2. Send to Gemini with a system prompt defining format and personality
3. Receive a two-speaker script with `[S1]` and `[S2]` tags
4. Validate script structure (has both speakers, reasonable length)

### 2.2 Prompt Templates (`src/script/prompts.py`)

**System prompt defines:**
- Two hosts: casual, educational tone ("two friends discussing markets over coffee")
- Script structure: opening hook → macro overview → equity movers → crypto update → commodities & forex → what to watch tomorrow → sign-off
- Target length: ~2500-3500 words (produces ~10-15 min audio)
- Output format: `[S1] text...\n[S2] text...\n` (Kokoro-compatible)
- Style guidelines: explain jargon, use analogies, keep it conversational

**User prompt:**
- Contains the serialized MarketSnapshot data
- Asks Gemini to prioritize the most impactful/interesting stories

---

## Module 3: Audio Generation (Kokoro-82M)

### 3.1 KokoroEngine (`src/audio/kokoro_engine.py`)

Wraps Kokoro-82M for podcast audio generation.

**Process:**
1. Load Kokoro model (one-time, cached after first load)
2. Parse script into ordered segments: `[(speaker, text), ...]`
3. Map speakers to Kokoro voices:
   - S1 → "af_adam" (male voice)
   - S2 → "af_bella" (female voice)
4. Generate audio for each segment
5. Return list of audio arrays

### 3.2 AudioProcessor (`src/audio/processor.py`)

Handles post-processing and export.

**Process:**
1. Concatenate audio segments with ~300ms silence between speaker turns
2. Normalize audio levels across the episode
3. Export as MP3 with metadata:
   - Title: "Market Pulse -- YYYY-MM-DD"
   - Episode number (auto-incremented)
4. Save to `output/YYYY-MM-DD-market-pulse.mp3`

---

## Module 4: Pipeline Orchestrator

### 4.1 main.py

Chains all modules in sequence:

```
1. Load config (API keys, voice settings, output path)
2. Run data collectors in parallel (asyncio.gather)
3. Merge results into MarketSnapshot
4. Generate podcast script via Gemini
5. Generate audio via Kokoro
6. Save MP3 to output directory
7. Log summary (episode length, file size, data sources used)
```

**CLI interface:**
- `python main.py` -- run full pipeline
- `python main.py --stage data` -- only collect data (save as JSON)
- `python main.py --stage script` -- generate script from saved data
- `python main.py --stage audio` -- generate audio from saved script
- `python main.py --date 2026-04-15` -- generate for a specific date

---

## Configuration

### config.yaml

```yaml
# API Keys (override with .env)
finnhub_api_key: ${FINNHUB_API_KEY}
marketaux_api_key: ${MARKETAUX_API_KEY}
gemini_api_key: ${GEMINI_API_KEY}

# Podcast Settings
podcast_name: "Market Pulse"
target_length_words: 3000
tone: "casual_educational"

# Voice Settings
speaker_1_voice: "af_adam"
speaker_2_voice: "af_bella"
pause_between_turns_ms: 300

# Output
output_dir: "output"
audio_format: "mp3"
```

### .env (gitignored)

```
FINNHUB_API_KEY=your_key_here
MARKETAUX_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

---

## Project Structure

```
Finance_Podcast/
├── main.py                  # Pipeline orchestrator + CLI
├── config.yaml              # Pipeline configuration
├── .env                     # API keys (gitignored)
├── .gitignore
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── finnhub_collector.py
│   │   ├── marketaux_collector.py
│   │   └── models.py           # MarketSnapshot dataclass
│   ├── script/
│   │   ├── __init__.py
│   │   ├── generator.py        # Gemini script generation
│   │   └── prompts.py          # Prompt templates
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── kokoro_engine.py    # Kokoro-82M TTS wrapper
│   │   └── processor.py        # Audio concatenation + MP3 export
│   └── utils/
│       ├── __init__.py
│       └── logger.py           # Structured logging
├── output/                     # Generated episodes (gitignored)
│   └── .gitkeep
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-04-16-finance-podcast-pipeline-design.md
```

---

## Dependencies

```
# Data collection
finnhub-python        # Finnhub API client
httpx                 # Async HTTP for MarketAux

# Script generation
google-genai          # Gemini API client

# Audio generation
kokoro>=0.9           # Kokoro-82M TTS
soundfile             # Audio I/O
numpy                 # Audio processing
pydub                 # MP3 export + audio concatenation

# Infrastructure
pyyaml                # Config parsing
python-dotenv         # .env loading
click                 # CLI interface
```

---

## Verification Plan

### End-to-End Test
1. Set up API keys in `.env`
2. Run `python main.py` -- full pipeline should produce an MP3 in `output/`
3. Listen to the generated episode -- verify two distinct voices, coherent content, ~10-15 min length

### Stage-by-Stage Testing
1. `python main.py --stage data` -- verify JSON output contains all categories (indices, crypto, forex, commodities, earnings, news)
2. `python main.py --stage script` -- verify script has `[S1]`/`[S2]` tags, ~2500-3500 words, covers all market categories
3. `python main.py --stage audio` -- verify MP3 output, two distinct voices, proper speaker transitions

### Edge Cases
- Market holidays (no trading data) -- should handle gracefully, focus on news/macro
- API rate limits -- verify retry logic works
- Empty data categories (no earnings today) -- script should skip that section naturally

---

## Future Enhancements (Not in Scope)
- Email/WhatsApp delivery
- Daily scheduling (cron/Task Scheduler)
- Web dashboard for episode history
- Custom voice cloning for consistent host identities
- Spotify/Apple Podcasts RSS feed generation
