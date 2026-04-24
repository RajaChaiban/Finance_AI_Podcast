# Conversational Podcast Script Design
**Date:** 2026-04-23  
**Objective:** Transform Market Pulse from a formal briefing to an authentic discussion between two hosts discovering market stories together.

---

## Overview

Currently, the podcast scripts follow a briefing format where one host delivers information and the other reacts passively. The goal is to shift to a **discussion format** where:
- Hosts ask each other genuine questions ("Did you see the AI stock rise?")
- One host naturally leads each segment (60/40 split), varying by topic
- Dialogue includes natural interruptions, tangents, and backchanneling
- Listeners feel like they're overhearing two professionals discovering stories together, not being lectured

---

## Current State

**strengths:**
- BASE_SYSTEM_PROMPT already includes dialogue examples and warns against monologues
- DIALOGUE STYLE section shows good vs. bad examples
- EMOTION_TAGS add prosody guidance for authenticity

**gaps:**
- Dialogue examples are still somewhat formal ("Oil spiked 3%. Saudi supply cut.")
- No guidance on topic-specific leadership variation
- No examples of natural interruptions or genuine discovery
- Instructions assume balanced 50/50 speaking time, not 60/40 with clear leaders

---

## Design

### 1. CATEGORY_SECTIONS Enhancement

Add two new fields to each category dict:

```python
CATEGORY_SECTIONS = {
    PodcastCategory.FINANCE_MACRO: {
        "title": "Macro Overview",
        "leader": "alex",  # NEW: who naturally leads this segment
        "dialogue_style": "narrative-driven",  # NEW: how dialogue should flow
        "instruction": "..."  # existing
    },
    # ... etc
}
```

**Leader assignments (reasoning below):**
- `FINANCE_MACRO`: **Alex** — macro stories need authoritative anchoring; Sam questions the implications
- `FINANCE_MICRO`: **Alex** — equity movers require confident analysis; Sam digs into "why"
- `CRYPTO`: **Sam** — more naturally tech-curious; Alex provides skeptical grounding
- `GEOPOLITICS`: **Alex** — complex stories need a steady lead; Sam connects to markets
- `AI_UPDATES`: **Sam** — tech enthusiasm drives narrative; Alex asks about market impact

**Dialogue styles:**
- `"narrative-driven"` — host tells a story; other host asks follow-ups
- `"question-discovery"` — hosts ask each other "what does this mean?"
- `"tangent-friendly"` — one host brings an idea; other explores it

---

### 2. BASE_SYSTEM_PROMPT Expansion

**Current "DIALOGUE STYLE" section (lines 46–51):** Keep existing good/bad examples.

**Add new section "AUTHENTIC DISCOVERY PATTERNS"** after DIALOGUE STYLE:

```
AUTHENTIC DISCOVERY PATTERNS
Hosts should sound like they're figuring things out together, not executing a plan.
Here's what authentic discovery sounds like:

- INTERRUPTION: [S1] "Oil jumped 3%." [S2] "Wait, why though?" [S1] "Saudi cut supply." 
  (Sam asks genuine curiosity; Alex answers; Sam doesn't wait for Alex to finish a monologue.)

- TANGENT: [S1] "Fed held rates steady." [S2] "Hmm, but that usually means..." [S1] "Exactly, 
  and that's why tech got hit." (Sam brings a connection; Alex builds on it; feels natural.)

- BACKCHANNELING: [S1] "...so energy prices are spiking." [S2] "Right, which ripples to..." 
  (Sam acknowledges and adds; short lines, rapid exchange.)

- NATURAL DOUBT: [S1] "This could push gold higher." [S2] "Or does it push it lower?" [S1] 
  "Good point, that's what we're watching." (Sam questions; Alex admits uncertainty; feels real.)

Do NOT sound like:
- One host explaining while the other listens passively
- Pre-scripted call-and-response ("Listeners, here's why..." "That's right, because...")
- Perfectly balanced sentences; let one host dominate a beat if the story calls for it
```

**Update "DIALOGUE STYLE -- EXAMPLES" section (lines 46–51):** Add 2–3 more examples showing:
- Natural interruptions ("Wait, so...")
- Tangent-friendly moments
- One host asking "what does this actually mean?" as if discovering it with the listener
- More use of "but", "hold on", "right so", "wait" to signal real conversation

**Strengthen "USE NATURAL WORD FILLERS LIBERALLY" section (lines 54–65):**
- Add more examples of fillers that signal genuine surprise or discovery
- Clarify that fillers should feel like thinking-aloud, not forced

---

### 3. build_system_prompt() Logic Update

Current flow: `build_system_prompt()` → constructs prompt → returns string

**New flow:**
1. Build category list
2. For each category, fetch `leader` and `dialogue_style`
3. When injecting category instructions into the prompt, add leader context

Example injection:
```
f"{i}. {section['title']} (led by {section['leader']}, {section['dialogue_style']}): 
  {section['instruction']}"
```

This tells the LLM:
- Who drives this segment
- What the tone should be
- The category's analysis goal (existing instruction)

---

### 4. Category Instruction Refinement

Update `CATEGORY_SECTIONS[...]["instruction"]` for each category to emphasize dialogue:

- **FINANCE_MACRO:** Alex anchors; add "Sam should ask questions that reveal what listeners need to know"
- **FINANCE_MICRO:** Alex leads with movers; add "Sam asks 'but why did it move?' in real time"
- **CRYPTO:** Sam curious; add "Alex provides skeptical grounding: 'is that actually material?'"
- **GEOPOLITICS:** Alex anchors; add "Sam connects to markets: 'so what does that mean for commodity prices?'"
- **AI_UPDATES:** Sam enthusiastic; add "Alex asks 'does this actually move the market?'"

---

## Success Criteria

Spec passes when updated prompts generate scripts where:
1. ✓ One host clearly leads each segment (60/40 split)
2. ✓ Leaders vary by topic (Sam leads AI; Alex leads Macro, etc.)
3. ✓ Dialogue includes natural interruptions, tangents, and genuine questions
4. ✓ Hosts sound like they're discovering stories, not delivering prepared remarks
5. ✓ Scripts feel like two professionals talking over coffee, not a newscast

---

## Implementation Scope

**Files to modify:** `src/script/prompts.py`

**Changes:**
- CATEGORY_SECTIONS: Add `leader` and `dialogue_style` to each entry
- BASE_SYSTEM_PROMPT: Add "AUTHENTIC DISCOVERY PATTERNS" section + enhance dialogue examples
- build_system_prompt(): Inject leader/dialogue_style into category instructions when building prompt

**No new files, no data changes, no API changes.**

---

## Rollout & Testing

1. Update prompts.py per design
2. Generate 2-3 sample scripts with updated prompts
3. Listen/read for: interruptions, tangents, genuine questions, topic-specific leaders
4. Iterate on wording if needed (e.g., if LLM isn't picking up dialogue cues)
5. Commit to `fastapi-htmx-rewrite` branch

---

## Open Questions / Risks

- **Risk:** Richer dialogue cues might make prompts longer or confuse the LLM. **Mitigation:** Start with incremental additions; iterate if needed.
- **Risk:** "Authentic discovery" might push toward too much tangent. **Mitigation:** Category instructions keep focus on market relevance.
- **Open:** Should "leader" vary within a segment? (e.g., Alex starts, Sam takes over?) **Decision:** Keep it simple; one leader per segment for now.

