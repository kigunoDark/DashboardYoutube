"""
АГЕНТ 1: МОНИТОРИНГ КОНКУРЕНТОВ
Собирает последние видео с каналов-конкурентов через yt-dlp (без API ключа).
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "--quiet"])
    import yt_dlp

# Paths
BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config.json"
DATA_DIR = BASE_DIR / "data" / "competitors"
REPORTS_DIR = BASE_DIR / "data" / "reports"

DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_channel_videos(channel_id: str, max_videos: int = 10):
    """Fetch recent videos from a YouTube channel."""
    url = f"https://www.youtube.com/channel/{channel_id}/videos"
    
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'playlistend': max_videos,
        'cookiefile': None,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        entries = info.get('entries', [])
        videos = []
        for entry in entries:
            videos.append({
                'video_id': entry.get('id'),
                'title': entry.get('title'),
                'url': f"https://www.youtube.com/watch?v={entry.get('id')}",
                'duration': entry.get('duration'),
                'thumbnail': entry.get('thumbnails', [{}])[-1].get('url') if entry.get('thumbnails') else None,
            })
        return videos
    except Exception as e:
        print(f"  ⚠️  Error fetching channel {channel_id}: {e}")
        return []


def fetch_video_details(video_id: str):
    """Fetch detailed metadata for a single video."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'writeinfojson': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        return {
            'video_id': video_id,
            'title': info.get('title'),
            'description': info.get('description'),
            'duration': info.get('duration'),
            'view_count': info.get('view_count'),
            'like_count': info.get('like_count'),
            'comment_count': info.get('comment_count'),
            'upload_date': info.get('upload_date'),
            'tags': info.get('tags', []),
            'categories': info.get('categories', []),
            'thumbnail': info.get('thumbnail'),
            'channel': info.get('channel'),
            'channel_id': info.get('channel_id'),
            'url': f"https://www.youtube.com/watch?v={video_id}",
        }
    except Exception as e:
        print(f"    ⚠️  Error fetching video {video_id}: {e}")
        return None


def run_monitoring():
    config = load_config()
    competitors = config['competitors']
    settings = config['settings']
    max_videos = settings['videos_per_competitor']
    
    today = datetime.now().strftime("%Y-%m-%d")
    report = {
        'date': today,
        'channels_scanned': 0,
        'videos_found': 0,
        'videos_detailed': 0,
        'data': []
    }
    
    print(f"\n{'='*60}")
    print(f"  AGENT 1: MONITORING COMPETITORS")
    print(f"  Date: {today}")
    print(f"  Competitors: {len(competitors)}")
    print(f"  Videos per channel: {max_videos}")
    print(f"{'='*60}\n")
    
    for i, comp in enumerate(competitors, 1):
        channel_id = comp['channel_id']
        print(f"[{i}/{len(competitors)}] Scanning channel: {channel_id}")
        
        # Step 1: Get video list
        videos = fetch_channel_videos(channel_id, max_videos)
        if not videos:
            print(f"  ❌ No videos found\n")
            continue
        
        print(f"  ✅ Found {len(videos)} videos")
        
        # Step 2: Get details for each video
        channel_data = {
            'channel_id': channel_id,
            'notes': comp.get('notes', ''),
            'videos': []
        }
        
        for j, video in enumerate(videos, 1):
            video_id = video['video_id']
            print(f"    [{j}/{len(videos)}] Fetching details: {video_id}")
            
            details = fetch_video_details(video_id)
            if details:
                channel_data['videos'].append(details)
                report['videos_detailed'] += 1
            else:
                # Fallback to basic info
                channel_data['videos'].append(video)
                report['videos_found'] += 1
            
            # Delay to avoid rate limiting
            time.sleep(1.5)
        
        report['data'].append(channel_data)
        report['channels_scanned'] += 1
        report['videos_found'] += len(videos)
        
        # Delay between channels
        if i < len(competitors):
            print(f"  ⏳ Waiting before next channel...\n")
            time.sleep(3)
    
    # Save report
    report_file = REPORTS_DIR / f"monitor_report_{today}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # Save raw data
    raw_file = DATA_DIR / f"raw_data_{today}.json"
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(report['data'], f, ensure_ascii=False, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"  REPORT SAVED")
    print(f"  Channels scanned: {report['channels_scanned']}")
    print(f"  Videos found: {report['videos_found']}")
    print(f"  Videos with full details: {report['videos_detailed']}")
    print(f"  Report file: {report_file}")
    print(f"{'='*60}\n")
    
    return report


if __name__ == "__main__":
    run_monitoring()
