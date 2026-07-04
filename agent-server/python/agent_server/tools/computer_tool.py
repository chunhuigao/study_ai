import json
import re
import subprocess


def computer_info(_tool_input: str = "") -> str:
    """Return basic screen and accessibility context for computer use."""
    resolution = _screen_resolution()
    script = """
    tell application "System Events"
      set appName to name of first application process whose frontmost is true
      set winTitle to ""
      try
        tell process appName
          if exists window 1 then set winTitle to name of window 1
        end tell
      end try
      return appName & "\\n" & winTitle
    end tell
    """
    ok, output = _run_osascript(script)
    if not ok:
        return f"屏幕分辨率: {resolution}; {output}"

    lines = output.splitlines()
    app_name = lines[0] if len(lines) > 0 else "未知"
    window_title = lines[1] if len(lines) > 1 else ""
    return f"屏幕分辨率: {resolution}; 前台应用: {app_name}; 当前窗口: {window_title or '无标题'}"


def computer_open(target: str) -> str:
    """Open a URL, app name, or local path through macOS open."""
    value = (target or "").strip()
    if not value:
        return "错误：请输入要打开的 URL、应用名称或文件路径"

    if re.match(r"^https?://", value, re.IGNORECASE):
        cmd = ["open", value]
    elif value.startswith("/") or value.startswith("~"):
        cmd = ["open", value]
    else:
        cmd = ["open", "-a", value]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=10)
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or str(error)).strip()
        return f"打开失败: {detail}"
    except Exception as error:
        return f"打开失败: {error}"

    return f"已请求打开: {value}"


def computer_move_mouse(tool_input: str) -> str:
    x, y = _parse_xy(tool_input)
    if x is None or y is None:
        return '错误：请输入坐标，格式例如 "320,240" 或 {"x":320,"y":240}'

    ok, output = _run_quartz(
        "move",
        {"x": x, "y": y},
    )
    return output if not ok else f"鼠标已移动到: ({x}, {y})"


def computer_click(tool_input: str) -> str:
    x, y = _parse_xy(tool_input)
    if x is None or y is None:
        return '错误：请输入点击坐标，格式例如 "320,240" 或 {"x":320,"y":240}'

    ok, output = _run_quartz(
        "click",
        {"x": x, "y": y},
    )
    return output if not ok else f"已点击坐标: ({x}, {y})"


def computer_type_text(text: str) -> str:
    value = text or ""
    if not value:
        return "错误：请输入要输入的文本"

    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    script = f"""
    tell application "System Events"
      keystroke "{escaped}"
    end tell
    """
    ok, output = _run_osascript(script)
    return output if not ok else f"已输入文本，长度: {len(value)}"


def computer_hotkey(tool_input: str) -> str:
    value = (tool_input or "").strip().lower()
    if not value:
        return '错误：请输入快捷键，例如 "cmd+l"、"cmd+tab"、"cmd+space"、"enter"'

    parts = [part.strip() for part in re.split(r"[+,]", value) if part.strip()]
    key = parts[-1] if parts else ""
    modifiers = parts[:-1]
    modifier_map = {
        "cmd": "command down",
        "command": "command down",
        "ctrl": "control down",
        "control": "control down",
        "alt": "option down",
        "option": "option down",
        "shift": "shift down",
    }

    special_keys = {
        "enter": "return",
        "return": "return",
        "tab": "tab",
        "esc": "escape",
        "escape": "escape",
        "space": "space",
        "delete": "delete",
        "backspace": "delete",
    }

    using = [modifier_map[item] for item in modifiers if item in modifier_map]
    if key in special_keys:
        key_expr = f"key code {_key_code(special_keys[key])}"
        action = key_expr
    elif len(key) == 1:
        action = f'keystroke "{key}"'
    else:
        return f"错误：不支持的快捷键: {tool_input}"

    using_expr = f" using {{{', '.join(using)}}}" if using else ""
    script = f"""
    tell application "System Events"
      {action}{using_expr}
    end tell
    """
    ok, output = _run_osascript(script)
    return output if not ok else f"已执行快捷键: {tool_input}"


def computer_wait(seconds: str) -> str:
    try:
        value = max(0.1, min(float((seconds or "1").strip()), 10.0))
    except ValueError:
        return "错误：请输入等待秒数，例如 1.5"

    script = f"delay {value}"
    ok, output = _run_osascript(script)
    return output if not ok else f"已等待 {value} 秒"


def _parse_xy(raw):
    value = (raw or "").strip()
    if not value:
        return None, None

    try:
        data = json.loads(value)
        if isinstance(data, dict):
            return int(data.get("x")), int(data.get("y"))
        if isinstance(data, list) and len(data) >= 2:
            return int(data[0]), int(data[1])
    except Exception:
        pass

    match = re.search(r"(-?\d+)\s*[,， ]\s*(-?\d+)", value)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def _key_code(key):
    codes = {
        "return": 36,
        "tab": 48,
        "space": 49,
        "delete": 51,
        "escape": 53,
    }
    return codes[key]


def _screen_resolution():
    script = r"""
try:
    import Quartz
    bounds = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
    print(f"{int(bounds.size.width)}x{int(bounds.size.height)}")
except Exception:
    print("未知")
"""
    for python_cmd in ("/usr/bin/python3", "python3"):
        try:
            result = subprocess.run(
                [python_cmd, "-c", script],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except FileNotFoundError:
            continue
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    return "未知"


def _run_osascript(script):
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError:
        return False, "Computer Use 仅支持 macOS osascript 环境"
    except Exception as error:
        return False, f"Computer Use 执行失败: {error}"

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        normalized = detail.lower()
        if (
            "not allowed assistive access" in normalized
            or "not authorized" in normalized
            or "-10822" in detail
            or "-1743" in detail
        ):
            return False, "Computer Use 需要在 macOS 系统设置中授予辅助功能/自动化权限"
        return False, f"Computer Use 执行失败: {detail}"

    return True, result.stdout.strip()


def _run_quartz(action, payload):
    script = r"""
import json
import sys
import time

try:
    import Quartz
except Exception as error:
    print(f"无法加载 Quartz: {error}", file=sys.stderr)
    sys.exit(2)

action = sys.argv[1]
payload = json.loads(sys.argv[2])
x = int(payload["x"])
y = int(payload["y"])
point = (x, y)

if action == "move":
    Quartz.CGWarpMouseCursorPosition(point)
elif action == "click":
    down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, point, Quartz.kCGMouseButtonLeft)
    up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, point, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.05)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
else:
    print(f"未知 Quartz 动作: {action}", file=sys.stderr)
    sys.exit(3)
"""
    encoded = json.dumps(payload)
    for python_cmd in ("/usr/bin/python3", "python3"):
        try:
            result = subprocess.run(
                [python_cmd, "-c", script, action, encoded],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except FileNotFoundError:
            continue
        except Exception as error:
            return False, f"Computer Use 执行失败: {error}"

        if result.returncode == 0:
            return True, result.stdout.strip()

        detail = (result.stderr or result.stdout or "").strip()
        if "No module named" in detail and "Quartz" in detail:
            continue
        return False, f"Computer Use 执行失败: {detail}"

    return False, "Computer Use 需要 macOS Quartz/PyObjC 支持"
