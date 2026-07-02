import re
from urllib.parse import quote_plus

from .utils import fetch_html


def web_search(query: str) -> str:
    """
    联网搜索工具，使用 Bing 搜索引擎获取搜索结果。

    流程：
    1. 将用户查询关键词编码后，请求 Bing 搜索页面
    2. 从返回的 HTML 中解析出搜索结果条目（标题 + 摘要 + 链接）
    3. 取前 5 条结果，格式化返回给 Agent

    Args:
        query: 搜索关键词，例如 "Python 最新版本" 或 "杭州亚运会"
    """
    query = (query or "").strip()
    if not query:
        return "错误：请输入搜索关键词"

    url = f"https://www.bing.com/search?q={quote_plus(query)}&setlang=zh-Hans"

    try:
        html = fetch_html(url)
    except Exception as error:
        return f"搜索失败: {error}"

    results = []
    for match in re.finditer(
        r'<li class="b_algo"[^>]*>(.*?)</li>', html, re.DOTALL
    ):
        block = match.group(1)
        title_m = re.search(r'<h2[^>]*><a[^>]*>(.*?)</a>', block, re.DOTALL)
        snippet_m = re.search(
            r'<div[^>]+class="b_caption"[^>]*>.*?<p[^>]*>(.*?)</p>',
            block,
            re.DOTALL,
        )
        if not snippet_m:
            snippet_m = re.search(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
        href_m = re.search(r'<h2[^>]*><a[^>]+href="([^"]*)"', block)

        title = _strip_tags(title_m.group(1)).strip() if title_m else ""
        snippet = _strip_tags(snippet_m.group(1)).strip() if snippet_m else ""
        link = href_m.group(1).strip() if href_m else ""

        if title:
            results.append({"title": title, "snippet": snippet, "link": link})

    if not results:
        return f"未找到与 \"{query}\" 相关的搜索结果"

    top = results[:5]
    lines = [f"搜索关键词: {query}", f"共找到 {len(results)} 条结果，显示前 {len(top)} 条:", ""]
    for i, item in enumerate(top, 1):
        lines.append(f"{i}. {item['title']}")
        if item["snippet"]:
            lines.append(f"   摘要: {item['snippet']}")
        if item["link"]:
            lines.append(f"   来源: {item['link']}")
        lines.append("")

    return "\n".join(lines)


def _strip_tags(html: str) -> str:
    text = re.sub(r"<[^>]+>", "", html)
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    text = re.sub(r"\s+", " ", text)
    return text