#!/usr/bin/env python3
"""
АВТОСБОРЩИК ДАННЫХ (GitHub Actions)
Собирает статистику каналов и последние видео конкурентов.
Бюджет квоты: ~1 + N (playlistItems) + 1 (videos) юнитов на запуск.
При 10 конкурентах ≈ 12 юнитов из 10 000 в день.

Запуск:
    YOUTUBE_API_KEY=... python scripts/collect.py
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

# Windows-консоль (cp1251) не умеет в emoji — переводим stdout в UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config.json"
CONFIG_TEMPLATE_PATH = BASE_DIR / "config.example.json"
REPORTS_DIR = BASE_DIR / "data" / "reports"
DASH_DATA_DIR = BASE_DIR / "dashboard" / "data"

API_KEY = os.environ.get("YOUTUBE_API_KEY", "")

def load_config():
    """Load local settings or the checked-in, secret-free CI template."""
    for path in (CONFIG_PATH, CONFIG_TEMPLATE_PATH):
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)
            break
    else:
        raise FileNotFoundError(
            "Configuration not found. Create config.json locally or add config.example.json."
        )

    competitors = config.get("competitors")
    if not isinstance(competitors, list) or not competitors:
        raise ValueError("Configuration must contain at least one competitor.")

    allowed_identifiers = ("channel_id", "channel_handle", "channel_username")
    for competitor in competitors:
        if not isinstance(competitor, dict):
            raise ValueError("Every competitor must be an object.")
        present = [key for key in allowed_identifiers if competitor.get(key)]
        if len(present) != 1:
            raise ValueError(
                "Every competitor must have exactly one of: " + ", ".join(allowed_identifiers)
            )

    if not isinstance(config.get("settings"), dict):
        config["settings"] = {}

    print(f"Using configuration: {path.name}")
    return config

# channels.list = 1 юнит за вызов
# playlistItems.list = 1 юнит за вызов
# videos.list = 1 юнит за вызов (до 50 ID)
# search.list = 100 юнитов — НЕ использовать в ежедневном сборе


def yt(endpoint, params):
    """Запрос к YouTube Data API v3."""
    params["key"] = API_KEY
    url = f"https://www.googleapis.com/youtube/v3/{endpoint}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def resolve_channel_ids(competitors):
    """Resolve handles/usernames once, then use canonical IDs for collection."""
    selector_by_field = {
        "channel_handle": "forHandle",
        "channel_username": "forUsername",
    }
    channel_ids = []
    seen = set()

    for competitor in competitors:
        channel_id = competitor.get("channel_id")
        if not channel_id:
            field = next(key for key in selector_by_field if competitor.get(key))
            lookup = yt("channels", {
                "part": "id",
                selector_by_field[field]: competitor[field],
            })
            items = lookup.get("items", [])
            if not items:
                raise ValueError(f"Channel not found for {field}: {competitor[field]}")
            channel_id = items[0]["id"]

        if channel_id not in seen:
            seen.add(channel_id)
            channel_ids.append(channel_id)

    return channel_ids


def parse_duration(iso_duration: str) -> int:
    """PT1H2M3S → секунды."""
    import re
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_duration or "")
    if not match:
        return 0
    h, m, s = match.groups(default='0')
    return int(h) * 3600 + int(m) * 60 + int(s)


def collect(config):
    """Собрать отчёт по всем конкурентам."""
    competitors = config["competitors"]
    max_videos = config["settings"].get("videos_per_competitor", 15)
    channel_ids = resolve_channel_ids(competitors)

    # 1 запрос: статистика всех каналов сразу
    ch_data = yt("channels", {
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(channel_ids),
    })
    channels_by_id = {item["id"]: item for item in ch_data.get("items", [])}

    report = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "channels_scanned": 0,
        "videos_found": 0,
        "data": [],
    }

    for cid in channel_ids:
        item = channels_by_id.get(cid)
        if not item:
            print(f"  ⚠️  Канал не найден: {cid}")
            continue

        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        uploads = item.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")

        channel_entry = {
            "channel_id": cid,
            "channel_title": snippet.get("title", cid),
            "subscriber_count": int(stats.get("subscriberCount", 0)),
            "video_count": int(stats.get("videoCount", 0)),
            "channel_thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            "videos": [],
        }

        if not uploads:
            report["data"].append(channel_entry)
            report["channels_scanned"] += 1
            continue

        # 1 запрос на канал: последние видео из uploads-плейлиста
        pl = yt("playlistItems", {
            "part": "snippet",
            "playlistId": uploads,
            "maxResults": max_videos,
        })
        items = pl.get("items", [])
        video_ids = [i["snippet"]["resourceId"]["videoId"] for i in items
                     if i.get("snippet", {}).get("resourceId", {}).get("videoId")]

        # 1 запрос: статистика по всем видео канала (до 50 ID)
        stats_map = {}
        if video_ids:
            vids = yt("videos", {
                "part": "statistics,contentDetails,snippet",
                "id": ",".join(video_ids),
            })
            stats_map = {v["id"]: v for v in vids.get("items", [])}

        for i in items:
            sn = i.get("snippet", {})
            vid = sn.get("resourceId", {}).get("videoId", "")
            if not vid:
                continue
            full = stats_map.get(vid, {})
            vstats = full.get("statistics", {})
            vsnippet = full.get("snippet", {})
            channel_entry["videos"].append({
                "video_id": vid,
                "title": sn.get("title", ""),
                "url": f"https://www.youtube.com/watch?v={vid}",
                "thumbnail": sn.get("thumbnails", {}).get("high", {}).get("url", ""),
                "published_at": sn.get("publishedAt", ""),
                "view_count": int(vstats.get("viewCount", 0)),
                "like_count": int(vstats.get("likeCount", 0)) if vstats.get("likeCount") else 0,
                "comment_count": int(vstats.get("commentCount", 0)) if vstats.get("commentCount") else 0,
                "tags": vsnippet.get("tags", []),
                "description": vsnippet.get("description", ""),
                "duration": parse_duration(full.get("contentDetails", {}).get("duration", "")),
            })

        report["data"].append(channel_entry)
        report["channels_scanned"] += 1
        report["videos_found"] += len(channel_entry["videos"])
        print(f"  ✅ {channel_entry['channel_title']}: {len(channel_entry['videos'])} видео, "
              f"{channel_entry['subscriber_count']:,} подписчиков")

    return report


def main():
    if not API_KEY:
        print("❌ YOUTUBE_API_KEY не задан (переменная окружения)")
        sys.exit(1)

    config = load_config()

    print(f"Collecting data for {len(config['competitors'])} competitors...")
    report = collect(config)

    today = report["date"]
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DASH_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Датированный отчёт + latest-алиасы для дашборда
    out_files = [
        REPORTS_DIR / f"monitor_report_{today}.json",
        DASH_DATA_DIR / f"monitor_report_{today}.json",
        DASH_DATA_DIR / "monitor_report_latest.json",
    ]
    for path in out_files:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"  💾 {path.relative_to(BASE_DIR)}")

    print(f"\nDone: {report['channels_scanned']} каналов, {report['videos_found']} видео")


if __name__ == "__main__":
    main()
