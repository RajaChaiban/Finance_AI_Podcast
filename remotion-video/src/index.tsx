import React from 'react';
import { Composition, registerRoot } from 'remotion';
import { VideoCompositionScene } from './scenes/VideoCompositionScene';

const Root: React.FC = () => {
  const width = 1920;
  const height = 1080;
  const fps = 30;
  const durationInSeconds = 20;
  const durationInFrames = durationInSeconds * fps;

  return (
    <Composition
      id="VideoComposition"
      component={() => (
        <div style={{ width, height, position: 'relative', overflow: 'hidden', backgroundColor: '#000' }}>
          <VideoCompositionScene width={width} height={height} />
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
