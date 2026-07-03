import re

from .utils import fetch_html


def read_webpage(url: str) -> str:
    """
    根据 URL 读取网页内容，提取正文文本返回给 Agent。

    流程：
    1. 请求目标 URL 获取 HTML
    2. 移除 script、style、nav、footer 等非正文标签
    3. 将 HTML 转为纯文本，清理多余空白
    4. 返回完整文本内容

    Args:
        url: 目标网页 URL，例如 "https://example.com/article"
    """
    url = (url or "").strip()
    if not url:
        return "错误：请输入网页 URL"

    if not re.match(r"^https?://", url, re.IGNORECASE):
        return '错误：URL 必须以 http:// 或 https:// 开头'

    try:
        html = fetch_html(url)
    except Exception as error:
        return f"读取网页失败: {error}"

    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<header[^>]*>.*?</header>', '', html, flags=re.DOTALL | re.IGNORECASE)

    title_m = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
    title = _strip_tags(title_m.group(1)).strip() if title_m else ""

    text = _strip_tags(html)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    lines = []
    if title:
        lines.append(f"标题: {title}")
        lines.append(f"来源: {url}")
        lines.append("")
    lines.append(text)

    return "\n".join(lines)


def _strip_tags(html: str) -> str:
    text = re.sub(r'<br\s*/?>|</?p[^>]*>', '\n', html, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    text = text.replace("&nbsp;", " ")
    text = re.sub(r'[ \t]+', ' ', text)
    return text