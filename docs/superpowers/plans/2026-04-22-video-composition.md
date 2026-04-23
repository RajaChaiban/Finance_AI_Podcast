# Video Composition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a 20-second Remotion video that composes two screen recordings (Generate and Dashboard) with UI interaction sounds and podcast audio, fading between them smoothly.

**Architecture:** Create a VideoCompositionScene component that loads two MP4 files using Remotion's `<Video>` component, manages opacity/volume animations for a fade crossfade transition at the 10-second mark, and layers UI sound effects (first 10s) with podcast audio (last 10s) for a seamless audio transition.

**Tech Stack:** Remotion (`<Video>` component), TypeScript, FFmpeg (audio extraction), existing MP4 recordings, audio files.

---

## Task 1: Create UI Sounds Audio File

**Files:**
- Create: `remotion-video/public/ui-sounds.mp3`

- [ ] **Step 1: Create UI sounds composition**

The ui-sounds.mp3 file should contain three layered elements over 10 seconds:
- Soft click sounds (0:02, 0:04, 0:06, 0:08) - 100ms duration each, -20dB volume
- Loading/processing tone (0:03-0:08) - continuous low ambient, -25dB volume
- Completion chime (0:09) - 100ms duration, -20dB volume
- Fade to silence (0:09-0:10) - linear fade from -20dB to -∞dB

Options to create this:
1. **If you have Audacity/GarageBand:** Create a new project, add silence (10s), then add the sound effects above
2. **If you have CLI tools:** Use ffmpeg/sox to generate tones and mix
3. **If using online editor:** Use a web-based audio editor (e.g., Audiotool, Murf) to create and export

Expected output: `ui-sounds.mp3` (~100-300KB, stereo, 48kHz sample rate to match Remotion)

- [ ] **Step 2: Verify audio file**

Check file properties:
```bash
ffprobe -show_format -show_streams remotion-video/public/ui-sounds.mp3
```

Expected:
- Duration: ~10 seconds
- Sample rate: 48000 Hz (or compatible)
- Codec: AAC or MP3
- Channels: Stereo or Mono

- [ ] **Step 3: Add audio file to git**

```bash
git add remotion-video/public/ui-sounds.mp3
git commit -m "audio: add UI interaction sounds for video composition"
```

---

## Task 2: Create VideoCompositionScene Component

**Files:**
- Create: `remotion-video/src/scenes/VideoCompositionScene.tsx`

- [ ] **Step 1: Create VideoCompositionScene component with video composition**

```tsx
import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { Video, Audio } from 'remotion';

interface VideoCompositionSceneProps {
  width: number;
  height: number;
}

export const VideoCompositionScene: React.FC<VideoCompositionSceneProps> = ({
  width,
  height,
}) => {
  const frame = useCurrentFrame();

  // Generate video: frames 0-300 (0:00-0:10 at 30fps)
  // Dashboard video: frames 300-600 (0:10-0:20)
  // Fade transition: frames 270-330 (0:09-0:11)

  // Generate video opacity: 100% until frame 270, then fade to 0% by frame 300
  const generateOpacity = interpolate(frame, [0, 270, 300], [1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Dashboard video opacity: 0% until frame 270, then fade to 100% by frame 300
  const dashboardOpacity = interpolate(frame, [270, 300, 600], [0, 1, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // UI sounds volume: 100% until frame 270, then fade to 0% by frame 300
  const uiSoundsVolume = interpolate(frame, [0, 270, 300], [1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Podcast audio volume: 0% until frame 270, then fade to 100% by frame 300
  const podcastVolume = interpolate(frame, [270, 300, 600], [0, 1, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Podcast audio starts at frame 300 (0:10s), so trim/offset accordingly
  const podcastStartFrame = 300;

  return (
    <>
      {/* Generate Video (0:00-0:10) */}
      <Video
        src={require('../../public/video/Generate — Market Pulse and 3 more pages - Personal - Microsoft​ Edge 2026-04-22 21-23-44.mp4')}
        style={{
          width,
          height,
          opacity: generateOpacity,
          position: 'absolute',
          top: 0,
          left: 0,
        }}
        muted
      />

      {/* Dashboard Video (0:10-0:20) - starts at frame 300 */}
      <Video
        src={require('../../public/video/Dashboard — Market Pulse and 3 more pages - Personal - Microsoft​ Edge 2026-04-22 21-23-05.mp4')}
        style={{
          width,
          height,
          opacity: dashboardOpacity,
          position: 'absolute',
          top: 0,
          left: 0,
        }}
        muted
      />

      {/* UI Sounds Audio (0:00-0:10, fade out at 0:09-0:10) */}
      <Audio
        src={require('../../public/ui-sounds.mp3')}
        volume={uiSoundsVolume}
        startFrom={0}
      />

      {/* Podcast Audio (0:10-0:20, fade in at 0:09-0:10) */}
      {/* Note: Extract the podcast audio from Dashboard video and save as separate file,
          OR if Dashboard video contains audio, use the Dashboard <Video> component's audio
          and mute the UI sounds instead. For simplicity here, assuming separate podcast audio file. */}
      <Audio
        src={require('../../public/podcast-audio.mp3')}
        volume={podcastVolume}
        startFrom={0}
      />
    </>
  );
};
```

