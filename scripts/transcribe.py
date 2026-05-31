"""
本地语音转写：用 faster-whisper。
首次运行会下载模型（small ~500MB / medium ~1.5GB / large-v3 ~3GB）。
Mac M 系列芯片：用 CPU + int8 已经足够快（~2-3x 实时）。
"""
import os
import sys
from pathlib import Path


def transcribe_audio(audio_path: Path,
                     model_size: str = "small",
                     language_hint: str | None = None,
                     compute_type: str = "int8") -> tuple[str | None, str | None]:
    """
    转写音频文件。
    model_size: tiny / base / small / medium / large-v3
        - small：约 500MB，Mac CPU 上够用，准确率不错
        - medium：约 1.5GB，准确率更好
        - large-v3：约 3GB，最强但慢
    language_hint: "zh" / "en" / None（自动检测）
    返回 (转写文本, 检测到的语言)。
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("[transcribe] faster-whisper 未安装。"
              "运行：pip install faster-whisper", file=sys.stderr)
        return None, None
    except Exception as e:
        print(f"[transcribe] faster-whisper import 失败：{e}", file=sys.stderr)
        print(f"   👉 这通常是 macOS 代码签名问题，尝试：", file=sys.stderr)
        print(f"      codesign --force --sign - $(python -c \"import faster_whisper, os; "
              f"print(os.path.dirname(faster_whisper.__file__))\")/*.so", file=sys.stderr)
        return None, None

    if not audio_path.exists():
        print(f"[transcribe] 音频文件不存在：{audio_path}", file=sys.stderr)
        return None, None

    print(f"[transcribe] 加载模型 {model_size}...", flush=True)
    try:
        # 模型缓存放到项目目录下
        cache_dir = Path(__file__).resolve().parent.parent / "models"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # M5+：先看本地是否有手动下好的模型（绕过 HuggingFace 网络问题）
        local_model_dir = cache_dir / f"models--Systran--faster-whisper-{model_size}" / "snapshots" / "main"
        if (local_model_dir / "model.bin").exists():
            print(f"[transcribe] 使用本地模型：{local_model_dir}", flush=True)
            model = WhisperModel(
                str(local_model_dir),
                device="cpu",
                compute_type=compute_type,
            )
        else:
            # 否则走默认（会尝试从 HuggingFace 下载）
            print(f"[transcribe] 本地未找到，尝试在线下载...", flush=True)
            model = WhisperModel(
                model_size,
                device="cpu",
                compute_type=compute_type,
                download_root=str(cache_dir),
            )
    except Exception as e:
        print(f"[transcribe] 模型加载失败：{e}", file=sys.stderr)
        print(f"[transcribe] 👉 国内网络下载常超时，建议手动下载模型到：", file=sys.stderr)
        print(f"   {cache_dir / f'models--Systran--faster-whisper-{model_size}' / 'snapshots' / 'main'}", file=sys.stderr)
        print(f"   下载地址：https://hf-mirror.com/Systran/faster-whisper-{model_size}/tree/main", file=sys.stderr)
        return None, None

    print(f"[transcribe] 开始转写：{audio_path.name}", flush=True)
    try:
        segments, info = model.transcribe(
            str(audio_path),
            language=language_hint,
            beam_size=5,
            vad_filter=True,       # 过滤静音段
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        lang = info.language
        lines = []
        for seg in segments:
            text = seg.text.strip()
            if text:
                lines.append(text)
        full_text = "\n".join(lines)
        print(f"[transcribe] 完成：{len(full_text)} 字符，语言 {lang}", flush=True)
        return full_text, lang
    except Exception as e:
        print(f"[transcribe] 转写异常：{e}", file=sys.stderr)
        return None, None


def check_ffmpeg() -> bool:
    """检查 ffmpeg 是否可用（faster-whisper 解码音频依赖它）。"""
    import shutil
    return shutil.which("ffmpeg") is not None


if __name__ == "__main__":
    if not check_ffmpeg():
        print("⚠️ 未检测到 ffmpeg。请安装：brew install ffmpeg")
    if len(sys.argv) < 2:
        print("用法：python transcribe.py <音频文件>")
        sys.exit(1)
    text, lang = transcribe_audio(Path(sys.argv[1]))
    if text:
        print(f"\n语言：{lang}\n字符数：{len(text)}\n---预览---\n{text[:500]}")
