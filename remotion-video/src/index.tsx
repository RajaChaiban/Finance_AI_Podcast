import React from 'react';
import { Composition, registerRoot, Audio } from 'remotion';
import { DashboardScene } from './scenes/DashboardScene';
import { ResultScene } from './scenes/ResultScene';
import podcastAudio from '../public/podcast-25s.mp3';

const Root: React.FC = () => {
  const width = 1920;
  const height = 1080;
  const fps = 30;
  const durationInSeconds = 30; // 25s podcast + 5s closing animation
  const durationInFrames = durationInSeconds * fps;

  return (
    <Composition
      id="MarketPulseVideo"
      component={() => (
        <div style={{ width, height, position: 'relative', overflow: 'hidden', backgroundColor: '#000' }}>
          <Audio src={podcastAudio} startFrom={0} />
          <DashboardScene width={width} height={height} />
          <ResultScene width={width} height={height} />
        </div>
      )}
      durationInFrames={durationInFrames}
      fps={fps}
      width={width}
      height={height}
    />
  );
};

registerRoot(Root);
