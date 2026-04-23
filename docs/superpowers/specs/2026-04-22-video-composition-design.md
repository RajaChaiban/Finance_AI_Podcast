# Video Composition Design: 20-Second Interactive Demo

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a 20-second video composition using Remotion that combines two screen recordings (Generate and Dashboard) with interactive UI sounds and podcast audio playback, allowing viewers to hear the actual generated podcast.

**Architecture:** Load two MP4 video files recorded from the Market Pulse website into Remotion's `<Video>` component, synchronize their playback with frame-based timing, add UI interaction sound effects during the first 10 seconds, and fade between videos with corresponding audio crossfade so the podcast audio becomes prominent in the second half.

**Tech Stack:** Remotion (`<Video>` component), TypeScript, FFmpeg (for audio extraction/creation), existing podcast audio files, UI sound effects (sourced/created).

---

## Video Composition Structure

### Timeline Overview

| Phase | Time | Duration | Video Content | Audio |
|-------|------|----------|---------------|-------|
| **Generate Workflow** | 0:00-0:10 | 10s | User selecting topics and clicking "Generate" | UI interaction sounds (clicks, loading tones) |
| **Fade Transition** | 0:09-0:11 | 2s | Opacity crossfade between videos | UI sounds fade out → Podcast audio fades in |
| **Podcast Playback** | 0:10-0:20 | 10s | Dashboard with podcast player displaying/playing | Real podcast audio (10 seconds of generated content) |
| **Total** | 0:00-0:20 | 20s | 2 MP4 files composed | Layered audio: UI → Podcast |

---

## Phase 1: Generate Video (0:00-0:10)

**Source:** `remotion-video/out/video/Generate — Market Pulse and 3 more pages - Personal - Microsoft​ Edge 2026-04-22 21-23-44.mp4`

**Duration in final video:** 10 seconds (may require trimming or speed adjustment if original is longer/shorter)

**Visual:** Screen recording showing the user/agent:
1. Selecting a podcast topic from the dashboard
2. Clicking "Start Generating" or similar button
3. Watching the generation process (loading indicators, status updates)
4. Waiting for the podcast to be generated

**Audio Layer:** UI Interaction Sounds
- **Soft click sounds** (100-150ms duration) when buttons/options are selected or hovered
  - Volume: -20dB (subtle, non-intrusive)
  - Frequency: High-pitched (3-5 kHz) for clarity
  - Example: Soft "tink" or "beep" sound
- **Processing/Loading ambient sound** (continuous, low volume) while generation is in progress
  - Volume: -25dB (very subtle background)
  - Tone: Subtle electrical hum, processing noise
  - Duration: ~4-6 seconds (covers the "waiting" phase)
- **Success/Completion sound** (100-200ms) when generation completes
  - Volume: -20dB
  - Tone: Satisfying "chime" or "ding" sound
  - Timing: At the moment generation finishes

**Style Reference:** Claude Code interface uses soft, satisfying UI feedback sounds that don't distract but provide confirmation. Apply similar aesthetic.

---

## Transition: Fade Crossfade (0:09-0:11)

**Visual Transition:**
- Start: Generate video at 100% opacity, Dashboard video at 0% opacity
- End: Generate video at 0% opacity, Dashboard video at 100% opacity
- Duration: 2 seconds (frames 270-330 at 30fps)
- Easing: Linear or ease-in-out for smooth cross-fade

**Audio Transition:**
- UI sounds (from Generate phase) fade out: 100% → 0% volume (1 second)
- Podcast audio (from Dashboard phase) fades in: 0% → 100% volume (1 second)
- Overlap ensures continuous audio without silence

**Timing:** Transition starts at frame 270 (0:09s) so it completes by frame 300 (0:10s) when Dashboard video takes over.

---

## Phase 2: Dashboard Video (0:10-0:20)

**Source:** `remotion-video/out/video/Dashboard — Market Pulse and 3 more pages - Personal - Microsoft​ Edge 2026-04-22 21-23-05.mp4`

**Duration in final video:** 10 seconds

**Visual:** Screen recording showing:
1. Dashboard/Library view with the generated podcast displayed
2. User clicking the play button on the podcast card
3. Podcast player showing playback controls (play, progress bar, timer)
4. Visual feedback indicating podcast is playing (waveform animation, elapsed time, etc.)

**Audio Layer:** Podcast Audio Playback
- **Source:** Real generated podcast audio (from the Dashboard video or separate file)
- **Duration:** 10 seconds of actual podcast content
- **Volume:** 0dB (primary audio, should be clear and centered)
- **Content:** Listeners hear the actual AI-generated podcast to understand quality and format
- **Start time:** At frame 300 (0:10s) aligned with Dashboard video start

---

## Audio Mixing Strategy

### Audio Tracks Layering

