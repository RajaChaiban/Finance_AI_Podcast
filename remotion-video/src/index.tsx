import React from 'react';
import { Composition, registerRoot } from 'remotion';
import { DashboardScene } from './scenes/DashboardScene';
import { AgentFlowScene } from './scenes/AgentFlowScene';
import { ResultScene } from './scenes/ResultScene';

const Root: React.FC = () => {
  const width = 1920;
  const height = 1080;
  const fps = 30;
  const durationInSeconds = 20;
  const durationInFrames = durationInSeconds * fps;

  return (
    <Composition
      id="MarketPulseVideo"
      component={() => (
        <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
          <DashboardScene width={width} height={height} />
          <AgentFlowScene width={width} height={height} />
          <ResultScene width={width} height={height} />
        </svg>
      )}
      durationInFrames={durationInFrames}
      fps={fps}
      width={width}
      height={height}
    />
  );
};

registerRoot(Root);
