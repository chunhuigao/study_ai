from urllib.parse import quote

from .utils import WEATHER_CODES, fetch_json


def get_weather(city: str) -> str:
    """获取城市当前天气。

    获取方式（两步）：
    1. 调用 Open-Meteo Geocoding API，将城市名称转换为经纬度
       - 接口: https://geocoding-api.open-meteo.com/v1/search
       - 参数: name=城市名, language=zh, count=1
    2. 用经纬度调用 Open-Meteo Forecast API 获取实时天气
       - 接口: https://api.open-meteo.com/v1/forecast
       - 参数: latitude/longitude, current=温度/湿度/体感温度/天气代码/风速
       - 天气代码通过 WEATHER_CODES 映射为中文描述
    """
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