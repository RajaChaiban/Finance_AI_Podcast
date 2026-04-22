import React from 'react';
import { useCurrentFrame } from 'remotion';
import { COLORS } from '../styles/colors';
import { AgentNode } from '../components/AgentNode';
import { FlowArrow } from '../components/FlowArrow';
import { DataIcon, BrainIcon, MicIcon } from '../assets/icons';

interface AgentFlowSceneProps {
  width: number;
  height: number;
}

export const AgentFlowScene: React.FC<AgentFlowSceneProps> = ({ width, height }) => {
  const frame = useCurrentFrame();

  // Scene timing: starts at frame 180 (6 sec * 30 fps)
  const sceneFrame = frame - 180;

  const centerY = height / 2;
  const nodeSpacing = (width - 200) / 2;
  const node1X = 160;
  const node2X = node1X + nodeSpacing;
  const node3X = node2X + nodeSpacing;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {/* Background (subtle gradient or solid) */}
      <defs>
        <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={COLORS.gray50} />
          <stop offset="100%" stopColor={COLORS.white} />
        </linearGradient>
      </defs>
      <rect width={width} height={height} fill="url(#bgGradient)" />

      {/* Agent nodes */}
      <AgentNode
        icon={<DataIcon size={48} color={COLORS.accent} />}
        label="Search Live Data"
        x={node1X}
        y={centerY}
        appearFrame={sceneFrame + 0}
      />

      <AgentNode
        icon={<BrainIcon size={48} color={COLORS.accent} />}
        label="Generate Script"
        x={node2X}
        y={centerY}
        appearFrame={sceneFrame + 15}
      />

      <AgentNode
        icon={<MicIcon size={48} color={COLORS.accent} />}
        label="Kokoro TTS"
        x={node3X}
        y={centerY}
        appearFrame={sceneFrame + 30}
      />

      {/* Flow arrows */}
      <FlowArrow
        fromX={node1X + 50}
        fromY={centerY}
        toX={node2X - 50}
        toY={centerY}
        startFrame={sceneFrame + 60}
        durationFrames={60}
      />

      <FlowArrow
        fromX={node2X + 50}
        fromY={centerY}
        toX={node3X - 50}
        toY={centerY}
        startFrame={sceneFrame + 120}
        durationFrames={60}
      />

      {/* Optional: Title text above nodes */}
      <text
        x={width / 2}
        y="80"
        textAnchor="middle"
        fontSize="32"
        fontWeight="600"
        fill={COLORS.text}
        style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
        opacity={Math.max(0, Math.min(1, (sceneFrame - 0) / 30))}
      >
        Multi-Agent Orchestration
      </text>
    </svg>
  );
};
