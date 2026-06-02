"""
订阅扫描：根据 channels.yaml 找出"上周"每个频道发了什么新内容。

实现策略（不依赖任何官方 API key）：
  - YouTube 频道：用 RSS（https://www.youtube.com/feeds/videos.xml?channel_id=XXX）
  - B 站 up 主：用 B 站 RSS 镜像 / yt-dlp 扫频道
  - 通用 RSS：直接解析 RSS XML
"""
import sys
import urllib.request
import urllib.error
import re
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET


DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
)

YT_RSS = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
YT_RSS_PLAYLIST = "https://www.youtube.com/feeds/videos.xml?playlist_id={playlist_id}"
YT_HANDLE_PAGE = "https://www.youtube.com/{handle}"

# 第三方代理 fallback（按可靠性排序，每个里面 {cid} 会被替换为 channel_id）
# 这些是"备胎中的备胎"——只在 YouTube 原生 endpoint 持续失败时启用
YT_RSS_FALLBACK_PROXIES = [
    "https://rsshub.app/youtube/channel/{cid}",          # RSSHub 官方主站
    "https://rsshub.rssforever.com/youtube/channel/{cid}",  # 国内可用的 RSSHub 镜像
    "https://yewtu.be/feed/channel/{cid}",               # Invidious 公共实例
    "https://invidious.fdn.fr/feed/channel/{cid}",       # Invidious 备用
]


def http_get(url: str, timeout: int = 20, quiet: bool = False,
             retries: int = 1, backoff: float = 1.0) -> bytes | None:
    """HTTP GET，支持简单的指数退避重试（针对 YouTube 这种间歇性 5xx 友好）。"""
    import time as _t
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_UA})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as e:
            last_err = e
            if attempt < retries:
                _t.sleep(backoff * (2 ** attempt))
    if not quiet:
        print(f"   [http_get] {url[:80]} → {last_err}", file=sys.stderr)
    return None


# ---------- YouTube ----------

def resolve_handle_to_channel_id(handle: str) -> str | None:
    """从 @handle 解析 channel_id（抓主页 HTML）。"""
    if not handle.startswith("@"):
        handle = "@" + handle
    html = http_get(YT_HANDLE_PAGE.format(handle=handle))
    if not html:
        return None
    text = html.decode("utf-8", errors="ignore")
    m = re.search(r'"channelId":"(UC[\w-]+)"', text) or \
        re.search(r'"externalId":"(UC[\w-]+)"', text)
    return m.group(1) if m else None


def _parse_youtube_atom(xml: bytes, source_name: str) -> list[dict]:
    """解析 YouTube Atom feed（原生 videos.xml + openrss 都是 Atom 格式）。
    返回 [] 表示空 feed（视为这一路 fetch 失败）。"""
    items: list[dict] = []
    try:
        ns = {"atom": "http://www.w3.org/2005/Atom",
              "media": "http://search.yahoo.com/mrss/",
              "yt": "http://www.youtube.com/xml/schemas/2015"}
        root = ET.fromstring(xml)
        for entry in root.findall("atom:entry", ns):
            vid_el = entry.find("yt:videoId", ns)
            title = entry.find("atom:title", ns)
            published = entry.find("atom:published", ns)
            link = entry.find("atom:link", ns)

            # openrss 没有 yt:videoId namespace，从 <link href> 解析
            vid = None
            if vid_el is not None and vid_el.text:
                vid = vid_el.text.strip()
            elif link is not None:
                href = link.attrib.get("href", "")
                m = re.search(r"v=([\w-]{11})", href) or re.search(r"/([\w-]{11})$", href)
                if m:
                    vid = m.group(1)

            if not vid or title is None:
                continue

            items.append({
                "url": f"https://www.youtube.com/watch?v={vid}",
                "title": (title.text or "").strip(),
                "published": published.text if published is not None else None,
                "source_name": source_name,
                "source_type": "youtube_channel",
            })
    except ET.ParseError as e:
        # XML 解析失败，让上层试下一个 fetcher
        return []
    except Exception as e:
        print(f"   [{source_name}] 解析 YouTube feed 异常：{e}")
        return []
    return items


