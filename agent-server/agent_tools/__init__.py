from .time_tool import get_current_time
from .location_tool import get_city_location
from .weather_tool import get_weather

TOOLS = {
    "get_current_time": get_current_time,
    "get_city_location": get_city_location,
    "get_weather": get_weather,
}

TOOL_DESC = """
## 扩展工具
- get_current_time: 获取当前日期和时间。输入为空字符串时返回本机当前时间；也可输入 UTC 偏移，例如 "UTC+8"。
- get_city_location: 获取城市地理位置。输入城市名称，例如 "上海" 或 "Beijing"。
- get_weather: 获取城市当前天气。输入城市名称，例如 "上海" 或 "Beijing"。
"""