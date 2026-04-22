import React from 'react';

interface IconProps {
  size?: number;
  color?: string;
}

export const DataIcon: React.FC<IconProps> = ({ size = 48, color = '#FF6B35' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="24" cy="24" r="20" stroke={color} strokeWidth="2"/>
    <path d="M12 24h24M16 18v12M24 16v16M32 20v8" stroke={color} strokeWidth="2" strokeLinecap="round"/>
  </svg>
);

export const BrainIcon: React.FC<IconProps> = ({ size = 48, color = '#FF6B35' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="24" cy="24" r="20" stroke={color} strokeWidth="2"/>
    <path d="M16 24c0-4.42 3-8 8-8s8 3.58 8 8-3 8-8 8-8-3.58-8-8Z" stroke={color} strokeWidth="2"/>
    <circle cx="24" cy="24" r="2" fill={color}/>
  </svg>
);

export const MicIcon: React.FC<IconProps> = ({ size = 48, color = '#FF6B35' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="24" cy="24" r="20" stroke={color} strokeWidth="2"/>
    <path d="M24 14v12M18 26c0 3.31 2.69 6 6 6s6-2.69 6-6" stroke={color} strokeWidth="2" strokeLinecap="round"/>
    <path d="M24 32v4" stroke={color} strokeWidth="2" strokeLinecap="round"/>
  </svg>
);
