import json
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = SERVER_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "model_config.json"
CONFIG_TEMPLATE_FILE = CONFIG_DIR / "model_config.example.json"

_DEFAULT_CONFIG = {
    "model": "glm-5.2",
    "api_key": "",
    "base_url": None,
    "max_tokens": 65536,
    "temperature": 0.7,
}


def load_config():
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            saved = json.load(f)
        merged = {**_DEFAULT_CONFIG, **saved}
    else:
        merged = dict(_DEFAULT_CONFIG)
    return merged


def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


config = load_config()
