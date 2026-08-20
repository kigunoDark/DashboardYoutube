import subprocess, sys

try:
    import yt_dlp
    print("yt-dlp already installed")
except ImportError:
    print("Installing yt-dlp...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "-q"])
    print("yt-dlp installed")
