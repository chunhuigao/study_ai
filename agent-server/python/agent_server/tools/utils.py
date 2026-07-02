import json
import os
import ssl
from urllib.request import urlopen


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


def _create_ssl_context():
    ctx = ssl.create_default_context()
    certifi_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "certifi.pem"
    )
    if os.path.exists(certifi_path):
        ctx.load_verify_locations(certifi_path)
        return ctx

    try:
        import certifi
        ctx.load_verify_locations(certifi.where())
        return ctx
    except ImportError:
        pass

    try:
        import pip._vendor.certifi as _certifi
        ctx.load_verify_locations(_certifi.where())
        return ctx
    except (ImportError, AttributeError):
        pass

    return ctx


_SSL_CONTEXT = _create_ssl_context()


def fetch_json(url):
    with urlopen(url, timeout=12, context=_SSL_CONTEXT) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return json.loads(response.read().decode(charset))


def fetch_html(url, headers=None):
    from urllib.request import Request

    req = Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)
    with urlopen(req, timeout=15, context=_SSL_CONTEXT) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")