#!/usr/bin/env python3
"""
BUKA YOUTUBE SYSTEM — MAIN PIPELINE
Оркестратор: запускает всех агентов последовательно.

Запуск:
    python run.py

Агенты:
    1. Мониторинг конкурентов (01_monitor.py)
    2. Аналитика + идеи (02_analyze.py)
    3. Сценарист (03_scriptwriter.py)
    4. (Опционально) Дизайнер обложек
    5. (Опционально) Нарезка шортсов
"""

import sys
import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

from scripts import 01_monitor, 02_analyze, 03_scriptwriter


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    start_time = datetime.now()
    
    print("=" * 70)
    print("  BUKA YOUTUBE SYSTEM — FULL PIPELINE")
    print(f"  Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    pipeline_report = {
        "date": today,
        "start_time": start_time.isoformat(),
        "steps": [],
        "status": "running"
    }
    
    # ═══════════════════════════════════════════════
    # STEP 1: MONITORING
    # ═══════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("  STEP 1/3: COMPETITOR MONITORING")
    print("─" * 70 + "\n")
    
    try:
        monitor_report = 01_monitor.run_monitoring()
        pipeline_report["steps"].append({
            "step": 1,
            "name": "monitoring",
            "status": "success",
            "channels_scanned": monitor_report.get("channels_scanned", 0),
            "videos_found": monitor_report.get("videos_found", 0),
            "report_file": str(BASE_DIR / "data" / "reports" / f"monitor_report_{today}.json")
        })
    except Exception as e:
        pipeline_report["steps"].append({
            "step": 1,
            "name": "monitoring",
            "status": "failed",
            "error": str(e)
        })
        print(f"❌ Monitoring failed: {e}")
        # Continue to next step anyway
    
    # ═══════════════════════════════════════════════
    # STEP 2: ANALYTICS
    # ═══════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("  STEP 2/3: ANALYTICS + IDEA GENERATION")
    print("─" * 70 + "\n")
    
    try:
        ideas_report = 02_analyze.run_analysis()
        pipeline_report["steps"].append({
            "step": 2,
            "name": "analytics",
            "status": "success",
            "ideas_generated": len(ideas_report.get("ideas", [])),
            "report_file": str(BASE_DIR / "data" / "reports" / f"ideas_report_{today}.json")
        })
    except Exception as e:
        pipeline_report["steps"].append({
            "step": 2,
            "name": "analytics",
            "status": "failed",
            "error": str(e)
        })
        print(f"❌ Analytics failed: {e}")
    
    # ═══════════════════════════════════════════════
    # STEP 3: SCRIPTWRITER
    # ═══════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("  STEP 3/3: SCRIPT GENERATION")
    print("─" * 70 + "\n")
    
    try:
        scripts_index = 03_scriptwriter.run_scriptwriter()
        pipeline_report["steps"].append({
            "step": 3,
            "name": "scriptwriter",
            "status": "success",
            "scripts_generated": len(scripts_index.get("generated_scripts", [])),
            "index_file": str(BASE_DIR / "data" / "reports" / f"scripts_index_{today}.json")
        })
    except Exception as e:
        pipeline_report["steps"].append({
            "step": 3,
            "name": "scriptwriter",
            "status": "failed",
            "error": str(e)
        })
        print(f"❌ Scriptwriter failed: {e}")
    
    # ═══════════════════════════════════════════════
    # FINAL REPORT
    # ═══════════════════════════════════════════════
    end_time = datetime.now()
    pipeline_report["end_time"] = end_time.isoformat()
    pipeline_report["duration_seconds"] = (end_time - start_time).total_seconds()
    
    # Overall status
    all_success = all(s["status"] == "success" for s in pipeline_report["steps"])
    pipeline_report["status"] = "success" if all_success else "partial"
    
    # Save pipeline report
    report_path = BASE_DIR / "data" / "reports" / f"pipeline_report_{today}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(pipeline_report, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print("\n" + "=" * 70)
    print("  PIPELINE COMPLETE")
    print("=" * 70)
    print(f"  Duration: {pipeline_report['duration_seconds']:.1f} seconds")
    print(f"  Status: {pipeline_report['status'].upper()}")
    print()
    
    for step in pipeline_report["steps"]:
        icon = "✅" if step["status"] == "success" else "❌"
        print(f"  {icon} Step {step['step']}: {step['name']} — {step['status']}")
    
    print()
    print(f"  📁 Full report: {report_path}")
    print("=" * 70 + "\n")
    
    return pipeline_report


if __name__ == "__main__":
    main()
