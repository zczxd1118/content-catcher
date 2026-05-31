"""用 yt-dlp 抓视频元信息（标题、作者、时长、简介、章节等），不下载实际内容。"""
import subprocess
import json
from pathlib import Path


YTDLP_BIN = "/Users/zoezczhou/.workbuddy/binaries/python/envs/content-catcher/bin/yt-dlp"


def get_metadata(url: str, cookies_from: str = None) -> dict:
    cmd = [YTDLP_BIN, "--dump-single-json", "--skip-download", "--no-warnings"]
    if cookies_from:
        cmd += ["--cookies-from-browser", cookies_from]
    cmd.append(url)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return {"error": result.stderr[:300]}
        data = json.loads(result.stdout)

        # 章节信息（B 站、YouTube 都可能有）
        chapters_raw = data.get("chapters") or []
        chapters = []
        for c in chapters_raw:
            chapters.append({
                "title": c.get("title"),
                "start_time": c.get("start_time"),
                "end_time": c.get("end_time"),
            })

        return {
            "title": data.get("title"),
            "uploader": data.get("uploader") or data.get("channel"),
            "duration_sec": data.get("duration"),
            "upload_date": data.get("upload_date"),
            "description": data.get("description") or "",  # 完整简介，不截断
            "chapters": chapters,
            "tags": data.get("tags") or [],
            "view_count": data.get("view_count"),
            "like_count": data.get("like_count"),
            "url": url,
        }
    except Exception as e:
        return {"error": str(e)}


def build_content_from_metadata(meta: dict) -> str:
    """
    从元信息（简介 + 章节）拼一份"伪字幕" —— 当真字幕和转写都拿不到时用。
    返回的内容比"只有标题"丰富得多，足够 LLM 写一份合理笔记。
    """
    parts = []

    title = meta.get("title")
    if title:
        parts.append(f"【视频标题】{title}\n")

    uploader = meta.get("uploader")
    duration = meta.get("duration_sec")
    if uploader or duration:
        info = []
        if uploader:
            info.append(f"作者：{uploader}")
        if duration:
            mins = int(duration) // 60
            info.append(f"时长：{mins} 分钟")
        parts.append("【基本信息】" + " | ".join(info) + "\n")

    desc = meta.get("description") or ""
    if desc.strip():
        parts.append(f"【作者简介】\n{desc.strip()}\n")

    chapters = meta.get("chapters") or []
    if chapters:
        parts.append("【作者标记的章节大纲】")
        for i, c in enumerate(chapters, 1):
            t = c.get("title") or f"章节{i}"
            st = c.get("start_time") or 0
            et = c.get("end_time") or 0
            mins_st = int(st) // 60
            secs_st = int(st) % 60
            mins_et = int(et) // 60
            secs_et = int(et) % 60
            parts.append(f"  {i}. {t} ({mins_st:02d}:{secs_st:02d} - {mins_et:02d}:{secs_et:02d})")
        parts.append("")

    tags = meta.get("tags") or []
    if tags:
        parts.append(f"【标签】{', '.join(tags[:10])}\n")

    return "\n".join(parts).strip()


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    cookies = sys.argv[2] if len(sys.argv) > 2 else None
    meta = get_metadata(url, cookies)
    print("=== 原始元信息 ===")
    print(json.dumps({k: v for k, v in meta.items() if k != "description"},
                     ensure_ascii=False, indent=2)[:1500])
    print()
    print("=== 拼成的伪字幕 ===")
    print(build_content_from_metadata(meta))

