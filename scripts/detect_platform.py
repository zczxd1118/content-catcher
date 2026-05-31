"""识别 URL 来自哪个平台。"""
from urllib.parse import urlparse


# 已知播客主站（非 Apple Podcasts/Spotify 入口的官网）
PODCAST_WEB_HOSTS = (
    "latent.space",        # Latent Space
    "acquired.fm",         # Acquired
    "lexfridman.com",      # Lex Fridman
    "twimlai.com",         # The TWIML AI Podcast
    "stratechery.com",     # Stratechery
    "hubermanlab.com",     # Huberman Lab
    "substack.com",        # 很多 AI 播客托管在 Substack
)


def detect_platform(url: str) -> str:
    """返回平台标识：youtube / bilibili / apple_podcast / spotify /
    xiaohongshu / xiaoyuzhou / podcast_web / unknown"""
    host = urlparse(url).hostname or ""
    host = host.lower()

    if "youtube.com" in host or "youtu.be" in host:
        return "youtube"
    if "bilibili.com" in host or "b23.tv" in host:
        return "bilibili"
    if "podcasts.apple.com" in host:
        return "apple_podcast"
    if "open.spotify.com" in host:
        return "spotify"
    if "xiaohongshu.com" in host or "xhslink.com" in host:
        return "xiaohongshu"
    if "xyzcn.app" in host or "xiaoyuzhoufm.com" in host:
        return "xiaoyuzhou"
    # 播客主站（多数支持 yt-dlp 或自带 RSS）
    if any(h in host for h in PODCAST_WEB_HOSTS):
        return "podcast_web"
    return "unknown"


def extract_youtube_id(url: str) -> str | None:
    """从 YouTube URL 提取视频 ID。"""
    parsed = urlparse(url)
    if "youtu.be" in (parsed.hostname or ""):
        return parsed.path.lstrip("/").split("?")[0]
    if "youtube.com" in (parsed.hostname or ""):
        from urllib.parse import parse_qs
        qs = parse_qs(parsed.query)
        return qs.get("v", [None])[0]
    return None


if __name__ == "__main__":
    tests = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.bilibili.com/video/BV1xx411c7mD",
        "https://www.xiaohongshu.com/explore/abc123",
    ]
    for u in tests:
        print(f"{detect_platform(u):15s}  {u}")
