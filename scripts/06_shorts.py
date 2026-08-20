"""
АГЕНТ 6: НАРЕЗКА ШОРТСОВ
Автоматически нарезает вертикальные Shorts из длинного видео.
"""

import json
from pathlib import Path
from moviepy import *

BASE_DIR = Path(__file__).parent.parent
SHORTS_DIR = BASE_DIR / "assets" / "shorts"
SHORTS_DIR.mkdir(parents=True, exist_ok=True)


def create_short(input_path: Path, output_path: Path, start: float, end: float, title: str = ""):
    """
    Create a vertical Short (9:16) from a horizontal video (16:9).
    Uses black background + centered original video.
    """
    print(f"  Processing segment {start}s - {end}s...")
    
    # Load video
    video = VideoFileClip(str(input_path))
    
    # Extract segment
    segment = video.subclipped(start, end)
    
    # Original dimensions
    w, h = segment.size
    
    # Target: 1080x1920 (9:16)
    target_w, target_h = 1080, 1920
    
    # Scale original to fit height
    scaled = segment.resized(height=target_h)
    new_w = scaled.size[0]
    
    # Create black background
    bg = ColorClip(size=(target_w, target_h), color=(0, 0, 0)).with_duration(segment.duration)
    
    # If scaled width is larger than target, crop center
    if new_w > target_w:
        x_start = (new_w - target_w) // 2
        scaled = scaled.cropped(x1=x_start, x2=x_start + target_w)
        new_w = target_w
    
    # Position scaled video in center
    x_pos = (target_w - scaled.size[0]) // 2
    y_pos = 0
    
    # Composite: background + main video
    composite = CompositeVideoClip([
        bg.with_duration(segment.duration),
        scaled.with_position((x_pos, y_pos)).with_duration(segment.duration)
    ], size=(target_w, target_h))
    
    # Add title text if provided
    if title:
        txt = TextClip(
            text=title,
            font_size=60,
            color='white',
            stroke_color='black',
            stroke_width=2,
            size=(target_w - 100, None),
            method='caption'
        )
        txt = txt.with_position(('center', 100)).with_duration(segment.duration)
        composite = CompositeVideoClip([
            composite.with_duration(segment.duration),
            txt.with_duration(segment.duration)
        ], size=(target_w, target_h))
    
    # Write output
    composite.write_videofile(
        str(output_path),
        fps=24,
        codec='libx264',
        audio=False,
        logger=None
    )
    
    video.close()
    print(f"  ✅ Short saved: {output_path}")
    return output_path


def run_shorts_generator(input_video: Path = None, timestamps: list = None):
    """
    Generate shorts from a video.
    
    Args:
        input_video: Path to source video
        timestamps: List of (start, end, title) tuples
    """
    if input_video is None:
        input_video = BASE_DIR / "assets" / "test_video.mp4"
    
    if not input_video.exists():
        print(f"❌ Video not found: {input_video}")
        return
    
    # Default timestamps for demo (3 clips from 15s video)
    if timestamps is None:
        timestamps = [
            (0, 5, "ОШИБКА 1"),
            (5, 10, "ОШИБКА 2"),
            (10, 15, "ОШИБКА 3"),
        ]
    
    print(f"\n{'='*60}")
    print(f"  AGENT 6: SHORTS GENERATOR")
    print(f"  Source: {input_video.name}")
    print(f"  Clips to generate: {len(timestamps)}")
    print(f"{'='*60}\n")
    
    generated = []
    for i, (start, end, title) in enumerate(timestamps, 1):
        output = SHORTS_DIR / f"short_{i:02d}_{title.replace(' ', '_')}.mp4"
        print(f"[{i}/{len(timestamps)}] Generating: {title}")
        create_short(input_video, output, start, end, title)
        generated.append(output)
    
    print(f"\n{'='*60}")
    print(f"  ✅ ALL SHORTS GENERATED")
    print(f"  Output folder: {SHORTS_DIR}")
    for g in generated:
        print(f"    - {g.name}")
    print(f"{'='*60}\n")
    
    return generated


if __name__ == "__main__":
    run_shorts_generator()
