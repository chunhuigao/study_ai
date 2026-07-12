import json
import os
import sqlite3
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


CC_SWITCH_DB = Path.home() / ".cc-switch" / "cc-switch.db"
DEFAULT_SYSTEM_PROMPT = "你是一个简洁、友好的聊天助手。默认用中文回答用户的问题。"


@dataclass(frozen=True)
class ChatModelConfig:
    provider_name: str
    model: str
    base_url: str | None
    use_responses_api: bool
    reasoning_effort: str | None
    has_api_key: bool


def _read_current_cc_switch_provider() -> dict[str, Any]:
    if not CC_SWITCH_DB.exists():
        return {}

    db_uri = f"file:{CC_SWITCH_DB}?mode=ro"
    with sqlite3.connect(db_uri, uri=True) as conn:
        row = conn.execute(
            """
            select name, settings_config
            from providers
            where app_type = 'codex' and is_current = 1
            limit 1
            """
        ).fetchone()

    if row is None:
        return {}

    name, settings_config = row
    try:
        parsed_settings = json.loads(settings_config)
    except json.JSONDecodeError:
        parsed_settings = {}

    config_text = parsed_settings.get("config") or ""
    try:
        codex_config = tomllib.loads(config_text) if config_text else {}
    except tomllib.TOMLDecodeError:
        codex_config = {}

    return {
        "name": name,
        "auth": parsed_settings.get("auth") or {},
        "config": codex_config,
    }


def load_chat_model_config() -> tuple[ChatModelConfig, str | None]:
    load_dotenv()

    current_provider = _read_current_cc_switch_provider()
    codex_config = current_provider.get("config") or {}
    provider_key = codex_config.get("model_provider")
    provider_config = {}
    if provider_key:
        provider_config = (
            (codex_config.get("model_providers") or {}).get(provider_key) or {}
        )

    api_key = (
        os.getenv("OPENAI_API_KEY")
        or (current_provider.get("auth") or {}).get("OPENAI_API_KEY")
    )
    model = os.getenv("OPENAI_MODEL") or codex_config.get("model") or "gpt-5-nano"
    base_url = (
        os.getenv("OPENAI_BASE_URL")
        or os.getenv("OPENAI_API_BASE")
        or provider_config.get("base_url")
    )
    wire_api = os.getenv("OPENAI_WIRE_API") or provider_config.get("wire_api")
    reasoning_effort = (
        os.getenv("OPENAI_REASONING_EFFORT")
        or codex_config.get("model_reasoning_effort")
    )
    provider_name = (
        provider_config.get("name")
        or current_provider.get("name")
        or "OpenAI"
    )

    return (
        ChatModelConfig(
            provider_name=provider_name,
            model=model,
            base_url=base_url,
            use_responses_api=wire_api == "responses",
            reasoning_effort=reasoning_effort,
            has_api_key=bool(api_key),
        ),
        api_key,
    )


def create_chat_model() -> ChatOpenAI:
    config, api_key = load_chat_model_config()
    if not api_key:
        raise RuntimeError("请先在 .env、环境变量或 cc switch 配置中设置 OPENAI_API_KEY。")

    kwargs: dict[str, Any] = {
        "model": config.model,
        "api_key": api_key,
    }
    if config.base_url:
        kwargs["base_url"] = config.base_url
    if config.use_responses_api:
        kwargs["use_responses_api"] = True
    if config.reasoning_effort:
        kwargs["reasoning_effort"] = config.reasoning_effort

    temperature = os.getenv("OPENAI_TEMPERATURE")
    if temperature is not None:
        kwargs["temperature"] = float(temperature)

    return ChatOpenAI(**kwargs)


def ai_message_to_text(message: Any) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts).strip()
    return str(content)
