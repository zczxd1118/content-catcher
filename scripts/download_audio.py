"""用 yt-dlp 下载音频（仅音轨，省带宽 + 加快转写）。"""
import subprocess
from pathlib import Path

from _bin import require_bin


def _ytdlp() -> str:
    return require_bin("yt-dlp", "pip install yt-dlp")


def download_audio(url: str, out_dir: Path,
                   cookies_from_browser: str | None = None,
                   cookies_file: str | None = None,
                   audio_format: str = "m4a") -> Path | None:
    """
    下载音频到 out_dir，返回文件路径；失败返回 None。
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(out_dir / "%(id)s.%(ext)s")

    cmd = [
        _ytdlp(),
        "-f", "bestaudio/best",
        "-x",                    # extract audio
        "--audio-format", audio_format,
        "--audio-quality", "5",  # 0=best, 9=worst（5 = 中等 ~96kbps，转写够用）
        "-o", out_template,
        "--no-playlist",
    ]
    if cookies_from_browser:
        cmd += ["--cookies-from-browser", cookies_from_browser]
    elif cookies_file:
        cmd += ["--cookies", cookies_file]
    cmd.append(url)

    try:
        # 先拿视频 id
        id_proc = subprocess.run(
            [_ytdlp(), "--get-id", "--no-playlist", url],
            capture_output=True, text=True, timeout=60,
        )
        video_id = id_proc.stdout.strip()
        if not video_id:
            print(f"[download_audio] 无法获取视频 id: {id_proc.stderr[:300]}")
            return None

        # 下载
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            print(f"[download_audio] 下载失败: {result.stderr[:500]}")
            return None

        # 找到产物文件
        for ext in (audio_format, "m4a", "mp3", "webm", "opus", "wav"):
            candidate = out_dir / f"{video_id}.{ext}"
            if candidate.exists():
                return candidate
        # 兜底：找最新的音频文件
        audios = sorted(out_dir.glob(f"{video_id}.*"), key=lambda p: p.stat().st_mtime, reverse=True)
        return audios[0] if audios else None
    except Exception as e:
        print(f"[download_audio] 异常: {e}")
        return None


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    out = Path(__file__).resolve().parent.parent / "output" / "audio"
    path = download_audio(url, out)
    print(f"音频文件：{path}")
