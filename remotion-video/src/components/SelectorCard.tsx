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
