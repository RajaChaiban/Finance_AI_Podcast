import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { PodcastCard } from './PodcastCard';

interface LibraryGridProps {
  x: number;
  y: number;
  startFrame: number;
  selectFrame: number;
}

export const LibraryGrid: React.FC<LibraryGridProps> = ({
  x,
  y,
  startFrame,
  selectFrame,
}) => {
  const frame = useCurrentFrame();

  // Grid fade in
  const fadeInProgress = interpolate(frame, [startFrame, startFrame + 20], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Top card expansion progress
  const expandProgress = interpolate(frame, [selectFrame, selectFrame + 40], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  const mockPodcasts = [
    { id: 0, title: 'Market Pulse Daily: Fed Decision Impact', duration: '12:34', date: 'Today' },
    { id: 1, title: 'Tech Stocks Rally on AI Gains', duration: '10:15', date: 'Yesterday' },
    { id: 2, title: 'Crypto Markets Stabilize', duration: '9:42', date: '2 days ago' },
    { id: 3, title: 'Economic Data Surprise', duration: '11:20', date: '3 days ago' },
    { id: 4, title: 'Banking Sector Update', duration: '8:50', date: '4 days ago' },
    { id: 5, title: 'Global Market Overview', duration: '13:05', date: '5 days ago' },
  ];

  return (
    <g opacity={fadeInProgress}>
      {mockPodcasts.map((podcast, index) => (
        <PodcastCard
          key={podcast.id}
          x={x + (index % 3) * 180}
          y={y + Math.floor(index / 3) * 140}
          title={podcast.title}
          duration={podcast.duration}
          date={podcast.date}
          staggerIndex={index}
          startFrame={startFrame}
          isSelected={index === 0}
          expandProgress={index === 0 ? expandProgress : 0}
        />
      ))}
    </g>
  );
};
