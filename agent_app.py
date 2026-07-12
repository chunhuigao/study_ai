import ast
import operator
from functools import lru_cache
from typing import Any
from zoneinfo import ZoneInfo

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from cc_switch_config import create_chat_model, message_content_to_text


SYSTEM_PROMPT = """你是一个简洁、可靠的 LangGraph Agent。
你可以直接回答普通问题；当用户询问时间或需要数学计算时，主动使用工具。
默认使用中文回答。"""

_checkpoint = MemorySaver()


@tool
def current_time(timezone: str = "Asia/Shanghai") -> str:
    """Get the current date and time for an IANA timezone."""
    from datetime import datetime

    try:
        now = datetime.now(ZoneInfo(timezone))
    except Exception:
        now = datetime.now(ZoneInfo("Asia/Shanghai"))
        timezone = "Asia/Shanghai"
    return f"{timezone}: {now:%Y-%m-%d %H:%M:%S}"


def _eval_math(node: ast.AST) -> float:
    binary_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    unary_ops = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    if isinstance(node, ast.Expression):
        return _eval_math(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in binary_ops:
        left = _eval_math(node.left)
        right = _eval_math(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise ValueError("指数过大。")
        return binary_ops[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in unary_ops:
        return unary_ops[type(node.op)](_eval_math(node.operand))
    raise ValueError("只支持数字和 + - * / // % ** 以及括号。")


@tool
def calculator(expression: str) -> str:
    """Safely calculate a basic arithmetic expression."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_math(tree)
    except Exception as exc:
        return f"计算失败：{exc}"
    return f"{expression} = {result}"


@lru_cache(maxsize=1)
def get_agent():
    llm = create_chat_model()
    return create_react_agent(
        llm,
        tools=[current_time, calculator],
        prompt=SYSTEM_PROMPT,
        checkpointer=_checkpoint,
    )


def _latest_turn_messages(messages: list[Any]) -> list[Any]:
    last_human_index = 0
    for index, message in enumerate(messages):
        if isinstance(message, HumanMessage):
            last_human_index = index
    return messages[last_human_index + 1 :]


def _extract_reply(messages: list[Any]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            text = message_content_to_text(message.content)
            if text:
                return text
    return ""


def _extract_steps(messages: list[Any]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    pending_calls: dict[str, dict[str, Any]] = {}

    for message in messages:
        if isinstance(message, AIMessage):
            for call in getattr(message, "tool_calls", []) or []:
                step = {
                    "name": call.get("name", "tool"),
                    "args": call.get("args", {}),
                    "output": None,
                }
                pending_calls[call.get("id")] = step
                steps.append(step)
        elif isinstance(message, ToolMessage):
            step = pending_calls.get(getattr(message, "tool_call_id", None))
            if step is not None:
                step["output"] = message_content_to_text(message.content)

    return steps


async def run_agent_turn(message: str, session_id: str) -> dict[str, Any]:
    result = await get_agent().ainvoke(
        {"messages": [HumanMessage(content=message)]},
        config={"configurable": {"thread_id": session_id}},
    )
    messages = result["messages"]
    turn_messages = _latest_turn_messages(messages)
    return {
        "reply": _extract_reply(turn_messages),
        "steps": _extract_steps(turn_messages),
    }
