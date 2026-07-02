from urllib.parse import quote

from .utils import fetch_json


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