#!/usr/bin/env python3
"""
Convert podcast MP3 to MP4 with logo overlay.
One-time conversion: 2026-04-25-market-pulse.mp3 -> 2026-04-25-market-pulse.mp4
"""

import subprocess
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw

def create_background_image(width: int, height: int, color: tuple, output_path: str):
    """Create a solid color background image."""
    img = Image.new('RGB', (width, height), color)
    img.save(output_path)
    print(f"[OK] Created background image: {output_path}")

def overlay_logo_on_background(
    bg_path: str,
    logo_path: str,
    output_path: str,
    width: int = 1080,
    height: int = 1080
):
    """Overlay logo image centered on background."""
    bg = Image.open(bg_path).convert('RGB')

    # Open and resize logo to fit (max 60% of frame width)
    logo = Image.open(logo_path).convert('RGBA')
    max_logo_width = int(width * 0.6)

    # Maintain aspect ratio
    aspect_ratio = logo.width / logo.height
    logo_width = max_logo_width
    logo_height = int(logo_width / aspect_ratio)
    logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

    # Center logo on background
    x = (width - logo_width) // 2
    y = (height - logo_height) // 2

    # Paste logo (with alpha channel)
    bg.paste(logo, (x, y), logo)
    bg.save(output_path)
    print(f"[OK] Overlaid logo on background: {output_path}")

def create_video_from_audio(
    audio_path: str,
    image_path: str,
    output_path: str,
    duration: float = None
):
    """
    Use FFmpeg to create MP4 from audio + static image.

    Args:
        audio_path: Path to input MP3
        image_path: Path to image (logo + background)
        output_path: Path to output MP4
        duration: Video duration in seconds. If None, uses audio duration.
    """
    # Build FFmpeg command
    # -loop 1: loop the image
    # -i: input image
    # -i: input audio
    # -c:v libx264: video codec
    # -c:a aac: audio codec
    # -shortest: match duration to shortest input (audio in this case)
    # -pix_fmt yuv420p: ensure compatibility

    cmd = [
        'ffmpeg',
        '-loop', '1',
        '-i', image_path,
        '-i', audio_path,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-shortest',
        '-pix_fmt', 'yuv420p',
        '-y',  # Overwrite output file
        output_path
    ]

    print(f"Running FFmpeg: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[ERROR] FFmpeg failed: {result.stderr}")
        return False

    print(f"[OK] Video created: {output_path}")
    return True

def main():
    # Configuration
    MP3_FILE = "remotion-video/out/2026-04-25-market-pulse.mp3"
    LOGO_FILE = "remotion-video/public/dashboard.png"
    OUTPUT_VIDEO = "remotion-video/out/2026-04-25-market-pulse.mp4"

    # Temporary files
    BG_IMAGE = "/tmp/bg.png"
    FINAL_IMAGE = "/tmp/final.png"

    # Video dimensions
    WIDTH = 1080
    HEIGHT = 1080
    BG_COLOR = (20, 20, 30)  # Dark blue/black (RGB)

    # Validate inputs
    if not os.path.exists(MP3_FILE):
        print(f"[ERROR] MP3 file not found: {MP3_FILE}")
        sys.exit(1)

    if not os.path.exists(LOGO_FILE):
        print(f"[ERROR] Logo file not found: {LOGO_FILE}")
        print(f"   Update LOGO_FILE in the script to point to your logo.")
        sys.exit(1)

    print(f"[INFO] Converting {MP3_FILE} to {OUTPUT_VIDEO}")
    print(f"   Logo: {LOGO_FILE}")
    print(f"   Format: {WIDTH}x{HEIGHT} (square)")

    try:
        # Step 1: Create solid background
        print("\n[1/3] Creating background...")
        create_background_image(WIDTH, HEIGHT, BG_COLOR, BG_IMAGE)

        # Step 2: Overlay logo
        print("\n[2/3] Overlaying logo...")
        overlay_logo_on_background(BG_IMAGE, LOGO_FILE, FINAL_IMAGE, WIDTH, HEIGHT)

        # Step 3: Create video
        print("\n[3/3] Creating video from audio + image...")
        success = create_video_from_audio(MP3_FILE, FINAL_IMAGE, OUTPUT_VIDEO)

        if success:
            # Cleanup temp files
            os.remove(BG_IMAGE)
            os.remove(FINAL_IMAGE)
            print(f"\n[SUCCESS] Conversion complete!")
            print(f"   Output: {OUTPUT_VIDEO}")
            return 0
        else:
            print(f"\n[ERROR] Conversion failed!")
            return 1

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
