# Tangent Exploration Prompt Improvements Design

**Date:** 2026-04-23  
**Context:** Rigorous testing revealed generated scripts lack natural tangent exploration and exploratory back-and-forth. This design adds prompt patterns and directives to enable organic tangent moments.

---

## Problem Statement

Generated podcast scripts show:
- ✅ Strong discovery questions (7 per script)
- ✅ Natural dialogue flow
- ❌ **Zero tangent exploration** — hosts never diverge from the main narrative thread to explore a related angle together
- ❌ **Structured Q&A format** — S1 delivers info → S2 asks → S1 answers → move to next topic (predictable, scripted)

Example of what's missing:
```
CURRENT (clean but linear):
[S1] "Bitcoin rallied on ETF inflows."
[S2] "Any specific catalyst for the inflow?"
[S1] "Institutions rotating in after the approval."
[S2] "Got it. Now let's talk about Ethereum..."

DESIRED (with tangent exploration):
[S1] "Bitcoin rallied on ETF inflows."
[S2] "Wait, but doesn't that mean institutions are rotating OUT of something?"
[S1] "Oh, good point — yeah, we're seeing Ethereum ETF outflows..."
[S2] "So they're consolidating into Bitcoin specifically?"
[S1] "Exactly. Which shapes the altcoin space."
[S2] "Right, and if Ethereum weakens..."
[S1] "...dominance shifts. That's the macro signal for the next segment."
```

The desired version shows S2 opening a tangent ("rotation OUT of something?"), both hosts exploring it for 2-3 exchanges, then S1 naturally closing and bridging to the next topic.

---

## Design

### 1. New Section: TANGENT EXPLORATION PATTERNS

**What:** A new section added to BASE_SYSTEM_PROMPT (after AUTHENTIC_DISCOVERY_PATTERNS, before EMOTION_TAGS) that teaches the LLM what exploratory tangent moments sound like.

**Purpose:** Provide concrete examples so the LLM understands:
- How to recognize when an idea has an exploratory angle
- How both hosts engage together in exploring it
- How to return to the main narrative naturally

**Content: 3 Examples**

Each example follows this structure:
- S1 delivers a market fact or analysis
- S2 asks a "but what about..." question that opens a *different angle* on the same topic
- S1 recognizes the tangent opening and explores it with S2 (1-2 back-and-forth exchanges)
- S1 naturally closes the tangent and returns to the main thread or bridges to next segment

**Example 1: Secondary Effects Tangent**
```
[S1] "Bitcoin rallied on ETF inflow news."
[S2] "Wait, but doesn't that mean institutions are rotating OUT of something else?"
[S1] "Oh, good point — yeah, we're seeing outflows from Ethereum ETFs..."
[S2] "So they're consolidating into Bitcoin specifically, not just buying crypto broadly?"
[S1] "Exactly. Which is why we're watching how this shapes the altcoin space."
[S2] "Right, so if Ethereum weakens relative to Bitcoin..."
[S1] "...dominance shifts. And that's the macro signal for the next segment."

(S2's "doesn't that mean institutions are rotating OUT?" opens a tangent about *what's being sold*, 
not just *what's being bought*. S1 explores it. Both dig deeper briefly, then S1 naturally closes 
and bridges to the next topic.)
```

**Example 2: Stakeholder Implication Tangent**
```
[S1] "Fed held rates steady, but signaled more hikes ahead."
[S2] "Hmm, but if the market was already pricing in hikes, doesn't that mean they're signaling even MORE than expected?"
[S1] "Exactly — the forward guidance was hawkish. Bond traders panicked."
[S2] "So banks benefit from higher rates, but tech gets hit?"
[S1] "Right. That's why we saw XLK rally and XLT selloff."
[S2] "Which ties into what we saw in crypto..."
[S1] "Yep, exactly."

(S2's tangent: "even MORE than expected?" — opening a discussion about *expectation management*, 
not just the rate decision itself. Quick exploration, then natural flow to next segment.)
```

**Example 3: Ecosystem Consequence Tangent**
```
[S1] "AI companies are committing massive infrastructure spending."
[S2] "But doesn't that drive up power demand and semiconductor scarcity?"
[S1] "Good catch — yeah, NVIDIA and the power grid companies are getting a boost."
[S2] "So geopolitical tensions around chip manufacturing become even MORE relevant?"
[S1] "Exactly. Which is why the Taiwan situation is so market-sensitive right now."
[S2] "Got it. So that segues into geopolitics..."

(S2's tangent: "power demand and semiconductor scarcity" — exploring the *upstream consequences* 
of the AI capex boom, not just the direct AI company impact.)
```

