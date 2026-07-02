import logging
import sys
from pathlib import Path

from agent_tools import TOOL_DESC as EXTRA_TOOL_DESC
from agent_tools import TOOLS as EXTRA_TOOLS

logger = logging.getLogger("agent")

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    import zhipu
except Exception as import_error:
    zhipu = None
    ZHIPU_IMPORT_ERROR = import_error
else:
    ZHIPU_IMPORT_ERROR = None


def get_tools():
    return {**zhipu.TOOLS, **EXTRA_TOOLS}


def get_system_prompt():
    return (
        f"{zhipu.SYSTEM_PROMPT}\n\n{EXTRA_TOOL_DESC}\n"
        "补充规则：当问题涉及天气、城市经纬度或当前时间时，优先调用对应工具。"
    )


def normalize_messages(raw_messages):
    messages = []
    for item in raw_messages:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content")

        if role not in ("user", "assistant"):
            continue
        if not isinstance(content, str) or not content.strip():
            continue

        messages.append({"role": role, "content": content.strip()})

    logger.info(
        "[normalize_messages] 输入 %d 条 -> 输出 %d 条有效消息",
        len(raw_messages),
        len(messages),
    )
    return messages


def build_prompt(messages):
    history_lines = []
    for message in messages[:-1]:
        speaker = "用户" if message["role"] == "user" else "助手"
        history_lines.append(f"{speaker}: {message['content']}")

    latest = messages[-1]["content"] if messages else ""
    if history_lines:
        prompt = (
            "以下是此前的多轮对话，请结合上下文回答最后一个问题。\n\n"
            + "\n".join(history_lines)
            + f"\n\n最后一个问题: {latest}"
        )
    else:
        prompt = latest

    logger.info(
        "[build_prompt] 构建提示词, 历史轮数=%d, 最新问题=%s",
        len(history_lines),
        latest[:200],
    )
    logger.debug("[build_prompt] 完整提示词: %s", prompt[:1000])
    return prompt


def call_model(messages):
    logger.info("[call_model] 调用模型, 消息条数=%d", len(messages))
    for idx, msg in enumerate(messages):
        logger.debug(
            "[call_model] messages[%d] role=%s content=%s",
            idx,
            msg["role"],
            msg["content"][:300],
        )

    response = zhipu.client.chat.completions.create(
        model="glm-5.2",
        messages=messages,
        max_tokens=65536,
        temperature=0.7,
    )

    content = ""
    usage = None
    for key, value in response:
        if key == "choices":
            content = value[0]["message"].get("content", "")
        elif key == "usage":
            usage = value

    logger.info(
        "[call_model] 模型返回, content长度=%d, usage=%s", len(content), usage
    )
    logger.debug("[call_model] 模型输出: %s", content[:1000])
    return content, usage


def run_agent_with_history(raw_messages, max_steps=10):
    if ZHIPU_IMPORT_ERROR is not None:
        return {
            "ok": False,
            "error": f"无法加载 zhipu.py: {ZHIPU_IMPORT_ERROR}",
            "answer": "",
            "trace": [],
        }

    chat_messages = normalize_messages(raw_messages)
    if not chat_messages:
        return {
            "ok": False,
            "error": "请输入至少一条用户消息。",
            "answer": "",
            "trace": [],
        }

    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": f"Question: {build_prompt(chat_messages)}"},
    ]
    tools = get_tools()
    trace = []

    for step in range(max_steps):
        logger.info("[agent_loop] ===== Step %d/%d =====", step + 1, max_steps)
        full_content, usage = call_model(messages)
        parsed = zhipu.parse_response(full_content)
        logger.info("[agent_loop] 解析结果 type=%s", parsed.get("type"))

        trace_item = {
            "step": step + 1,
            "modelOutput": full_content,
            "usage": usage,
            "type": parsed.get("type"),
        }

        if parsed["type"] == "final":
            trace_item["finalAnswer"] = parsed["content"]
            trace.append(trace_item)
            logger.info("[agent_loop] 最终答案: %s", parsed["content"][:500])
            return {
                "ok": True,
                "answer": parsed["content"],
                "trace": trace,
            }

        if parsed["type"] == "action":
            tool_name = parsed["tool"]
            tool_input = parsed["input"]
            trace_item["tool"] = tool_name
            trace_item["toolInput"] = tool_input
            logger.info(
                "[agent_loop] 调用工具: %s, 输入: %s", tool_name, tool_input[:200]
            )

            if tool_name in tools:
                try:
                    observation = tools[tool_name](tool_input)
                    logger.info(
                        "[agent_loop] 工具返回: %s", str(observation)[:500]
                    )
                except Exception as error:
                    observation = f"工具执行出错: {error}"
                    logger.error("[agent_loop] 工具执行出错: %s", error)
            else:
                observation = (
                    f"未知工具: {tool_name}，可用工具: {', '.join(tools.keys())}"
                )
                logger.warning("[agent_loop] 未知工具: %s", tool_name)

            trace_item["observation"] = observation
            trace.append(trace_item)
            messages.append({"role": "assistant", "content": full_content})
            messages.append({"role": "user", "content": f"Observation: {observation}"})
            continue

        logger.info("[agent_loop] 仅Thought无Action, 提示继续")
        trace.append(trace_item)
        messages.append({"role": "assistant", "content": full_content})
        messages.append(
            {
                "role": "user",
                "content": "请继续。要么给出 Action 调用工具，要么给出 Final Answer。",
            }
        )

    return {
        "ok": False,
        "error": f"已达到最大步骤数 ({max_steps})，未能得出最终答案。",
        "answer": "",
        "trace": trace,
    }