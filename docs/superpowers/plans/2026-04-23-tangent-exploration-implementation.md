# Tangent Exploration Prompt Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add tangent exploration patterns and directives to prompts so LLM generates organic exploratory dialogue moments in appropriate segments.

**Architecture:** Add a new TANGENT EXPLORATION PATTERNS section to BASE_SYSTEM_PROMPT with 3 concrete examples, then modify 3 question-discovery category instructions (FINANCE_MICRO, CRYPTO, AI_UPDATES) to include tangent directives. Narrative-driven categories (FINANCE_MACRO, GEOPOLITICS) remain unchanged to maintain focus.

**Tech Stack:** Python 3.x, existing prompts.py structure

---

## File Structure

**Modify:** `src/script/prompts.py`
- Add TANGENT EXPLORATION PATTERNS section to BASE_SYSTEM_PROMPT (after AUTHENTIC_DISCOVERY_PATTERNS, before EMOTION_TAGS)
- Update FINANCE_MICRO category instruction to include tangent directive
- Update CRYPTO category instruction to include tangent directive
- Update AI_UPDATES category instruction to include tangent directive
- FINANCE_MACRO and GEOPOLITICS instructions remain unchanged

**No new files required.**

---

## Tasks

### Task 1: Add TANGENT_EXPLORATION_PATTERNS Section to BASE_SYSTEM_PROMPT

**Files:**
- Modify: `src/script/prompts.py:36-111` (BASE_SYSTEM_PROMPT)

- [ ] **Step 1: Locate insertion point in BASE_SYSTEM_PROMPT**

Find the line `"EMOTION TAGS (optional prosody guidance..."` around line 96. We'll insert the new section just before this.

- [ ] **Step 2: Insert TANGENT_EXPLORATION_PATTERNS section**

After AUTHENTIC_DISCOVERY_PATTERNS section (around line 95) and before EMOTION TAGS section (line 96), insert:

```
TANGENT EXPLORATION PATTERNS
Sometimes the most natural conversations diverge briefly to explore a related angle, then return to the main thread. 
This is how real people discover ideas together. Here's what authentic tangent exploration sounds like:

EXAMPLE 1 - SECONDARY EFFECTS TANGENT:
[S1] "Bitcoin rallied on this ETF inflow news."
[S2] "Wait, but doesn't that mean institutions are rotating OUT of something else?"
[S1] "Oh, good point -- yeah, we're seeing outflows from Ethereum ETFs..."
[S2] "So they're consolidating into Bitcoin specifically, not just buying crypto broadly?"
[S1] "Exactly. Which is why we're watching how this shapes the altcoin space."
[S2] "Right, so if Ethereum weakens relative to Bitcoin..."
[S1] "...dominance shifts. And that's the macro signal for the next segment."

(S2 opens the tangent with a "but what about..." question: "rotating OUT of something else?" 
This is genuine curiosity, not rhetorical. Both explore briefly together, then S1 naturally closes the tangent 
and bridges to the next topic. The tangent felt like a discovery, not a detour.)

EXAMPLE 2 - EXPECTATION IMPLICATIONS TANGENT:
[S1] "Fed held rates steady, but signaled more hikes ahead."
[S2] "Hmm, but if the market was already pricing in hikes, doesn't that mean they're signaling even MORE than expected?"
[S1] "Exactly -- the forward guidance was hawkish. Bond traders panicked."
[S2] "So banks benefit from higher rates, but tech gets hit?"
[S1] "Right. That's why we saw XLK rally and XLT selloff."
[S2] "Which ties into what we saw in crypto..."
[S1] "Yep, exactly."

(S2's tangent: "even MORE than expected?" opens discussion about *expectation management*, 
not just the rate decision. Quick exploration, natural flow to next segment.)

EXAMPLE 3 - ECOSYSTEM CONSEQUENCE TANGENT:
[S1] "AI companies are committing massive infrastructure spending."
[S2] "But doesn't that drive up power demand and semiconductor scarcity?"
[S1] "Good catch -- yeah, NVIDIA and the power grid companies are getting a boost."
[S2] "So geopolitical tensions around chip manufacturing become even MORE relevant?"
[S1] "Exactly. Which is why the Taiwan situation is so market-sensitive right now."
[S2] "Got it. So that segues into geopolitics..."

(S2's tangent explores the *upstream consequences* of the AI capex boom. Opens naturally, 
both explore, S1 resolves and transitions.)

PATTERN RECOGNITION:
- Tangent starts with S2 asking "but what about..." or "doesn't that mean..." (genuine curiosity)
- Represents a *sideways* exploration (different angle on same topic), not a topic jump
- Gets 1-2 back-and-forth exchanges (brief, contained)
- Closes naturally with S1 returning to main narrative or bridging to next segment
- Feels like organic discovery, not mechanical insertion
```

