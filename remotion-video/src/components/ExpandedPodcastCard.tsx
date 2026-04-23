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
      style={{ transformOrigin: '80px 60px' } as any}
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
        style={{ fontFamily: 'Inter, system-ui, sans-serif' } as any}
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
