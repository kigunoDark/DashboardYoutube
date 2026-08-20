#!/usr/bin/env python3
"""
СПРОС-СЛОЙ (Google Trends, YouTube-режим)
Для топ-20 Golden Topics проверяет динамику спроса за 3 месяца:
    rising  — тема растёт (recent/earlier >= 1.3)
    stable  — стабильна
    falling — падает (<= 0.7)
    new     — раньше спроса не было, появился недавно
    unknown — не удалось проверить (Google ограничил и т.п.)

Никогда не роняет workflow: при любой ошибке пишет "unknown".

Запуск:
    pip install pytrends
    python scripts/demand.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / "data" / "reports"
DASH_DATA_DIR = BASE_DIR / "dashboard" / "data"

GOLDEN_MIN_MULTIPLIER = 3
TOP_N = 20

try:
    from pytrends.request import TrendReq
except ImportError:
    TrendReq = None


def median(arr):
    s = sorted(arr)
    if not s:
        return 0
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


def load_monitor_report():
    """Свежий monitor report: из dashboard/data или data/reports."""
    candidates = [DASH_DATA_DIR / "monitor_report_latest.json"]
    candidates += sorted(REPORTS_DIR.glob("monitor_report_*.json"), reverse=True)
    for path in candidates:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    return None


def compute_golden_topics(report):
    """Та же формула, что в dashboard/js/golden.js — держать синхронно."""
    videos = []
    for ch in report.get("data", []):
        for v in ch.get("videos", []):
            videos.append({
                "title": v.get("title", ""),
                "view_count": v.get("view_count", 0) or 0,
                "channel_id": ch.get("channel_id", "unknown"),
            })

    by_channel = {}
    for v in videos:
        by_channel.setdefault(v["channel_id"], []).append(v["view_count"])
    medians = {c: median(views) for c, views in by_channel.items()}

    topics = []
    for v in videos:
        med = medians.get(v["channel_id"]) or 1
        mult = v["view_count"] / med if med > 0 else 0
        if mult >= GOLDEN_MIN_MULTIPLIER:
            topics.append({"title": v["title"], "multiplier": mult})
    topics.sort(key=lambda t: -t["multiplier"])
    return topics[:TOP_N]


def trend_signal(pt, keyword):
    """rising | stable | falling | new | none | unknown"""
    try:
        pt.build_payload([keyword], timeframe="today 3-m", gprop="youtube")
        df = pt.interest_over_time()
        if df.empty or keyword not in df.columns:
            return "none"
        s = df[keyword]
        recent, earlier = s.tail(4).mean(), s.head(4).mean()
        if earlier == 0:
            return "new" if recent > 5 else "none"
        ratio = recent / earlier
        if ratio >= 1.3:
            return "rising"
        if ratio <= 0.7:
            return "falling"
        return "stable"
    except Exception as e:
        print(f"  ⚠️  Trends error for '{keyword}': {e}")
        return "unknown"


def main():
    report = load_monitor_report()
    if not report:
        print("❌ Нет monitor report — сначала запустите collect.py")
        sys.exit(0)  # не роняем workflow

    topics = compute_golden_topics(report)
    print(f"Golden topics: {len(topics)}")

    today = datetime.now().strftime("%Y-%m-%d")
    result = {
        "date": today,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "topics": [],
    }

    if TrendReq is None:
        print("⚠️  pytrends не установлен — все темы получат 'unknown'")
        for t in topics:
            result["topics"].append({**t, "trend": "unknown"})
    else:
        pt = TrendReq()
        for i, t in enumerate(topics, 1):
            # Запрос в Trends — сам заголовок (YouTube-режим неплохо матчит фразы)
            trend = trend_signal(pt, t["title"])
            result["topics"].append({**t, "trend": trend})
            print(f"  [{i}/{len(topics)}] {trend:8s} {t['multiplier']:.1f}x — {t['title'][:60]}")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DASH_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for path in (REPORTS_DIR / f"demand_{today}.json",
                 DASH_DATA_DIR / f"demand_{today}.json",
                 DASH_DATA_DIR / "demand_latest.json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    print("💾 demand reports saved")


if __name__ == "__main__":
    main()
