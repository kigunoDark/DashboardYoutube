#!/usr/bin/env python3
"""Fail CI when it would publish incomplete or stale dashboard reports."""

import json
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TODAY = datetime.now().strftime("%Y-%m-%d")

REQUIRED_REPORTS = {
    "monitor": [
        BASE_DIR / "data" / "reports" / f"monitor_report_{TODAY}.json",
        BASE_DIR / "dashboard" / "data" / f"monitor_report_{TODAY}.json",
        BASE_DIR / "dashboard" / "data" / "monitor_report_latest.json",
    ],
    "ideas": [
        BASE_DIR / "data" / "reports" / f"ideas_report_{TODAY}.json",
        BASE_DIR / "dashboard" / "data" / f"ideas_report_{TODAY}.json",
        BASE_DIR / "dashboard" / "data" / "ideas_report_latest.json",
    ],
    "scripts": [
        BASE_DIR / "data" / "reports" / f"scripts_index_{TODAY}.json",
        BASE_DIR / "dashboard" / "data" / f"scripts_index_{TODAY}.json",
        BASE_DIR / "dashboard" / "data" / "scripts_index_latest.json",
    ],
    "demand": [
        BASE_DIR / "data" / "reports" / f"demand_{TODAY}.json",
        BASE_DIR / "dashboard" / "data" / f"demand_{TODAY}.json",
        BASE_DIR / "dashboard" / "data" / "demand_latest.json",
    ],
}


def read_report(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None, "missing"
    except json.JSONDecodeError as error:
        return None, f"invalid JSON ({error})"

    if not isinstance(data, dict):
        return None, "JSON root must be an object"
    if data.get("date") != TODAY:
        return None, f"expected date {TODAY}, got {data.get('date')!r}"
    return data, None


def main():
    errors = []
    primary_reports = {}

    for name, paths in REQUIRED_REPORTS.items():
        for path in paths:
            data, error = read_report(path)
            if error:
                errors.append(f"{path.relative_to(BASE_DIR)}: {error}")
            elif path == paths[0]:
                primary_reports[name] = data

    if primary_reports.get("monitor", {}).get("data") == []:
        errors.append("monitor report contains no channels")
    if primary_reports.get("ideas", {}).get("ideas") == []:
        errors.append("ideas report contains no ideas")
    if primary_reports.get("scripts", {}).get("generated_scripts") == []:
        errors.append("script index contains no scripts")

    if errors:
        print("Dashboard report validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"Dashboard reports validated for {TODAY}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
