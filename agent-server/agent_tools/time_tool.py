from datetime import datetime, timezone, timedelta
import re


def get_current_time(tool_input: str = "") -> str:
    value = (tool_input or "").strip()
    if not value:
        return f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    normalized = value.upper().replace(" ", "")
    match = re.fullmatch(r"UTC([+-])(\d{1,2})(?::?(\d{2}))?", normalized)
    if not match:
        return "错误：当前时间工具仅支持空输入或 UTC 偏移，例如 UTC+8、UTC-05:00"

    sign = 1 if match.group(1) == "+" else -1
    hours = int(match.group(2))
    minutes = int(match.group(3) or "0")
    if hours > 14 or minutes > 59:
        return "错误：UTC 偏移范围无效"

    tz = timezone(sign * timedelta(hours=hours, minutes=minutes))
    return f"{value} 当前时间: {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}"