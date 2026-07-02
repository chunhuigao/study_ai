from datetime import datetime, timezone, timedelta
from urllib.parse import quote
from urllib.request import urlopen
import json
import re


TOOL_DESC = """
## 扩展工具
- get_current_time: 获取当前日期和时间。输入为空字符串时返回本机当前时间；也可输入 UTC 偏移，例如 "UTC+8"。
- get_city_location: 获取城市地理位置。输入城市名称，例如 "上海" 或 "Beijing"。
- get_weather: 获取城市当前天气。输入城市名称，例如 "上海" 或 "Beijing"。
"""


WEATHER_CODES = {
    0: "晴",
    1: "大部晴朗",
    2: "局部多云",
    3: "阴",
    45: "雾",
    48: "雾凇",
    51: "小毛毛雨",
    53: "中等毛毛雨",
    55: "大毛毛雨",
    56: "小冻毛毛雨",
    57: "大冻毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "小冻雨",
    67: "大冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "小阵雨",
    81: "中等阵雨",
    82: "强阵雨",
    85: "小阵雪",
    86: "强阵雪",
    95: "雷暴",
    96: "雷暴伴小冰雹",
    99: "雷暴伴大冰雹",
}


def fetch_json(url):
    with urlopen(url, timeout=12) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return json.loads(response.read().decode(charset))


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


def get_city_location(city: str) -> str:
    query = (city or "").strip()
    if not query:
        return "错误：请输入城市名称"

    url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={quote(query)}&count=1&language=zh&format=json"
    )

    try:
        data = fetch_json(url)
    except Exception as error:
        return f"获取城市地理位置失败: {error}"

    results = data.get("results") or []
    if not results:
        return f"未找到城市: {query}"

    location = results[0]
    name = location.get("name", query)
    country = location.get("country", "")
    admin1 = location.get("admin1", "")
    latitude = location.get("latitude")
    longitude = location.get("longitude")
    timezone_name = location.get("timezone", "")

    parts = [str(part) for part in [country, admin1, name] if part]
    display_name = " / ".join(parts) if parts else name
    return (
        f"城市: {display_name}; "
        f"纬度: {latitude}; 经度: {longitude}; 时区: {timezone_name}"
    )


def get_weather(city: str) -> str:
    query = (city or "").strip()
    if not query:
        return "错误：请输入城市名称"

    url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={quote(query)}&count=1&language=zh&format=json"
    )

    try:
        location_data = fetch_json(url)
    except Exception as error:
        return f"获取城市地理位置失败: {error}"

    results = location_data.get("results") or []
    if not results:
        return f"未找到城市: {query}"

    location = results[0]
    latitude = location.get("latitude")
    longitude = location.get("longitude")
    if latitude is None or longitude is None:
        return f"城市缺少经纬度信息: {query}"

    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
        "weather_code,wind_speed_10m"
        "&timezone=auto"
    )

    try:
        weather_data = fetch_json(weather_url)
    except Exception as error:
        return f"获取天气失败: {error}"

    current = weather_data.get("current") or {}
    units = weather_data.get("current_units") or {}
    code = current.get("weather_code")
    description = WEATHER_CODES.get(code, f"未知天气代码 {code}")

    name = location.get("name", query)
    country = location.get("country", "")
    admin1 = location.get("admin1", "")
    place = " / ".join(str(part) for part in [country, admin1, name] if part)

    return (
        f"{place} 当前天气: {description}; "
        f"温度: {current.get('temperature_2m')}{units.get('temperature_2m', '')}; "
        f"体感温度: {current.get('apparent_temperature')}{units.get('apparent_temperature', '')}; "
        f"相对湿度: {current.get('relative_humidity_2m')}{units.get('relative_humidity_2m', '')}; "
        f"风速: {current.get('wind_speed_10m')}{units.get('wind_speed_10m', '')}; "
        f"观测时间: {current.get('time')}"
    )


TOOLS = {
    "get_current_time": get_current_time,
    "get_city_location": get_city_location,
    "get_weather": get_weather,
}
