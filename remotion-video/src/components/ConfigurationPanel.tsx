import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { SelectorCard } from './SelectorCard';
import { COLORS } from '../styles/colors';

interface ConfigurationPanelProps {
  x: number;
  y: number;
  startFrame: number;
  selectFrames: [number, number, number];
}

export const ConfigurationPanel: React.FC<ConfigurationPanelProps> = ({
  x,
  y,
  startFrame,
  selectFrames,
}) => {
  const frame = useCurrentFrame();

  // Slide in from right
  const slideInProgress = interpolate(frame, [startFrame, startFrame + 25], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const displayX = interpolate(slideInProgress, [0, 1], [x + 300, x]);

  const topicOptions = ['Markets', 'Tech', 'Economics', 'Crypto'];
  const timeOptions = ['Daily', 'Weekly', 'Monthly'];
  const styleOptions = ['Formal', 'Casual', 'Mixed'];

  return (
    <g transform={`translate(${displayX}, ${y})`}>
      {/* Panel background */}
      <rect
        x={0}
        y={0}
        width={320}
        height={200}
        fill={COLORS.gray50}
        rx={12}
        stroke={COLORS.border}
        strokeWidth={1}
      />

      {/* Selector cards */}
      <SelectorCard
        x={12}
        y={12}
        width={296}
        height={56}
        label="Topic"
        options={topicOptions}
        selectedIndex={0}
        startFrame={startFrame}
        selectFrame={selectFrames[0]}
        staggerDelay={0}
      />

      <SelectorCard
        x={12}
        y={76}
        width={296}
        height={56}
        label="Time Frame"
        options={timeOptions}
        selectedIndex={0}
        startFrame={startFrame}
        selectFrame={selectFrames[1]}
        staggerDelay={10}
      />

      <SelectorCard
        x={12}
        y={140}
        width={296}
        height={56}
        label="Style"
        options={styleOptions}
        selectedIndex={0}
        startFrame={startFrame}
        selectFrame={selectFrames[2]}
        staggerDelay={20}
      />
    </g>
  );
};
