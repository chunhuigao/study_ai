import contextlib
import io
import json
import sys
from pathlib import Path

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

    return messages


def build_prompt(messages):
    history_lines = []
    for message in messages[:-1]:
        speaker = "用户" if message["role"] == "user" else "助手"
        history_lines.append(f"{speaker}: {message['content']}")

    latest = messages[-1]["content"] if messages else ""
    if history_lines:
        return "以下是此前的多轮对话，请结合上下文回答最后一个问题。\n\n" + "\n".join(
            history_lines
        ) + f"\n\n最后一个问题: {latest}"

    return latest


def call_model(messages):
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
        {"role": "system", "content": zhipu.SYSTEM_PROMPT},
        {"role": "user", "content": f"Question: {build_prompt(chat_messages)}"},
    ]
    trace = []

    for step in range(max_steps):
        full_content, usage = call_model(messages)
        parsed = zhipu.parse_response(full_content)

        trace_item = {
            "step": step + 1,
            "modelOutput": full_content,
            "usage": usage,
            "type": parsed.get("type"),
        }

        if parsed["type"] == "final":
            trace_item["finalAnswer"] = parsed["content"]
            trace.append(trace_item)
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

            if tool_name in zhipu.TOOLS:
                try:
                    observation = zhipu.TOOLS[tool_name](tool_input)
                except Exception as error:
                    observation = f"工具执行出错: {error}"
            else:
                observation = (
                    f"未知工具: {tool_name}，可用工具: {', '.join(zhipu.TOOLS.keys())}"
                )

            trace_item["observation"] = observation
            trace.append(trace_item)
            messages.append({"role": "assistant", "content": full_content})
            messages.append({"role": "user", "content": f"Observation: {observation}"})
            continue

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


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        raw_messages = payload.get("messages", [])
        max_steps = payload.get("maxSteps", 10)
        if not isinstance(max_steps, int) or max_steps < 1:
            max_steps = 10

        with contextlib.redirect_stdout(io.StringIO()):
            result = run_agent_with_history(raw_messages, max_steps=max_steps)

        print(json.dumps(result, ensure_ascii=False))
    except Exception as error:
        print(
            json.dumps(
                {"ok": False, "error": str(error), "answer": "", "trace": []},
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
