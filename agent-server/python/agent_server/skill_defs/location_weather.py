SKILL = {
    "id": "location_weather",
    "name": "位置与天气",
    "description": "查询城市地理位置和当前天气。",
    "enabled": True,
    "builtin": True,
    "tools": ["get_city_location", "get_weather"],
    "instructions": "当用户询问城市经纬度、时区或天气时，调用位置与天气工具，并在最终答案中保留工具返回的完整数据。",
}