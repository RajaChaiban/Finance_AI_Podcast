# Interactive Platform Demo Video Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a 30-second Remotion video demonstrating Market Pulse's interactive user flow: agent-driven podcast generation with configuration selection, library browsing, and playback, culminating in a premium power-down closing animation.

**Architecture:** The video follows a three-act structure: website navigation with simulated agent interactions (0-20s), brand introduction woven throughout, and a dramatic power-down fade with logo reveal (20-30s). All UI interactions are rendered as flat modern SVG animations with smooth easing, eliminating the need for screen recordings. Audio pairs minimal voiceover callouts with background music to guide the viewer through the flow.

**Tech Stack:** Remotion (React-based video composition), TypeScript, SVG for UI components, Easing animations, Audio component for music + voiceover mixing.

---

## Scene Structure

### Timeline Overview

| Time | Duration | Content |
|------|----------|---------|
| 0-3s | 3s | Dashboard intro, title appears |
| 3-7s | 4s | Agent selects "Start Generating" |
| 7-13s | 6s | Configuration panel: topic, timeframe, style selection |
| 13-17s | 4s | Transition to Library, cards load |
| 17-20s | 3s | Top podcast card enlarges, play button activates, waveform animates |
| 20-24s | 4s | Screen darkens (power-down begins) |
| 24-30s | 6s | Logo + tagline fade in as screen fades to black |

### Section 1: Dashboard Intro (0-3s)

**Elements:**
- Fade in dashboard background (similar to previous 30s video)
- "Market Pulse" title text fades in at center, positioned above interaction area
- Dark overlay establishes visual hierarchy

**Animation:**
- Dashboard opacity: interpolate from 0 to 1 over 30 frames with cubic easing
- Title opacity: same easing, staggered 10 frames after dashboard

---

### Section 2: Start Generating Interaction (3-7s)