- [ ] **Step 2: Verify component compiles**

Run: `npx tsc --noEmit`
Expected: No errors (may show import warnings for video files, which is OK)

- [ ] **Step 3: Commit**

```bash
git add remotion-video/src/scenes/VideoCompositionScene.tsx
git commit -m "feat: create VideoCompositionScene with fade transition between videos"
```

---

## Task 3: Extract Podcast Audio from Dashboard Video

**Files:**
- Create: `remotion-video/public/podcast-audio.mp3`

- [ ] **Step 1: Extract audio from Dashboard video**

The Dashboard video contains the podcast audio playing. Extract it using ffmpeg:

```bash
ffmpeg -i 'remotion-video/out/video/Dashboard — Market Pulse and 3 more pages - Personal - Microsoft​ Edge 2026-04-22 21-23-05.mp4' -q:a 5 -n remotion-video/public/podcast-audio.mp3
```

Expected: `podcast-audio.mp3` created in `remotion-video/public/`

- [ ] **Step 2: Verify podcast audio duration and content**

```bash
ffprobe -show_format remotion-video/public/podcast-audio.mp3
```

Expected: Duration ~10 seconds (the podcast playback portion of the Dashboard video)

- [ ] **Step 3: Trim podcast audio if needed**

If the extracted audio is longer than 10 seconds, trim it:

```bash
ffmpeg -i remotion-video/public/podcast-audio.mp3 -t 10 -q:a 5 -n remotion-video/public/podcast-audio-trimmed.mp3 && mv remotion-video/public/podcast-audio-trimmed.mp3 remotion-video/public/podcast-audio.mp3
```

- [ ] **Step 4: Add podcast audio to git**

```bash
git add remotion-video/public/podcast-audio.mp3
git commit -m "audio: extract podcast audio from Dashboard video"
```

---

## Task 4: Update Root Composition

**Files:**
- Modify: `remotion-video/src/index.tsx`

- [ ] **Step 1: Update index.tsx to use VideoCompositionScene**

Replace the current index.tsx with:

```tsx
import React from 'react';
import { Composition, registerRoot } from 'remotion';
import { VideoCompositionScene } from './scenes/VideoCompositionScene';

const Root: React.FC = () => {
  const width = 1920;
  const height = 1080;
  const fps = 30;
  const durationInSeconds = 20;
  const durationInFrames = durationInSeconds * fps;

  return (
    <Composition
      id="VideoComposition"
      component={() => (
        <div style={{ width, height, position: 'relative', overflow: 'hidden', backgroundColor: '#000' }}>
          <VideoCompositionScene width={width} height={height} />
        </div>
      )}
      durationInFrames={durationInFrames}
      fps={fps}
      width={width}
      height={height}
    />
  );
};

registerRoot(Root);
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add remotion-video/src/index.tsx
git commit -m "feat: update Root composition to use VideoCompositionScene"
```

