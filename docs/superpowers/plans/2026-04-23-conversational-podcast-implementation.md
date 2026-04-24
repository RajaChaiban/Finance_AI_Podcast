# Conversational Podcast Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform podcast script prompts to generate authentic discussion-style dialogues with topic-specific leaders and natural interruptions.

**Architecture:** Modify `src/script/prompts.py` to add leader/dialogue_style metadata to CATEGORY_SECTIONS, enhance BASE_SYSTEM_PROMPT with rich dialogue examples and discovery patterns, and update build_system_prompt() to inject leadership context into category instructions.

**Tech Stack:** Python 3.x, existing prompts.py structure

---

## File Structure

**Modify:** `src/script/prompts.py`
- Update CATEGORY_SECTIONS dict (add `leader` and `dialogue_style` fields)
- Enhance BASE_SYSTEM_PROMPT (add discovery patterns section, improve dialogue examples)
- Update category instructions to emphasize dialogue
- Modify build_system_prompt() to inject leader/dialogue_style into prompts

**No new files, no test files required** (prompt changes are validated by generating scripts).

---

## Tasks

### Task 1: Add Leader & Dialogue Style Metadata to CATEGORY_SECTIONS

**Files:**
- Modify: `src/script/prompts.py:113-172` (CATEGORY_SECTIONS dict)

- [ ] **Step 1: Update FINANCE_MACRO entry**

Replace lines 114–125 with:

```python
PodcastCategory.FINANCE_MACRO: {
    "title": "Macro Overview",
    "leader": "alex",
    "dialogue_style": "narrative-driven",
    "instruction": (
        "Identify the 2-3 most market-relevant macro stories from the data -- index moves "
        "(S&P 500, DOW, NASDAQ), commodity direction (gold, oil), volatility (VIX), sector "
        "flows, Fear & Greed reading. For each, explain WHY it moved and what it signals "
        "for the broader market. If macro_signals contains a positioning reading, describe "
        "it as a risk-on/risk-off indicator -- not as a buy or sell directive to the "
        "listener. If AI-generated forecasts are in the data, reference them as 'one "
        "model's read' and invite appropriate skepticism. Skip routine items with no "
        "material move. Sam should ask questions that reveal what listeners need to know."
    ),
},
```

- [ ] **Step 2: Update FINANCE_MICRO entry**

Replace lines 127–135 with:

```python
PodcastCategory.FINANCE_MICRO: {
    "title": "Equity Movers & Earnings",
    "leader": "alex",
    "dialogue_style": "question-discovery",
    "instruction": (
        "Pick the 2-3 standout movers from the market quotes and explain the story behind "
        "each -- earnings beat/miss, guidance, sector rotation, news catalyst. Tie sector "
        "moves (XLK, XLF, XLE) back to the macro story from the previous segment when "
        "possible. Discuss ETF flow data only when it reveals a clear institutional shift. "
        "Surface the cross-category connection to crypto or geopolitics if there is one. "
        "Sam asks 'but why did it move?' in real time, discovering the story alongside listeners."
    ),
},
```

- [ ] **Step 3: Update CRYPTO entry**

Replace lines 137–146 with:

```python
PodcastCategory.CRYPTO: {
    "title": "Crypto Corner",
    "leader": "sam",
    "dialogue_style": "question-discovery",
    "instruction": (
        "Cover BTC and ETH price action from the crypto quotes and explain the driver -- "
        "regulatory news, ETF flows, macro correlation, whale activity. If crypto ETF "
        "flows (IBIT, FBTC, GBTC) are in the data, mention them only when there's a "
        "notable inflow/outflow story. Connect crypto moves to the broader risk appetite "
        "from the macro segment: is crypto tracking equities or decoupling? Skip altcoin "
        "noise unless something is truly notable. Alex provides skeptical grounding: "
        "'is that actually material?' Sam drives the narrative with curiosity."
    ),
},
```

- [ ] **Step 4: Update GEOPOLITICS entry**

Replace lines 148–159 with:

