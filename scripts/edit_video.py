#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

# Fix Unicode output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

video_dir = Path("remotion-video/out")
input_file = video_dir / "Dashboard — Market Pulse and 1 more page - Personal - Microsoft​ Edge 2026-04-23 20-32-04.mp4"
output_file = video_dir / "Dashboard_edited.mp4"

try:
    print("Trimming to 24 seconds and speeding up 2x...")
    subprocess.run([
        "ffmpeg", "-i", str(input_file),
        "-t", "24",
        "-vf", "setpts=PTS/2",
        "-af", "atempo=2.0",
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac",
        str(output_file)
    ], check=True)

    print(f"✓ Done! Output: {output_file.name}")
    print(f"  Original length: 24 seconds at 2x speed = 12 seconds final duration")

finally:
    pass
