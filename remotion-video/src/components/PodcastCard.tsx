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
        } as any}
      >
        {title.substring(0, 20)}
      </text>

      {/* Metadata */}
      <text
        x={8}
        y={85}
        fontSize={9}
        fill={COLORS.textMuted}
        style={{ fontFamily: 'Inter, system-ui, sans-serif' } as any}
      >
        {duration}
      </text>

      <text
        x={8}
        y={100}
        fontSize={9}
        fill={COLORS.textMuted}
        style={{ fontFamily: 'Inter, system-ui, sans-serif' } as any}
      >
        {date}
      </text>
    </g>
  );
};
