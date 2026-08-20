from moviepy import vfx
print("Available vfx:")
for name in sorted(dir(vfx)):
    if not name.startswith('_'):
        print(f"  - {name}")
