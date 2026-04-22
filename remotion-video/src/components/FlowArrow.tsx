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
