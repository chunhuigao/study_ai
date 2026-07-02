import logging
import sys
from pathlib import Path

from agent_tools import TOOL_DESC as EXTRA_TOOL_DESC
from agent_tools import TOOLS as EXTRA_TOOLS
from model_config import config
from zai import ZhipuAiClient

logger = logging.getLogger("agent")

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    _api_key = config["api_key"]
    if not _api_key:
        raise ValueError("model_config.json 中 api_key 为空，请先配置")
    client = ZhipuAiClient(
        api_key=_api_key,
        base_url=config.get("base_url"),
    )
except Exception as import_error:
    client = None
    CLIENT_INIT_ERROR = import_error
else:
    CLIENT_INIT_ERROR = None


BUILTIN_TOOLS = {}

BUILTIN_TOOL_DESC = ""

SYSTEM_PROMPT = f"""你是一个具有工具调用能力的AI助手，请通过"思考→行动→观察"的循环来回答问题。

{BUILTIN_TOOL_DESC}

你必须严格按照以下格式回复：

Thought: 分析当前情况，思考下一步该做什么
Action: 工具名称: 工具的输入参数
Observation: 工具返回的结果
...（重复 Thought/Action/Observation 直到获得足够信息）
Thought: 我已经获得足够信息
Final Answer: 对用户的最终回答

规则：
- 每次只能调用一个工具
- 得到 Observation 后必须继续 Thought
- 不要编造工具结果，必须等待实际 Observation
- 一旦有了答案，立即输出 Final Answer
- Final Answer 必须包含工具返回的完整数据，不要省略或概括。例如查询天气时，必须包含温度、体感温度、湿度、风速等全部信息；查询时间时，必须包含完整的日期和时间
"""


def get_tools():
    return {**BUILTIN_TOOLS, **EXTRA_TOOLS}


def get_system_prompt():
    return (
        f"{SYSTEM_PROMPT}\n\n{EXTRA_TOOL_DESC}\n"
        "补充规则：当问题涉及天气、城市经纬度或当前时间时，优先调用对应工具。"
    )


def parse_response(text: str) -> dict:
    lines = text.strip().split("\n")

    action_line = None
    final_answer_idx = None

    for i, line in enumerate(lines):
        if line.startswith("Action:") and action_line is None:
            action_line = line
        if line.startswith("Final Answer:") and final_answer_idx is None:
            final_answer_idx = i

    if action_line is not None:
        raw = action_line[len("Action:"):].strip()
        colon_pos = raw.find(":")
        if colon_pos != -1:
            tool_name = raw[:colon_pos].strip()
            tool_input = raw[colon_pos + 1:].strip()
            return {"type": "action", "tool": tool_name, "input": tool_input}
        else:
            return {"type": "action", "tool": raw, "input": ""}

    if final_answer_idx is not None:
        first_line = lines[final_answer_idx][len("Final Answer:"):].strip()
        remaining = "\n".join(lines[final_answer_idx + 1:]).strip()
        content = f"{first_line}\n{remaining}" if remaining else first_line
        return {"type": "final", "content": content.strip()}

    return {"type": "thought", "content": text}


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
    if CLIENT_INIT_ERROR is not None:
        raise CLIENT_INIT_ERROR

    logger.info(
        "[call_model] 调用模型 %s, 消息条数=%d", config["model"], len(messages)
    )
    for idx, msg in enumerate(messages):
        logger.debug(
            "[call_model] messages[%d] role=%s content=%s",
            idx,
            msg["role"],
            msg["content"][:300],
        )

    response = client.chat.completions.create(
        model=config["model"],
        messages=messages,
        max_tokens=config.get("max_tokens", 65536),
        temperature=config.get("temperature", 0.7),
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
    if CLIENT_INIT_ERROR is not None:
        return {
            "ok": False,
            "error": f"无法初始化模型客户端: {CLIENT_INIT_ERROR}",
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
        parsed = parse_response(full_content)
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