# Market Pulse LinkedIn Video Design

**Date:** 2026-04-21  
**Project:** Market Pulse (Open Source AI Podcast Generator)  
**Medium:** 15–30 second Remotion video for LinkedIn  
**Goal:** Showcase the multi-agent orchestrator that powers Market Pulse and drive viewers to the GitHub repository

---

## Overview

Create a Claude-style polished video that reveals the technical innovation behind Market Pulse: a multi-agent system where one agent searches live market data, another generates the podcast script, and Kokoro TTS voices the result. The video leads with the product benefit (daily market podcast) before unveiling the tech stack.

---

## Video Structure

### Scene 1: Product Showcase (0–6 seconds)
**Objective:** Establish the end-user value proposition.

- Dashboard fades in from black
- Today's episode card is highlighted (clean, modern design matching the FastAPI + Tailwind interface)
- Hero text animates in with fade/slide: **"Your daily market podcast, ready each morning."**
- Audio player is the focal point
- Subtle zoom/pan to emphasize the listening experience
- Ambient background music (no voiceover in this section)

**Visual Details:**
- Dashboard screenshot or live component render from the FastAPI web app
- Use actual Tailwind color palette (accent color for highlights)
- Smooth 2–3 second animation for text entrance

---

### Scene 2: The Reveal – Agent Orchestration (6–15 seconds)
**Objective:** Demonstrate the multi-agent innovation.

- Dashboard gently blurs and fades as background
- Three animated agent nodes appear in the center (left to right):
  - **Data Agent** (left): 📊 icon, label "Search Live Data", animated lines representing data collection
  - **Generation Agent** (middle): 🧠 icon, label "Generate Script" (or "Gemini AI"), glow effect to indicate active processing
  - **Voice Agent** (right): 🎙️ icon, label "Kokoro TTS", waveform animation suggesting audio synthesis

- Animated arrows/flow lines connect the nodes left-to-right, showing data passage between agents
- Small text labels appear above each node
- Nodes maintain a clean, circular design with light outlines and accent-color glows
- Duration: 6–7 seconds for the agent visualization

**Visual Details:**
- Nodes are simple filled circles (~80px diameter) with icon centers
- Flow arrows animate with a "travel" effect (appear to move data through the pipeline)
- Color scheme: Use the primary accent color for active flows/glows, neutral grays for node outlines
- No voiceover; let the animation tell the story

---

### Scene 3: Result & Call-to-Action (15–20 seconds)
**Objective:** Circle back to the podcast, reinforce the brand, and drive to GitHub.

- Agent nodes dissolve/fade out
- Podcast player re-appears (or stays visible with enhanced emphasis)
- Full audio waveform animates as if currently playing
- Text appears in sequence:
  - **Line 1:** "Market Pulse"
  - **Line 2:** "Multi-Agent AI Podcast Generator"
  - **Line 3:** GitHub repository URL with "Star on GitHub" or "Open Source" badge

- Final frame holds for 1–2 seconds
- Optional: Subtle call-to-action voiceover (see Messaging section below)

**Visual Details:**
- Use clean typography (Inter or similar), large and legible
- Waveform animation: simple sine-wave or bar visualization, colored with the accent color
- GitHub URL appears with a faint background highlight or button-like styling

---

## Messaging & Voiceover

**Option A: Text-Only (Recommended for tight pacing)**
- No voiceover; let the visuals and music carry the narrative
- All information conveyed via on-screen text and animation

**Option B: Subtle Voiceover (Optional)**
*Script (read slowly and clearly):*  
"Market Pulse searches live market data, generates a podcast script, and voices it — all in minutes. Open source. Multi-agent. Ready to listen."

- Voiceover timing: Play throughout Scene 2 and into Scene 3
- Tone: Professional, calm, confident
- No background music if voiceover is used; use voiceover with subtle ambient sound

---

## Visual Style

**Inspiration:** Claude's advertisement videos — clean, minimalist, polished animations with professional pacing.

