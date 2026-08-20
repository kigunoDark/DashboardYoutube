import json
from pathlib import Path

config_path = Path(__file__).parent.parent / "config.json"
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

# Restore full config
config['competitors'] = [
    {"channel_id": "UC2UXDak6o7rBm23k3Vv5dww", "notes": ""},
    {"channel_id": "UCwr-evhuzGZgDFrq_1pLt_A", "notes": ""},
    {"channel_id": "UCbILxHiByrV3fPDYxpqUlWQ", "notes": ""},
    {"channel_id": "UCjQ2f-S5_9LNXZ0oALoxZBw", "notes": ""},
    {"channel_id": "UCJKzyA7mf4L6CtdNuRFExTw", "notes": ""},
    {"channel_id": "UCPhyA52nHlW3L6r-7sDfcyg", "notes": ""},
    {"channel_id": "UCfBHkCIezL1pzMI6Vu4GUVw", "notes": ""},
    {"channel_id": "UCN7DlL9ImJCfsPNU_SgFlRQ", "notes": ""},
    {"channel_id": "UCQsdoxsb3kqgwUrRSnoqJaw", "notes": ""},
    {"channel_id": "UCzfoE4EpXFoGxTnq0uPU4Hw", "notes": ""}
]
config['settings']['videos_per_competitor'] = 10

with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print("Config restored to full mode: 10 channels, 10 videos each")
