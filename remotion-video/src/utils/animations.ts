import { interpolate, Easing } from 'remotion';

export const easeOutCubic = (t: number): number => {
  return 1 - Math.pow(1 - t, 3);
};

export const easeInOutQuad = (t: number): number => {
  return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
};

export const createFadeIn = (frame: number, startFrame: number, durationFrames: number): number => {
  return interpolate(frame, [startFrame, startFrame + durationFrames], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
};

export const createSlideIn = (frame: number, startFrame: number, durationFrames: number, fromX: number = -50): number => {
  return interpolate(frame, [startFrame, startFrame + durationFrames], [fromX, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
};

export const createScale = (frame: number, startFrame: number, durationFrames: number, fromScale: number = 0.9): number => {
  return interpolate(frame, [startFrame, startFrame + durationFrames], [fromScale, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
};