**Track 1: UI Sounds (0:00-0:10)**
- Baseline: -20dB to -25dB (subtle background)
- Peaks (clicks, completion): -15dB to -18dB
- Fade out: 0:09-0:10 (linear fade to silence)

**Track 2: Podcast Audio (0:10-0:20)**
- Baseline: -3dB to 0dB (clear, audible)
- Fade in: 0:09-0:10 (linear fade from silence)
- Maintained at consistent level throughout playback

### Master Output
- Stereo mix of UI sounds + Podcast audio
- Target loudness: -14dB LUFS (YouTube/streaming standard)
- No compression or limiting applied (preserve natural audio quality)
- Final format: AAC stereo at 48kHz (matches Remotion audio standards)

---

## Implementation: Remotion Video Composition

### Component Structure

**Main Composition:** `VideoComposition`
- Width: 1920px, Height: 1080px
- Duration: 600 frames (20 seconds at 30fps)
- FPS: 30

**Video Layer 1 (Generate):**
```
<Video src={generateVideoPath} startFrom={0} endAt={300} opacity={generateOpacity} />
```
- Plays frames 0-300 (first 10 seconds)
- Opacity animated: frame 0-270 = 1.0, frame 270-300 = 1.0→0.0 (fade out)

**Video Layer 2 (Dashboard):**
```
<Video src={dashboardVideoPath} startFrom={0} opacity={dashboardOpacity} />
```
- Starts at frame 300 (0:10s into composition)
- Opacity animated: frame 270-300 = 0.0→1.0 (fade in), frame 300-600 = 1.0

**Audio Track 1 (UI Sounds):**
```
<Audio src={uiSoundsAudioPath} volume={uiSoundsVolume} startFrom={0} endAt={300} />
```
- Plays 0:00-0:10
- Volume fades: 100% → 0% during frames 270-300

**Audio Track 2 (Podcast):**
```
<Audio src={podcastAudioPath} volume={podcastVolume} startFrom={0} />
```
- Starts at frame 300 (0:10s)
- Volume fades: 0% → 100% during frames 270-300

### Frame Timing

| Phase | Frame Range | Time | Action |
|-------|-------------|------|--------|
| Generate | 0-300 | 0:00-0:10 | Video 1 at 100% opacity, Audio 1 at -20dB |
| Transition | 270-330 | 0:09-0:11 | Opacity/Volume crossfade |
| Dashboard | 300-600 | 0:10-0:20 | Video 2 at 100% opacity, Audio 2 at 0dB |

---

## File Assets Required

**Input Files:**
- `remotion-video/out/video/Generate — Market Pulse and 3 more pages - Personal - Microsoft​ Edge 2026-04-22 21-23-44.mp4` (screen recording)
- `remotion-video/out/video/Dashboard — Market Pulse and 3 more pages - Personal - Microsoft​ Edge 2026-04-22 21-23-05.mp4` (screen recording)
- Podcast audio file: 10 seconds of generated content (extract from Dashboard video or use separate file)

**Audio to Create/Source:**
- `remotion-video/public/ui-sounds.mp3` — Composite audio with clicking, loading, and completion sounds (10 seconds)
  - Soft click sounds at interaction moments
  - Loading ambient tone during processing
  - Completion chime when done
  - Fade to silence in final second

**Output File:**
- `remotion-video/out/video-composition.mp4` (20 seconds, 1920×1080, H.264, AAC audio)

---

## Success Criteria

✅ Video duration: 20 seconds (±0.5 seconds tolerance for render overhead)
✅ Resolution: 1920×1080 at 30fps
✅ Generate video plays first 10 seconds with UI sounds
✅ Smooth fade transition between videos and audio tracks
✅ Dashboard video plays second 10 seconds with clear podcast audio
✅ Viewers can hear actual generated podcast (quality/content demonstration)
✅ No audio dropouts or glitches during transition
✅ Audio levels balanced (UI subtle, podcast clear)
✅ File size: < 5MB (ready for social sharing)

---

## Testing & Validation

- Render video locally and preview at full resolution
- Check audio sync: UI sounds align with visual interactions, podcast audio aligns with playback visualization
- Spot-check fade transition: Smooth opacity and audio volume curves
- Verify duration: ffprobe shows 20.0 seconds
- Mobile preview: Confirm text/UI readable at small size, audio plays correctly
- Sound balance: UI sounds don't overpower, podcast audio is clear

---

## Notes for Implementation

- Video file names contain special characters (spaces, em-dash); ensure proper escaping in Remotion imports
- If Generate video duration differs from 10 seconds, may need speed adjustment (Remotion `playbackRate` prop) or trimming (FFmpeg pre-processing)
- Podcast audio may need extraction from Dashboard video using FFmpeg before integrating into Remotion composition
- Test cross-fade timing carefully—too fast looks jarring, too slow loses momentum
