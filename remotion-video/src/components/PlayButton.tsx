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
        } as any}
      />

      {/* Play icon (triangle) */}
      <polygon
        points={`${-radius * 0.25},${-radius * 0.4} ${-radius * 0.25},${radius * 0.4} ${radius * 0.4},0`}
        fill={COLORS.white}
        style={{
          transform: `scale(${scaleAmount})`,
          transformOrigin: '0 0',
        } as any}
      />
    </g>
  );
};
