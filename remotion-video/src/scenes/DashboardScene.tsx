import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { COLORS } from '../styles/colors';

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

  // Hero text fade in and slide (30-90 frames)
  const heroOpacity = interpolate(frame, [30, 60], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  const heroY = interpolate(frame, [30, 60], [20, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  // Dashboard blur start (at frame 180, prepare for transition)
  const dashboardBlur = interpolate(frame, [180, 195], [0, 8], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {/* Background */}
      <rect width={width} height={height} fill={COLORS.background} />

      {/* Dashboard screenshot */}
      <image
        href="dashboard.png"
        x="0"
        y="0"
        width={width}
        height={height}
        opacity={dashboardOpacity}
        style={{
          filter: `blur(${dashboardBlur}px)`,
        }}
      />

      {/* Dark overlay for text readability */}
      <rect
        width={width}
        height={height}
        fill={COLORS.black}
        opacity={heroOpacity * 0.2}
      />

      {/* Hero text container */}
      <g opacity={heroOpacity} transform={`translate(0, ${heroY})`}>
        {/* Text background (optional subtle box) */}
        <rect
          x="80"
          y="200"
          width="1760"
          height="300"
          fill="none"
          rx="12"
        />

        {/* Main headline */}
        <text
          x={width / 2}
          y="280"
          textAnchor="middle"
          fontSize="56"
          fontWeight="700"
          fill={COLORS.white}
          style={{
            fontFamily: 'Inter, system-ui, sans-serif',
            textShadow: `0 2px 16px rgba(0,0,0,0.5)`,
          }}
        >
          Your daily market podcast,
        </text>

        <text
          x={width / 2}
          y="360"
          textAnchor="middle"
          fontSize="56"
          fontWeight="700"
          fill={COLORS.white}
          style={{
            fontFamily: 'Inter, system-ui, sans-serif',
            textShadow: `0 2px 16px rgba(0,0,0,0.5)`,
          }}
        >
          ready each morning.
        </text>

        {/* Subheader */}
        <text
          x={width / 2}
          y="430"
          textAnchor="middle"
          fontSize="18"
          fill={COLORS.gray200}
          style={{
            fontFamily: 'Inter, system-ui, sans-serif',
            textShadow: `0 1px 8px rgba(0,0,0,0.5)`,
          }}
        >
          Powered by multi-agent AI orchestration.
        </text>
      </g>
    </svg>
  );
};
