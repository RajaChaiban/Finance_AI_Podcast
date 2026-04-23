import React from 'react';
import { Composition, registerRoot, Audio } from 'remotion';
import { InteractiveDemoScene } from './scenes/InteractiveDemoScene';
import demoMusic from '../public/demo-music.mp3';

const Root: React.FC = () => {
  const width = 1920;
  const height = 1080;
  const fps = 30;
  const durationInSeconds = 30;
  const durationInFrames = durationInSeconds * fps;

  return (
    <Composition
      id="InteractiveDemoVideo"
      component={() => (
        <div style={{ width, height, position: 'relative', overflow: 'hidden', backgroundColor: '#000' }}>
          <Audio src={demoMusic} startFrom={0} />
          <InteractiveDemoScene width={width} height={height} />
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
