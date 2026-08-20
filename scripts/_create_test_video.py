from moviepy import *
from pathlib import Path

# Create test video: 15 seconds, black background with text
print("Creating test video...")

texts = [
    ("ОШИБКА 1", 0, 5),
    ("Язык обязанностей", 5, 10),
    ("вместо результатов", 10, 15),
]

clips = []
for txt, start, end in texts:
    clip = TextClip(text=txt, font_size=70, color='white', bg_color='black', size=(1920, 1080), duration=end-start)
    clip = clip.with_start(start)
    clips.append(clip)

video = CompositeVideoClip(clips, size=(1920, 1080))
video = video.with_duration(15)

output = Path(__file__).parent.parent / "assets" / "test_video.mp4"
video.write_videofile(str(output), fps=24, codec='libx264', audio=False, logger=None)
print(f"✅ Test video saved: {output}")
