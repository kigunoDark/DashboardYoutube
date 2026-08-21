#!/usr/bin/env python3
"""Collect private YouTube Studio metrics for one channel into the static dashboard."""
import json
import os
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPORTS = ROOT / "data" / "reports"
DASHBOARD = ROOT / "dashboard" / "data"


def request_json(url, token=None, data=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if data is not None:
        data = urllib.parse.urlencode(data).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Google API request failed ({error.code}): {details}") from error


def access_token():
    required = ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")
    present = [name for name in required if os.environ.get(name)]
    if not present:
        print("Feedback sync skipped: add GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET and YOUTUBE_REFRESH_TOKEN secrets to enable it.")
        return None
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError("Missing GitHub Secrets: " + ", ".join(missing))
    payload = request_json("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    })
    if "access_token" not in payload:
        raise RuntimeError(payload.get("error_description", "Unable to refresh Google access token"))
    return payload["access_token"]


def analytics(token, start, end, metrics):
    params = urllib.parse.urlencode({
        "ids": "channel==MINE", "startDate": start, "endDate": end,
        "dimensions": "video", "sort": "-views", "maxResults": "200", "metrics": metrics,
    })
    report = request_json(f"https://youtubeanalytics.googleapis.com/v2/reports?{params}", token)
    headers = [item["name"] for item in report.get("columnHeaders", [])]
    return {row[headers.index("video")]: dict(zip(headers, row)) for row in report.get("rows", [])}


def collect():
    token = access_token()
    if token is None:
        return
    channel = request_json("https://www.googleapis.com/youtube/v3/channels?part=snippet,contentDetails&mine=true", token).get("items", [None])[0]
    if not channel:
        raise RuntimeError("No YouTube channel found for the authorized account")
    uploads = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    playlist = request_json("https://www.googleapis.com/youtube/v3/playlistItems?" + urllib.parse.urlencode({"part": "contentDetails", "playlistId": uploads, "maxResults": 50}), token)
    ids = [item["contentDetails"]["videoId"] for item in playlist.get("items", [])]
    details = request_json("https://www.googleapis.com/youtube/v3/videos?" + urllib.parse.urlencode({"part": "snippet,statistics", "id": ",".join(ids)}), token).get("items", []) if ids else []
    today = datetime.now(timezone.utc).date()
    date = lambda days: str(today - timedelta(days=days))
    basic_metrics = "views,likes,comments,averageViewPercentage,subscribersGained"
    reach_metrics = "videoThumbnailImpressions,videoThumbnailImpressionsClickRate"
    daily = {}
    for days in (1, 7, 30):
        basic = analytics(token, date(days), str(today), basic_metrics)
        try:
            reach = analytics(token, date(days), str(today), reach_metrics)
        except Exception as error:
            print(f"Reach metrics unavailable for {days}d: {error}")
            reach = {}
        daily[days] = {video_id: {**values, **reach.get(video_id, {})} for video_id, values in basic.items()}
    try:
        revenue = analytics(token, date(30), str(today), "estimatedRevenue")
    except Exception:
        revenue = {}
    videos = []
    for item in details:
        video_id = item["id"]
        metric30 = daily[30].get(video_id, {})
        videos.append({
            "id": video_id, "title": item["snippet"]["title"], "url": f"https://www.youtube.com/watch?v={video_id}",
            "publishedAt": item["snippet"]["publishedAt"][:10], "thumbnailUrl": item["snippet"].get("thumbnails", {}).get("medium", {}).get("url"),
            "views24h": int(daily[1].get(video_id, {}).get("views", 0)), "views7d": int(daily[7].get(video_id, {}).get("views", 0)), "views30d": int(metric30.get("views", 0)),
            "impressions": int(metric30.get("videoThumbnailImpressions", 0)), "ctr": float(metric30.get("videoThumbnailImpressionsClickRate", 0)), "averageViewedPercent": float(metric30.get("averageViewPercentage", 0)),
            "likes": int(item.get("statistics", {}).get("likeCount", 0)), "comments": int(item.get("statistics", {}).get("commentCount", 0)),
            "subscribersGained": int(metric30.get("subscribersGained", 0)), "estimatedRevenue": float(revenue.get(video_id, {}).get("estimatedRevenue", 0)),
        })
    report = {"generatedAt": datetime.now(timezone.utc).isoformat(), "channel": {"id": channel["id"], "title": channel["snippet"]["title"]}, "videos": videos}
    REPORTS.mkdir(parents=True, exist_ok=True)
    DASHBOARD.mkdir(parents=True, exist_ok=True)
    stamp = today.isoformat()
    for path in (REPORTS / f"my_videos_{stamp}.json", DASHBOARD / "my_videos_latest.json"):
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(videos)} videos for {channel['snippet']['title']}")


if __name__ == "__main__":
    collect()