def _fetch_youtube_feed(channel_id: str, source_name: str) -> list[dict]:
    """YouTube feed fetcher chain（按稳定性 / 速度排序）：
      1. 原生 videos.xml?channel_id=UCxxx           —— YouTube 官方，有重试
      2. videos.xml?playlist_id=UULFxxx             —— UC→UULF 变体，自动滤 Shorts
      3. RSSHub / Invidious 公共实例（第三方代理）  —— 备胎中的备胎，可能限流

    背景：YouTube 在 2025 年开始让原生 videos.xml endpoint 间歇性 5xx/404
    （见 Open RSS 项目对 YouTube 的公开投诉）。靠重试 + 多 fetcher 来兜底。

    任何一路返回非空 items 立即停止；全失败时返回 []。
    """
    # 1. 原生 channel_id（带 2 次重试）
    xml = http_get(YT_RSS.format(channel_id=channel_id), quiet=True, retries=2)
    if xml:
        items = _parse_youtube_atom(xml, source_name)
        if items:
            return items
        print(f"   [{source_name}] 原生 videos.xml 返回但 0 item，尝试 fallback...")
    else:
        print(f"   [{source_name}] 原生 videos.xml 失败，尝试 fallback...")

    # 2. UC→UULF playlist_id（同源 endpoint 但走另一条 backend 路径）
    if channel_id.startswith("UC"):
        playlist_id = "UULF" + channel_id[2:]
        xml = http_get(YT_RSS_PLAYLIST.format(playlist_id=playlist_id),
                       quiet=True, retries=1)
        if xml:
            items = _parse_youtube_atom(xml, source_name)
            if items:
                print(f"   [{source_name}] ✅ UULF playlist 后备生效")
                return items

    # 3. 第三方代理逐个试
    for proxy_template in YT_RSS_FALLBACK_PROXIES:
        url = proxy_template.format(cid=channel_id)
        xml = http_get(url, quiet=True, timeout=15)
        if xml:
            items = _parse_youtube_atom(xml, source_name)
            if items:
                host = url.split("/")[2]
                print(f"   [{source_name}] ✅ 代理 {host} 生效")
                return items

    print(f"   [{source_name}] ❌ 所有 YouTube fetcher 全部失败")
    return []


def scan_youtube_channel(cfg: dict) -> list[dict]:
    """返回 [{url, title, published, source_name}, ...]"""
    cid = cfg.get("channel_id")
    if not cid and cfg.get("handle"):
        cid = resolve_handle_to_channel_id(cfg["handle"])
        if cid:
            print(f"   [{cfg['name']}] handle 解析到 channel_id={cid}")
    if not cid:
        print(f"   [{cfg['name']}] 缺 channel_id，跳过")
        return []

    return _fetch_youtube_feed(cid, cfg["name"])


# ---------- 通用 RSS ----------

def scan_rss(cfg: dict) -> list[dict]:
    url = cfg.get("url")
    if not url:
        return []
    xml = http_get(url)
    if not xml:
        return []

    items = []
    try:
        root = ET.fromstring(xml)
        # RSS 2.0 / Atom 都支持
        for item in root.findall(".//item"):
            link = item.find("link")
            title = item.find("title")
            pub = item.find("pubDate")
            if link is None or title is None:
                continue
            items.append({
                "url": (link.text or "").strip(),
                "title": (title.text or "").strip(),
                "published": pub.text if pub is not None else None,
                "source_name": cfg["name"],
                "source_type": "rss",
            })
        # 兜底：Atom
        if not items:
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns):
                link_el = entry.find("atom:link", ns)
                title_el = entry.find("atom:title", ns)
                pub_el = entry.find("atom:published", ns) or entry.find("atom:updated", ns)
                if link_el is None or title_el is None:
                    continue
                items.append({
                    "url": link_el.attrib.get("href", ""),
                    "title": title_el.text,
                    "published": pub_el.text if pub_el is not None else None,
                    "source_name": cfg["name"],
                    "source_type": "rss",
                })
    except Exception as e:
        print(f"   [{cfg['name']}] RSS 解析失败：{e}")
    return items


# ---------- B 站 ----------

