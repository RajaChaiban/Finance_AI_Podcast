#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
import io

# Fix Unicode output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

video_dir = Path("remotion-video/out")
video1 = video_dir / "Dashboard — Market Pulse and 1 more page - Personal - Microsoft​ Edge 2026-04-23 20-49-00.mp4"
video2 = video_dir / "Dashboard_edited.mp4"
output = video_dir / "combined_with_transition.mp4"

print("Combining videos with crossfade transition...")

# FFmpeg filter for crossfade with 0.5s overlap
subprocess.run([
    "ffmpeg",
    "-i", str(video1),
    "-i", str(video2),
    "-filter_complex",
    (
        "[0:v]fade=t=out:st=9.5:d=0.5[v0];"
        "[1:v]fade=t=in:st=0:d=0.5[v1];"
        "[v0][v1]xfade=transition=fade:duration=0.5:offset=9.5[vout];"
        "[0:a][1:a]acrossfade=d=0.5[aout]"
    ),
    "-map", "[vout]",
    "-map", "[aout]",
    "-c:v", "libx264", "-preset", "fast",
    "-c:a", "aac",
    str(output)
], check=True)

print("Done! Output: combined_with_transition.mp4")
