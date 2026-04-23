import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { Video, Audio } from 'remotion';

interface VideoCompositionSceneProps {
  width: number;
  height: number;
}

export const VideoCompositionScene: React.FC<VideoCompositionSceneProps> = ({
  width,
  height,
}) => {
  const frame = useCurrentFrame();

  // Generate video: frames 0-300 (0:00-0:10 at 30fps)
  // Dashboard video: frames 300-600 (0:10-0:20)
  // Fade transition: frames 270-330 (0:09-0:11)

  // Generate video opacity: 100% until frame 270, then fade to 0% by frame 300
  const generateOpacity = interpolate(frame, [0, 270, 300], [1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Dashboard video opacity: 0% until frame 270, then fade to 100% by frame 300
  const dashboardOpacity = interpolate(frame, [270, 300, 600], [0, 1, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // UI sounds volume: 100% until frame 270, then fade to 0% by frame 300
  const uiSoundsVolume = interpolate(frame, [0, 270, 300], [1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Podcast audio volume: 0% until frame 270, then fade to 100% by frame 300
  const podcastVolume = interpolate(frame, [270, 300, 600], [0, 1, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <>
      {/* Generate Video (0:00-0:10) */}
      <Video
        src={require('../../public/video/Generate — Market Pulse and 3 more pages - Personal - Microsoft​ Edge 2026-04-22 21-23-44.mp4')}
        style={{
          width,
          height,
          opacity: generateOpacity,
          position: 'absolute',
          top: 0,
          left: 0,
        }}
        muted
      />

      {/* Dashboard Video (0:10-0:20) - starts at frame 300 */}
      <Video
        src={require('../../public/video/Dashboard — Market Pulse and 3 more pages - Personal - Microsoft​ Edge 2026-04-22 21-30-51.mp4')}
        style={{
          width,
          height,
          opacity: dashboardOpacity,
          position: 'absolute',
          top: 0,
          left: 0,
        }}
        muted
      />

      {/* UI Sounds Audio (0:00-0:10, fade out at 0:09-0:10) */}
      <Audio
        src={require('../../public/ui-sounds.mp3')}
        volume={uiSoundsVolume}
        startFrom={0}
      />

      {/* Podcast Audio (0:10-0:20, fade in at 0:09-0:10) */}
      <Audio
        src={require('../../public/podcast-25s.mp3')}
        volume={podcastVolume}
        startFrom={0}
      />
    </>
  );
};
