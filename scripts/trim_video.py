#!/usr/bin/env python3
import subprocess
from pathlib import Path

video_dir = Path("remotion-video/out")
video_file = video_dir / "Dashboard_edited.mp4"
temp_file = video_dir / "_trim_temp.mp4"

print("Trimming to first 12 seconds...")
subprocess.run([
    "ffmpeg", "-i", str(video_file),
    "-t", "12",
    "-c", "copy",
    str(temp_file)
], check=True)

# Replace original
temp_file.replace(video_file)
print(f"✓ Done! Overwrote {video_file.name}")
