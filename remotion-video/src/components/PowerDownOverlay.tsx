import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { COLORS } from '../styles/colors';

interface PowerDownOverlayProps {
  width: number;
  height: number;
  startFrame: number;
}

export const PowerDownOverlay: React.FC<PowerDownOverlayProps> = ({
  width,
  height,
  startFrame,
}) => {
  const frame = useCurrentFrame();

  // Dark overlay opacity
  const overlayOpacity = interpolate(frame, [startFrame, startFrame + 120], [0, 0.7], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Logo fade in
  const logoFadeProgress = interpolate(frame, [startFrame + 120, startFrame + 180], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Logo scale
  const logoScale = interpolate(logoFadeProgress, [0, 1], [0.8, 1]);

  // Tagline fade in (staggered)
  const taglineFadeProgress = interpolate(frame, [startFrame + 150, startFrame + 210], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {/* Dark overlay */}
      <rect
        width={width}
        height={height}
        fill={COLORS.black}
        opacity={overlayOpacity}
      />

      {/* Logo text */}
      <g
        transform={`translate(${width / 2}, ${height / 2 - 40})`}
        opacity={logoFadeProgress}
        style={{
          transform: `translate(${width / 2}px, ${height / 2 - 40}px) scale(${logoScale})`,
          transformOrigin: '0 0',
          transition: 'all 0.3s ease-out',
        } as any}
      >
        <text
          x={0}
          y={0}
          textAnchor="middle"
          fontSize={72}
          fontWeight={700}
          fill={COLORS.accent}
          style={{ fontFamily: 'Inter, system-ui, sans-serif' } as any}
        >
          Market Pulse
        </text>
      </g>

      {/* Tagline text */}
      <text
        x={width / 2}
        y={height / 2 + 40}
        textAnchor="middle"
        fontSize={24}
        fill={COLORS.white}
        opacity={taglineFadeProgress}
        style={{ fontFamily: 'Inter, system-ui, sans-serif' } as any}
      >
        Multi-Agent AI Podcast Generator
      </text>
    </svg>
  );
};
