# ============================================================
#  agent_app.py -- 基于 LangGraph 的对话 Agent
#  提供"查时间"和"数学计算"两个工具，AI 根据用户问题自动调用。
# ============================================================

# ---- 标准库（Python 自带的模块）导入 ----
import ast          # 抽象语法树：把字符串表达式解析成树结构，安全求值
import operator     # 运算符函数：如 operator.add 对应 "+" 加法操作
from functools import lru_cache  # 缓存装饰器：函数结果只算一次，后续直接复用
from typing import Any           # 类型提示：Any 表示"任意类型都可以"
from zoneinfo import ZoneInfo    # 时区信息：如 "Asia/Shanghai" 表示上海时区

# ---- 第三方库（LangChain / LangGraph）导入 ----
# 三种消息类型：
#   HumanMessage -> 用户发的消息
#   AIMessage    -> AI 回复的消息
#   ToolMessage  -> 工具执行后返回的结果
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool  # @tool 装饰器：把普通函数注册为 Agent 工具
from langgraph.checkpoint.memory import MemorySaver  # 对话历史保存在内存中（重启丢失）
from langgraph.prebuilt import create_react_agent  # 预构建的 ReAct 循环 Agent

# ---- 本地模块导入 ----
from cc_switch_config import create_chat_model, message_content_to_text
# create_chat_model()      -> 创建大模型实例（OpenAI 等）
# message_content_to_text() -> 把消息内容统一转成纯文本字符串


# ============================================================
#  系统提示词（System Prompt）
#  作用：告诉 AI "你是谁、该怎么回答"，相当于给 AI 设定人设。
# ============================================================
SYSTEM_PROMPT = """你是一个简洁、可靠的 LangGraph Agent。
你可以直接回答普通问题；当用户询问时间或需要数学计算时，主动使用工具。
默认使用中文回答。"""

# ============================================================
#  对话检查点（Checkpoint）
#  MemorySaver 把对话历史保存在内存中，同一 session 的多轮对话
#  可以记住上下文。注意：程序重启后内存数据会丢失。
# ============================================================
_checkpoint = MemorySaver()


# ============================================================
#  工具1：查询当前时间
#  @tool 装饰器把它标记为 Agent 可调用的工具函数
# ============================================================
@tool
def current_time(timezone: str = "Asia/Shanghai") -> str:
    """Get the current date and time for an IANA timezone."""
    from datetime import datetime  # 延迟导入：只在调用时才加载，减少启动开销

    try:
        # 根据用户给的时区名（如 "Asia/Shanghai"）获取当前时间
        now = datetime.now(ZoneInfo(timezone))
    except Exception:
        # 时区名无效时，回退到上海时区
        now = datetime.now(ZoneInfo("Asia/Shanghai"))
        timezone = "Asia/Shanghai"
    # f-string 格式化输出，%Y-%m-%d %H:%M:%S = 年-月-日 时:分:秒
    return f"{timezone}: {now:%Y-%m-%d %H:%M:%S}"


# ============================================================
#  工具2的辅助函数：安全求值数学表达式
#  为什么不用 eval()？因为 eval() 可以执行任意 Python 代码，非常危险！
#  例如 eval("__import__('os').system('rm -rf /')") 会删光所有文件。
#  所以用 ast 模块把表达式解析成语法树，只允许安全的算术运算。
# ============================================================
def _eval_math(node: ast.AST) -> float:
    """递归遍历 AST 节点，只允许基本算术运算，拒绝任何危险操作。

    工作流程：
      1. ast.parse("1+2*3") 把字符串变成一棵语法树
      2. 本函数从根节点开始，逐层向下递归遍历
      3. 每遇到一个节点，检查它是否在白名单中（数字、加减乘除等）
      4. 遇到不允许的节点（如函数调用、属性访问），立刻抛出异常

    Args:
        node: AST 语法树中的某个节点

    Returns:
        该节点代表的数学表达式的计算结果

    Raises:
        ValueError: 遇到不支持的节点类型时抛出
    """
    # 二元运算映射表：AST 运算符类型 -> 对应的 Python 运算函数
    binary_ops = {
        ast.Add: operator.add,          # +  加法
        ast.Sub: operator.sub,          # -  减法
        ast.Mult: operator.mul,         # *  乘法
        ast.Div: operator.truediv,      # /  真除法（5/2=2.5）
        ast.FloorDiv: operator.floordiv,# // 整除（5//2=2）
        ast.Mod: operator.mod,          # %  取余
        ast.Pow: operator.pow,          # ** 幂运算
    }
    # 一元运算映射表：正号和负号
    unary_ops = {
        ast.UAdd: operator.pos,  # +x（正号，不改变值）
        ast.USub: operator.neg,  # -x（负号，取反）
    }

    # 情况1：顶层 Expression 节点 -> 递归处理真正的表达式
    if isinstance(node, ast.Expression):
        return _eval_math(node.body)

    # 情况2：数字常量（如 42、3.14）-> 直接返回数值
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    # 情况3：二元运算（如 a + b、x * y）
    if isinstance(node, ast.BinOp) and type(node.op) in binary_ops:
        left = _eval_math(node.left)    # 递归求值左边
        right = _eval_math(node.right)  # 递归求值右边
        # 安全限制：幂运算的指数不能太大，防止 2**999999 耗尽资源
        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise ValueError("指数过大。")
        # 从映射表取出对应运算函数并执行，如 operator.add(3, 5) -> 8
        return binary_ops[type(node.op)](left, right)

    # 情况4：一元运算（如 -5、+3）
    if isinstance(node, ast.UnaryOp) and type(node.op) in unary_ops:
        return unary_ops[type(node.op)](_eval_math(node.operand))

    # 其他所有情况都不允许，拒绝执行
    raise ValueError("只支持数字和 + - * / // % ** 以及括号。")


