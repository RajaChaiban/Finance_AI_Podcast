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