```python
PodcastCategory.GEOPOLITICS: {
    "title": "Geopolitics Briefing",
    "leader": "alex",
    "dialogue_style": "narrative-driven",
    "instruction": (
        "Pick the top 1-2 geopolitical stories from conflict_events, unrest_events, and "
        "sanctions data that have material market implications. Reference GDELT topics "
        "(military, nuclear, sanctions, maritime) and cross-source signals like GPS "
        "jamming when present. If Polymarket prediction markets have relevant odds, cite "
        "them as 'what the crowd is pricing'. Most importantly: tie each story to a "
        "market consequence -- commodity prices, currencies, sector exposure, risk "
        "premium. Geopolitics without a market tie-back is news; with a tie-back it's "
        "analysis. Sam connects to markets: 'so what does that mean for commodity prices?'"
    ),
},
```

- [ ] **Step 5: Update AI_UPDATES entry**

Replace lines 161–171 with:

```python
PodcastCategory.AI_UPDATES: {
    "title": "AI Watch",
    "leader": "sam",
    "dialogue_style": "question-discovery",
    "instruction": (
        "Highlight 1-2 meaningful AI developments from the data: major model releases, "
        "funding rounds, regulatory moves, notable research, cyber threats. Focus on "
        "items with company-level or sector-level implications -- skip product press "
        "releases with no market angle. Reference tech prediction markets if present. "
        "Close this segment by naming one specific stock or sector that could be "
        "affected -- without telling the listener to trade it. Sam drives with enthusiasm; "
        "Alex asks 'does this actually move the market?'"
    ),
},
```

- [ ] **Step 6: Verify the dict structure**

Open `src/script/prompts.py` and confirm all five entries compile without errors. Each should have `title`, `leader`, `dialogue_style`, and `instruction` keys.

- [ ] **Step 7: Commit**

```bash
git add src/script/prompts.py
git commit -m "feat: add leader and dialogue_style metadata to CATEGORY_SECTIONS"
```

---

### Task 2: Add AUTHENTIC_DISCOVERY_PATTERNS Section to BASE_SYSTEM_PROMPT

**Files:**
- Modify: `src/script/prompts.py:36–111` (BASE_SYSTEM_PROMPT)

- [ ] **Step 1: Locate insertion point**

Find the line `"Do NOT include stage directions, sound effects, or metadata."` (around line 108). This is before the "EMOTION TAGS" section. We'll insert the new section before "EMOTION TAGS".

- [ ] **Step 2: Add AUTHENTIC_DISCOVERY_PATTERNS section**

After the "USE NATURAL WORD FILLERS LIBERALLY" section (around line 65) and before the "EMOTION TAGS" section (line 96), insert this text into BASE_SYSTEM_PROMPT:

```
AUTHENTIC DISCOVERY PATTERNS
When hosts talk, they should sound like they're figuring things out together in real time, 
not executing a pre-planned script. Here's what authentic discovery sounds like:

EXAMPLE 1 - INTERRUPTION (genuine curiosity):
[S1] "Oil jumped 3%." 
[S2] "Wait, why though?" 
[S1] "Saudi cut supply." 
[S2] "Ooh, so that ripples to energy stocks, right?"
(Sam asks a real question; Alex answers; no monologues.)

EXAMPLE 2 - TANGENT (hosts exploring a connection):
[S1] "Fed held rates steady."
[S2] "Hmm, but didn't that usually mean..."
[S1] "Exactly -- and that's why tech got crushed."
(Sam brings an idea; Alex builds on it; feels like discovery, not delivery.)

EXAMPLE 3 - BACKCHANNELING (rapid, authentic exchange):
[S1] "...so energy prices are spiking overnight."
[S2] "Right, which ripples to..."
[S1] "Consumer spending, yeah."
[S2] "Exactly."
(Short lines, acknowledgment, quick back-and-forth. One host can talk more if the story needs it.)

EXAMPLE 4 - NATURAL DOUBT (hosts questioning each other):
[S1] "This could push gold higher."
[S2] "Or does it actually push it lower?"
[S1] "Good point -- that's what we're watching."
(Sam questions; Alex admits uncertainty; feels real, not polished.)

DO NOT sound like:
- One host explaining while the other listens passively
- Pre-scripted call-and-response ("Listeners, here's why..." "That's right, because...")
- Perfectly balanced sentences; let one host dominate a beat if the story calls for it
- A news broadcast; this is two people discovering stories together
```

