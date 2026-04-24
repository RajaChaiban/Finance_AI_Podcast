#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

video_dir = Path("remotion-video/out")
video1 = video_dir / "Dashboard — Market Pulse and 1 more page - Personal - Microsoft​ Edge 2026-04-23 20-49-00.mp4"
video2 = video_dir / "Dashboard_edited.mp4"
output = video_dir / "combined_with_transition.mp4"

print("Fixing video - simple concatenation without transition...")

# Simple concat without complex transitions
subprocess.run([
    "ffmpeg",
    "-i", str(video1),
    "-i", str(video2),
    "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1",
    "-c:v", "libx264", "-preset", "fast",
    "-c:a", "aac",
    "-y",
    str(output)
], check=True)

print(f"Done! Fixed video: {output.name}")
