import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { COLORS } from '../styles/colors';

interface AgentNodeProps {
  icon: React.ReactNode;
  label: string;
  x: number;
  y: number;
  appearFrame: number;
  glowIntensity?: number;
}

export const AgentNode: React.FC<AgentNodeProps> = ({
  icon,
  label,
  x,
  y,
  appearFrame,
  glowIntensity = 1,
}) => {
  const frame = useCurrentFrame();

  // Fade in animation
  const opacity = interpolate(frame, [appearFrame, appearFrame + 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  // Subtle pulsing glow
  const glowOpacity = 0.3 + 0.2 * Math.sin((frame * 0.05) + (appearFrame * 0.1));

  return (
    <g opacity={opacity} transform={`translate(${x}, ${y})`}>
      {/* Glow effect */}
      <circle
        cx="0"
        cy="0"
        r="52"
        fill={COLORS.accent}
        opacity={glowOpacity * glowIntensity * 0.2}
        style={{ filter: 'blur(8px)' }}
      />

      {/* Node circle */}
      <circle
        cx="0"
        cy="0"
        r="48"
        fill="none"
        stroke={COLORS.accent}
        strokeWidth="2"
        style={{ filter: `drop-shadow(0 0 8px ${COLORS.accent}${Math.floor(glowOpacity * 255).toString(16).padStart(2, '0')})` }}
      />

      {/* Icon center */}
      <g transform="translate(-24, -24)">{icon}</g>

      {/* Label below node */}
      <text
        x="0"
        y="70"
        textAnchor="middle"
        fontSize="16"
        fontWeight="600"
        fill={COLORS.text}
        style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
      >
        {label}
      </text>
    </g>
  );
};
