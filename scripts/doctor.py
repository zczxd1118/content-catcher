"""
环境体检：一次性检查 content-catcher 所有依赖。
"""
import shutil
import subprocess
import sys


def check(name: str, ok: bool, hint: str = "", warn_only: bool = False):
    icon = "✅" if ok else ("⚠️" if warn_only else "❌")
    print(f"  {icon} {name}")
    if not ok and hint:
        print(f"     👉 {hint}")


def safe_import(import_name: str) -> tuple[bool, str]:
    """尝试 import，返回 (是否成功, 失败原因摘要)。"""
    try:
        __import__(import_name)
        return True, ""
    except ImportError as e:
        return False, "未安装"
    except Exception as e:
        msg = str(e)
        if "code signature" in msg or "Team IDs" in msg:
            return False, "原生扩展签名问题（沙箱常见，本机正常环境一般无此问题）"
        return False, str(e)[:100]


def main():
    print("\n🩺 content-catcher 环境体检\n")

    print("📦 Python 包：")
    for import_name, pkg_name, hint in [
        ("yt_dlp", "yt-dlp", "pip install yt-dlp"),
        ("youtube_transcript_api", "youtube-transcript-api", "pip install youtube-transcript-api"),
        ("langdetect", "langdetect", "pip install langdetect"),
        ("charset_normalizer", "charset-normalizer", "pip install charset-normalizer"),
        ("yaml", "PyYAML（订阅配置）", "pip install PyYAML"),
    ]:
        ok, reason = safe_import(import_name)
        check(pkg_name + (f"（{reason}）" if not ok else ""), ok, hint)

    ok, reason = safe_import("faster_whisper")
    check("faster-whisper（可选，转写兜底）" + (f"（{reason}）" if not ok else ""),
          ok, "pip install faster-whisper（无字幕视频才用得到）", warn_only=True)

    ok, reason = safe_import("ebooklib")
    check("ebooklib（可选，EPUB 导出）" + (f"（{reason}）" if not ok else ""),
          ok, "pip install ebooklib lxml（要导 EPUB 才装）", warn_only=True)

    ok, reason = safe_import("markdown")
    check("markdown（可选，邮件 HTML 美化）" + (f"（{reason}）" if not ok else ""),
          ok, "pip install markdown（发周报邮件想要漂亮 HTML 时装）", warn_only=True)

    # 系统二进制
    print("\n🔧 系统工具：")
    check("ffmpeg（faster-whisper 依赖）",
          shutil.which("ffmpeg") is not None,
          "brew install ffmpeg")

    # LLM key
    print("\n🔑 LLM API（自动模式可选）：")
    import os
    check("ANTHROPIC_API_KEY", bool(os.getenv("ANTHROPIC_API_KEY")),
          "export ANTHROPIC_API_KEY=sk-...")
    check("OPENAI_API_KEY", bool(os.getenv("OPENAI_API_KEY")),
          "export OPENAI_API_KEY=sk-...")

    # SMTP（订阅模式发邮件用）
    print("\n📧 SMTP 邮件（订阅模式 --send-email 需要）：")
    check("SMTP_PASS", bool(os.getenv("SMTP_PASS")),
          "export SMTP_PASS=你的SMTP授权码（QQ邮箱要用授权码、不是登录密码）")

    print("\n✨ 体检完成。")
    print("   - 投喂包模式：Python 包齐全即可。")
    print("   - 转写兜底模式：还需要 ffmpeg + faster-whisper。")
    print("   - 全自动模式：还需要 LLM API key。")
    print("   - 订阅周报模式：需要 PyYAML；如要发邮件，需要 SMTP_PASS；如要 EPUB，需要 ebooklib+lxml。\n")


if __name__ == "__main__":
    main()
