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
