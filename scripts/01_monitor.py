"""
АГЕНТ 1: МОНИТОРИНГ КОНКУРЕНТОВ
Собирает последние видео с каналов-конкурентов.
Приоритет: YouTube Data API v3 → yt-dlp fallback
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.parse

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

API_KEY = None
USE_API = False


def load_config():
    global API_KEY, USE_API
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    API_KEY = config.get("youtube_api_key", "")
    USE_API = config.get("use_youtube_api", False) and bool(API_KEY)
    return config


# ═══════════════════════════════════════════
# YOUTUBE DATA API v3
# ═══════════════════════════════════════════

def api_request(endpoint, params):
    """Make a YouTube Data API request."""
    if not API_KEY:
        return None
    params["key"] = API_KEY
    url = f"https://www.googleapis.com/youtube/v3/{endpoint}?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"  ⚠️  API error: {e}")
        return None


def fetch_channel_info_api(channel_id: str):
    """Get channel info via YouTube API."""
    # Try channel ID directly first, then search by handle
    if channel_id.startswith("@") or channel_id.startswith("UC") is False and len(channel_id) < 24:
        # Search for channel
        search_data = api_request("search", {
            "part": "snippet",
            "q": channel_id if channel_id.startswith("@") else f"@{channel_id}",
            "type": "channel",
            "maxResults": 1
        })
        if search_data and search_data.get("items"):
            channel_id = search_data["items"][0]["snippet"]["channelId"]

    data = api_request("channels", {
        "part": "snippet,statistics,contentDetails",
        "id": channel_id
    })
    if not data or not data.get("items"):
        return None

    item = data["items"][0]
    stats = item.get("statistics", {})
    snippet = item.get("snippet", {})

    return {
        "channel_id": channel_id,
        "title": snippet.get("title", channel_id),
        "description": snippet.get("description", ""),
        "subscriber_count": int(stats.get("subscriberCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
        "view_count": int(stats.get("viewCount", 0)),
        "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", "")
    }


def fetch_videos_api(channel_id: str, max_videos: int = 10):
    """Get recent videos from channel via API."""
    # First get uploads playlist ID
    channel_data = api_request("channels", {
        "part": "contentDetails",
        "id": channel_id
    })
    if not channel_data or not channel_data.get("items"):
        return []

    uploads_playlist_id = channel_data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Get videos from playlist
    playlist_data = api_request("playlistItems", {
        "part": "snippet",
        "playlistId": uploads_playlist_id,
        "maxResults": max_videos
    })
    if not playlist_data or not playlist_data.get("items"):
        return []

    videos = []
    video_ids = []
    for item in playlist_data["items"]:
        snippet = item.get("snippet", {})
        video_id = snippet.get("resourceId", {}).get("videoId", "")
        if video_id:
            videos.append({
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                "published_at": snippet.get("publishedAt", ""),
                "channel": snippet.get("channelTitle", ""),
                "channel_id": channel_id,
            })
            video_ids.append(video_id)

    # Get statistics for all videos (batch request)
    if video_ids:
        stats_data = api_request("videos", {
            "part": "statistics,contentDetails,snippet",
            "id": ",".join(video_ids)
        })
        if stats_data and stats_data.get("items"):
            stats_map = {item["id"]: item for item in stats_data["items"]}
            for v in videos:
                sid = v["video_id"]
                if sid in stats_map:
                    stats = stats_map[sid].get("statistics", {})
                    snippet = stats_map[sid].get("snippet", {})
                    v["view_count"] = int(stats.get("viewCount", 0))
                    v["like_count"] = int(stats.get("likeCount", 0)) if stats.get("likeCount") else 0
                    v["comment_count"] = int(stats.get("commentCount", 0)) if stats.get("commentCount") else 0
                    v["tags"] = snippet.get("tags", [])
                    v["description"] = snippet.get("description", "")
                    v["category_id"] = snippet.get("categoryId", "")
                    duration = stats_map[sid].get("contentDetails", {}).get("duration", "")
                    v["duration"] = parse_duration(duration)

    return videos


def parse_duration(iso_duration: str) -> int:
    """Parse PT1H2M3S to seconds."""
    import re
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
    if not match:
        return 0
    h, m, s = match.groups(default='0')
    return int(h) * 3600 + int(m) * 60 + int(s)


# ═══════════════════════════════════════════
# YT-DLP FALLBACK
# ═══════════════════════════════════════════

def fetch_channel_videos_ytdlp(channel_id: str, max_videos: int = 10):
    """Fetch recent videos from a YouTube channel via yt-dlp."""
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


def fetch_video_details_ytdlp(video_id: str):
    """Fetch detailed metadata for a single video via yt-dlp."""
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


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

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
    print(f"  YouTube API: {'ENABLED ✅' if USE_API else 'DISABLED (fallback to yt-dlp)'}")
    print(f"{'='*60}\n")

    for i, comp in enumerate(competitors, 1):
        channel_id = comp['channel_id']
        print(f"[{i}/{len(competitors)}] Scanning channel: {channel_id}")

        channel_info = None
        videos = []

        # Try YouTube API first
        if USE_API:
            channel_info = fetch_channel_info_api(channel_id)
            if channel_info:
                real_channel_id = channel_info['channel_id']
                videos = fetch_videos_api(real_channel_id, max_videos)
                print(f"  ✅ API: {channel_info.get('title', channel_id)} | {channel_info.get('subscriber_count', 0):,} subs | {len(videos)} videos")

        # Fallback to yt-dlp
        if not videos:
            print(f"  🔄 Falling back to yt-dlp...")
            videos = fetch_channel_videos_ytdlp(channel_id, max_videos)
            if videos:
                print(f"  ✅ yt-dlp: {len(videos)} videos found")

        if not videos:
            print(f"  ❌ No videos found\n")
            continue

        # Get details for each video (if using yt-dlp fallback)
        channel_data = {
            'channel_id': channel_info['channel_id'] if channel_info else channel_id,
            'channel_title': channel_info['title'] if channel_info else None,
            'subscriber_count': channel_info['subscriber_count'] if channel_info else None,
            'video_count': channel_info['video_count'] if channel_info else None,
            'channel_description': channel_info['description'] if channel_info else None,
            'channel_thumbnail': channel_info['thumbnail'] if channel_info else None,
            'notes': comp.get('notes', ''),
            'videos': []
        }

        if USE_API and videos and 'view_count' in videos[0]:
            # Already have full data from API
            channel_data['videos'] = videos
            report['videos_detailed'] += len(videos)
        else:
            # Need to fetch details via yt-dlp
            for j, video in enumerate(videos, 1):
                video_id = video['video_id']
                print(f"    [{j}/{len(videos)}] Fetching details: {video_id}")

                details = fetch_video_details_ytdlp(video_id)
                if details:
                    channel_data['videos'].append(details)
                    report['videos_detailed'] += 1
                else:
                    channel_data['videos'].append(video)

                time.sleep(1.0)

        report['data'].append(channel_data)
        report['channels_scanned'] += 1
        report['videos_found'] += len(videos)

        if i < len(competitors):
            print(f"  ⏳ Waiting before next channel...\n")
            time.sleep(2)

    # Save report
    report_file = REPORTS_DIR / f"monitor_report_{today}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    raw_file = DATA_DIR / f"raw_data_{today}.json"
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(report['data'], f, ensure_ascii=False, indent=2)

    # Also copy to dashboard data
    dash_data_dir = BASE_DIR / "dashboard" / "data"
    dash_data_dir.mkdir(parents=True, exist_ok=True)
    dash_report = dash_data_dir / f"monitor_report_{today}.json"
    with open(dash_report, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

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