**Pattern Recognition:** Each tangent:
- Starts with S2 asking "but what about..." or "doesn't that mean..." (genuine curiosity, not rhetorical)
- Represents a *sideways* exploration (different angle on the same topic), not a topic jump
- Gets 1-3 back-and-forth exchanges (brief, not a subplot)
- Closes naturally with S1 either resolving it or bridging to the next segment

---

### 2. Modify Category Instructions for Question-Discovery Segments

**Which categories get the tangent directive:**
- `FINANCE_MICRO` (question-discovery style)
- `CRYPTO` (question-discovery style)
- `AI_UPDATES` (question-discovery style)

**Which categories do NOT get tangent directives:**
- `FINANCE_MACRO` (narrative-driven — needs focus and authority)
- `GEOPOLITICS` (narrative-driven — complex stories need linearity)

**Directive to add to each question-discovery category instruction:**

```
S2 should open 1-2 tangents by asking "but what about..." or "doesn't that mean..." questions 
that naturally extend the topic sideways (e.g., asking about secondary effects, stakeholder rotation, 
ecosystem implications). These should be genuine curiosity questions, not rhetorical. S1 should 
recognize these openings and explore briefly with S2 for 1-2 exchanges before naturally returning 
to the main narrative thread or bridging to the next segment. Tangents should feel organic 
discoveries, not scripted diversions.
```

**Example of modified CRYPTO instruction:**

```
"Cover BTC and ETH price action from the crypto quotes and explain the driver -- 
regulatory news, ETF flows, macro correlation, whale activity. If crypto ETF 
flows (IBIT, FBTC, GBTC) are in the data, mention them only when there's a 
notable inflow/outflow story. Connect crypto moves to the broader risk appetite 
from the macro segment: is crypto tracking equities or decoupling? Skip altcoin 
noise unless something is truly notable. 

S2 should open 1-2 tangents by asking 'but what about...' or 'doesn't that mean...' 
questions that explore secondary effects (e.g., 'if institutions rotate into Bitcoin, 
what are they rotating out of?'). S1 should recognize these openings and explore 
briefly with S2 for 1-2 exchanges before returning to the main narrative. Alex 
provides skeptical grounding: 'is that actually material?' Sam drives the narrative 
with curiosity."
```

---

### 3. How the Pieces Work Together

| Component | Role | Impact |
|-----------|------|--------|
| **TANGENT EXPLORATION PATTERNS** section | Teaches the LLM what tangent moments sound like | Provides concrete examples so the model recognizes the pattern |
| **Question-discovery category directives** | Tell S2 when to open tangents, S1 when to engage | Activates the pattern at the right moments |
| **Narrative-driven categories untouched** | Keep MACRO, GEO focused and authoritative | Prevents tangents in segments that need structure |
| **Result** | Organic exploratory moments, confined to the right segments | Scripts feel like genuine discussion, not scripted Q&A |

---

## Success Criteria

After implementation, generated scripts should show:

1. ✓ Question-discovery segments (CRYPTO, AI_UPDATES, FINANCE_MICRO) contain **1-2 tangent moments per segment**
2. ✓ Each tangent starts with S2's "but what about..." or "doesn't that mean..." question (genuine curiosity)
3. ✓ Both hosts engage for 1-2 back-and-forth exchanges exploring the tangent
4. ✓ Tangent closes naturally with S1 returning to main narrative or bridging to next topic
5. ✓ Narrative-driven segments (MACRO, GEO) remain focused, no tangents
6. ✓ Tangents feel like organic discoveries, not mechanical insertions

---

## Implementation Scope

**Files to modify:** `src/script/prompts.py`

**Changes:**
- Add TANGENT EXPLORATION PATTERNS section to BASE_SYSTEM_PROMPT (with 3 detailed examples)
- Modify FINANCE_MICRO instruction to include tangent directive
- Modify CRYPTO instruction to include tangent directive
- Modify AI_UPDATES instruction to include tangent directive
- Leave FINANCE_MACRO and GEOPOLITICS instructions unchanged (narrative-driven, no tangents)

**No new files, no API changes, no data changes.**

---

## Testing & Validation

After implementation:
1. Generate 2-3 sample scripts using updated prompts
2. Check CRYPTO and AI_UPDATES segments for 1-2 tangent moments per segment
3. Verify tangents follow the pattern (S2 opening → both exploring → S1 closing)
4. Verify narrative segments stay focused
5. Compare to baseline (2026-04-22 script) to show improvement

---

## Notes & Open Questions

- **Tangent frequency:** Directive says "1-2 tangents per segment". Could adjust if scripts show too many or too few.
- **Tangent length:** Current design targets "1-2 exchanges". May need iteration if tangents feel too brief or too long.
- **Naturalness:** Success depends on LLM recognizing when tangent openings are appropriate. May need refinement if tangents feel forced.
- **Future work:** After tangent exploration is solid, next iteration should enforce topic-specific leadership (S2 leading CRYPTO/AI fully, not just opening tangents).