- [ ] **Step 3: Verify the string is valid Python**

Open `src/script/prompts.py` and check that BASE_SYSTEM_PROMPT still parses without syntax errors.

You can test with: `python -m py_compile src/script/prompts.py`

- [ ] **Step 4: Commit**

```bash
git add src/script/prompts.py
git commit -m "feat: add TANGENT_EXPLORATION_PATTERNS section to BASE_SYSTEM_PROMPT"
```

---

### Task 2: Modify FINANCE_MICRO Category Instruction

**Files:**
- Modify: `src/script/prompts.py:127-135` (FINANCE_MICRO instruction)

- [ ] **Step 1: Locate FINANCE_MICRO instruction**

Find the CATEGORY_SECTIONS dict entry for `PodcastCategory.FINANCE_MICRO` around line 127.

- [ ] **Step 2: Replace the instruction**

Replace the current `"instruction"` value with:

```python
"instruction": (
    "Pick the 2-3 standout movers from the market quotes and explain the story behind "
    "each -- earnings beat/miss, guidance, sector rotation, news catalyst. Tie sector "
    "moves (XLK, XLF, XLE) back to the macro story from the previous segment when "
    "possible. Discuss ETF flow data only when it reveals a clear institutional shift. "
    "Surface the cross-category connection to crypto or geopolitics if there is one. "
    "Sam asks 'but why did it move?' in real time, discovering the story alongside listeners. "
    "\n\n"
    "TANGENT EXPLORATION: S2 should open 1-2 tangents by asking 'but what about...' or "
    "'doesn't that mean...' questions that naturally extend the topic sideways (e.g., asking "
    "about secondary effects, stakeholder rotation, sector ecosystem implications). These should "
    "be genuine curiosity questions, not rhetorical. S1 should recognize these openings and "
    "explore briefly with S2 for 1-2 exchanges before naturally returning to the main narrative "
    "thread or bridging to the next segment. Tangents should feel like organic discoveries, "
    "not scripted diversions."
),
```

- [ ] **Step 3: Verify syntax**

Check `src/script/prompts.py` compiles: `python -m py_compile src/script/prompts.py`

- [ ] **Step 4: Commit**

```bash
git add src/script/prompts.py
git commit -m "feat: add tangent exploration directive to FINANCE_MICRO instruction"
```

---

### Task 3: Modify CRYPTO Category Instruction

**Files:**
- Modify: `src/script/prompts.py:137-146` (CRYPTO instruction)

- [ ] **Step 1: Locate CRYPTO instruction**

Find the CATEGORY_SECTIONS dict entry for `PodcastCategory.CRYPTO` around line 137.

- [ ] **Step 2: Replace the instruction**

Replace the current `"instruction"` value with:

```python
"instruction": (
    "Cover BTC and ETH price action from the crypto quotes and explain the driver -- "
    "regulatory news, ETF flows, macro correlation, whale activity. If crypto ETF "
    "flows (IBIT, FBTC, GBTC) are in the data, mention them only when there's a "
    "notable inflow/outflow story. Connect crypto moves to the broader risk appetite "
    "from the macro segment: is crypto tracking equities or decoupling? Skip altcoin "
    "noise unless something is truly notable. Alex provides skeptical grounding: "
    "'is that actually material?' Sam drives the narrative with curiosity. "
    "\n\n"
    "TANGENT EXPLORATION: S2 should open 1-2 tangents by asking 'but what about...' or "
    "'doesn't that mean...' questions that explore secondary effects (e.g., 'if institutions "
    "rotate into Bitcoin, what are they rotating out of?' or 'what does that do to altcoins?'). "
    "These should be genuine curiosity questions. S1 should recognize these openings and "
    "explore briefly with S2 for 1-2 exchanges before returning to the main narrative. "
    "Tangents should feel like organic discoveries, not scripted diversions."
),
```

- [ ] **Step 3: Verify syntax**

Check `src/script/prompts.py` compiles: `python -m py_compile src/script/prompts.py`

