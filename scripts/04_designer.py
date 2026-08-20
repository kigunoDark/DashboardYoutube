from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Config
BG_PATH = Path(__file__).parent.parent / "assets" / "thumbnail_resume_bg.png"
OUTPUT_PATH = Path(__file__).parent.parent / "assets" / "thumbnail_final_resume.png"

# Load image
img = Image.open(BG_PATH)
width, height = img.size

draw = ImageDraw.Draw(img)

# Fonts
try:
    font_huge = ImageFont.truetype("C:/Windows/Fonts/impact.ttf", 170)
    font_medium = ImageFont.truetype("C:/Windows/Fonts/impact.ttf", 80)
    font_badge = ImageFont.truetype("C:/Windows/Fonts/impact.ttf", 40)
except:
    font_huge = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 170)
    font_medium = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 80)
    font_badge = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 40)

# Colors
WHITE = "#FFFFFF"
ORANGE = "#FF6B00"
BLACK = "#000000"

# Dark overlay on left
overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
overlay_draw = ImageDraw.Draw(overlay)
overlay_draw.rectangle([40, 120, 900, 750], fill=(0, 0, 0, 130))
img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
draw = ImageDraw.Draw(img)

# Text position
x = 80
y = 220

# Line 1: "3 ОШИБКИ"
draw.text((x, y), "3 ОШИБКИ", font=font_huge, fill=WHITE, stroke_width=5, stroke_fill=BLACK)

# Line 2: "В РЕЗЮМЕ"
bbox = draw.textbbox((0, 0), "3 ОШИБКИ", font=font_huge)
y += (bbox[3] - bbox[1]) + 10
draw.text((x, y), "В РЕЗЮМЕ", font=font_huge, fill=ORANGE, stroke_width=5, stroke_fill=BLACK)

# Line 3: "я не беру"
bbox2 = draw.textbbox((0, 0), "В РЕЗЮМЕ", font=font_huge)
y += (bbox2[3] - bbox2[1]) + 30
draw.text((x, y), "я не беру", font=font_medium, fill=WHITE, stroke_width=3, stroke_fill=BLACK)

# Badge
badge_y = height - 100
draw.text((x, badge_y), "ОТ STAFF-ИНЖЕНЕРА", font=font_badge, fill=WHITE, stroke_width=2, stroke_fill=BLACK)

# Save
img.save(OUTPUT_PATH, "PNG")
print(f"✅ Обложка сохранена: {OUTPUT_PATH}")