---

## Task 5: Update Render Configuration

**Files:**
- Modify: `remotion-video/render.ts`

- [ ] **Step 1: Update render.ts composition ID and output**

Update the composition ID from "InteractiveDemoVideo" to "VideoComposition" and output filename from "interactive-demo-video.mp4" to "video-composition.mp4".

Example changes:
```ts
// Change from:
composition: 'InteractiveDemoVideo',
outputLocation: `s3://my-bucket/interactive-demo-video.mp4`,

// To:
composition: 'VideoComposition',
outputLocation: path.resolve(path.join(__dirname, 'out', 'video-composition.mp4')),
```

- [ ] **Step 2: Verify render.ts is valid**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add remotion-video/render.ts
git commit -m "feat: update render.ts for VideoComposition"
```

---

## Task 6: Render the Final Video

**Files:**
- Output: `remotion-video/out/video-composition.mp4`

- [ ] **Step 1: Run render command**

```bash
npx ts-node --project tsconfig.json render.ts
```

Expected: Rendering starts, progress shown in console. Duration: 2-5 minutes depending on system.

- [ ] **Step 2: Verify output file exists**

```bash
ls -lh remotion-video/out/video-composition.mp4
```

Expected: File exists, size 2-5MB

- [ ] **Step 3: Check video properties**

```bash
ffprobe -show_format -show_streams remotion-video/out/video-composition.mp4
```

Expected:
- Duration: ~20 seconds
- Width: 1920, Height: 1080
- Codec: h264 (video) + aac (audio)

- [ ] **Step 4: Spot-check playback (first 15 seconds)**

Play the video using your media player and verify:
- First 10 seconds: Generate video with UI sounds (clicks, loading tones)
- Around 10 seconds: Smooth fade transition between videos
- Last 10 seconds: Dashboard video with podcast audio playing
- Audio is layered correctly (UI sounds fade out, podcast audio fades in)
- No audio dropouts during transition
- No visual glitches or black frames

- [ ] **Step 5: Commit**

```bash
git add remotion-video/out/video-composition.mp4
git commit -m "video: render video composition (20s, 1920x1080, H.264)"
```

---

## Task 7: Final Verification and Quality Check

**Files:**
- Output: Ready for LinkedIn upload

- [ ] **Step 1: Verify video meets all requirements**

Checklist:
- ✅ Duration: 20 seconds (±0.5s tolerance)
- ✅ Resolution: 1920×1080
- ✅ FPS: 30
- ✅ Codec: H.264 video + AAC audio
- ✅ File size: < 5MB
- ✅ First 10 seconds: Generate video with UI sounds
- ✅ Fade transition: Smooth opacity and audio crossfade
- ✅ Last 10 seconds: Dashboard video with podcast audio
- ✅ Audio levels: UI sounds subtle (-20dB), podcast clear (0dB)
- ✅ No artifacts, glitches, or dropouts

- [ ] **Step 2: Test on mobile preview**

View video at 16:9 aspect ratio (LinkedIn mobile playback) and confirm:
- UI readable at small size
- Audio plays correctly
- Fade transition is smooth
- No cropping or distortion

- [ ] **Step 3: Clean final commit**

```bash
git status
git log --oneline -5
```

Expected: Clean working directory, all video-related commits visible

---

## Summary

After completing all 7 tasks, you will have:

✅ UI sounds audio file (10 seconds)
✅ VideoCompositionScene component compositing two videos with fade transition
✅ Podcast audio extracted from Dashboard video
✅ Root composition updated to use VideoCompositionScene
✅ Render configuration updated
✅ Final video rendered: 20 seconds, 1920×1080, H.264
✅ Full git history with descriptive commits

**Output file:** `remotion-video/out/video-composition.mp4` — Ready for LinkedIn upload
