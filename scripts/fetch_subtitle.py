"""
字幕优先策略：能抓到字幕就跳过转写，节省时间和算力。
支持 YouTube（用 youtube-transcript-api）和 yt-dlp 自带的字幕提取。
M2 升级：支持 --cookies-from-browser，解决 B 站等需登录态的平台。
"""
import subprocess
import re
from pathlib import Path
from detect_platform import detect_platform, extract_youtube_id


from _bin import require_bin
def _ytdlp() -> str:
    return require_bin("yt-dlp", "pip install yt-dlp")


def fetch_youtube_subtitle(url: str) -> tuple[str | None, str | None]:
    """用 youtube-transcript-api 抓 YouTube 字幕。"""
    video_id = extract_youtube_id(url)
    if not video_id:
        return None, None
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        for lang_pref in [["zh-Hans", "zh-CN", "zh"], ["en", "en-US"], None]:
            try:
                if lang_pref:
                    transcript = api.fetch(video_id, languages=lang_pref)
                else:
                    transcript = api.fetch(video_id)
                snippets = transcript.snippets if hasattr(transcript, "snippets") else transcript
                text = "\n".join(
                    s.text if hasattr(s, "text") else s.get("text", "")
                    for s in snippets
                )
                lang = getattr(transcript, "language_code",
                               lang_pref[0] if lang_pref else "unknown")
                return text, lang
            except Exception:
                continue
    except Exception as e:
        print(f"[fetch_youtube_subtitle] 抓字幕失败：{e}")
    return None, None


def fetch_via_ytdlp(url: str, out_dir: Path,
                    cookies_from_browser: str | None = None,
                    cookies_file: str | None = None) -> tuple[str | None, str | None]:
    """
    用 yt-dlp 抓字幕，支持 cookies 注入。
    cookies_from_browser: "safari" / "chrome" / "firefox" 等
    cookies_file: 直接传 cookies.txt 路径
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        _ytdlp(),
        "--skip-download",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs", "zh.*,en.*",
        "--sub-format", "vtt/srt/best",
        "--convert-subs", "srt",
        "-o", str(out_dir / "%(id)s.%(ext)s"),
    ]
    if cookies_from_browser:
        cmd += ["--cookies-from-browser", cookies_from_browser]
    elif cookies_file:
        cmd += ["--cookies", cookies_file]
    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"[yt-dlp] stderr: {result.stderr[:500]}")
    except Exception as e:
        print(f"[fetch_via_ytdlp] 调用失败：{e}")
        return None, None

    srt_files = list(out_dir.glob("*.srt"))
    if not srt_files:
        return None, None

    zh_files = [f for f in srt_files if re.search(r"\.zh", f.name)]
    en_files = [f for f in srt_files if re.search(r"\.en", f.name)]
    target = (zh_files or en_files or srt_files)[0]
    text = parse_srt(target.read_text(encoding="utf-8"))
    lang = "zh" if target in zh_files else ("en" if target in en_files else "unknown")
    return text, lang


def parse_srt(srt_text: str) -> str:
    """从 SRT/VTT 字幕中抽纯文本。"""
    lines = srt_text.splitlines()
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.isdigit():
            continue
        if "-->" in line:
            continue
        if line.upper().startswith(("WEBVTT", "NOTE", "STYLE")):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        out.append(line)
    return "\n".join(out)


def fetch_subtitle(url: str, out_dir: Path,
                   cookies_from_browser: str | None = None,
                   cookies_file: str | None = None) -> tuple[str | None, str | None, str]:
    """
    顶层入口。
    返回 (字幕文本, 语言代码, 来源说明)。
    来源说明示例：
      youtube-transcript-api / yt-dlp / yt-dlp+cookies(safari)
      no-subtitle / platform-not-supported:xxx
    """
    platform = detect_platform(url)

    if platform == "youtube":
        text, lang = fetch_youtube_subtitle(url)
        if text:
            return text, lang, "youtube-transcript-api"
        text, lang = fetch_via_ytdlp(url, out_dir, cookies_from_browser, cookies_file)
        if text:
            src = f"yt-dlp+cookies({cookies_from_browser})" if cookies_from_browser else "yt-dlp"
            return text, lang, src
        return None, None, "no-subtitle"

    if platform in ("bilibili", "apple_podcast", "spotify", "xiaoyuzhou"):
        text, lang = fetch_via_ytdlp(url, out_dir, cookies_from_browser, cookies_file)
        if text:
            src = f"yt-dlp+cookies({cookies_from_browser})" if cookies_from_browser else "yt-dlp"
            return text, lang, src
        return None, None, "no-subtitle"

    return None, None, f"platform-not-supported: {platform}"


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    cookies = sys.argv[2] if len(sys.argv) > 2 else None
    out = Path(__file__).resolve().parent.parent / "output" / "subs"
    text, lang, source = fetch_subtitle(url, out, cookies_from_browser=cookies)
    print(f"来源：{source}  语言：{lang}")
    if text:
        print(f"字幕长度：{len(text)} 字符")
        print("---前 500 字预览---")
        print(text[:500])
    else:
        print("未抓到字幕。")