def scan_bilibili_uploader(cfg: dict) -> list[dict]:
    """
    抓 B 站 up 主近期投稿。
    优先用 yt-dlp + 浏览器 cookies（避开 API 反爬限流和 412）；
    没 cookies 时退到原始 API 调用（大概率被反爬）。
    """
    mid = cfg.get("mid")
    if not mid:
        return []

    cookies_from = cfg.get("cookies_from")
    space_url = f"https://space.bilibili.com/{mid}/video"

    # 优先：yt-dlp + cookies
    import subprocess
    YTDLP_BIN = "/Users/zoezczhou/.workbuddy/binaries/python/envs/content-catcher/bin/yt-dlp"
    # 用 flat-playlist 拿 url 列表（快）；但 flat 模式下 title/timestamp 缺失
    # 所以再用 --print 单独取每个视频的 metadata
    cmd = [
        YTDLP_BIN, "--no-warnings", "--flat-playlist",
        "--print", "%(id)s|%(title)s|%(timestamp)s|%(upload_date)s",
        "--playlist-items", "1-10",
    ]
    if cookies_from:
        cmd += ["--cookies-from-browser", cookies_from]
    cmd.append(space_url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0 and result.stdout.strip():
            items = []
            for line in result.stdout.strip().split("\n"):
                parts = line.split("|", 3)
                if len(parts) < 2:
                    continue
                bv = parts[0].strip()
                title = parts[1].strip() if len(parts) > 1 else ""
                ts = parts[2].strip() if len(parts) > 2 else ""
                upload_date = parts[3].strip() if len(parts) > 3 else ""

                # 解析时间：优先 timestamp（unix 秒），其次 upload_date
                published = None
                if ts and ts != "NA" and ts.isdigit():
                    published = int(ts)
                elif upload_date and upload_date != "NA":
                    published = upload_date

                if not bv or bv == "NA":
                    continue
                items.append({
                    "url": f"https://www.bilibili.com/video/{bv}",
                    "title": title if title != "NA" else bv,
                    "published": published,
                    "source_name": cfg["name"],
                    "source_type": "bilibili_uploader",
                })
            if items:
                return items
        else:
            err = result.stderr[:200] if result.stderr else "no output"
            print(f"   [{cfg['name']}] yt-dlp 抓取失败：{err}")
    except Exception as e:
        print(f"   [{cfg['name']}] yt-dlp 异常：{e}")

    # 兜底：直接 API（容易被限流）
    api = f"https://api.bilibili.com/x/space/arc/search?mid={mid}&ps=10&order=pubdate"
    data = http_get(api)
    if not data:
        return []
    try:
        j = json.loads(data)
        if j.get("code") != 0:
            print(f"   [{cfg['name']}] B 站 API 返回 code={j.get('code')} ({j.get('message')})")
            return []
        vlist = (j.get("data") or {}).get("list", {}).get("vlist", [])
        items = []
        for v in vlist:
            bv = v.get("bvid")
            if not bv:
                continue
            items.append({
                "url": f"https://www.bilibili.com/video/{bv}",
                "title": v.get("title"),
                "published": v.get("created"),
                "source_name": cfg["name"],
                "source_type": "bilibili_uploader",
            })
        return items
    except Exception as e:
        print(f"   [{cfg['name']}] B 站接口解析失败：{e}")
        return []


# ---------- 时间过滤 ----------

def parse_dt(s):
    """尽量宽容地解析时间字符串/数字。"""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return datetime.fromtimestamp(s, tz=timezone.utc)
    s = str(s).strip()
    # YYYYMMDD 格式（yt-dlp 的 upload_date）
    if len(s) == 8 and s.isdigit():
        try:
            return datetime.strptime(s, "%Y%m%d").replace(tzinfo=timezone.utc)
        except Exception:
            pass
    # ISO 8601
    try:
        s2 = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s2)
    except Exception:
        pass
    # RSS RFC 822
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(s)
    except Exception:
        return None


def filter_recent(items: list[dict], days: int) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    for it in items:
        dt = parse_dt(it.get("published"))
        if dt is None:
            # 时间不明确就保留（保守）
            out.append(it)
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if dt >= cutoff:
            it["_published_dt"] = dt.isoformat()
            out.append(it)
    return out


# ---------- 主入口 ----------

def scan_channel(cfg: dict) -> list[dict]:
    t = cfg.get("type")
    if t == "youtube_channel":
        return scan_youtube_channel(cfg)
    if t == "bilibili_uploader":
        return scan_bilibili_uploader(cfg)
    if t == "rss":
        return scan_rss(cfg)
    print(f"   [{cfg.get('name')}] 未知类型：{t}")
    return []


def scan_all(yaml_path: Path,
             days: int | None = None,
             max_per_channel: int | None = None) -> dict:
    cfg = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    defaults = cfg.get("defaults", {}) or {}
    eff_days = days or defaults.get("days", 7)
    eff_cap = max_per_channel or defaults.get("max_per_channel", 5)

    print(f"📡 订阅扫描：days={eff_days}, max_per_channel={eff_cap}\n")

    all_items = []
    per_channel = {}
    for ch in cfg.get("channels", []):
        if not ch.get("enabled", True):
            continue
        print(f"🔍 扫 {ch['name']} ({ch['type']})")
        items = scan_channel(ch)
        recent = filter_recent(items, eff_days)
        recent = recent[:eff_cap]
        print(f"   → 抓到 {len(items)} 条，近 {eff_days} 天 {len(recent)} 条")
        per_channel[ch["name"]] = recent
        all_items.extend(recent)

    return {
        "newsletter": cfg.get("newsletter", {}),
        "items": all_items,
        "per_channel": per_channel,
    }


if __name__ == "__main__":
    import sys
    yaml_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("channels.yaml")
    if not yaml_path.exists():
        print(f"❌ 找不到 {yaml_path}，请先 cp channels.example.yaml channels.yaml 并配置")
        sys.exit(1)
    result = scan_all(yaml_path)
    print(f"\n📊 共抓到 {len(result['items'])} 条新内容")
    for it in result["items"]:
        print(f"  [{it['source_name']}] {it['title'][:60]}  → {it['url']}")
