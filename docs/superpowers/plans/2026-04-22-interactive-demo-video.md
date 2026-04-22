# Interactive Demo Video Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a 30-second Remotion video showing Market Pulse's interactive user flow with agent-driven interactions, configuration selection, library browsing, and power-down closing animation.

**Architecture:** Build composable SVG animation components for each interaction phase (agent button click, config selection, library browsing, playback, power-down), then orchestrate them in a single InteractiveDemoScene using frame-based timing and easing. Reuse existing Waveform component for playback visualization.

**Tech Stack:** Remotion 4.0, React 19, TypeScript, SVG animations, Easing utilities, Audio component.

---

## Task 1: Create AgentIndicator Component

**Files:**
- Create: `remotion-video/src/components/AgentIndicator.tsx`

- [ ] **Step 1: Create AgentIndicator component with animated arrow**

```tsx
import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';

interface AgentIndicatorProps {
  startFrame: number;
  endFrame: number;
  startX: number;
  startY: number;
  endX: number;
  endY: number;
}

export const AgentIndicator: React.FC<AgentIndicatorProps> = ({
  startFrame,
  endFrame,
  startX,
  startY,
  endX,
  endY,
}) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [startFrame, endFrame], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  const currentX = interpolate(progress, [0, 1], [startX, endX]);
  const currentY = interpolate(progress, [0, 1], [startY, endY]);
  const opacity = interpolate(frame, [startFrame, startFrame + 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <g opacity={opacity} transform={`translate(${currentX}, ${currentY})`}>
      {/* Arrow icon */}
      <polygon
        points="0,-8 8,8 0,4 -8,8"
        fill="#FF6B35"
        style={{ filter: 'drop-shadow(0 2px 4px rgba(255,107,53,0.3))' }}
      />
    </g>
  );
};
```

- [ ] **Step 2: Verify component compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add remotion-video/src/components/AgentIndicator.tsx
git commit -m "feat: create AgentIndicator component with animated arrow"
```

---

## Task 2: Create StartGeneratingButton Component

**Files:**
- Create: `remotion-video/src/components/StartGeneratingButton.tsx`

- [ ] **Step 1: Create button component with glow and scale effects**

```tsx
import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { COLORS } from '../styles/colors';

interface StartGeneratingButtonProps {
  x: number;
  y: number;
  onSelectFrame: number;
}

