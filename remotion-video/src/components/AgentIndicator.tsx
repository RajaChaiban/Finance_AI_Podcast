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
