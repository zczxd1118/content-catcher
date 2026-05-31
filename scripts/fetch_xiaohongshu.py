"""
抓取小红书笔记（图文/视频）的元信息和正文。

策略：
  1. 用 urllib 抓 HTML（无需 cookies 也能拿到结构化数据）
  2. 从 HTML 中解析 __INITIAL_STATE__ 或 OG 标签
  3. 失败兜底：用正则提取标题/描述/话题

注意：
  - 小红书反爬较严，第一版只做无需登录的笔记
  - 视频笔记的视频字幕需走 yt-dlp/whisper（参见 catch.py 主调度）
"""
import re
import json
import urllib.request
import urllib.error
from typing import Any


DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def fetch_html(url: str, timeout: int = 20) -> str | None:
    """带浏览器 UA 抓 HTML。"""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": DEFAULT_UA,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            # 小红书可能返回 gbk 或 utf-8
            for enc in ("utf-8", "gbk"):
                try:
                    return data.decode(enc)
                except UnicodeDecodeError:
                    continue
            return data.decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        print(f"[fetch_xiaohongshu] HTTPError {e.code}: {e.reason}")
    except Exception as e:
        print(f"[fetch_xiaohongshu] 抓 HTML 失败：{e}")
    return None


def parse_og_meta(html: str) -> dict:
    """从 OG / meta 标签里解析基础信息（兜底）。"""
    out = {}
    patterns = {
        "title": [
            r'<meta\s+property="og:title"\s+content="([^"]+)"',
            r'<meta\s+name="og:title"\s+content="([^"]+)"',
            r"<title>([^<]+)</title>",
        ],
        "description": [
            r'<meta\s+property="og:description"\s+content="([^"]+)"',
            r'<meta\s+name="description"\s+content="([^"]+)"',
        ],
        "image": [
            r'<meta\s+property="og:image"\s+content="([^"]+)"',
        ],
    }
    for key, plist in patterns.items():
        for p in plist:
            m = re.search(p, html, flags=re.IGNORECASE)
            if m:
                out[key] = m.group(1).strip()
                break
    return out


def parse_initial_state(html: str) -> dict | None:
    """
    尝试从 window.__INITIAL_STATE__ 提取结构化数据。
    """
    m = re.search(r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*</script>", html, flags=re.DOTALL)
    if not m:
        return None
    raw = m.group(1)
    # 小红书会用 undefined，先替换成 null
    raw = re.sub(r"\bundefined\b", "null", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def extract_note_from_state(state: dict) -> dict | None:
    """
    在 INITIAL_STATE 里寻找笔记数据。
    小红书的结构会变，这里做尽可能宽容的搜索。
    """
    def walk(obj: Any, depth: int = 0):
        if depth > 8:
            return
        if isinstance(obj, dict):
            # 典型笔记字段
            keys = obj.keys()
            if {"title", "desc"} <= set(keys) or {"title", "content"} <= set(keys):
                yield obj
            for v in obj.values():
                yield from walk(v, depth + 1)
        elif isinstance(obj, list):
            for v in obj:
                yield from walk(v, depth + 1)

    candidates = list(walk(state))
    if not candidates:
        return None
    # 选 desc/content 最长的那个
    best = max(candidates, key=lambda x: len(str(x.get("desc") or x.get("content") or "")))
    return best


def extract_tags(text: str) -> list[str]:
    """从描述里提取 # 话题标签。"""
    return re.findall(r"#([\w\u4e00-\u9fff]+)", text or "")


def fetch_xiaohongshu(url: str) -> dict:
    """
    抓小红书笔记。返回统一格式：
        {
          "title": str,
          "author": str | None,
          "text": str,            # 笔记正文
          "tags": list[str],
          "kind": "image" | "video" | "unknown",
          "image": str | None,
          "video_url": str | None,
          "source": str,          # 数据来源说明
          "raw_meta": dict,
        }
    """
    html = fetch_html(url)
    if not html:
        return {"error": "html-fetch-failed"}

    og = parse_og_meta(html)
    state = parse_initial_state(html)
    note = extract_note_from_state(state) if state else None

    title = (note or {}).get("title") or og.get("title", "")
    text = (note or {}).get("desc") or (note or {}).get("content") or og.get("description", "")
    author = None
    if note:
        user = note.get("user") or {}
        author = user.get("nickname") or user.get("name")

    # 判断图文 / 视频
    kind = "unknown"
    if note:
        if note.get("type") == "video" or note.get("video"):
            kind = "video"
        elif note.get("type") == "normal" or note.get("imageList") or note.get("images"):
            kind = "image"
    if kind == "unknown":
        # 兜底：URL 里包含 /video/ 或 OG 标签暗示视频
        if "video" in url.lower() or "video" in (og.get("title") or "").lower():
            kind = "video"
        else:
            kind = "image"

    tags = extract_tags(text)
    # 标题里的标签也提取出来
    tags.extend(extract_tags(title))
    tags = list(dict.fromkeys(tags))  # 去重保序

    return {
        "title": title.strip(),
        "author": author,
        "text": text.strip(),
        "tags": tags,
        "kind": kind,
        "image": og.get("image"),
        "video_url": (note or {}).get("video", {}).get("media", {}).get("video", {}).get("url") if note else None,
        "source": "initial_state" if note else ("og_meta" if og else "none"),
        "url": url,
        "raw_meta": og,
    }


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.xiaohongshu.com/explore/abc"
    result = fetch_xiaohongshu(url)
    print(json.dumps(result, ensure_ascii=False, indent=2))