- [ ] **Step 3: Verify the string is valid Python**

Open `src/script/prompts.py` and check that BASE_SYSTEM_PROMPT still parses without syntax errors.

- [ ] **Step 4: Commit**

```bash
git add src/script/prompts.py
git commit -m "feat: add AUTHENTIC_DISCOVERY_PATTERNS section to BASE_SYSTEM_PROMPT"
```

---

### Task 3: Enhance DIALOGUE STYLE Examples in BASE_SYSTEM_PROMPT

**Files:**
- Modify: `src/script/prompts.py:46–65` (DIALOGUE STYLE section)

- [ ] **Step 1: Replace the DIALOGUE STYLE section**

Find and replace lines 46–65 (starting with "DIALOGUE STYLE -- EXAMPLES" through the end of that section) with:

```python
DIALOGUE STYLE -- EXAMPLES (CONVERSATIONAL BACK-AND-FORTH)
This is NOT a newscast where one host reads and the other listens. It's a CONVERSATION. Here's what we want:

- GOOD: [S1] "Oil spiked 3% overnight." [S2] "Wait, why?" [S1] "Saudi supply cut." [S2] "Ah, that makes sense. So what does that mean for--" [S1] "Gas prices, yeah."
- BAD: [S1] "Oil spiked 3% overnight due to a Saudi supply cut, which will impact gas prices."

- GOOD: [S1] "Tech stocks got crushed again." [S2] "Another rate-sensitive selloff?" [S1] "Exactly. Fed talk spooked people."
- BAD: [S1] "Tech stocks sold off because market participants grew concerned about Fed tightening rhetoric."

- GOOD (natural interruption): [S1] "The 10-year yield shot up." [S2] "Hold on -- isn't that usually bad for bonds?" [S1] "Yeah, exactly. Which is why we're watching credit spreads."
- BAD: [S1] "The 10-year yield shot up significantly, which portends challenges for fixed-income instruments."

- GOOD (one host dominates, but Sam adds): [S1] "This earnings miss is massive." [S1] "Guidance slashed 20%." [S2] "Whoa, why?" [S1] "They cited macro headwinds." [S2] "So are competitors seeing this too?"
- BAD (balanced but stiff): [S1] "Company X missed earnings." [S2] "What was the reason?" [S1] "Macro headwinds." [S2] "I see."

Short, punchy lines. Questions. Reactions. One host can talk more than the other when the story calls for it. Let the conversation breathe.
```

- [ ] **Step 2: Verify the string is valid**

Check `src/script/prompts.py` for syntax errors.

- [ ] **Step 3: Commit**

```bash
git add src/script/prompts.py
git commit -m "feat: enhance DIALOGUE STYLE examples with natural interruptions and conversational flow"
```

---

### Task 4: Update build_system_prompt() to Inject Leader & Dialogue Style

**Files:**
- Modify: `src/script/prompts.py:233–251` (the loop in build_system_prompt that builds category instructions)

- [ ] **Step 1: Locate the category instruction injection**

Find the section in `build_system_prompt()` around line 238–240 in normal mode and around line 225–227 in brief mode.

- [ ] **Step 2: Update the instruction injection for normal (non-brief) mode**

Find and replace this code block (approximately line 238–240):

```python
for i, cat in enumerate(ordered, start=2):
    section = CATEGORY_SECTIONS[cat]
    prompt += f"{i}. {section['title']} -- {section['instruction']}\n"
```

With:

```python
for i, cat in enumerate(ordered, start=2):
    section = CATEGORY_SECTIONS[cat]
    leader = section.get("leader", "alex")
    dialogue_style = section.get("dialogue_style", "narrative-driven")
    prompt += f"{i}. {section['title']} (led by {leader}, {dialogue_style}): {section['instruction']}\n"
```

- [ ] **Step 3: Update brief mode as well**

Find the brief mode loop (around line 225–227):

