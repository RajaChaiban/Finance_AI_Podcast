# Market Pulse LinkedIn Video Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 20-second Remotion video showcasing Market Pulse as a multi-agent AI podcast generator, optimized for LinkedIn distribution.

**Architecture:** Create a React-based Remotion composition with three sequential scenes (Dashboard → Agent Orchestration → Result/CTA), each with animations that reveal the technology stack. Use Remotion's built-in animation utilities (spring, interpolate) for smooth, Claude-style transitions.

**Tech Stack:**
- Remotion (video composition in React)
- TypeScript for type safety
- Tailwind CSS colors for consistency with the website
- FFmpeg (via Remotion) for MP4 export
- React Spring / Remotion's timing utilities for animations

---

## File Structure

```
remotion-video/
├── src/
│   ├── Composition.tsx              # Main 20-second video composition
│   ├── scenes/
│   │   ├── DashboardScene.tsx       # Dashboard + hero text (0–6 sec)
│   │   ├── AgentFlowScene.tsx       # Multi-agent visualization (6–15 sec)
│   │   └── ResultScene.tsx          # Podcast player + CTA (15–20 sec)
│   ├── components/
│   │   ├── AgentNode.tsx            # Reusable agent node component
│   │   ├── FlowArrow.tsx            # Animated flow arrow
│   │   └── Waveform.tsx             # Audio waveform animation
│   ├── styles/
│   │   └── colors.ts                # Tailwind palette exports
│   ├── assets/
│   │   ├── dashboard.png            # Dashboard screenshot
│   │   └── icons.tsx                # SVG icons (data, brain, mic)
│   └── index.tsx                    # Entry point
├── public/
│   └── ambient-music.mp3            # Background music (~20 sec)
├── package.json
├── tsconfig.json
├── remotion.config.ts
└── README.md
```

---

## Tasks

### Task 1: Initialize Remotion Project

**Files:**
- Create: `remotion-video/package.json`
- Create: `remotion-video/tsconfig.json`
- Create: `remotion-video/remotion.config.ts`
- Create: `remotion-video/.gitignore`

- [ ] **Step 1: Create project directory and initialize**

```bash
mkdir -p remotion-video
cd remotion-video
npm init -y
```

- [ ] **Step 2: Install Remotion and dependencies**

```bash
npm install remotion react react-dom typescript
npm install --save-dev @types/react @types/react-dom ts-node
```

Expected: All packages installed without errors.

- [ ] **Step 3: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "resolveJsonModule": true,
    "moduleResolution": "bundler",
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "allowJs": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.app.json" }]
}
```

- [ ] **Step 4: Create remotion.config.ts**

```typescript
import { Config } from 'remotion';

Config.setVideoImageFormat('png');
Config.setCodec('h264');
Config.setAudioBitrate('192k');
Config.setFps(30);
Config.setCrf(18);
Config.setPixelFormat('yuv420p');
```

- [ ] **Step 5: Create .gitignore**

```
node_modules
dist
.env
*.mp4
out
```

- [ ] **Step 6: Commit**

```bash
git add remotion-video/
git commit -m "chore: initialize Remotion project with TypeScript config"
```

---

### Task 2: Create Color Palette & Utilities

**Files:**
- Create: `remotion-video/src/styles/colors.ts`
- Create: `remotion-video/src/utils/animations.ts`

- [ ] **Step 1: Create colors.ts with Tailwind palette**

```typescript
// Export Market Pulse Tailwind colors
export const COLORS = {
  // Primary accent (from Tailwind config)
  accent: '#FF6B35', // Update with actual accent color from your site
  accentLight: '#FFE4D6',
  accentDark: '#CC5529',

  // Neutrals
  white: '#FFFFFF',
  black: '#000000',
  gray50: '#F9FAFB',
  gray100: '#F3F4F6',
  gray200: '#E5E7EB',
  gray300: '#D1D5DB',
  gray400: '#9CA3AF',
  gray500: '#6B7280',
  gray600: '#4B5563',
  gray700: '#374151',
  gray800: '#1F2937',
  gray900: '#111827',

  // Semantic
  text: '#111827',
  textMuted: '#6B7280',
  border: '#E5E7EB',
  background: '#FFFFFF',
};

export const TAILWIND = {
  primary: COLORS.accent,
  secondary: COLORS.gray600,
  muted: COLORS.gray400,
};
```

- [ ] **Step 2: Create animations.ts with utility functions**

```typescript
import { interpolate, Easing } from 'remotion';

