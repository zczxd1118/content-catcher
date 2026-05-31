"""
从播客主站 URL 抓取那一期的 RSS show notes。
适用于 latent.space / acquired.fm / lexfridman.com / substack 等。

工作原理：
1. 已知映射：直接拿 RSS feed URL
2. 未知站点：探测网页 <link rel="alternate" type="application/rss+xml">
3. 解析 RSS，按 link / guid / 标题模糊匹配找到那一期
4. 提取 description / itunes:summary 作为内容
"""
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


# 已知播客 → RSS feed 映射
KNOWN_RSS = {
    "latent.space": "https://api.substack.com/feed/podcast/1084089.rss",
    "acquired.fm": "https://feeds.transistor.fm/acquired",
    "lexfridman.com": "https://lexfridman.com/feed/podcast/",
    "twimlai.com": "https://twimlai.com/feed/podcast/",
    "stratechery.com": "https://stratechery.com/feed/",
    "hubermanlab.com": "https://feeds.megaphone.fm/hubermanlab",
}

NS = {
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
    "content": "http://purl.org/rss/1.0/modules/content/",
}


def http_get(url: str, timeout: int = 30) -> bytes | None:
    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0 Safari/537.36"
        })
        with urlopen(req, timeout=timeout) as r:
            return r.read()
    except (URLError, HTTPError, Exception) as e:
        print(f"   [rss] http get 失败: {e}")
        return None


def find_rss_feed_for_url(url: str) -> str | None:
    """根据 URL 找 RSS feed 地址。"""
    host = (urlparse(url).hostname or "").lower()

    # 1. 已知映射
    for known_host, rss in KNOWN_RSS.items():
        if known_host in host:
            return rss

    # 2. Substack 通用：从网页里找 RSS 链接
    if "substack.com" in host or True:  # 兜底也试一下
        html_bytes = http_get(url)
        if html_bytes:
            html = html_bytes.decode("utf-8", errors="ignore")
            # 找 <link rel="alternate" type="application/rss+xml" href="...">
            for m in re.finditer(
                r'<link[^>]+rel="alternate"[^>]+(?:type="application/rss\+xml"[^>]+href="([^"]+)"|href="([^"]+)"[^>]+type="application/rss\+xml")',
                html,
                re.IGNORECASE,
            ):
                rss_url = m.group(1) or m.group(2)
                if rss_url and rss_url.startswith("http"):
                    return rss_url

    return None


def clean_html(html: str) -> str:
    """清理 HTML，保留段落结构。"""
    # 处理 <br>、</p>
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"</p>", "\n\n", text)
    # 删除其他标签
    text = re.sub(r"<[^>]+>", "", text)
    # 处理 HTML 实体
    text = (text.replace("&nbsp;", " ")
                .replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&quot;", '"')
                .replace("&#39;", "'")
                .replace("&rsquo;", "'")
                .replace("&lsquo;", "'")
                .replace("&ldquo;", '"')
                .replace("&rdquo;", '"'))
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    # 压缩多余空白
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    return text


def normalize(s: str) -> str:
    """标准化字符串用于模糊比对。"""
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", (s or "").lower())


def fetch_episode_from_rss(target_url: str, rss_url: str | None = None) -> dict | None:
    """
    根据目标网页 URL，从 RSS 找到对应那一期的 show notes。
    返回 {title, description, duration_sec, link, audio_url, source_rss}
    或 None。
    """
    if not rss_url:
        rss_url = find_rss_feed_for_url(target_url)
    if not rss_url:
        print(f"   [rss] 找不到 {target_url} 对应的 RSS feed")
        return None

    print(f"   [rss] 用 RSS feed: {rss_url}")
    rss_bytes = http_get(rss_url, timeout=60)
    if not rss_bytes:
        return None

    try:
        root = ET.fromstring(rss_bytes)
    except ET.ParseError as e:
        print(f"   [rss] 解析失败: {e}")
        return None

    items = root.findall(".//item")
    if not items:
        print(f"   [rss] feed 没有 item")
        return None

    # 从 target_url 提取关键词，模糊匹配
    target_norm = normalize(target_url)
    target_path_tail = target_url.rstrip("/").split("/")[-1].lower()

    best = None
    best_score = 0

    for item in items:
        link_el = item.find("link")
        link = link_el.text if link_el is not None else ""
        title_el = item.find("title")
        title = (title_el.text or "") if title_el is not None else ""

        score = 0
        # link 完全相同 / 子串
        if link:
            if link.rstrip("/") == target_url.rstrip("/"):
                score = 1000
            elif normalize(link) == target_norm:
                score = 999
            elif target_path_tail and target_path_tail in link.lower():
                score = 100
            elif normalize(link) in target_norm or target_norm in normalize(link):
                score = 50

        # 标题包含 url path 末尾关键词
        if score < 100 and target_path_tail:
            if target_path_tail in normalize(title):
                score = 80

        if score > best_score:
            best_score = score
            best = item

    if best is None or best_score < 50:
        # fallback：拿最新一期
        print(f"   [rss] 没找到精确匹配（best_score={best_score}），用最新一期")
        best = items[0]

    # 提取信息
    title = (best.find("title").text or "") if best.find("title") is not None else ""
    desc_el = best.find("description")
    desc = desc_el.text if desc_el is not None and desc_el.text else ""

    # itunes:summary 作为备选
    if len(desc) < 500:
        sum_el = best.find("itunes:summary", NS)
        if sum_el is not None and sum_el.text:
            desc = sum_el.text

    # content:encoded 作为备选（更长的版本）
    if len(desc) < 500:
        cont_el = best.find("content:encoded", NS)
        if cont_el is not None and cont_el.text:
            desc = cont_el.text

    desc_clean = clean_html(desc)

    duration = best.find("itunes:duration", NS)
    duration_sec = None
    if duration is not None and duration.text:
        d = duration.text.strip()
        if d.isdigit():
            duration_sec = int(d)
        elif ":" in d:
            parts = [int(x) for x in d.split(":")]
            if len(parts) == 3:
                duration_sec = parts[0] * 3600 + parts[1] * 60 + parts[2]
            elif len(parts) == 2:
                duration_sec = parts[0] * 60 + parts[1]

    enc = best.find("enclosure")
    audio_url = enc.get("url") if enc is not None else None
    link_el = best.find("link")
    link_url = link_el.text if link_el is not None else None

    return {
        "title": title,
        "description": desc_clean,
        "duration_sec": duration_sec,
        "link": link_url,
        "audio_url": audio_url,
        "source_rss": rss_url,
        "match_score": best_score,
    }


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.latent.space/p/esmfold2"
    result = fetch_episode_from_rss(url)
    if result:
        print(f"\n标题：{result['title']}")
        print(f"时长：{result['duration_sec']} 秒")
        print(f"匹配分：{result['match_score']}")
        print(f"内容字数：{len(result['description'])}")
        print(f"\n=== 前 500 字符 ===")
        print(result["description"][:500])
    else:
        print("❌ 没拿到")