**Color Palette:**
- Primary accent: Market Pulse's existing Tailwind accent color (from the website)
- Neutrals: White, light gray, dark text (ensure high contrast for readability)
- Glow/highlight: Accent color with subtle opacity variations

**Typography:**
- Font: Inter or system sans-serif
- Sizes: Hero text ~48px, labels ~20px, body ~16px
- Weight: Mix of 400 (regular) and 600 (semibold) for hierarchy

**Animations:**
- Easing: Smooth cubic-bezier or ease-out for natural motion
- Transitions: Fade (200–400ms), slide (300–500ms), scale (subtle, 1–5% change)
- No jarring cuts; all scene changes should flow smoothly
- Music: Optional subtle ambient/electronic background track (~120–140 BPM)

---

## Remotion Technical Architecture

### Components & Structure
```
<MarketPulseVideo> (20 seconds, 30fps)
├── <DashboardScene /> (0–6 sec)
├── <AgentFlowScene /> (6–15 sec)
└── <ResultScene /> (15–20 sec)
```

### DashboardScene Component
- Props: `backgroundColor`, `accentColor`
- Renders: Dashboard screenshot/static image or live component snapshot
- Animations: Fade-in (0–1 sec), zoom-pan (1–5 sec), fade-out start (5–6 sec)

### AgentFlowScene Component
- Props: `accentColor`, `showVoiceover` (boolean)
- Renders: Three agent nodes with icons, animated flow lines, text labels
- Animations:
  - Nodes fade in sequentially (0.5 sec each, staggered)
  - Flow arrows animate (travel effect, 1–2 sec per arrow)
  - Nodes maintain subtle pulsing glow (looping)

### ResultScene Component
- Props: `accentColor`, `githubUrl`, `voiceoverPlaying` (boolean)
- Renders: Podcast player, waveform animation, text overlay, GitHub CTA
- Animations: Nodes dissolve (0.5 sec), player emphasis (zoom, 0.3 sec), text appears sequentially

### Assets Required
- Dashboard screenshot (from the FastAPI web app at `/dashboard`)
- SVG icons for agents (📊, 🧠, 🎙️) or custom circular icon designs
- Optional: Small brand logo or favicon for final frame
- Background music track (royalty-free, ~20–30 seconds)

### Output Specification
- **Format:** MP4, H.264 codec
- **Resolution:** 1920×1080 (1080p)
- **Aspect Ratio:** 16:9 (standard for LinkedIn)
- **Frame Rate:** 30 FPS
- **Duration:** 20 seconds
- **File Size:** ~10–20 MB (optimized for web)

---

## Timing & Pacing

| Scene | Duration | Key Action |
|-------|----------|-----------|
| Dashboard fade-in | 1 sec | Set context |
| Hero text animation | 2–3 sec | Establish value |
| Dashboard hold | 2 sec | Emphasis |
| Dashboard blur | 0.5 sec | Transition |
| Agent nodes appear | 1.5 sec | Reveal tech |
| Flow animation | 5–6 sec | Demonstrate orchestration |
| Nodes dissolve | 0.5 sec | Transition |
| Player emphasis | 1 sec | Return to product |
| Text overlay | 2 sec | Brand + messaging |
| Final frame hold | 1–2 sec | CTA exposure |
| **Total** | **20 seconds** | |

---

## Success Criteria

- ✅ Viewers understand what Market Pulse does (daily AI podcast)
- ✅ Viewers understand the technical innovation (multi-agent orchestration)
- ✅ Visual style matches Claude's advertisement aesthetic
- ✅ Video is optimized for LinkedIn (16:9, 20 sec, MP4)
- ✅ Clear CTA drives to GitHub repository
- ✅ All animations are smooth and professional (no jank)

---

## Notes

- The video prioritizes **clarity** and **pacing** over complexity. Every animation serves a purpose.
- Accessibility: Ensure all text has sufficient contrast and is readable at smaller sizes (LinkedIn on mobile).
- The agent visualization is intentionally abstract (nodes and flows) rather than realistic, maintaining the minimalist Claude-style aesthetic.
- Optional A/B test: Test both text-only and voiceover versions on LinkedIn to see which performs better.

