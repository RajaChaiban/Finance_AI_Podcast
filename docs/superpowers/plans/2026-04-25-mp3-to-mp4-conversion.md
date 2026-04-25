# MP3→MP4 Podcast Video Conversion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert `remotion-video/out/2026-04-25-market-pulse.mp3` to MP4 with Market Pulse logo on solid background (1080x1080 square format).

**Architecture:** Single Python script (`convert_podcast_to_video.py`) that uses FFmpeg to generate a solid color frame, overlay logo image, merge with MP3 audio, and output MP4. No external dependencies beyond FFmpeg and Pillow.

**Tech Stack:** Python 3.x, FFmpeg, Pillow (PIL)

---

## File Structure

**Create:**
- `convert_podcast_to_video.py` — Main conversion script using FFmpeg CLI

**No modifications to existing files.**
**No tests required** (one-time conversion tool).

---

## Tasks

### Task 1: Verify FFmpeg Installation & Get Logo Path

**Files:**
- Reference: `convert_podcast_to_video.py` (will create)

- [ ] **Step 1: Check FFmpeg is installed**

Run: `ffmpeg -version`

Expected: Version output (e.g., `ffmpeg version 6.0...`)

If not installed: `brew install ffmpeg` (Mac) or `choco install ffmpeg` (Windows) or `apt-get install ffmpeg` (Linux)

- [ ] **Step 2: Identify logo file path**

You must provide the exact path to your Market Pulse logo file. It should be PNG, SVG, or JPG.

Expected: A path like `C:\Users\rajac\OneDrive\Desktop\Python\Finance_Podcast\assets\logo.png`

Store this for use in Task 2.

---

### Task 2: Create `convert_podcast_to_video.py`

**Files:**
- Create: `convert_podcast_to_video.py` (in project root)

- [ ] **Step 1: Write the conversion script**

Create file `convert_podcast_to_video.py` with the following content:

```python
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
    print(f"✓ Created background image: {output_path}")

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
    print(f"✓ Overlaid logo on background: {output_path}")

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
        print(f"❌ FFmpeg failed: {result.stderr}")
        return False
    
    print(f"✓ Video created: {output_path}")
    return True

def main():
    # Configuration
    MP3_FILE = "remotion-video/out/2026-04-25-market-pulse.mp3"
    LOGO_FILE = "assets/logo.png"  # CHANGE THIS TO YOUR LOGO PATH
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
        print(f"❌ MP3 file not found: {MP3_FILE}")
        sys.exit(1)
    
    if not os.path.exists(LOGO_FILE):
        print(f"❌ Logo file not found: {LOGO_FILE}")
        print(f"   Update LOGO_FILE in the script to point to your logo.")
        sys.exit(1)
    
    print(f"📝 Converting {MP3_FILE} to {OUTPUT_VIDEO}")
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
            print(f"\n✅ Conversion complete!")
            print(f"   Output: {OUTPUT_VIDEO}")
            return 0
        else:
            print(f"\n❌ Conversion failed!")
            return 1
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Update logo path in script**

Open `convert_podcast_to_video.py` and find this line:

```python
LOGO_FILE = "assets/logo.png"  # CHANGE THIS TO YOUR LOGO PATH
```

Replace `assets/logo.png` with the actual path to your Market Pulse logo file.

Example: `LOGO_FILE = "C:\\Users\\rajac\\Desktop\\market-pulse-logo.png"`

- [ ] **Step 3: Verify script syntax**

Run: `python convert_podcast_to_video.py --help` (or just import it)

Actually, the script has no --help yet. Just verify it imports cleanly:

```bash
python -c "import convert_podcast_to_video; print('✓ Script syntax OK')"
```

Expected: No syntax errors

---

### Task 3: Run Conversion on 2026-04-25-market-pulse.mp3

**Files:**
- Reference: `convert_podcast_to_video.py`
- Input: `remotion-video/out/2026-04-25-market-pulse.mp3`
- Output: `remotion-video/out/2026-04-25-market-pulse.mp4`

- [ ] **Step 1: Verify input MP3 exists**

Run: `ls -lh remotion-video/out/2026-04-25-market-pulse.mp3`

Expected: File exists and shows size (e.g., `5.2M`)

- [ ] **Step 2: Run conversion script**

Run: `python convert_podcast_to_video.py`

Expected: 
```
📝 Converting remotion-video/out/2026-04-25-market-pulse.mp3 to remotion-video/out/2026-04-25-market-pulse.mp4
   Logo: [your logo path]
   Format: 1080x1080 (square)

[1/3] Creating background...
✓ Created background image...

[2/3] Overlaying logo...
✓ Overlaid logo on background...

[3/3] Creating video from audio + image...
Running FFmpeg: ffmpeg -loop 1 -i /tmp/final.png -i remotion-video/out/2026-04-25-market-pulse.mp3...
✓ Video created: remotion-video/out/2026-04-25-market-pulse.mp4

✅ Conversion complete!
   Output: remotion-video/out/2026-04-25-market-pulse.mp4
```

If FFmpeg fails, ensure it's installed and in PATH.

- [ ] **Step 3: Verify output MP4**

Run: `ls -lh remotion-video/out/2026-04-25-market-pulse.mp4`

Expected: MP4 file exists (size depends on audio length, likely 10-30 MB)

- [ ] **Step 4: Quick play test (optional)**

Run: `ffplay remotion-video/out/2026-04-25-market-pulse.mp4` (or open with media player)

Expected: Video plays with logo + audio (no visual distortion)

- [ ] **Step 5: Commit**

```bash
git add convert_podcast_to_video.py
git commit -m "feat: add MP3 to MP4 conversion script with logo overlay"
```

---

## Plan Summary

This plan creates a standalone Python script that converts the specific podcast MP3 to an MP4 with logo overlay. Three tasks:

1. **Verify dependencies** — Check FFmpeg + identify logo path
2. **Create script** — Write FFmpeg-based conversion script
3. **Run conversion** — Execute on 2026-04-25-market-pulse.mp3, verify output

Total time: ~10-15 minutes.

**Note:** This is a one-time conversion. To convert future podcasts, run the same script with updated file paths. No integration with `main.py` needed.