**Elements:**
- Large button labeled "Start Generating" appears on dashboard
- Button has orange accent background (#FF6B35), subtle border
- Visual indicator (animated arrow or circle) "moves toward" button to show agent action
- Button responds with glow effect and state change when "clicked" (no actual click detection needed)

**Animation:**
- Button slides in from left: x position interpolates from -200 to final position over 20 frames
- Glow effect: border opacity pulses 0.3 → 0.8 → 0.3 as agent selects
- Button slightly scales 1.0 → 1.05 on selection
- Cursor element follows a smooth path toward button (use quadratic easing)

**Audio Cue:** Subtle "click" sound effect + voiceover: "Starting generation..."

---

### Section 3: Configuration Selection (7-13s)

**Elements:**
- Config panel slides in from right containing three selectors:
  - **Topic:** Dropdown showing "Markets", "Tech", "Economics", "Crypto"
  - **Time Frame:** Selector showing "Daily", "Weekly", "Monthly"
  - **Style:** Selector showing "Formal", "Casual", "Mixed"
- Each selector is a card-like component with rounded corners, light background
- Agent "selects" one option from each category with visual highlight

**Animation:**
- Panel slides in: x position from +300 to final position over 25 frames
- Each selector card fades in staggered (100ms apart)
- When agent selects option: card background highlights briefly, text glows slightly
- Selection ripple effect expands from click point then fades

**Audio Cue:** Voiceover: "Selecting configuration..." with light background music

**Content:**
- Config options use realistic Market Pulse categories
- Agent selections: Markets, Daily, Formal (or similar logical combo)

---

### Section 4: Library Navigation & Playback (13-20s)

**Sequence A: Transition to Library (13-17s)**
- Config panel slides out to left
- Library view fades in showing grid of podcast cards
- Cards stagger-animate into view (each 80ms offset)
- Each card shows: thumbnail/icon, title, date, duration

**Sequence B: Top Podcast Selection & Playback (17-20s)**
- Top card in grid enlarges and centers
- Play button animates into center of card (scales 0 → 1)
- Waveform bars animate upward beneath the play button (representing "now playing" state)
- Card remains at center with visual emphasis

**Animation Details:**
- Library fade-in: opacity 0 → 1 over 20 frames
- Card stagger: each card x-position from -150, animates to grid position with delay
- Top card enlargement: width/height scale 1.0 → 1.3, centered on screen
- Play button pulse: scales 1.0 → 1.2 → 1.0 continuously (loop) to indicate readiness
- Waveform bars: heights animate as if podcast is playing (synchronized across bars)

**Audio Cue:** Music transitions to include subtle upbeat element + voiceover: "Playing top episode..."

**Content Detail:**
- Top podcast: realistic title (e.g., "Market Pulse Daily: Fed Decision Impact"), 
- Duration displayed (e.g., "12:34"), date (e.g., "Today")
- Thumbnail uses icon/gradient (not a full image, for simplicity)

---

### Section 5: Power-Down Fade & Branding (20-30s)

**Sequence:**
- Black overlay gradually increases opacity from 0% to 70% over 4 seconds (frames 20-24)
- Podcast card and UI elements darken along with screen
- At frame 24, logo animation begins
- Market Pulse logo fades in and scales to center (0.8 → 1.0 scale)
- Tagline "Multi-Agent AI Podcast Generator" fades in below logo
- Final frame (28-30s) holds logo + tagline on dark background

**Animation Details:**
- Dark overlay opacity: interpolate(frame, [600, 720], [0, 0.7])
- Logo fade-in: interpolate(frame, [720, 780], [0, 1])
- Logo scale: interpolate(frame, [720, 780], [0.8, 1.0])
- Tagline fade-in: interpolate(frame, [750, 810], [0, 1]) (staggered 30 frames after logo)
- Hold duration: frames 840-900 (last 2 seconds)

**Visual Polish:**
- Logo: simplified text logo "Market Pulse" in orange (#FF6B35) and white, or use existing SVG logo if available (no complex branding required, simplicity preferred)
- Tagline: sans-serif font (Inter, system-ui fallback) in white, 40-60% size of logo text
- Both centered on dark background with proper spacing
- No jarring transitions—all easing uses cubic out

**Audio Cue:** Subtle "power-down" tone or ambient sound, then silence. Optional: very subtle voiceover "Market Pulse" as logo appears.

---

## Audio Strategy

**Track 1: Background Music**
- Upbeat but professional instrumental (duration: full 30s)
- Fades in gently at 0-3s, plays throughout
- Smooth fade-out from 24-30s as screen darkens

**Track 2: Voiceover**
- Minimal, strategic callouts at key moments
- No script jargon—conversational and clear
- Callouts:
  - 3-4s: "Starting generation..."
  - 8-9s: "Selecting configuration..."
  - 15-16s: "Playing top episode..."
  - Optional: 26-27s: "Market Pulse" (whispered or spoken softly)

**Track 3: Sound Effects**
- Subtle click/confirm sounds on agent interactions (low volume, ~-20dB)
- Soft transition whoosh when Library appears
- Optional soft "power-down" tone at 20-24s (very subtle, ambient)

**Mixing:**
- Music: primary level throughout, ducks slightly under voiceover
- Voiceover: clear and audible, sits above music
- Sound effects: accent layer, doesn't overpower
- Final 2 seconds (power-down): fade all audio to silence

---

## Component Breakdown

**Components to Create/Modify:**

1. **DashboardBackground** — Fades in, serves as stage for all interactions
2. **StartGeneratingButton** — Slides in, glows on selection, scales on click
3. **ConfigurationPanel** — Slides in from right, contains three selector cards
4. **SelectorCard** — Reusable card for topic/time/style selection, highlights on select
5. **LibraryGrid** — Grid of podcast cards, fades in with stagger animation
6. **PodcastCard** — Individual card with title, date, duration, icon
7. **ExpandedPodcastCard** — Enlarged, centered version of podcast card with play button
8. **PlayButton** — Centered on card, pulses to indicate readiness
9. **Waveform** — Reuse existing Waveform component from previous video, animates with progress=1 to show active playback state
10. **PowerDownOverlay** — Black overlay that increases opacity over time
11. **LogoAndTagline** — Market Pulse branding display, fades in and scales

**Shared Utilities:**
- Animation easing constants (cubic out, ease-in-out)
- Color palette (use existing COLORS object)
- Timing constants (frame offsets for each scene)

---

## Data & Content

**Static Content:**
- Dashboard screenshot or styled background
- Market Pulse logo (SVG or imported image)
- Podcast icons/thumbnails (simplified gradients, no full images)

**Dynamic Content (Configurable):**
- Topic options: ["Markets", "Tech", "Economics", "Crypto"]
- Time frame options: ["Daily", "Weekly", "Monthly"]
- Style options: ["Formal", "Casual", "Mixed"]
- Top podcast card: realistic title, duration, date
- Music file: background instrumental (30s or longer, looped/trimmed)
- Voiceover: MP3 or composed audio track with callouts

---

## Success Criteria

✅ Video renders at 1920x1080, 30fps, 30 seconds total
✅ All animations use smooth easing (cubic out preferred)
✅ Agent interactions feel responsive and natural
✅ Logo reveal at end is visually striking and on-brand
✅ Audio (music + voiceover) guides the viewer through the flow
✅ No jank, stuttering, or frame drops
✅ Reads well at small sizes (LinkedIn preview, mobile)

---

## Testing & Validation

- Render video locally, preview at full resolution
- Test audio sync: verify voiceovers align with visual moments
- Spot-check frame counts: ensure no off-by-one timing errors
- Mobile preview: confirm text reads and animations feel smooth on phone-sized viewport
- Sound balance: voiceover clearly audible but doesn't drown out music