# ============================================================
#  工具2：安全计算器
# ============================================================
@tool
def calculator(expression: str) -> str:
    """Safely calculate a basic arithmetic expression."""
    try:
        # ast.parse 把字符串解析为 AST，mode="eval" 表示只接受表达式
        tree = ast.parse(expression, mode="eval")
        # 调用 _eval_math 递归求值
        result = _eval_math(tree)
    except Exception as exc:
        return f"计算失败：{exc}"
    return f"{expression} = {result}"


# ============================================================
#  获取 Agent 实例（带缓存）
#  @lru_cache(maxsize=1)：只缓存 1 个结果，首次调用时创建 Agent，
#  之后每次调用都返回同一个 Agent 对象，避免重复创建。
# ============================================================
@lru_cache(maxsize=1)
def get_agent():
    # 创建大语言模型实例（配置来自 cc_switch_config）
    llm = create_chat_model()
    # create_react_agent 是 LangGraph 提供的预构建 Agent：
    #   llm          -> 使用的大模型
    #   tools        -> 可用的工具列表
    #   prompt       -> 系统提示词
    #   checkpointer -> 对话历史保存方式
    # ReAct = Reasoning(推理) + Acting(行动)，Agent 会先思考再决定是否调用工具
    return create_react_agent(
        llm,
        tools=[current_time, calculator],
        prompt=SYSTEM_PROMPT,
        checkpointer=_checkpoint,
    )


# ============================================================
#  辅助函数：提取本轮对话的消息
#  对话历史可能包含很多轮，此函数只返回最后一轮的消息
#  （即最后一次用户发言之后的所有 AI 回复和工具调用）。
# ============================================================
def _latest_turn_messages(messages: list[Any]) -> list[Any]:
    # 找到最后一条用户消息的位置
    last_human_index = 0
    for index, message in enumerate(messages):
        if isinstance(message, HumanMessage):
            last_human_index = index
    # 返回该用户消息之后的所有消息
    return messages[last_human_index + 1 :]


# ============================================================
#  辅助函数：从消息列表中提取 AI 的文本回复
#  从后往前找第一条有文本内容的 AIMessage。
# ============================================================
def _extract_reply(messages: list[Any]) -> str:
    for message in reversed(messages):  # 从后往前遍历
        if isinstance(message, AIMessage):
            # 消息内容可能是字符串或列表，统一转成文本
            text = message_content_to_text(message.content)
            if text:
                return text
    return ""


# ============================================================
#  辅助函数：提取工具调用的步骤信息
#  返回格式：
#    [{"name": "calculator", "args": {"expression": "1+2"}, "output": "1+2 = 3"}]
#  用于前端展示：AI 调用了哪些工具、传了什么参数、得到什么结果。
# ============================================================
def _extract_steps(messages: list[Any]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []            # 最终返回的步骤列表
    pending_calls: dict[str, dict[str, Any]] = {}  # 等待结果的调用，key=调用ID

    for message in messages:
        if isinstance(message, AIMessage):
            # AI 消息中可能包含 tool_calls（工具调用请求）
            for call in getattr(message, "tool_calls", []) or []:
                step = {
                    "name": call.get("name", "tool"),   # 工具名，如 "calculator"
                    "args": call.get("args", {}),       # 传的参数，如 {"expression": "1+2"}
                    "output": None,                     # 结果暂为空，等 ToolMessage 补上
                }
                # 用调用 ID 记录，后续 ToolMessage 可通过 ID 匹配并填充 output
                pending_calls[call.get("id")] = step
                steps.append(step)
        elif isinstance(message, ToolMessage):
            # 工具执行结果，通过 tool_call_id 找到对应的 step
            step = pending_calls.get(getattr(message, "tool_call_id", None))
            if step is not None:
                step["output"] = message_content_to_text(message.content)

    return steps


# ============================================================
#  主入口函数：运行一轮 Agent 对话
#  这是整个模块对外暴露的核心接口，前端调用它即可获得 AI 回复。
#
#  执行流程：
#    1. 把用户消息包装成 HumanMessage
#    2. 调用 Agent.ainvoke()（异步），Agent 自动进行 ReAct 循环
#    3. 从返回的消息中提取本轮的 AI 回复和工具调用步骤
#    4. 返回结构化结果
# ============================================================
async def run_agent_turn(message: str, session_id: str) -> dict[str, Any]:
    # ainvoke 是异步调用，不会阻塞事件循环
    # thread_id 用来区分不同用户/会话，确保各自的对话历史互不干扰
    result = await get_agent().ainvoke(
        {"messages": [HumanMessage(content=message)]},
        config={"configurable": {"thread_id": session_id}},
    )
    # result["messages"] 包含完整的对话历史（从第一轮到现在的所有消息）
    messages = result["messages"]
    # 只取本轮（最后一次用户发言之后）的消息
    turn_messages = _latest_turn_messages(messages)
    # 返回结构化结果
    return {
        "reply": _extract_reply(turn_messages),   # AI 的最终文本回复
        "steps": _extract_steps(turn_messages),   # 工具调用步骤列表
    }