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

AVAILABLE_MODELS = [
    {"id": "glm-5.2", "name": "GLM-5.2", "description": "智谱AI最新旗舰模型，能力最强"},
    {"id": "glm-4-plus", "name": "GLM-4-Plus", "description": "智谱AI高性能模型，性价比高"},
    {"id": "glm-4-flash", "name": "GLM-4-Flash", "description": "智谱AI快速模型，响应最快"},
    {"id": "glm-4-long", "name": "GLM-4-Long", "description": "智谱AI长文本模型，支持128K上下文"},
]


def load_config():
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            saved = json.load(f)
        merged = {**_DEFAULT_CONFIG, **saved}
    else:
        merged = dict(_DEFAULT_CONFIG)
    return merged


def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_available_models():
    current = load_config()
    model_ids = [m["id"] for m in AVAILABLE_MODELS]
    if current.get("model") not in model_ids:
        AVAILABLE_MODELS.append({
            "id": current["model"],
            "name": current["model"],
            "description": "自定义模型",
        })
    return AVAILABLE_MODELS


def switch_model(model_id):
    models = get_available_models()
    model_ids = [m["id"] for m in models]
    if model_id not in model_ids:
        return False, f"未知模型: {model_id}，可用模型: {', '.join(model_ids)}"

    cfg = load_config()
    cfg["model"] = model_id
    save_config(cfg)
    return True, f"已切换到模型: {model_id}"


config = load_config()