- [ ] **Step 4: Commit**

```bash
git add src/script/prompts.py
git commit -m "feat: add tangent exploration directive to CRYPTO instruction"
```

---

### Task 4: Modify AI_UPDATES Category Instruction

**Files:**
- Modify: `src/script/prompts.py:161-171` (AI_UPDATES instruction)

- [ ] **Step 1: Locate AI_UPDATES instruction**

Find the CATEGORY_SECTIONS dict entry for `PodcastCategory.AI_UPDATES` around line 161.

- [ ] **Step 2: Replace the instruction**

Replace the current `"instruction"` value with:

```python
"instruction": (
    "Highlight 1-2 meaningful AI developments from the data: major model releases, "
    "funding rounds, regulatory moves, notable research, cyber threats. Focus on "
    "items with company-level or sector-level implications -- skip product press "
    "releases with no market angle. Reference tech prediction markets if present. "
    "Close this segment by naming one specific stock or sector that could be "
    "affected -- without telling the listener to trade it. Sam drives with enthusiasm; "
    "Alex asks 'does this actually move the market?' "
    "\n\n"
    "TANGENT EXPLORATION: S2 should open 1-2 tangents by asking 'but what about...' or "
    "'doesn't that mean...' questions that explore broader implications (e.g., 'what does "
    "this mean for power consumption and data centers?' or 'how does this reshape the "
    "competitive landscape?'). These should be genuine curiosity questions. S1 should "
    "recognize these openings and explore briefly with S2 for 1-2 exchanges before returning "
    "to the main narrative. Tangents should feel like organic discoveries, not scripted diversions."
),
```

- [ ] **Step 3: Verify syntax**

Check `src/script/prompts.py` compiles: `python -m py_compile src/script/prompts.py`

- [ ] **Step 4: Commit**

```bash
git add src/script/prompts.py
git commit -m "feat: add tangent exploration directive to AI_UPDATES instruction"
```

---

### Task 5: Verify FINANCE_MACRO and GEOPOLITICS Remain Unchanged

**Files:**
- Reference: `src/script/prompts.py:113-125` (FINANCE_MACRO) and `src/script/prompts.py:148-159` (GEOPOLITICS)

- [ ] **Step 1: Confirm FINANCE_MACRO unchanged**

Open `src/script/prompts.py` and verify the FINANCE_MACRO instruction does NOT contain any tangent directives. Should remain as narrative-driven without tangent exploration.

- [ ] **Step 2: Confirm GEOPOLITICS unchanged**

Verify the GEOPOLITICS instruction does NOT contain any tangent directives. Should remain as narrative-driven without tangent exploration.

- [ ] **Step 3: Verify overall syntax**

Run: `python -m py_compile src/script/prompts.py`

Expected: No errors

---

### Task 6: Test with Sample Script Generation

**Files:**
- Reference: `src/script/prompts.py` (modified prompts)
- No new files

- [ ] **Step 1: Create test script**

In project root, create `test_tangent_gen.py`:

