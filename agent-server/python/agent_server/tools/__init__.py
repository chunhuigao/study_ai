from .time_tool import get_current_time
from .location_tool import get_city_location
from .weather_tool import get_weather
from .web_search_tool import web_search
from .read_webpage_tool import read_webpage
from .computer_tool import (
    computer_click,
    computer_hotkey,
    computer_info,
    computer_move_mouse,
    computer_open,
    computer_type_text,
    computer_wait,
)

TOOLS = {
    "get_current_time": get_current_time,
    "get_city_location": get_city_location,
    "get_weather": get_weather,
    "web_search": web_search,
    "read_webpage": read_webpage,
    "computer_info": computer_info,
    "computer_open": computer_open,
    "computer_move_mouse": computer_move_mouse,
    "computer_click": computer_click,
    "computer_type_text": computer_type_text,
    "computer_hotkey": computer_hotkey,
    "computer_wait": computer_wait,
}

TOOL_DESCRIPTIONS = {
    "get_current_time": '获取当前日期和时间。输入为空字符串时返回本机当前时间；也可输入 UTC 偏移，例如 "UTC+8"。',
    "get_city_location": '获取城市地理位置。输入城市名称，例如 "上海" 或 "Beijing"。',
    "get_weather": '获取城市当前天气。输入城市名称，例如 "上海" 或 "Beijing"。',
    "web_search": '联网搜索。输入搜索关键词，例如 "Python 最新版本" 或 "2026年世界杯"。',
    "read_webpage": '根据 URL 读取网页正文内容。输入网页 URL，例如 "https://example.com/article"。',
    "computer_info": "获取屏幕分辨率、前台应用和当前窗口标题。",
    "computer_open": '打开 URL、应用名称或本地路径。输入例如 "https://example.com" 或 "Safari"。',
    "computer_move_mouse": '移动鼠标到指定坐标。输入例如 "320,240" 或 {"x":320,"y":240}。',
    "computer_click": '点击指定屏幕坐标。输入例如 "320,240" 或 {"x":320,"y":240}。',
    "computer_type_text": "向当前焦点输入文本。",
    "computer_hotkey": '执行快捷键。输入例如 "cmd+l"、"cmd+tab"、"enter"。',
    "computer_wait": "等待指定秒数，最多 10 秒。",
}

TOOL_DESC = "## 扩展工具\n" + "\n".join(
    f"- {name}: {description}"
    for name, description in TOOL_DESCRIPTIONS.items()
)
