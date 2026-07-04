import json
from pathlib import Path

from .skill_defs import get_builtin_skills
from .tools import TOOL_DESCRIPTIONS, TOOLS

SERVER_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = SERVER_DIR / "config"
SKILLS_FILE = CONFIG_DIR / "skills.json"


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
        for skill in get_builtin_skills()
    }
    configured = _load_configured_skills()

    result = dict(builtin_by_id)
    for skill in configured:
        if skill["id"] in builtin_by_id:
            builtin_skill = builtin_by_id[skill["id"]]
            merged_tools = [
                *builtin_skill.get("tools", []),
                *[
                    tool_name
                    for tool_name in skill.get("tools", [])
                    if tool_name not in builtin_skill.get("tools", [])
                ],
            ]
            merged = {
                **builtin_skill,
                **skill,
                "name": builtin_skill["name"],
                "description": builtin_skill["description"],
                "builtin": True,
                "tools": merged_tools,
                "instructions": _merge_builtin_instructions(
                    builtin_skill.get("instructions", ""),
                    skill.get("instructions", ""),
                ),
            }
            result[skill["id"]] = merged
        else:
            result[skill["id"]] = skill

    return list(result.values())


def _merge_builtin_instructions(builtin_instructions, configured_instructions):
    builtin_text = (builtin_instructions or "").strip()
    configured_text = (configured_instructions or "").strip()
    if not configured_text or configured_text == builtin_text:
        return builtin_text
    if configured_text in builtin_text:
        return builtin_text

    extra_parts = []
    for part in _split_instruction_parts(configured_text):
        if part and not _instruction_part_is_covered(part, builtin_text):
            extra_parts.append(part)
    if not extra_parts:
        return builtin_text
    extra_text = "；".join(extra_parts)
    return f"{builtin_text} 本地补充规则: {extra_text}" if builtin_text else extra_text


def _split_instruction_parts(text):
    return [
        part.strip()
        for part in text.replace("。", "；").replace(";", "；").split("；")
        if part.strip()
    ]


def _instruction_part_is_covered(part, builtin_text):
    if part in builtin_text:
        return True

    normalized_part = _normalize_instruction_text(part)
    normalized_builtin = _normalize_instruction_text(builtin_text)
    if normalized_part and normalized_part in normalized_builtin:
        return True

    keywords = {
        "只有当用户明确要求操作电脑、浏览器或桌面应用时才使用": ("明确要求", "电脑", "浏览器", "桌面应用"),
        "执行点击和输入前，先用 computer_info 确认当前前台应用": ("点击", "输入", "computer_info"),
        "不要执行删除文件、提交表单、购买、转账或其他高风险操作": ("删除文件", "提交表单", "购买", "转账", "高风险"),
    }
    for known_part, required_keywords in keywords.items():
        if known_part in part:
            return all(keyword in builtin_text for keyword in required_keywords)
    return False


def _normalize_instruction_text(text):
    return "".join(str(text).replace("登陆", "登录").split())


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
    if skill["id"] in {item["id"] for item in get_builtin_skills()}:
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
