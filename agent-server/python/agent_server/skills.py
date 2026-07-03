import json
from pathlib import Path

from .tools import TOOL_DESCRIPTIONS, TOOLS

SERVER_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = SERVER_DIR / "config"
SKILLS_FILE = CONFIG_DIR / "skills.json"


BUILTIN_SKILLS = [
    {
        "id": "time",
        "name": "时间助手",
        "description": "获取当前时间，支持 UTC 偏移。",
        "enabled": True,
        "builtin": True,
        "tools": ["get_current_time"],
        "instructions": "当用户询问当前时间、日期或指定 UTC 偏移时间时，调用 get_current_time。",
    },
    {
        "id": "location_weather",
        "name": "位置与天气",
        "description": "查询城市地理位置和当前天气。",
        "enabled": True,
        "builtin": True,
        "tools": ["get_city_location", "get_weather"],
        "instructions": "当用户询问城市经纬度、时区或天气时，调用位置与天气工具，并在最终答案中保留工具返回的完整数据。",
    },
    {
        "id": "web_research",
        "name": "网页研究",
        "description": "联网搜索并读取网页内容。",
        "enabled": True,
        "builtin": True,
        "tools": ["web_search", "read_webpage"],
        "instructions": "当用户需要最新信息、网页资料或要求读取 URL 时，优先使用 web_search 或 read_webpage。",
    },
]


def _normalize_tool_names(tool_names):
    if not isinstance(tool_names, list):
        return []
    result = []
    for name in tool_names:
        if isinstance(name, str) and name in TOOLS and name not in result:
            result.append(name)
    return result


def _normalize_skill(raw_skill, *, builtin=False):
    if not isinstance(raw_skill, dict):
        return None

    skill_id = str(raw_skill.get("id", "")).strip()
    name = str(raw_skill.get("name", "")).strip()
    if not skill_id or not name:
        return None

    return {
        "id": skill_id,
        "name": name,
        "description": str(raw_skill.get("description", "")).strip(),
        "enabled": bool(raw_skill.get("enabled", True)),
        "builtin": bool(raw_skill.get("builtin", builtin)),
        "tools": _normalize_tool_names(raw_skill.get("tools", [])),
        "instructions": str(raw_skill.get("instructions", "")).strip(),
    }


def _load_configured_skills():
    if not SKILLS_FILE.exists():
        return []
    try:
        data = json.loads(SKILLS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    raw_skills = data.get("skills", data if isinstance(data, list) else [])
    if not isinstance(raw_skills, list):
        return []

    configured = []
    for item in raw_skills:
        skill = _normalize_skill(item)
        if skill:
            configured.append(skill)
    return configured


def load_skills():
    builtin_by_id = {
        skill["id"]: _normalize_skill(skill, builtin=True)
        for skill in BUILTIN_SKILLS
    }
    configured = _load_configured_skills()

    result = dict(builtin_by_id)
    for skill in configured:
        if skill["id"] in builtin_by_id:
            merged = {**builtin_by_id[skill["id"]], **skill, "builtin": True}
            result[skill["id"]] = merged
        else:
            result[skill["id"]] = skill

    return list(result.values())


def save_configured_skills(skills):
    custom_skills = []
    builtin_overrides = []

    for raw_skill in skills:
        skill = _normalize_skill(raw_skill)
        if not skill:
            continue
        if skill["builtin"]:
            builtin_overrides.append(skill)
        else:
            custom_skills.append(skill)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"skills": [*builtin_overrides, *custom_skills]}
    SKILLS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def set_skill_enabled(skill_id, enabled):
    skills = load_skills()
    found = False
    for skill in skills:
        if skill["id"] == skill_id:
            skill["enabled"] = bool(enabled)
            found = True
            break

    if not found:
        return False, f"未知 skill: {skill_id}"

    save_configured_skills(skills)
    return True, "已更新 skill 状态"


def upsert_skill(skill_data):
    skill = _normalize_skill({**skill_data, "builtin": False})
    if not skill:
        return False, "skill 配置无效", None
    if skill["id"] in {item["id"] for item in BUILTIN_SKILLS}:
        return False, "不能覆盖内置 skill，请使用其他 id", None

    skills = [item for item in load_skills() if item["id"] != skill["id"]]
    skills.append(skill)
    save_configured_skills(skills)
    return True, "已保存 skill", skill


def get_enabled_tools_and_prompt():
    enabled_skills = [skill for skill in load_skills() if skill["enabled"]]
    tool_names = []
    prompt_lines = ["## Skills"]

    for skill in enabled_skills:
        prompt_lines.append(f"- {skill['name']} ({skill['id']}): {skill['description']}")
        if skill["instructions"]:
            prompt_lines.append(f"  使用规则: {skill['instructions']}")
        if skill["tools"]:
            prompt_lines.append(f"  可用工具: {', '.join(skill['tools'])}")
        for tool_name in skill["tools"]:
            if tool_name not in tool_names:
                tool_names.append(tool_name)

    enabled_tools = {name: TOOLS[name] for name in tool_names if name in TOOLS}
    if enabled_tools:
        prompt_lines.append("")
        prompt_lines.append("## 启用工具")
        for tool_name in tool_names:
            description = TOOL_DESCRIPTIONS.get(tool_name, "")
            prompt_lines.append(f"- {tool_name}: {description}")
    return enabled_tools, "\n".join(prompt_lines)


def list_skill_payload():
    return {
        "skills": load_skills(),
        "availableTools": sorted(TOOLS.keys()),
    }