export const StartGeneratingButton: React.FC<StartGeneratingButtonProps> = ({
  x,
  y,
  onSelectFrame,
}) => {
  const frame = useCurrentFrame();

  // Slide in animation
  const slideInProgress = interpolate(frame, [90, 110], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const displayX = interpolate(slideInProgress, [0, 1], [x - 200, x]);

  // Glow effect on selection
  const glowOpacity = interpolate(frame, [onSelectFrame, onSelectFrame + 20], [0.3, 0.8], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Scale on click
  const scaleProgress = interpolate(frame, [onSelectFrame, onSelectFrame + 15], [1, 1.05], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  return (
    <g transform={`translate(${displayX}, ${y})`}>
      {/* Glow background */}
      <rect
        x={0}
        y={0}
        width={200}
        height={50}
        fill={COLORS.accent}
        rx={8}
        opacity={glowOpacity * 0.2}
        filter="url(#glow)"
      />

      {/* Button background */}
      <rect
        x={0}
        y={0}
        width={200}
        height={50}
        fill={COLORS.accent}
        rx={8}
        style={{
          transform: `scale(${scaleProgress})`,
          transformOrigin: '100px 25px',
          transition: 'all 0.2s ease-out',
        }}
      />

      {/* Button text */}
      <text
        x={100}
        y={32}
        textAnchor="middle"
        fontSize={16}
        fontWeight={600}
        fill={COLORS.white}
        style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
      >
        Start Generating
      </text>
    </g>
  );
};
```

- [ ] **Step 2: Verify component compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add remotion-video/src/components/StartGeneratingButton.tsx
git commit -m "feat: create StartGeneratingButton with glow and scale effects"
```

---

## Task 3: Create SelectorCard Component

**Files:**
- Create: `remotion-video/src/components/SelectorCard.tsx`

- [ ] **Step 1: Create reusable selector card component**

```tsx
import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { COLORS } from '../styles/colors';

interface SelectorCardProps {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  options: string[];
  selectedIndex: number;
  startFrame: number;
  selectFrame: number;
  staggerDelay: number;
}

export const SelectorCard: React.FC<SelectorCardProps> = ({
  x,
  y,
  width,
  height,
  label,
  options,
  selectedIndex,
  startFrame,
  selectFrame,
  staggerDelay,
}) => {
  const frame = useCurrentFrame();
  const displayStartFrame = startFrame + staggerDelay;

  // Fade in animation
  const fadeInProgress = interpolate(frame, [displayStartFrame, displayStartFrame + 20], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Selection highlight
  const highlightOpacity = interpolate(frame, [selectFrame, selectFrame + 15], [0, 0.4], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <g opacity={fadeInProgress} transform={`translate(${x}, ${y})`}>
      {/* Card background */}
      <rect
        x={0}
        y={0}
        width={width}
        height={height}
        fill={COLORS.gray50}
        rx={8}
        stroke={COLORS.border}
        strokeWidth={1}
      />

      {/* Selection highlight */}
      <rect
        x={0}
        y={0}
        width={width}
        height={height}
        fill={COLORS.accent}
        rx={8}
        opacity={highlightOpacity}
      />

      {/* Label */}
      <text
        x={12}
        y={24}
        fontSize={12}
        fontWeight={600}
        fill={COLORS.textMuted}
        style={{ fontFamily: 'Inter, system-ui, sans-serif', textTransform: 'uppercase' }}
      >
        {label}
      </text>

      {/* Selected value */}
      <text
        x={12}
        y={50}
        fontSize={16}
        fontWeight={700}
        fill={COLORS.text}
        style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
      >
        {options[selectedIndex]}
      </text>
    </g>
  );
};
```

- [ ] **Step 2: Verify component compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add remotion-video/src/components/SelectorCard.tsx
git commit -m "feat: create SelectorCard with highlight animation"
```

---

## Task 4: Create ConfigurationPanel Component

**Files:**
- Create: `remotion-video/src/components/ConfigurationPanel.tsx`

- [ ] **Step 1: Create configuration panel with three selector cards**

```tsx
import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { SelectorCard } from './SelectorCard';
import { COLORS } from '../styles/colors';

interface ConfigurationPanelProps {
  x: number;
  y: number;
  startFrame: number;
  selectFrames: [number, number, number];
}

export const ConfigurationPanel: React.FC<ConfigurationPanelProps> = ({
  x,
  y,
  startFrame,
  selectFrames,
}) => {
  const frame = useCurrentFrame();

  // Slide in from right
  const slideInProgress = interpolate(frame, [startFrame, startFrame + 25], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const displayX = interpolate(slideInProgress, [0, 1], [x + 300, x]);

  const topicOptions = ['Markets', 'Tech', 'Economics', 'Crypto'];
  const timeOptions = ['Daily', 'Weekly', 'Monthly'];
  const styleOptions = ['Formal', 'Casual', 'Mixed'];

  return (
    <g transform={`translate(${displayX}, ${y})`}>
      {/* Panel background */}
      <rect
        x={0}
        y={0}
        width={320}
        height={200}
        fill={COLORS.gray50}
        rx={12}
        stroke={COLORS.border}
        strokeWidth={1}
      />

      {/* Selector cards */}
      <SelectorCard
        x={12}
        y={12}
        width={296}
        height={56}
        label="Topic"
        options={topicOptions}
        selectedIndex={0}
        startFrame={startFrame}
        selectFrame={selectFrames[0]}
        staggerDelay={0}
      />

      <SelectorCard
        x={12}
        y={76}
        width={296}
        height={56}
        label="Time Frame"
        options={timeOptions}
        selectedIndex={0}
        startFrame={startFrame}
        selectFrame={selectFrames[1]}
        staggerDelay={10}
      />

      <SelectorCard
        x={12}
        y={140}
        width={296}
        height={56}
        label="Style"
        options={styleOptions}
        selectedIndex={0}
        startFrame={startFrame}
        selectFrame={selectFrames[2]}
        staggerDelay={20}
      />
    </g>
  );
};
```

- [ ] **Step 2: Verify component compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add remotion-video/src/components/ConfigurationPanel.tsx
git commit -m "feat: create ConfigurationPanel with three selector cards"
```

---

## Task 5: Create PodcastCard Component

**Files:**
- Create: `remotion-video/src/components/PodcastCard.tsx`

- [ ] **Step 1: Create individual podcast card for library**

```tsx
import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { COLORS } from '../styles/colors';

interface PodcastCardProps {
  x: number;
  y: number;
  title: string;
  duration: string;
  date: string;
  staggerIndex: number;
  startFrame: number;
  isSelected?: boolean;
  expandProgress?: number;
}

export const PodcastCard: React.FC<PodcastCardProps> = ({
  x,
  y,
  title,
  duration,
  date,
  staggerIndex,
  startFrame,
  isSelected = false,
  expandProgress = 0,
}) => {
  const frame = useCurrentFrame();
  const animStartFrame = startFrame + staggerIndex * 8;

  // Slide in from left
  const slideInProgress = interpolate(frame, [animStartFrame, animStartFrame + 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const displayX = interpolate(slideInProgress, [0, 1], [x - 150, x]);

  // Opacity for non-selected cards during expansion
  const opacity = isSelected ? 1 : interpolate(expandProgress, [0, 0.3], [1, 0.3], {
    extrapolateRight: 'clamp',
  });

  return (
    <g opacity={opacity} transform={`translate(${displayX}, ${y})`}>
      {/* Card background */}
      <rect
        x={0}
        y={0}
        width={160}
        height={120}
        fill={COLORS.gray50}
        rx={8}
        stroke={isSelected ? COLORS.accent : COLORS.border}
        strokeWidth={isSelected ? 2 : 1}
      />

      {/* Icon placeholder */}
      <circle
        cx={80}
        cy={30}
        r={20}
        fill={COLORS.accent}
        opacity={0.3}
      />

      {/* Title */}
      <text
        x={8}
        y={65}
        fontSize={11}
        fontWeight={600}
        fill={COLORS.text}
        style={{
          fontFamily: 'Inter, system-ui, sans-serif',
          wordWrap: 'break-word',
          width: 144,
        }}
      >
        {title.substring(0, 20)}
      </text>

      {/* Metadata */}
      <text
        x={8}
        y={85}
        fontSize={9}
        fill={COLORS.textMuted}
        style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
      >
        {duration}
      </text>

      <text
        x={8}
        y={100}
        fontSize={9}
        fill={COLORS.textMuted}
        style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
      >
        {date}
      </text>
    </g>
  );
};
```

- [ ] **Step 2: Verify component compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add remotion-video/src/components/PodcastCard.tsx
git commit -m "feat: create PodcastCard component for library grid"
```

---

## Task 6: Create LibraryGrid Component

**Files:**
- Create: `remotion-video/src/components/LibraryGrid.tsx`

- [ ] **Step 1: Create grid of podcast cards with stagger animation**

```tsx
import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { PodcastCard } from './PodcastCard';

interface LibraryGridProps {
  x: number;
  y: number;
  startFrame: number;
  selectFrame: number;
}

export const LibraryGrid: React.FC<LibraryGridProps> = ({
  x,
  y,
  startFrame,
  selectFrame,
}) => {
  const frame = useCurrentFrame();

  // Grid fade in
  const fadeInProgress = interpolate(frame, [startFrame, startFrame + 20], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Top card expansion progress
  const expandProgress = interpolate(frame, [selectFrame, selectFrame + 40], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  const mockPodcasts = [
    { id: 0, title: 'Market Pulse Daily: Fed Decision Impact', duration: '12:34', date: 'Today' },
    { id: 1, title: 'Tech Stocks Rally on AI Gains', duration: '10:15', date: 'Yesterday' },
    { id: 2, title: 'Crypto Markets Stabilize', duration: '9:42', date: '2 days ago' },
    { id: 3, title: 'Economic Data Surprise', duration: '11:20', date: '3 days ago' },
    { id: 4, title: 'Banking Sector Update', duration: '8:50', date: '4 days ago' },
    { id: 5, title: 'Global Market Overview', duration: '13:05', date: '5 days ago' },
  ];

  return (
    <g opacity={fadeInProgress}>
      {mockPodcasts.map((podcast, index) => (
        <PodcastCard
          key={podcast.id}
          x={x + (index % 3) * 180}
          y={y + Math.floor(index / 3) * 140}
          title={podcast.title}
          duration={podcast.duration}
          date={podcast.date}
          staggerIndex={index}
          startFrame={startFrame}
          isSelected={index === 0}
          expandProgress={index === 0 ? expandProgress : 0}
        />
      ))}
    </g>
  );
};
```

- [ ] **Step 2: Verify component compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add remotion-video/src/components/LibraryGrid.tsx
git commit -m "feat: create LibraryGrid with staggered card animations"
```

---

## Task 7: Create PlayButton Component

**Files:**
- Create: `remotion-video/src/components/PlayButton.tsx`

- [ ] **Step 1: Create pulsing play button component**

```tsx
import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { COLORS } from '../styles/colors';

interface PlayButtonProps {
  x: number;
  y: number;
  radius: number;
  startFrame: number;
}

export const PlayButton: React.FC<PlayButtonProps> = ({
  x,
  y,
  radius,
  startFrame,
}) => {
  const frame = useCurrentFrame();

  // Fade in
  const fadeProgress = interpolate(frame, [startFrame, startFrame + 20], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Pulse animation
  const pulseProgress = (frame - startFrame) * 0.02;
  const scaleAmount = 1 + Math.sin(pulseProgress) * 0.1;

  return (
    <g opacity={fadeProgress} transform={`translate(${x}, ${y})`}>
      {/* Button circle */}
      <circle
        cx={0}
        cy={0}
        r={radius}
        fill={COLORS.accent}
        style={{
          transform: `scale(${scaleAmount})`,
          transformOrigin: '0 0',
          transition: 'all 0.05s ease-out',
        }}
      />

      {/* Play icon (triangle) */}
      <polygon
        points={`${-radius * 0.25},${-radius * 0.4} ${-radius * 0.25},${radius * 0.4} ${radius * 0.4},0`}
        fill={COLORS.white}
        style={{
          transform: `scale(${scaleAmount})`,
          transformOrigin: '0 0',
        }}
      />
    </g>
  );
};
```

- [ ] **Step 2: Verify component compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add remotion-video/src/components/PlayButton.tsx
git commit -m "feat: create PlayButton with pulse animation"
```

---

## Task 8: Create ExpandedPodcastCard Component

**Files:**
- Create: `remotion-video/src/components/ExpandedPodcastCard.tsx`

- [ ] **Step 1: Create enlarged card with play button and waveform**

```tsx
import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { PlayButton } from './PlayButton';
import { Waveform } from './Waveform';
import { COLORS } from '../styles/colors';

interface ExpandedPodcastCardProps {
  x: number;
  y: number;
  title: string;
  duration: string;
  expandProgress: number;
  startFrame: number;
}

export const ExpandedPodcastCard: React.FC<ExpandedPodcastCardProps> = ({
  x,
  y,
  title,
  duration,
  expandProgress,
  startFrame,
}) => {
  const frame = useCurrentFrame();

  // Scale card based on expansion
  const scale = interpolate(expandProgress, [0, 1], [1, 1.3]);
  const displayX = interpolate(expandProgress, [0, 1], [x, x - 60]);
  const displayY = interpolate(expandProgress, [0, 1], [y, y - 60]);

  // Waveform progress
  const waveProgress = interpolate(frame, [startFrame + 40, startFrame + 100], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <g
      transform={`translate(${displayX}, ${displayY}) scale(${scale})`}
      style={{ transformOrigin: '80px 60px' }}
    >
      {/* Card background */}
      <rect
        x={0}
        y={0}
        width={160}
        height={120}
        fill={COLORS.gray50}
        rx={8}
        stroke={COLORS.accent}
        strokeWidth={2}
      />

      {/* Icon */}
      <circle cx={80} cy={30} r={20} fill={COLORS.accent} opacity={0.3} />

      {/* Title */}
      <text
        x={8}
        y={65}
        fontSize={11}
        fontWeight={600}
        fill={COLORS.text}
        style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
      >
        {title.substring(0, 20)}
      </text>

      {/* Play button at center */}
      <PlayButton x={80} y={100} radius={20} startFrame={startFrame + 40} />

      {/* Waveform below play button (only visible when expanded) */}
      {expandProgress > 0.5 && (
        <g opacity={interpolate(expandProgress, [0.5, 1], [0, 1])}>
          <Waveform
            x={20}
            y={110}
            width={120}
            height={30}
            bars={16}
            progress={waveProgress}
            color={COLORS.accent}
          />
        </g>
      )}
    </g>
  );
};
```

- [ ] **Step 2: Verify component compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add remotion-video/src/components/ExpandedPodcastCard.tsx
git commit -m "feat: create ExpandedPodcastCard with play button and waveform"
```

---

## Task 9: Create PowerDownOverlay Component

**Files:**
- Create: `remotion-video/src/components/PowerDownOverlay.tsx`

- [ ] **Step 1: Create power-down fade with logo and tagline**

```tsx
import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { COLORS } from '../styles/colors';

interface PowerDownOverlayProps {
  width: number;
  height: number;
  startFrame: number;
}

export const PowerDownOverlay: React.FC<PowerDownOverlayProps> = ({
  width,
  height,
  startFrame,
}) => {
  const frame = useCurrentFrame();

  // Dark overlay opacity
  const overlayOpacity = interpolate(frame, [startFrame, startFrame + 120], [0, 0.7], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Logo fade in
  const logoFadeProgress = interpolate(frame, [startFrame + 120, startFrame + 180], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Logo scale
  const logoScale = interpolate(logoFadeProgress, [0, 1], [0.8, 1]);

  // Tagline fade in (staggered)
  const taglineFadeProgress = interpolate(frame, [startFrame + 150, startFrame + 210], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {/* Dark overlay */}
      <rect
        width={width}
        height={height}
        fill={COLORS.black}
        opacity={overlayOpacity}
      />

      {/* Logo text */}
      <g
        transform={`translate(${width / 2}, ${height / 2 - 40})`}
        opacity={logoFadeProgress}
        style={{
          transform: `translate(${width / 2}px, ${height / 2 - 40}px) scale(${logoScale})`,
          transformOrigin: '0 0',
          transition: 'all 0.3s ease-out',
        }}
      >
        <text
          x={0}
          y={0}
          textAnchor="middle"
          fontSize={72}
          fontWeight={700}
          fill={COLORS.accent}
          style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
        >
          Market Pulse
        </text>
      </g>

      {/* Tagline text */}
      <text
        x={width / 2}
        y={height / 2 + 40}
        textAnchor="middle"
        fontSize={24}
        fill={COLORS.white}
        opacity={taglineFadeProgress}
        style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
      >
        Multi-Agent AI Podcast Generator
      </text>
    </svg>
  );
};
```

- [ ] **Step 2: Verify component compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add remotion-video/src/components/PowerDownOverlay.tsx
git commit -m "feat: create PowerDownOverlay with logo and tagline fade-in"
```

---

## Task 10: Create InteractiveDemoScene Component

**Files:**
- Create: `remotion-video/src/scenes/InteractiveDemoScene.tsx`

- [ ] **Step 1: Create main scene orchestrating all sections**

```tsx
import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { COLORS } from '../styles/colors';
import { AgentIndicator } from '../components/AgentIndicator';
import { StartGeneratingButton } from '../components/StartGeneratingButton';
import { ConfigurationPanel } from '../components/ConfigurationPanel';
import { LibraryGrid } from '../components/LibraryGrid';
import { ExpandedPodcastCard } from '../components/ExpandedPodcastCard';
import { PowerDownOverlay } from '../components/PowerDownOverlay';

interface InteractiveDemoSceneProps {
  width: number;
  height: number;
}

export const InteractiveDemoScene: React.FC<InteractiveDemoSceneProps> = ({
  width,
  height,
}) => {
  const frame = useCurrentFrame();

  // Frame timings (based on 30fps)
  const SECTION_1_START = 0;     // 0-3s: Dashboard intro
  const SECTION_2_START = 90;    // 3-7s: Start generating
  const SECTION_3_START = 210;   // 7-13s: Configuration
  const SECTION_4_START = 390;   // 13-17s: Library
  const SECTION_5_START = 510;   // 17-20s: Playback
  const SECTION_6_START = 600;   // 20-30s: Power-down

  const centerX = width / 2;
  const centerY = height / 2;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {/* Background */}
      <rect width={width} height={height} fill={COLORS.background} />

      {/* Section 1: Dashboard intro (fade in) */}
      <g
        opacity={interpolate(frame, [SECTION_1_START, SECTION_1_START + 30], [0, 1], {
          extrapolateRight: 'clamp',
        })}
      >
        <rect
          x={centerX - 400}
          y={centerY - 200}
          width={800}
          height={400}
          fill={COLORS.gray50}
          rx={12}
          stroke={COLORS.border}
          strokeWidth={1}
        />
        <text
          x={centerX}
          y={centerY - 150}
          textAnchor="middle"
          fontSize={48}
          fontWeight={700}
          fill={COLORS.accent}
          style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
        >
          Market Pulse
        </text>
      </g>

      {/* Section 2: Start generating button */}
      <AgentIndicator
        startFrame={SECTION_2_START}
        endFrame={SECTION_2_START + 40}
        startX={centerX - 300}
        startY={centerY}
        endX={centerX}
        endY={centerY + 80}
      />

      <StartGeneratingButton
        x={centerX}
        y={centerY + 80}
        onSelectFrame={SECTION_2_START + 40}
      />

      {/* Section 3: Configuration panel */}
      <ConfigurationPanel
        x={centerX + 100}
        y={centerY - 100}
        startFrame={SECTION_3_START}
        selectFrames={[
          SECTION_3_START + 60,
          SECTION_3_START + 90,
          SECTION_3_START + 120,
        ]}
      />

      {/* Section 4: Library grid (fades out during expansion) */}
      <g
        opacity={interpolate(frame, [SECTION_4_START, SECTION_5_START], [1, 0.3], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })}
      >
        <LibraryGrid
          x={centerX - 280}
          y={centerY - 180}
          startFrame={SECTION_4_START}
          selectFrame={SECTION_5_START}
        />
      </g>

      {/* Section 5: Expanded podcast card (large, centered) */}
      <ExpandedPodcastCard
        x={centerX - 80}
        y={centerY - 60}
        title="Market Pulse Daily: Fed Decision Impact"
        duration="12:34"
        expandProgress={interpolate(
          frame,
          [SECTION_5_START, SECTION_5_START + 40],
          [0, 1],
          { extrapolateRight: 'clamp' }
        )}
        startFrame={SECTION_5_START}
      />

      {/* Section 6: Power-down overlay with logo */}
      <PowerDownOverlay width={width} height={height} startFrame={SECTION_6_START} />
    </svg>
  );
};
```

- [ ] **Step 2: Verify component compiles**

Run: `npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add remotion-video/src/scenes/InteractiveDemoScene.tsx
git commit -m "feat: create InteractiveDemoScene orchestrating all sections"
```

---

## Task 11: Update Root Composition

**Files:**
- Modify: `remotion-video/src/index.tsx`

- [ ] **Step 1: Update Root to use InteractiveDemoScene**

Replace the current index.tsx with:

```tsx
import React from 'react';
import { Composition, registerRoot, Audio } from 'remotion';
import { InteractiveDemoScene } from './scenes/InteractiveDemoScene';
import demoMusic from '../public/demo-music.mp3';

const Root: React.FC = () => {
  const width = 1920;
  const height = 1080;
  const fps = 30;
  const durationInSeconds = 30;
  const durationInFrames = durationInSeconds * fps;

  return (
    <Composition
      id="InteractiveDemoVideo"
      component={() => (
        <div style={{ width, height, position: 'relative', overflow: 'hidden', backgroundColor: '#000' }}>
          <Audio src={demoMusic} startFrom={0} />
          <InteractiveDemoScene width={width} height={height} />
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
git commit -m "feat: update Root composition to use InteractiveDemoScene"
```

---

## Task 12: Update Render Configuration

**Files:**
- Modify: `remotion-video/render.ts`

- [ ] **Step 1: Update render.ts to render new composition**

Replace the composition ID and output name:

```ts
const browserInstance = await openBrowser();
const { errors } = await bundleOnLambda({
  entryPoint: path.resolve(path.join(__dirname, 'src', 'index.tsx')),
  outDir: path.resolve(path.join(__dirname, 'out')),
  region: 'us-east-1',
  timeoutInMilliseconds: 300000,
});

if (errors.length > 0) {
  errors.forEach((err) => console.error(err));
  process.exit(1);
}

await renderMediaOnLambda({
  region: 'us-east-1',
  functionName: 'remotion-render',
  serveUrl: `file://${path.resolve(path.join(__dirname, 'out'))}`,
  composition: 'InteractiveDemoVideo',
  outputLocation: `s3://my-bucket/interactive-demo-video.mp4`,
  inputProps: {},
  codec: 'h264',
  crf: 18,
  maxRetries: 1,
});

await browserInstance.close();
console.log('Rendering complete!');
```

Or for local rendering (if using local render method):

```ts
const { audioCodec, codeCodec } = await renderMedia({
  composition: 'InteractiveDemoVideo',
  fps: 30,
  numberOfFrames: 900,
  outputLocation: path.resolve(path.join(__dirname, 'out', 'interactive-demo-video.mp4')),
  codec: 'h264',
  crf: 18,
});
```

- [ ] **Step 2: Test render command (dry run)**

Run: `npx ts-node --project tsconfig.json render.ts --dry-run` (if supported)
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add remotion-video/render.ts
git commit -m "feat: update render.ts for InteractiveDemoVideo composition"
```

---

## Task 13: Create Demo Music and Voiceover Audio

**Files:**
- Create: `remotion-video/public/demo-music.mp3`
- Create: `remotion-video/public/voiceover.mp3` (optional)

- [ ] **Step 1: Source or create background music file (30s)**

Source a 30-second upbeat instrumental music track and save as `remotion-video/public/demo-music.mp3`. 
Recommendation: Use royalty-free music from Freepik, Epidemic Sound, or similar.

Expected file size: ~500KB

- [ ] **Step 2: (Optional) Create voiceover audio file**

If using pre-recorded voiceover, save as `remotion-video/public/voiceover.mp3` with callouts at:
- 0:04 "Starting generation..."
- 0:09 "Selecting configuration..."
- 0:16 "Playing top episode..."

Alternatively, use text-to-speech (e.g., Google Cloud TTS, ElevenLabs) to generate voiceover.

Expected file size: ~200KB

- [ ] **Step 3: Add audio files to git**

Run: `git add remotion-video/public/demo-music.mp3` (and voiceover if created)
Expected: Files added to staging

- [ ] **Step 4: Commit audio files**

```bash
git commit -m "audio: add background music and optional voiceover tracks"
```

---

## Task 14: Render the Final Video

**Files:**
- Output: `remotion-video/out/interactive-demo-video.mp4`

- [ ] **Step 1: Run render command**

Run: `npx ts-node --project tsconfig.json render.ts`
Expected: Rendering starts, progress shown in console

- [ ] **Step 2: Wait for render to complete**

Expected duration: 2-5 minutes depending on system
Expected output: `remotion-video/out/interactive-demo-video.mp4` (~2-3MB)

- [ ] **Step 3: Verify video file exists and plays**

Run: `ls -lh remotion-video/out/interactive-demo-video.mp4`
Expected: File size 2-3MB, readable

- [ ] **Step 4: Spot-check video playback (at least 10 seconds)**

Using your media player, verify:
- Dashboard intro fades in smoothly
- Agent indicator moves toward button
- Button glows and scales
- Configuration panel slides in
- Library grid appears
- Top card enlarges and play button pulses
- Screen fades to black with logo reveal

- [ ] **Step 5: Commit rendered video**

```bash
git add remotion-video/out/interactive-demo-video.mp4
git commit -m "video: render interactive demo video (30s, 1080p)"
```

---

## Task 15: Final Verification and Cleanup

**Files:**
- Output: Ready for LinkedIn upload

- [ ] **Step 1: Verify final video properties**

Run: `ffprobe -v error -show_format -show_streams remotion-video/out/interactive-demo-video.mp4`
Expected output includes:
- duration: 30.0 (or close to 30)
- width: 1920
- height: 1080
- codec: h264

- [ ] **Step 2: Final spot-check on mobile preview**

View the video at 16:9 aspect ratio (LinkedIn mobile playback size) and confirm:
- Text is readable
- Animations are smooth (no stuttering)
- Audio syncs with visuals
- All sections visible without cropping

- [ ] **Step 3: Document any notes or known issues**

If any issues are found (timing off, visual glitches, audio sync problems), note them here for future refinement.

- [ ] **Step 4: Clean final commit**

```bash
git status
git log --oneline -10
```

Expected: Clean working directory, all video-related commits visible in history

---

## Summary

After completing all 15 tasks, you will have:

✅ Fully implemented 30-second interactive demo video
✅ All components created and tested
✅ Rendered MP4 file ready for LinkedIn
✅ Full git history with descriptive commits
✅ Responsive animations with proper timing
✅ Audio integrated (music + optional voiceover)

The video is ready for upload to LinkedIn. See user's documentation for LinkedIn upload instructions.
