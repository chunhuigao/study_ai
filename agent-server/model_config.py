import json
import os

_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_config.json")

_DEFAULT_CONFIG = {
    "model": "glm-5.2",
    "api_key": "",
    "base_url": None,
    "max_tokens": 65536,
    "temperature": 0.7,
}


def load_config():
    if os.path.exists(_CONFIG_FILE):
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        merged = {**_DEFAULT_CONFIG, **saved}
    else:
        merged = dict(_DEFAULT_CONFIG)
    return merged


def save_config(config):
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


config = load_config()