"""
内容捕手（content-catcher）M4 主入口。

M4 新增：
  - 批量模式：--batch <urls.txt>（一个链接一行）
  - 合并模式：--mode index / topic / compare
  - 链接级缓存：--no-cache 关闭
  - 失败容错：单个失败不影响整体

用法：
  python catch.py <URL>                          # 单链接
  python catch.py URL1 URL2 URL3                 # 多链接（命令行）
  python catch.py --batch urls.txt               # 批量（文件）
  python catch.py --batch urls.txt --mode topic  # 专题合集
  python catch.py --batch urls.txt --mode compare --batch-name "AutoGLM 竞品分析"
                                                  # 跨平台对比
  python catch.py <URL> --auto                   # LLM 全自动
  python catch.py <URL> --cookies-from safari    # B 站需登录态
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))

from detect_platform import detect_platform
from get_metadata import get_metadata
from fetch_subtitle import fetch_subtitle
from detect_language import detect_language
from save_output import save, safe_filename
from build_prompt import save_bundle, DEFAULT_CHUNK_SIZE
from run_llm import run_llm, is_available as llm_available
from batch import read_urls_from_file, run_batch


# ============ 单链路处理 ============

def try_transcribe(url, cookies_from, model_size):
    from download_audio import download_audio
    from transcribe import transcribe_audio, check_ffmpeg

    if not check_ffmpeg():
        print("   ⚠️ 未装 ffmpeg。brew install ffmpeg")
        return None, None, "no-ffmpeg"

    audio_dir = ROOT / "output" / "audio"
    print(f"   📥 下载音频...")
    audio_path = download_audio(url, audio_dir, cookies_from_browser=cookies_from)
    if not audio_path:
        return None, None, "audio-download-failed"

    print(f"   🎤 Whisper 转写（{model_size}）...")
    text, lang = transcribe_audio(audio_path, model_size=model_size)
    if not text:
        return None, None, "transcribe-failed"
    return text, lang, f"faster-whisper({model_size})"


def process_xiaohongshu(url, cookies_from, raw, **kwargs):
    """单条小红书。返回结构化结果。"""
    from fetch_xiaohongshu import fetch_xiaohongshu

    print(f"   📔 抓小红书...")
    note = fetch_xiaohongshu(url)
    if "error" in note:
        return {"ok": False, "error": note["error"]}

    text = note.get("text") or ""
    src = note.get("source", "")
    if not text and note.get("kind") == "video" and not kwargs.get("no_transcribe"):
        print(f"   🎤 视频笔记无文字，尝试转写...")
        text, _, tsrc = try_transcribe(url, cookies_from, kwargs.get("whisper_model", "small"))
        if text:
            src = f"{src}+{tsrc}"
    if not text:
        return {"ok": False, "error": "no-content"}

    meta = {
        "title": note.get("title"),
        "author": note.get("author"),
        "uploader": note.get("author"),
        "url": url,
        "tags": note.get("tags", []),
    }

    notes_dir = ROOT / "output" / "notes"
    save(meta, text, "xhs", src, notes_dir)
    print(f"   ✅ {note.get('title')}")

    if raw:
        return {"ok": True, "title": meta["title"], "platform": "xiaohongshu",
                "source": src, "chars": len(text), "bundle_path": None}

    bundles_dir = ROOT / "output" / "bundles"
    result = save_bundle(meta, text, "xhs", src, bundles_dir,
                         chunk_size=kwargs.get("chunk_size", DEFAULT_CHUNK_SIZE))
    return {"ok": True, "title": meta["title"], "platform": "xiaohongshu",
            "source": src, "chars": len(text),
            "bundle_path": str(result["prompts"][0]),
            "chunks": result["chunks"]}


def process_audio_video(url, cookies_from, raw, **kwargs):
    """单条音视频。返回结构化结果。"""
    print(f"   📋 元信息...")

    platform = detect_platform(url)
    rss_episode = None  # 如果是播客主站，提前从 RSS 抓 show notes

    # 播客主站特殊路径：先试 RSS（show notes 通常比网页元信息丰富）
    if platform == "podcast_web":
        print(f"   📻 播客主站，尝试 RSS 抓 show notes...")
        try:
            from fetch_podcast_rss import fetch_episode_from_rss
            rss_episode = fetch_episode_from_rss(url)
            if rss_episode and len(rss_episode.get("description", "")) > 500:
                print(f"      ✅ RSS show notes：{len(rss_episode['description'])} 字符")
            else:
                print(f"      ⚠️ RSS show notes 太短，回退到 yt-dlp 抓网页")
                rss_episode = None
        except Exception as e:
            print(f"      ⚠️ RSS 抓取异常：{e}")
            rss_episode = None

    meta = get_metadata(url, cookies_from=cookies_from)
    if "error" in meta and not rss_episode:
        return {"ok": False, "error": meta["error"][:200]}

    # 如果 RSS 拿到了，元信息也用 RSS 的（更准）
    if rss_episode:
        if not meta or "error" in meta:
            meta = {}
        meta["title"] = rss_episode["title"] or meta.get("title")
        meta["duration_sec"] = rss_episode.get("duration_sec") or meta.get("duration_sec")
        meta["description"] = rss_episode["description"]
        meta["url"] = url

    print(f"      {meta.get('title')}")

    # podcast_web 且 RSS 拿到了完整内容 → 直接当字幕用，跳过 fetch_subtitle
    if platform == "podcast_web" and rss_episode:
        text = rss_episode["description"]
        lang_hint = None
        source = "rss-shownotes"
        print(f"   ✅ 用 RSS show notes 作为内容（{len(text)} 字符）")
    else:
        print(f"   📜 字幕...")
        subs_dir = ROOT / "output" / "subs"
        text, lang_hint, source = fetch_subtitle(
            url, subs_dir,
            cookies_from_browser=cookies_from,
            cookies_file=kwargs.get("cookies_file"),
        )

    if not text:
        print(f"      ⚠️ 无字幕（{source}）")

        # 三层降级策略：
        # 1. 不转写模式（no_transcribe=True）：直接 fallback 到元信息
        # 2. 智能转写模式：短视频走 Whisper，长视频跳过用元信息
        # 3. 兜底：用元信息（简介+章节）作为内容
        from get_metadata import build_content_from_metadata

        no_transcribe = kwargs.get("no_transcribe", False)
        # 深度/完整版模式：希望有真内容，放宽时长限制（除非显式 no_transcribe）
        is_deep_mode = kwargs.get("deep", False)
        is_full_mode = kwargs.get("full", False)
        max_transcribe_min = kwargs.get("max_transcribe_min", 20)
        if (is_deep_mode or is_full_mode) and not no_transcribe:
            max_transcribe_min = 9999  # 深度/完整模式默认转写所有视频
            mode_name = "深度" if is_deep_mode else "完整版"
            print(f"      📜 {mode_name}模式：放宽时长限制，强制转写")

        duration_sec = (meta.get("duration_sec") or 0)
        duration_min = duration_sec / 60 if duration_sec else 0

        # 决定要不要走 Whisper
        should_transcribe = (
            not no_transcribe                            # 没显式禁用
            and duration_min > 0                         # 知道时长
            and duration_min <= max_transcribe_min       # 不超过阈值
        )

        if should_transcribe:
            print(f"      🎤 视频 {duration_min:.1f} 分钟 ≤ {max_transcribe_min}，走 Whisper 转写...")
            text, lang_hint, source = try_transcribe(url, cookies_from,
                                                      kwargs.get("whisper_model", "tiny"))
            if not text:
                print(f"      ⚠️ 转写失败，降级到元信息")
                # 转写失败也降级到 metadata fallback

        if not text:
            # 走 metadata fallback
            if duration_min > max_transcribe_min and not no_transcribe:
                print(f"      ⏭️ 视频 {duration_min:.1f} 分钟 > {max_transcribe_min}，跳过转写")
            full_meta = get_metadata(url, cookies_from=cookies_from)
            fallback_text = build_content_from_metadata(full_meta)
            if fallback_text and len(fallback_text) > 100:
                print(f"      📋 Fallback 用元信息（简介+章节）：{len(fallback_text)} 字符")
                text = fallback_text
                lang_hint = None
                source = "metadata-fallback"
                full_meta["url"] = url
                meta = full_meta
            else:
                return {"ok": False, "error": f"no-content (subtitle/transcribe/metadata all failed)"}

    lang = detect_language(text, hint=lang_hint)
    template_key = {"zh": "zh", "en": "en"}.get(lang, "zh")

    # 深度模式 / 完整版模式：覆盖默认模板
    if kwargs.get("deep"):
        template_key = "deep"
        print(f"   📖 深度模式：用精装电子书模板（蒸馏改写）")
    elif kwargs.get("full"):
        template_key = "full"
        print(f"   📜 完整版模式：用逐字稿+导读模板（不删减）")

    notes_dir = ROOT / "output" / "notes"
    save(meta, text, lang, source, notes_dir)

    platform = detect_platform(url)
    print(f"   ✅ {len(text)} 字符，{lang}")

    if raw:
        return {"ok": True, "title": meta.get("title"), "platform": platform,
                "source": source, "chars": len(text), "bundle_path": None}

    bundles_dir = ROOT / "output" / "bundles"
    result = save_bundle(meta, text, template_key, source, bundles_dir,
                         chunk_size=kwargs.get("chunk_size", DEFAULT_CHUNK_SIZE))
    return {"ok": True, "title": meta.get("title"), "platform": platform,
            "source": source, "chars": len(text),
            "bundle_path": str(result["prompts"][0]),
            "chunks": result["chunks"]}


def process_one(url, cookies_from, raw, **kwargs):
    """单链路总入口。"""
    platform = detect_platform(url)
    print(f"   🔍 平台：{platform}")
    if platform == "xiaohongshu":
        return process_xiaohongshu(url, cookies_from, raw, **kwargs)
    if platform in ("youtube", "bilibili", "apple_podcast", "spotify", "xiaoyuzhou", "podcast_web"):
        return process_audio_video(url, cookies_from, raw, **kwargs)
    return {"ok": False, "error": f"unsupported-platform: {platform}"}


# ============ 命令行入口 ============

def main():
    parser = argparse.ArgumentParser(
        description="内容捕手 M5：单条 / 批量 / 跨平台 / 订阅周报")
    parser.add_argument("urls", nargs="*", help="一个或多个链接（命令行多链接模式）")
    parser.add_argument("--batch", dest="batch_file", default=None,
                        help="URL 文件（每行一个链接，# 注释，支持行内 --cookies-from）")
    parser.add_argument("--mode", choices=["index", "topic", "compare"], default="index",
                        help="批量模式：index=只索引 / topic=专题合集 / compare=跨平台对比")
    parser.add_argument("--batch-name", dest="batch_name", default=None,
                        help="批次名（用于命名输出目录），默认按时间戳")
    parser.add_argument("--subscribe", dest="subscribe_file", default=None,
                        help="订阅配置文件（channels.yaml），开启周报模式")
    parser.add_argument("--days", type=int, default=None,
                        help="订阅模式：抓近多少天的新内容（默认按 yaml 配置）")
    parser.add_argument("--send-email", action="store_true",
                        help="订阅模式：发送邮件到 yaml 配置的邮箱")
    parser.add_argument("--send-only", dest="send_only", default=None,
                        help="跳过抓取，直接把指定 digest 目录里现成的 weekly-digest.md 发邮件 "
                             "（Claude 代笔后用这个一键发出）。"
                             "传入 digest 目录名（如 weekly-2026-W22-20260529）")
    parser.add_argument("--no-cache", action="store_true",
                        help="不使用链接级缓存，强制重抓")
    parser.add_argument("--auto", action="store_true", help="调 LLM API 全自动")
    parser.add_argument("--raw", action="store_true", help="只抓原文")
    parser.add_argument("--deep", action="store_true",
                        help="深度模式：精装电子书风格（蒸馏改写，叙事体长文）")
    parser.add_argument("--full", action="store_true",
                        help="完整版模式：逐字稿+导读（不删减原文，加章节索引和金句标注）")
    parser.add_argument("--target-length", dest="target_length", default=None,
                        help="深度模式下的目标字数（如 '1500-3000' / '3000-6000' / '不限'）。"
                             "不指定则按输入内容长度自适应。")
    parser.add_argument("--cookies-from", dest="cookies_from", default=None,
                        help="从浏览器读 cookies（safari/chrome/firefox/edge）")
    parser.add_argument("--cookies-file", dest="cookies_file", default=None,
                        help="cookies.txt 路径")
    parser.add_argument("--no-transcribe", action="store_true",
                        help="字幕没抓到完全不走 Whisper（直接用元信息 fallback）")
    parser.add_argument("--max-transcribe-min", dest="max_transcribe_min",
                        type=int, default=20,
                        help="超过此时长（分钟）的视频跳过 Whisper 转写，用元信息 fallback。默认 20。")
    parser.add_argument("--whisper-model", dest="whisper_model", default="tiny",
                        choices=["tiny", "base", "small", "medium", "large-v3"],
                        help="Whisper 模型大小（默认 tiny 快但准确率较低）")
    parser.add_argument("--chunk-size", dest="chunk_size", type=int,
                        default=DEFAULT_CHUNK_SIZE,
                        help="长文本分段大小")
    args = parser.parse_args()

    # 决定要处理的 URL 列表
    url_items: list[tuple[str, str | None]] = []

    # ===== --send-only 快捷入口：把已写好的 digest 直接发邮件 =====
    if args.send_only:
        from digest import send_weekly_email
        import yaml as _yaml

        if not args.subscribe_file:
            print("❌ --send-only 需要同时指定 --subscribe channels.yaml 来读取邮箱配置")
            sys.exit(1)

        yaml_path = Path(args.subscribe_file)
        scan_min = _yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

        digest_dir = ROOT / "output" / "digest" / args.send_only
        if not digest_dir.exists():
            print(f"❌ 找不到 digest 目录：{digest_dir}")
            sys.exit(1)

        body_md = digest_dir / "weekly-digest.md"
        if not body_md.exists():
            # 回退到 fallback
            body_md = digest_dir / "weekly-digest.fallback.md"
        if not body_md.exists():
            print(f"❌ {digest_dir} 里既没有 weekly-digest.md 也没有 fallback 文件")
            sys.exit(1)

        # 收集附件：EPUB + 投喂包
        attachments = []
        for p in digest_dir.iterdir():
            if p.suffix.lower() in (".epub", ".pdf"):
                attachments.append(p)
            elif p.name.endswith(".WEEKLY.prompt.md"):
                attachments.append(p)

        print(f"\n📤 直发模式：{args.send_only}")
        print(f"   正文：{body_md.name}")
        print(f"   附件：{[a.name for a in attachments]}")
        send_weekly_email(scan_min, body_md, attachments=attachments)
        return

    # ===== 订阅模式 =====
    if args.subscribe_file:
        from subscribe import scan_all
        from digest_history import filter_new, mark_sent
        from digest import (build_weekly_bundle, auto_generate_weekly,
                            build_epub_if_many, send_weekly_email)

        yaml_path = Path(args.subscribe_file)
        if not yaml_path.exists():
            print(f"❌ 找不到订阅配置：{yaml_path}")
            sys.exit(1)

        print(f"\n🚀 订阅模式：{yaml_path}")
        scan = scan_all(yaml_path, days=args.days)
        before = len(scan["items"])
        scan["items"] = filter_new(ROOT, scan["items"])
        after = len(scan["items"])
        print(f"\n🧠 增量过滤：{before} 条 → {after} 条新内容")
        if after == 0:
            print(f"✅ 本周没有新内容，跳过。")
            return

        extra = {
            "cookies_file": args.cookies_file,
            "no_transcribe": args.no_transcribe,   # 周报模式默认 False = 启用智能转写
            "max_transcribe_min": args.max_transcribe_min,
            "whisper_model": args.whisper_model,
            "chunk_size": args.chunk_size,
            "cookies_from": args.cookies_from,
        }
        bundle = build_weekly_bundle(
            ROOT, scan, process_one,
            cookies_from=args.cookies_from,
            whisper_model=args.whisper_model,
            chunk_size=args.chunk_size,
            no_transcribe=args.no_transcribe,
            max_transcribe_min=args.max_transcribe_min,
        )

        if bundle["items_processed"] == 0:
            print("\n⚠️ 没有任何内容成功处理。")
            return

        # 自动模式
        final_md = None
        if args.auto:
            final_md = auto_generate_weekly(ROOT, bundle["weekly_prompt_path"])

        # EPUB
        epub_path = build_epub_if_many(ROOT, bundle, threshold=5)

        # 邮件
        if args.send_email:
            from pathlib import Path as _P

            attachments = [epub_path] if epub_path else []
            wp = _P(bundle["weekly_prompt_path"])
            if wp.exists():
                attachments.append(wp)

            # 邮件正文优先级：
            #   1) --auto 跑出来的 final_md（API 路线）
            #   2) Claude 代笔放在 digest 目录的 weekly-digest.md（人机分工路线）
            #   3) Fallback 占位（最少惊喜）
            digest_dir = wp.parent
            human_written = digest_dir / "weekly-digest.md"

            if final_md:
                body_path = final_md
                source = "LLM auto"
            elif human_written.exists():
                body_path = human_written
                source = "Claude 代笔"
            else:
                # Fallback：没正文也发，至少把附件送达
                items = bundle.get("epub_candidates", [])
                fallback_md = (
                    f"# {scan.get('newsletter', {}).get('name', '订阅周报')}\n\n"
                    f"> 本周抓到 **{len(items)} 条** 新内容（正文待 Claude 撰写）\n\n"
                    "## 📦 本期清单\n\n"
                    + "\n".join(
                        f"- [{r.get('title','(无标题)')}]({r.get('url','')})"
                        for r in items
                    )
                    + "\n\n## 📎 附件\n\n"
                    "- **EPUB 电子书**：所有笔记打包，可投递到 Kindle / iPad\n"
                    "- **完整投喂包（.WEEKLY.prompt.md）**：含全部 transcript\n\n"
                    "> 💡 把投喂包发给 Claude 即可生成精装周报正文；"
                    "或加 `--auto` + API key 让 skill 自动撰写。\n"
                )
                fb = digest_dir / "weekly-digest.fallback.md"
                fb.write_text(fallback_md, encoding="utf-8")
                body_path = fb
                source = "fallback 占位"

            print(f"📧 邮件正文来源：{source}（{body_path.name}）")
            send_weekly_email(scan, body_path, attachments=attachments)

        # 标记已发
        mark_sent(ROOT, [r["url"] for r in bundle.get("epub_candidates", [])],
                  bundle["digest_name"])

        print(f"\n🎉 周报完成！")
        print(f"   投喂包：{bundle['weekly_prompt_path']}")
        if final_md:
            print(f"   最终周报：{final_md}")
        if epub_path:
            print(f"   EPUB：{epub_path}")
        return

    # ===== 批量 / 单条模式（原有逻辑）=====
    if args.batch_file:
        url_items = read_urls_from_file(Path(args.batch_file))
        if not url_items:
            print(f"❌ {args.batch_file} 没读到任何链接")
            sys.exit(1)
    elif args.urls:
        url_items = [(u, args.cookies_from) for u in args.urls]
    else:
        parser.error("请提供至少一个 URL 或 --batch <file>")

    extra = {
        "cookies_file": args.cookies_file,
        "no_transcribe": args.no_transcribe,
        "max_transcribe_min": args.max_transcribe_min,
        "whisper_model": args.whisper_model,
        "chunk_size": args.chunk_size,
        "cookies_from": args.cookies_from,
        "deep": args.deep,
        "full": args.full,
    }

    # 单链接走简化路径（保留 M3 的输出体验）
    if len(url_items) == 1 and not args.batch_file:
        url, cookies_from = url_items[0]
        print(f"\n🚀 单链接模式")
        # 单链接调用时 cookies_from 用位置参数传，所以 extra 里要剔除
        single_extra = {k: v for k, v in extra.items() if k != "cookies_from"}
        r = process_one(url, cookies_from, args.raw, **single_extra)
        if r.get("ok"):
            print(f"\n✅ 完成：{r.get('title')}")
            if r.get("bundle_path"):
                print(f"   📦 投喂包：{r['bundle_path']}")
        else:
            print(f"\n❌ 失败：{r.get('error')}")
            sys.exit(2)
        return

    # 批量模式
    batch_name = args.batch_name or f"batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    summary = run_batch(
        ROOT, url_items, process_one, batch_name,
        mode=args.mode,
        use_cache=not args.no_cache,
        raw=args.raw,
        extra_args=extra,
    )
    if summary["ok"] == 0:
        sys.exit(3)


if __name__ == "__main__":
    main()
