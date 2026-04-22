import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { COLORS } from '../styles/colors';
import { Waveform } from '../components/Waveform';
import dashboardImage from '../../public/dashboard.png';

interface DashboardSceneProps {
  width: number;
  height: number;
}

export const DashboardScene: React.FC<DashboardSceneProps> = ({ width, height }) => {
  const frame = useCurrentFrame();

  // Fade in dashboard (0-30 frames)
  const dashboardOpacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  // Player overlay fade in (30-60 frames)
  const playerOpacity = interpolate(frame, [30, 60], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  // Waveform progress (60-300 frames = 2-10 seconds at 30fps, covers the 10s podcast intro)
  const waveProgress = interpolate(frame, [60, 300], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {/* Background */}
      <rect width={width} height={height} fill={COLORS.background} />

      {/* Dashboard screenshot - stays visible throughout */}
      <image
        href={dashboardImage}
        x="0"
        y="0"
        width={width}
        height={height}
        opacity={dashboardOpacity}
      />

      {/* Dark overlay for player readability */}
      <rect
        width={width}
        height={height}
        fill={COLORS.black}
        opacity={playerOpacity * 0.3}
      />

      {/* Podcast player card - centered, appears after intro */}
      <g opacity={playerOpacity}>
        {/* Card background */}
        <rect
          x={width / 2 - 400}
          y={height / 2 - 200}
          width="800"
          height="400"
          fill={COLORS.gray900}
          rx="20"
          style={{
            boxShadow: `0 20px 60px rgba(0,0,0,0.5)`,
          }}
        />

        {/* Border accent */}
        <rect
          x={width / 2 - 400}
          y={height / 2 - 200}
          width="800"
          height="400"
          fill="none"
          stroke={COLORS.accent}
          strokeWidth="2"
          rx="20"
          opacity="0.3"
        />

        {/* Now Playing label */}
        <text
          x={width / 2}
          y={height / 2 - 130}
          textAnchor="middle"
          fontSize="14"
          fill={COLORS.accent}
          fontWeight="600"
          style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
        >
          NOW PLAYING
        </text>

        {/* Episode title */}
        <text
          x={width / 2}
          y={height / 2 - 80}
          textAnchor="middle"
          fontSize="32"
          fontWeight="700"
          fill={COLORS.white}
          style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
        >
          Market Pulse
        </text>

        {/* Waveform visualization */}
        <g transform={`translate(${width / 2 - 320}, ${height / 2})`}>
          <Waveform progress={waveProgress} bars={32} barWidth={12} gap={4} color={COLORS.accent} />
        </g>

        {/* Play indicator dot */}
        <circle
          cx={width / 2 - 350}
          cy={height / 2 + 100}
          r="6"
          fill={COLORS.accent}
          opacity={interpolate(frame, [60, 90], [0, 1], { extrapolateRight: 'clamp' })}
        />

        {/* Playing text */}
        <text
          x={width / 2 - 320}
          y={height / 2 + 110}
          fontSize="14"
          fill={COLORS.gray300}
          style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
        >
          Playing...
        </text>

        {/* Market Pulse subtitle */}
        <text
          x={width / 2}
          y={height / 2 + 150}
          textAnchor="middle"
          fontSize="16"
          fill={COLORS.gray400}
          style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
        >
          AI-powered market insights, daily.
        </text>
      </g>
    </svg>
  );
};
