import json, sys
from pathlib import Path

# Quick test with 2 channels, 3 videos each
config_path = Path(__file__).parent.parent / "config.json"
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

# Temp override for quick test
config['competitors'] = config['competitors'][:2]
config['settings']['videos_per_competitor'] = 3

with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print("Config updated for quick test: 2 channels, 3 videos each")
