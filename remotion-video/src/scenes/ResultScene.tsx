import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { COLORS } from '../styles/colors';
import { Waveform } from '../components/Waveform';

interface ResultSceneProps {
  width: number;
  height: number;
  githubUrl?: string;
}

export const ResultScene: React.FC<ResultSceneProps> = ({
  width,
  height,
  githubUrl = 'https://github.com/RajaChaiban/Finance_AI_Podcast',
}) => {
  const frame = useCurrentFrame();

  // Scene starts at frame 450 (15 sec * 30 fps)
  const sceneFrame = frame - 450;

  // Player emphasis fade in
  const playerOpacity = interpolate(sceneFrame, [0, 20], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  // Title fade in
  const titleOpacity = interpolate(sceneFrame, [30, 60], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Subtitle fade in
  const subtitleOpacity = interpolate(sceneFrame, [60, 90], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // CTA fade in
  const ctaOpacity = interpolate(sceneFrame, [100, 130], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const centerX = width / 2;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {/* Background */}
      <rect width={width} height={height} fill={COLORS.background} />

      {/* Podcast player card */}
      <g opacity={playerOpacity}>
        {/* Card background */}
        <rect
          x={centerX - 300}
          y={height / 2 - 120}
          width="600"
          height="240"
          fill={COLORS.gray50}
          stroke={COLORS.border}
          strokeWidth="1"
          rx="16"
        />

        {/* "Now Playing" label */}
        <text
          x={centerX - 280}
          y={height / 2 - 90}
          fontSize="12"
          fontWeight="600"
          fill={COLORS.textMuted}
          style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
          textTransform="uppercase"
        >
          Now Playing
        </text>

        {/* Episode title */}
        <text
          x={centerX - 280}
          y={height / 2 - 60}
          fontSize="20"
          fontWeight="700"
          fill={COLORS.text}
          style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
        >
          Market Pulse Daily Edition
        </text>

        {/* Waveform inside player */}
        <Waveform
          x={centerX - 280}
          y={height / 2 - 20}
          width="560"
          height="40"
          bars={20}
          startFrame={sceneFrame + 50}
        />

        {/* Play button */}
        <circle
          cx={centerX}
          cy={height / 2 + 100}
          r="28"
          fill={COLORS.accent}
          style={{ cursor: 'pointer' }}
        />
        <polygon
          points={`${centerX - 8},${height / 2 + 90} ${centerX - 8},${height / 2 + 110} ${centerX + 12},${height / 2 + 100}`}
          fill={COLORS.white}
        />
      </g>

      {/* Brand & Messaging */}
      <text
        x={centerX}
        y={height / 2 + 200}
        textAnchor="middle"
        fontSize="36"
        fontWeight="700"
        fill={COLORS.text}
        style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
        opacity={titleOpacity}
      >
        Market Pulse
      </text>

      <text
        x={centerX}
        y={height / 2 + 250}
        textAnchor="middle"
        fontSize="20"
        fill={COLORS.textMuted}
        style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
        opacity={subtitleOpacity}
      >
        Multi-Agent AI Podcast Generator
      </text>

      {/* GitHub CTA */}
      <g opacity={ctaOpacity}>
        {/* Button background */}
        <rect
          x={centerX - 200}
          y={height / 2 + 290}
          width="400"
          height="60"
          fill={COLORS.accent}
          rx="8"
        />

        {/* Button text */}
        <text
          x={centerX}
          y={height / 2 + 328}
          textAnchor="middle"
          fontSize="18"
          fontWeight="600"
          fill={COLORS.white}
          style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
        >
          Star on GitHub
        </text>

        {/* URL below button */}
        <text
          x={centerX}
          y={height / 2 + 370}
          textAnchor="middle"
          fontSize="14"
          fill={COLORS.textMuted}
          style={{ fontFamily: 'monospace' }}
        >
          {githubUrl.replace('https://', '')}
        </text>
      </g>
    </svg>
  );
};