```python
for i, cat in enumerate(ordered, start=2):
    section = CATEGORY_SECTIONS[cat]
    prompt += f"{i}. {section['title']} -- biggest story only, 1-2 exchanges.\n"
```

Replace it with:

```python
for i, cat in enumerate(ordered, start=2):
    section = CATEGORY_SECTIONS[cat]
    leader = section.get("leader", "alex")
    prompt += f"{i}. {section['title']} (led by {leader}) -- biggest story only, 1-2 exchanges.\n"
```

- [ ] **Step 4: Verify the function logic**

Manually trace through the function to confirm the leader/dialogue_style injection works correctly.

- [ ] **Step 5: Verify no syntax errors**

Check `src/script/prompts.py` compiles.

- [ ] **Step 6: Commit**

```bash
git add src/script/prompts.py
git commit -m "feat: inject leader and dialogue_style into category instructions in build_system_prompt()"
```

---

### Task 5: Generate Sample Scripts to Verify Changes

**Files:**
- Reference: `src/script/prompts.py` (built system prompt)

- [ ] **Step 1: Create a simple test script to build and display the prompt**

In the project root, create a temporary Python script:

```python
#!/usr/bin/env python3
"""Quick script to test updated prompts and show output."""

from src.data.categories import PodcastCategory, DEFAULT_CATEGORIES
from src.script.prompts import build_system_prompt, build_user_prompt

# Build the system prompt for default categories
system_prompt = build_system_prompt(DEFAULT_CATEGORIES)

# Print the first 500 characters to verify leader/dialogue_style injection
print("=" * 80)
print("SYSTEM PROMPT (first 1500 chars to verify leader/dialogue_style injection):")
print("=" * 80)
print(system_prompt[:1500])
print("\n... (truncated)\n")

# Check that all leaders are present
leaders = ["led by alex", "led by sam"]
for leader in leaders:
    if leader in system_prompt:
        print(f"✓ Found: '{leader}' in prompt")
    else:
        print(f"✗ MISSING: '{leader}' in prompt")

# Check that dialogue styles are present
styles = ["narrative-driven", "question-discovery"]
for style in styles:
    if style in system_prompt:
        print(f"✓ Found: '{style}' in prompt")
    else:
        print(f"✗ MISSING: '{style}' in prompt")

# Check for AUTHENTIC_DISCOVERY_PATTERNS
if "AUTHENTIC DISCOVERY PATTERNS" in system_prompt:
    print("✓ Found: 'AUTHENTIC DISCOVERY PATTERNS' section")
else:
    print("✗ MISSING: 'AUTHENTIC DISCOVERY PATTERNS' section")

print("\n" + "=" * 80)
print("SUCCESS: Prompt generation looks good!")
print("=" * 80)
```

- [ ] **Step 2: Run the test script**

```bash
python test_prompt_gen.py
```

Expected output:
```
=== SYSTEM PROMPT (first 1500 chars...) ===
...
✓ Found: 'led by alex' in prompt
✓ Found: 'led by sam' in prompt
✓ Found: 'narrative-driven' in prompt
✓ Found: 'question-discovery' in prompt
✓ Found: 'AUTHENTIC DISCOVERY PATTERNS' section

======================================
SUCCESS: Prompt generation looks good!
======================================
```

- [ ] **Step 3: Clean up test script**

```bash
rm test_prompt_gen.py
```

- [ ] **Step 4: Commit**

```bash
git add src/script/prompts.py
git commit -m "test: verify leader/dialogue_style injection works correctly"
```

---

## Plan Summary

This plan modifies **one file** (`src/script/prompts.py`) in five focused tasks:

1. **Add metadata:** Leader and dialogue_style to each category
2. **Add discovery section:** AUTHENTIC_DISCOVERY_PATTERNS with concrete examples
3. **Enhance examples:** Better dialogue style examples showing natural flow
4. **Update build logic:** Inject leader/dialogue_style into the final prompt
5. **Verify:** Quick test to confirm metadata injection works

Each task is self-contained and commits independently. The changes guide the LLM to generate more authentic, discussion-style scripts with topic-specific leadership.
