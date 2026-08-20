import subprocess, sys, json, os

# Install yt-dlp if missing
try:
    import yt_dlp
    print("yt_dlp already available")
except ImportError:
    print("Installing yt_dlp...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "--quiet"])
    import yt_dlp
    print("yt_dlp installed")

# Test: fetch metadata for first competitor
CHANNEL_ID = "UC2UXDak6o7rBm23k3Vv5dww"
CHANNEL_URL = f"https://www.youtube.com/channel/{CHANNEL_ID}/videos"

ydl_opts = {
    'quiet': True,
    'extract_flat': True,
    'playlistend': 5,  # test with 5 videos
}

print(f"\nTesting fetch for channel: {CHANNEL_ID}")
print("This may take 30-60 seconds...\n")

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(CHANNEL_URL, download=False)
        
    if 'entries' in info:
        print(f"✅ SUCCESS! Found {len(info['entries'])} videos")
        for i, entry in enumerate(info['entries'][:3]):
            print(f"  {i+1}. {entry.get('title', 'N/A')}")
            print(f"     ID: {entry.get('id', 'N/A')}")
    else:
        print("⚠️ No entries found")
        print(json.dumps(info, indent=2, default=str)[:1000])
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