```python
#!/usr/bin/env python3
"""Test that tangent exploration directives are present in generated prompts."""

from src.data.categories import PodcastCategory, DEFAULT_CATEGORIES
from src.script.prompts import build_system_prompt, CATEGORY_SECTIONS

print("=" * 80)
print("TESTING TANGENT EXPLORATION DIRECTIVES")
print("=" * 80)

# Build system prompt
system_prompt = build_system_prompt(DEFAULT_CATEGORIES)

# Check 1: TANGENT_EXPLORATION_PATTERNS section exists
if "TANGENT EXPLORATION PATTERNS" in system_prompt:
    print("\n✓ Found: 'TANGENT EXPLORATION PATTERNS' section in BASE_SYSTEM_PROMPT")
else:
    print("\n✗ MISSING: 'TANGENT EXPLORATION PATTERNS' section")

# Check 2: All 3 examples present
examples = [
    "SECONDARY EFFECTS TANGENT",
    "EXPECTATION IMPLICATIONS TANGENT",
    "ECOSYSTEM CONSEQUENCE TANGENT"
]

for example in examples:
    if example in system_prompt:
        print(f"✓ Found: '{example}'")
    else:
        print(f"✗ MISSING: '{example}'")

# Check 3: Tangent directives in question-discovery categories
print("\n[Category Instruction Checks]")

crypto_instruction = CATEGORY_SECTIONS[PodcastCategory.CRYPTO]["instruction"]
if "TANGENT EXPLORATION" in crypto_instruction:
    print("✓ CRYPTO instruction contains TANGENT EXPLORATION directive")
else:
    print("✗ CRYPTO instruction missing TANGENT EXPLORATION directive")

ai_instruction = CATEGORY_SECTIONS[PodcastCategory.AI_UPDATES]["instruction"]
if "TANGENT EXPLORATION" in ai_instruction:
    print("✓ AI_UPDATES instruction contains TANGENT EXPLORATION directive")
else:
    print("✗ AI_UPDATES instruction missing TANGENT EXPLORATION directive")

micro_instruction = CATEGORY_SECTIONS[PodcastCategory.FINANCE_MICRO]["instruction"]
if "TANGENT EXPLORATION" in micro_instruction:
    print("✓ FINANCE_MICRO instruction contains TANGENT EXPLORATION directive")
else:
    print("✗ FINANCE_MICRO instruction missing TANGENT EXPLORATION directive")

# Check 4: Narrative-driven categories unchanged
print("\n[Narrative-Driven Categories (Should NOT have tangent directives)]")

macro_instruction = CATEGORY_SECTIONS[PodcastCategory.FINANCE_MACRO]["instruction"]
if "TANGENT EXPLORATION" not in macro_instruction:
    print("✓ FINANCE_MACRO instruction correctly has NO tangent directive")
else:
    print("✗ FINANCE_MACRO should not have tangent directive")

geo_instruction = CATEGORY_SECTIONS[PodcastCategory.GEOPOLITICS]["instruction"]
if "TANGENT EXPLORATION" not in geo_instruction:
    print("✓ GEOPOLITICS instruction correctly has NO tangent directive")
else:
    print("✗ GEOPOLITICS should not have tangent directive")

# Check 5: Print sample of prompt
print("\n[Sample Output] First 1500 characters of generated prompt:")
print("-" * 80)
print(system_prompt[:1500])
print("...")
print("-" * 80)

print("\n" + "=" * 80)
print("✅ VERIFICATION COMPLETE")
print("=" * 80)
```

- [ ] **Step 2: Run test script**

```bash
python test_tangent_gen.py
```

Expected output:
```
================================================================================
TESTING TANGENT EXPLORATION DIRECTIVES
================================================================================

✓ Found: 'TANGENT EXPLORATION PATTERNS' section in BASE_SYSTEM_PROMPT
✓ Found: 'SECONDARY EFFECTS TANGENT'
✓ Found: 'EXPECTATION IMPLICATIONS TANGENT'
✓ Found: 'ECOSYSTEM CONSEQUENCE TANGENT'

[Category Instruction Checks]
✓ CRYPTO instruction contains TANGENT EXPLORATION directive
✓ AI_UPDATES instruction contains TANGENT EXPLORATION directive
✓ FINANCE_MICRO instruction contains TANGENT EXPLORATION directive

[Narrative-Driven Categories (Should NOT have tangent directives)]
✓ FINANCE_MACRO instruction correctly has NO tangent directive
✓ GEOPOLITICS instruction correctly has NO tangent directive

[Sample Output] First 1500 characters...
...
================================================================================
✅ VERIFICATION COMPLETE
================================================================================
```

- [ ] **Step 3: Clean up test script**

```bash
rm test_tangent_gen.py
```

- [ ] **Step 4: Commit**

```bash
git add src/script/prompts.py
git commit -m "test: verify tangent exploration directives in all categories"
```

---

## Plan Summary

This plan modifies **one file** (`src/script/prompts.py`) in 6 focused tasks:

1. **Add TANGENT_EXPLORATION_PATTERNS section** — Teaching LLM what tangent moments look like (3 concrete examples)
2. **Modify FINANCE_MICRO instruction** — Add tangent directive to question-discovery segment
3. **Modify CRYPTO instruction** — Add tangent directive to question-discovery segment
4. **Modify AI_UPDATES instruction** — Add tangent directive to question-discovery segment
5. **Verify unchanged categories** — Confirm FINANCE_MACRO and GEOPOLITICS have no tangent directives
6. **Test verification** — Quick test to confirm all directives are in place

Each task is self-contained and commits independently. The changes teach the LLM to generate organic exploratory dialogue moments in appropriate segments while keeping narrative-driven segments focused.
