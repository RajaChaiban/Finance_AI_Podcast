import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { COLORS } from '../styles/colors';

interface WaveformProps {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  bars?: number;
  barWidth?: number;
  gap?: number;
  startFrame?: number;
  progress?: number;
  color?: string;
}

export const Waveform: React.FC<WaveformProps> = ({
  x = 0,
  y = 0,
  width = 400,
  height = 60,
  bars = 24,
  barWidth: customBarWidth,
  gap = 0,
  startFrame = 0,
  progress: externalProgress,
  color = COLORS.accent,
}) => {
  const frame = useCurrentFrame();
  const calculatedProgress = externalProgress !== undefined ? externalProgress : interpolate(frame, [startFrame, startFrame + 20], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const bw = customBarWidth || (width / bars) - gap;

  return (
    <g transform={`translate(${x}, ${y})`}>
      {Array.from({ length: bars }).map((_, i) => {
        const baseHeight = height * (0.2 + 0.8 * Math.sin((i / bars) * Math.PI * 2));
        const animatedHeight = baseHeight * (0.5 + 0.5 * Math.sin(frame * 0.1 + i * 0.3));
        const displayHeight = animatedHeight * calculatedProgress;

        return (
          <rect
            key={i}
            x={i * (bw + gap)}
            y={height / 2 - displayHeight / 2}
            width={bw}
            height={displayHeight}
            fill={color}
            rx="2"
            opacity={calculatedProgress}
          />
        );
      })}
    </g>
  );
};