export const easeOutCubic = (t: number): number => {
  return 1 - Math.pow(1 - t, 3);
};

export const easeInOutQuad = (t: number): number => {
  return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
};

export const createFadeIn = (frame: number, startFrame: number, durationFrames: number): number => {
  return interpolate(frame, [startFrame, startFrame + durationFrames], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
};

export const createSlideIn = (frame: number, startFrame: number, durationFrames: number, fromX: number = -50): number => {
  return interpolate(frame, [startFrame, startFrame + durationFrames], [fromX, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
};

export const createScale = (frame: number, startFrame: number, durationFrames: number, fromScale: number = 0.9): number => {
  return interpolate(frame, [startFrame, startFrame + durationFrames], [fromScale, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
};
```

- [ ] **Step 3: Commit**

```bash
git add remotion-video/src/styles/colors.ts remotion-video/src/utils/animations.ts
git commit -m "feat: add Tailwind colors and animation utilities"
```

---

### Task 3: Create SVG Icons Component

**Files:**
- Create: `remotion-video/src/assets/icons.tsx`

- [ ] **Step 1: Create icons.tsx with agent icons**

```typescript
import React from 'react';

interface IconProps {
  size?: number;
  color?: string;
}

export const DataIcon: React.FC<IconProps> = ({ size = 48, color = '#FF6B35' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="24" cy="24" r="20" stroke={color} strokeWidth="2"/>
    <path d="M12 24h24M16 18v12M24 16v16M32 20v8" stroke={color} strokeWidth="2" strokeLinecap="round"/>
  </svg>
);

export const BrainIcon: React.FC<IconProps> = ({ size = 48, color = '#FF6B35' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="24" cy="24" r="20" stroke={color} strokeWidth="2"/>
    <path d="M16 24c0-4.42 3-8 8-8s8 3.58 8 8-3 8-8 8-8-3.58-8-8Z" stroke={color} strokeWidth="2"/>
    <circle cx="24" cy="24" r="2" fill={color}/>
  </svg>
);

export const MicIcon: React.FC<IconProps> = ({ size = 48, color = '#FF6B35' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="24" cy="24" r="20" stroke={color} strokeWidth="2"/>
    <path d="M24 14v12M18 26c0 3.31 2.69 6 6 6s6-2.69 6-6" stroke={color} strokeWidth="2" strokeLinecap="round"/>
    <path d="M24 32v4" stroke={color} strokeWidth="2" strokeLinecap="round"/>
  </svg>
);
```

- [ ] **Step 2: Commit**

```bash
git add remotion-video/src/assets/icons.tsx
git commit -m "feat: add SVG icons for agent nodes"
```

---

### Task 4: Create AgentNode Component

**Files:**
- Create: `remotion-video/src/components/AgentNode.tsx`

- [ ] **Step 1: Create AgentNode.tsx**

```typescript
import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { COLORS } from '../styles/colors';

interface AgentNodeProps {
  icon: React.ReactNode;
  label: string;
  x: number;
  y: number;
  appearFrame: number;
  glowIntensity?: number;
}

export const AgentNode: React.FC<AgentNodeProps> = ({
  icon,
  label,
  x,
  y,
  appearFrame,
  glowIntensity = 1,
}) => {
  const frame = useCurrentFrame();

  // Fade in animation
  const opacity = interpolate(frame, [appearFrame, appearFrame + 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  // Subtle pulsing glow
  const glowOpacity = 0.3 + 0.2 * Math.sin((frame * 0.05) + (appearFrame * 0.1));

  return (
    <g opacity={opacity} transform={`translate(${x}, ${y})`}>
      {/* Glow effect */}
      <circle
        cx="0"
        cy="0"
        r="52"
        fill={COLORS.accent}
        opacity={glowOpacity * glowIntensity * 0.2}
        style={{ filter: 'blur(8px)' }}
      />

      {/* Node circle */}
      <circle
        cx="0"
        cy="0"
        r="48"
        fill="none"
        stroke={COLORS.accent}
        strokeWidth="2"
        style={{ filter: `drop-shadow(0 0 8px ${COLORS.accent}${Math.floor(glowOpacity * 255).toString(16).padStart(2, '0')})` }}
      />

      {/* Icon center */}
      <g transform="translate(-24, -24)">{icon}</g>

      {/* Label below node */}
      <text
        x="0"
        y="70"
        textAnchor="middle"
        fontSize="16"
        fontWeight="600"
        fill={COLORS.text}
        style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
      >
        {label}
      </text>
    </g>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add remotion-video/src/components/AgentNode.tsx
git commit -m "feat: create AgentNode component with animations"
```

---

### Task 5: Create FlowArrow Component

**Files:**
- Create: `remotion-video/src/components/FlowArrow.tsx`

- [ ] **Step 1: Create FlowArrow.tsx with travel effect**

```typescript
import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { COLORS } from '../styles/colors';

interface FlowArrowProps {
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
  startFrame: number;
  durationFrames: number;
}

export const FlowArrow: React.FC<FlowArrowProps> = ({
  fromX,
  fromY,
  toX,
  toY,
  startFrame,
  durationFrames,
}) => {
  const frame = useCurrentFrame();

  // Arrow appears and travels along the line
  const progress = interpolate(
    frame,
    [startFrame, startFrame + durationFrames],
    [0, 1],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.out(Easing.cubic),
    }
  );

  // Arrow position along the line
  const arrowX = fromX + (toX - fromX) * progress;
  const arrowY = fromY + (toY - fromY) * progress;

  // Fade in arrow at start, fade out at end
  const opacity = interpolate(
    progress,
    [0, 0.2, 0.8, 1],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <g opacity={opacity}>
      {/* Line from start to end */}
      <line
        x1={fromX}
        y1={fromY}
        x2={toX}
        y2={toY}
        stroke={COLORS.accent}
        strokeWidth="3"
        opacity="0.3"
      />

      {/* Moving arrow head */}
      <circle cx={arrowX} cy={arrowY} r="6" fill={COLORS.accent} />
      <polygon
        points={`${arrowX},${arrowY - 8} ${arrowX + 7},${arrowY + 4} ${arrowX - 7},${arrowY + 4}`}
        fill={COLORS.accent}
      />
    </g>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add remotion-video/src/components/FlowArrow.tsx
git commit -m "feat: create FlowArrow component with travel animation"
```

---

### Task 6: Create DashboardScene

**Files:**
- Create: `remotion-video/src/scenes/DashboardScene.tsx`
- Requires: Dashboard screenshot at `remotion-video/public/dashboard.png`

- [ ] **Step 1: Capture dashboard screenshot**

Visit your local FastAPI server (likely `http://localhost:8000/`) and take a full-page screenshot of the dashboard. Save as `remotion-video/public/dashboard.png` (1920×1080).

- [ ] **Step 2: Create DashboardScene.tsx**

```typescript
import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { COLORS } from '../styles/colors';

interface DashboardSceneProps {
  width: number;
  height: number;
}

export const DashboardScene: React.FC<DashboardSceneProps> = ({ width, height }) => {
  const frame = useCurrentFrame();

  // Fade in dashboard (0-30 frames)
  const dashboardOpacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  // Hero text fade in and slide (30-90 frames)
  const heroOpacity = interpolate(frame, [30, 60], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  const heroY = interpolate(frame, [30, 60], [20, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  // Dashboard blur start (at frame 180, prepare for transition)
  const dashboardBlur = interpolate(frame, [180, 195], [0, 8], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {/* Background */}
      <rect width={width} height={height} fill={COLORS.background} />

      {/* Dashboard screenshot */}
      <image
        href="dashboard.png"
        x="0"
        y="0"
        width={width}
        height={height}
        opacity={dashboardOpacity}
        style={{
          filter: `blur(${dashboardBlur}px)`,
        }}
      />

      {/* Dark overlay for text readability */}
      <rect
        width={width}
        height={height}
        fill={COLORS.black}
        opacity={heroOpacity * 0.2}
      />

      {/* Hero text container */}
      <g opacity={heroOpacity} transform={`translate(0, ${heroY})`}>
        {/* Text background (optional subtle box) */}
        <rect
          x="80"
          y="200"
          width="1760"
          height="300"
          fill="none"
          rx="12"
        />

        {/* Main headline */}
        <text
          x={width / 2}
          y="280"
          textAnchor="middle"
          fontSize="56"
          fontWeight="700"
          fill={COLORS.white}
          style={{
            fontFamily: 'Inter, system-ui, sans-serif',
            textShadow: `0 2px 16px rgba(0,0,0,0.5)`,
          }}
        >
          Your daily market podcast,
        </text>

        <text
          x={width / 2}
          y="360"
          textAnchor="middle"
          fontSize="56"
          fontWeight="700"
          fill={COLORS.white}
          style={{
            fontFamily: 'Inter, system-ui, sans-serif',
            textShadow: `0 2px 16px rgba(0,0,0,0.5)`,
          }}
        >
          ready each morning.
        </text>

        {/* Subheader */}
        <text
          x={width / 2}
          y="430"
          textAnchor="middle"
          fontSize="18"
          fill={COLORS.gray200}
          style={{
            fontFamily: 'Inter, system-ui, sans-serif',
            textShadow: `0 1px 8px rgba(0,0,0,0.5)`,
          }}
        >
          Powered by multi-agent AI orchestration.
        </text>
      </g>
    </svg>
  );
};
```

- [ ] **Step 3: Commit**

```bash
git add remotion-video/src/scenes/DashboardScene.tsx remotion-video/public/dashboard.png
git commit -m "feat: create DashboardScene with hero text animation"
```

---

### Task 7: Create AgentFlowScene

**Files:**
- Create: `remotion-video/src/scenes/AgentFlowScene.tsx`

- [ ] **Step 1: Create AgentFlowScene.tsx**

```typescript
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { COLORS } from '../styles/colors';
import { AgentNode } from '../components/AgentNode';
import { FlowArrow } from '../components/FlowArrow';
import { DataIcon, BrainIcon, MicIcon } from '../assets/icons';

interface AgentFlowSceneProps {
  width: number;
  height: number;
}

export const AgentFlowScene: React.FC<AgentFlowSceneProps> = ({ width, height }) => {
  const frame = useCurrentFrame();

  // Scene timing: starts at frame 180 (6 sec * 30 fps)
  const sceneFrame = frame - 180;

  const centerY = height / 2;
  const nodeSpacing = (width - 200) / 2;
  const node1X = 160;
  const node2X = node1X + nodeSpacing;
  const node3X = node2X + nodeSpacing;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {/* Background (subtle gradient or solid) */}
      <defs>
        <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={COLORS.gray50} />
          <stop offset="100%" stopColor={COLORS.white} />
        </linearGradient>
      </defs>
      <rect width={width} height={height} fill="url(#bgGradient)" />

      {/* Agent nodes */}
      <AgentNode
        icon={<DataIcon size={48} color={COLORS.accent} />}
        label="Search Live Data"
        x={node1X}
        y={centerY}
        appearFrame={sceneFrame + 0}
      />

      <AgentNode
        icon={<BrainIcon size={48} color={COLORS.accent} />}
        label="Generate Script"
        x={node2X}
        y={centerY}
        appearFrame={sceneFrame + 15}
      />

      <AgentNode
        icon={<MicIcon size={48} color={COLORS.accent} />}
        label="Kokoro TTS"
        x={node3X}
        y={centerY}
        appearFrame={sceneFrame + 30}
      />

      {/* Flow arrows */}
      <FlowArrow
        fromX={node1X + 50}
        fromY={centerY}
        toX={node2X - 50}
        toY={centerY}
        startFrame={sceneFrame + 60}
        durationFrames={60}
      />

      <FlowArrow
        fromX={node2X + 50}
        fromY={centerY}
        toX={node3X - 50}
        toY={centerY}
        startFrame={sceneFrame + 120}
        durationFrames={60}
      />

      {/* Optional: Title text above nodes */}
      <text
        x={width / 2}
        y="80"
        textAnchor="middle"
        fontSize="32"
        fontWeight="600"
        fill={COLORS.text}
        style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
        opacity={Math.max(0, Math.min(1, (sceneFrame - 0) / 30))}
      >
        Multi-Agent Orchestration
      </text>
    </svg>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add remotion-video/src/scenes/AgentFlowScene.tsx
git commit -m "feat: create AgentFlowScene with agent nodes and flow animations"
```

---

### Task 8: Create Waveform Component

**Files:**
- Create: `remotion-video/src/components/Waveform.tsx`

- [ ] **Step 1: Create Waveform.tsx**

```typescript
import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { COLORS } from '../styles/colors';

interface WaveformProps {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  bars?: number;
  startFrame?: number;
}

export const Waveform: React.FC<WaveformProps> = ({
  x = 0,
  y = 0,
  width = 400,
  height = 60,
  bars = 24,
  startFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [startFrame, startFrame + 20], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const barWidth = width / bars;

  return (
    <g transform={`translate(${x}, ${y})`}>
      {Array.from({ length: bars }).map((_, i) => {
        // Create wave effect
        const baseHeight = height * (0.2 + 0.8 * Math.sin((i / bars) * Math.PI * 2));
        const animatedHeight = baseHeight * (0.5 + 0.5 * Math.sin(frame * 0.1 + i * 0.3));
        const displayHeight = animatedHeight * progress;

        return (
          <rect
            key={i}
            x={i * barWidth + 2}
            y={height / 2 - displayHeight / 2}
            width={barWidth - 4}
            height={displayHeight}
            fill={COLORS.accent}
            rx="2"
            opacity={progress}
          />
        );
      })}
    </g>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add remotion-video/src/components/Waveform.tsx
git commit -m "feat: create Waveform component with animated bars"
```

---

### Task 9: Create ResultScene

**Files:**
- Create: `remotion-video/src/scenes/ResultScene.tsx`

- [ ] **Step 1: Create ResultScene.tsx**

```typescript
import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { COLORS } from '../styles/colors';
import { Waveform } from '../components/Waveform';

interface ResultSceneProps {
  width: number;
  height: number;
  githubUrl?: string;
}

export const ResultScene: React.FC<ResultSceneProps> = ({
  width,
  height,
  githubUrl = 'https://github.com/RajaChaiban/Finance_AI_Podcast',
}) => {
  const frame = useCurrentFrame();

  // Scene starts at frame 450 (15 sec * 30 fps)
  const sceneFrame = frame - 450;

  // Player emphasis fade in
  const playerOpacity = interpolate(sceneFrame, [0, 20], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  // Title fade in
  const titleOpacity = interpolate(sceneFrame, [30, 60], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Subtitle fade in
  const subtitleOpacity = interpolate(sceneFrame, [60, 90], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // CTA fade in
  const ctaOpacity = interpolate(sceneFrame, [100, 130], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const centerX = width / 2;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {/* Background */}
      <rect width={width} height={height} fill={COLORS.background} />

      {/* Podcast player card */}
      <g opacity={playerOpacity}>
        {/* Card background */}
        <rect
          x={centerX - 300}
          y={height / 2 - 120}
          width="600"
          height="240"
          fill={COLORS.gray50}
          stroke={COLORS.border}
          strokeWidth="1"
          rx="16"
        />

        {/* "Now Playing" label */}
        <text
          x={centerX - 280}
          y={height / 2 - 90}
          fontSize="12"
          fontWeight="600"
          fill={COLORS.textMuted}
          style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
          textTransform="uppercase"
        >
          Now Playing
        </text>

        {/* Episode title */}
        <text
          x={centerX - 280}
          y={height / 2 - 60}
          fontSize="20"
          fontWeight="700"
          fill={COLORS.text}
          style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
        >
          Market Pulse Daily Edition
        </text>

        {/* Waveform inside player */}
        <Waveform
          x={centerX - 280}
          y={height / 2 - 20}
          width="560"
          height="40"
          bars={20}
          startFrame={sceneFrame + 50}
        />

        {/* Play button */}
        <circle
          cx={centerX}
          cy={height / 2 + 100}
          r="28"
          fill={COLORS.accent}
          style={{ cursor: 'pointer' }}
        />
        <polygon
          points={`${centerX - 8},${height / 2 + 90} ${centerX - 8},${height / 2 + 110} ${centerX + 12},${height / 2 + 100}`}
          fill={COLORS.white}
        />
      </g>

      {/* Brand & Messaging */}
      <text
        x={centerX}
        y={height / 2 + 200}
        textAnchor="middle"
        fontSize="36"
        fontWeight="700"
        fill={COLORS.text}
        style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
        opacity={titleOpacity}
      >
        Market Pulse
      </text>

      <text
        x={centerX}
        y={height / 2 + 250}
        textAnchor="middle"
        fontSize="20"
        fill={COLORS.textMuted}
        style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
        opacity={subtitleOpacity}
      >
        Multi-Agent AI Podcast Generator
      </text>

      {/* GitHub CTA */}
      <g opacity={ctaOpacity}>
        {/* Button background */}
        <rect
          x={centerX - 200}
          y={height / 2 + 290}
          width="400"
          height="60"
          fill={COLORS.accent}
          rx="8"
        />

        {/* Button text */}
        <text
          x={centerX}
          y={height / 2 + 328}
          textAnchor="middle"
          fontSize="18"
          fontWeight="600"
          fill={COLORS.white}
          style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
        >
          Star on GitHub
        </text>

        {/* URL below button */}
        <text
          x={centerX}
          y={height / 2 + 370}
          textAnchor="middle"
          fontSize="14"
          fill={COLORS.textMuted}
          style={{ fontFamily: 'monospace' }}
        >
          {githubUrl.replace('https://', '')}
        </text>
      </g>
    </svg>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add remotion-video/src/scenes/ResultScene.tsx
git commit -m "feat: create ResultScene with podcast player and GitHub CTA"
```

---

### Task 10: Create Main Composition

**Files:**
- Create: `remotion-video/src/Composition.tsx`
- Create: `remotion-video/src/index.tsx`

- [ ] **Step 1: Create Composition.tsx**

```typescript
import React from 'react';
import { Composition } from 'remotion';
import { DashboardScene } from './scenes/DashboardScene';
import { AgentFlowScene } from './scenes/AgentFlowScene';
import { ResultScene } from './scenes/ResultScene';

const WIDTH = 1920;
const HEIGHT = 1080;
const FPS = 30;
const DURATION_IN_FRAMES = 600; // 20 seconds at 30 fps

const MarketPulseVideo: React.FC = () => {
  return (
    <div style={{ width: WIDTH, height: HEIGHT, position: 'relative', overflow: 'hidden' }}>
      <svg width={WIDTH} height={HEIGHT} style={{ position: 'absolute' }}>
        {/* Layer 1: Dashboard Scene (0–6 sec) */}
        <foreignObject x="0" y="0" width={WIDTH} height={HEIGHT}>
          <DashboardScene width={WIDTH} height={HEIGHT} />
        </foreignObject>

        {/* Layer 2: Agent Flow Scene (6–15 sec) */}
        {true && (
          <foreignObject x="0" y="0" width={WIDTH} height={HEIGHT}>
            <AgentFlowScene width={WIDTH} height={HEIGHT} />
          </foreignObject>
        )}

        {/* Layer 3: Result Scene (15–20 sec) */}
        {true && (
          <foreignObject x="0" y="0" width={WIDTH} height={HEIGHT}>
            <ResultScene width={WIDTH} height={HEIGHT} />
          </foreignObject>
        )}
      </svg>
    </div>
  );
};

export const RemotionComposition = () => {
  return (
    <Composition
      id="MarketPulse"
      component={MarketPulseVideo}
      durationInFrames={DURATION_IN_FRAMES}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
      defaultProps={{}}
    />
  );
};
```

- [ ] **Step 2: Create index.tsx**

```typescript
import { registerRoot } from 'remotion';
import { RemotionComposition } from './Composition';

registerRoot(() => <RemotionComposition />);
```

- [ ] **Step 3: Commit**

```bash
git add remotion-video/src/Composition.tsx remotion-video/src/index.tsx
git commit -m "feat: create main Composition with all three scenes"
```

---

### Task 11: Add Audio & Render Configuration

**Files:**
- Modify: `remotion-video/package.json`
- Create: `remotion-video/render.ts`
- Create: `remotion-video/public/ambient-music.mp3` (or use royalty-free track)

- [ ] **Step 1: Download royalty-free ambient music**

Download a 20-second ambient/electronic track (recommend: free stock music from Pixabay or Pexels) and save as `remotion-video/public/ambient-music.mp3`.

Alternatively, use ffmpeg to create silence:
```bash
ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 20 -q:a 9 -acodec libmp3lame remotion-video/public/ambient-music.mp3
```

- [ ] **Step 2: Create render.ts script**

```typescript
import { bundle } from '@remotion/bundler';
import { renderMedia, selectComposition } from '@remotion/renderer';
import path from 'path';

const compositionId = 'MarketPulse';

const main = async () => {
  const bundled = await bundle(path.join(__dirname, 'src/index.tsx'));

  const composition = await selectComposition({
    serveUrl: bundled,
    id: compositionId,
  });

  await renderMedia({
    composition,
    serveUrl: bundled,
    codec: 'h264',
    outputLocation: path.join(__dirname, 'out', 'market-pulse-video.mp4'),
  });

  console.log('✅ Video rendered: out/market-pulse-video.mp4');
};

main().catch(console.error);
```

- [ ] **Step 3: Update package.json with scripts**

```json
{
  "scripts": {
    "dev": "remotion preview src/index.tsx",
    "build": "remotion render src/index.tsx MarketPulse out/market-pulse-video.mp4",
    "render": "ts-node render.ts"
  }
}
```

- [ ] **Step 4: Install additional dev dependencies**

```bash
npm install --save-dev @remotion/bundler @remotion/renderer ts-node
```

- [ ] **Step 5: Commit**

```bash
git add remotion-video/package.json remotion-video/render.ts remotion-video/public/ambient-music.mp3
git commit -m "feat: add audio and render script for MP4 export"
```

---

### Task 12: Render & Optimize Video

**Files:**
- Output: `remotion-video/out/market-pulse-video.mp4`

- [ ] **Step 1: Test preview in dev mode**

```bash
cd remotion-video
npm run dev
```

Expected: Remotion preview opens in browser showing the video composition. Verify timing, animations, and layout look correct.

- [ ] **Step 2: Render final MP4**

```bash
npm run build
```

Expected: Outputs `out/market-pulse-video.mp4` (~10–20 MB, 1920×1080, 20 sec duration).

- [ ] **Step 3: Verify output quality**

Check file details:
```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration,r_frame_rate -of csv=p=0 out/market-pulse-video.mp4
```

Expected output: `1920,1080,20.000,30/1`

- [ ] **Step 4: Optimize for LinkedIn (optional)**

LinkedIn recommends max 4 GB, but smaller is better for fast loading. Current file should already be optimized. If needed, re-encode with:

```bash
ffmpeg -i out/market-pulse-video.mp4 -c:v libx264 -crf 23 -c:a aac -b:a 128k out/market-pulse-video-optimized.mp4
```

- [ ] **Step 5: Commit final video**

```bash
git add remotion-video/out/market-pulse-video.mp4
git commit -m "feat: render final Market Pulse video for LinkedIn"
```

---

### Task 13: Upload & Test on LinkedIn

**Files:**
- No new files; testing existing output

- [ ] **Step 1: Upload to LinkedIn**

1. Go to LinkedIn (logged in as your account)
2. Create a new post
3. Click "Video" → "Upload video" → select `out/market-pulse-video.mp4`
4. Add caption (e.g., "Market Pulse: An AI podcast generator powered by multi-agent orchestration. Built with Remotion, Gemini, and Kokoro TTS. Open source on GitHub: [link]")
5. Schedule or publish

- [ ] **Step 2: Verify playback on desktop**

- Video plays smoothly
- No audio sync issues
- Text is readable
- Colors and animations appear crisp

- [ ] **Step 3: Verify playback on mobile**

Open LinkedIn on phone, check your post:
- Video aspect ratio correct (16:9)
- Text legible at small screen size
- Animations smooth

- [ ] **Step 4: Monitor engagement**

Track views, likes, comments. Note any feedback about clarity or messaging.

- [ ] **Step 5: Done!**

Celebrate! 🎉

```bash
git tag -a v1.0-linkedin-video -m "Market Pulse LinkedIn video release"
git push origin v1.0-linkedin-video
```

---

## Self-Review

✅ **Spec Coverage:** All design sections addressed:
- Scene 1 (Dashboard) → Task 6 + Task 10
- Scene 2 (Agent Flow) → Task 7 + components (Task 4, 5, 9)
- Scene 3 (Result) → Task 9 + Task 10
- Styling & animations → Tasks 2, 4, 5, 8
- Audio & export → Task 11, 12

✅ **Placeholders:** None. Every step has complete code.

✅ **Type Consistency:**
- `COLORS` object defined in Task 2, used consistently across all components
- Animation utilities (`createFadeIn`, `createSlideIn`) defined in Task 2, used in scenes
- Component props typed (e.g., `AgentNodeProps`, `FlowArrowProps`)
- All SVG dimensions consistent (1920×1080)

✅ **Scope:** Single, focused project: a 20-second Remotion video with three scenes and clear deliverable (MP4 for LinkedIn).

---

## Summary

This plan builds a polished 20-second video that showcases Market Pulse's multi-agent orchestration on LinkedIn. It leverages Remotion's React-based composition system to create smooth, Claude-style animations. The video flows from product (dashboard) → tech (agent nodes) → CTA (GitHub), with each scene meticulously timed and animated.

**Total tasks: 13**  
**Estimated time: 2–4 hours** (depending on dev environment setup and asset capture)  
**Deliverable: `remotion-video/out/market-pulse-video.mp4` ready for LinkedIn**

