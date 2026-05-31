"""
Newsletter 主调度：
  订阅扫描 → 抓内容 → 构造周报投喂包 → (可选)LLM 生成 → (可选)发邮件 + EPUB 附件
"""
import sys
from pathlib import Path
from datetime import datetime


def build_weekly_bundle(root: Path,
                        scan_result: dict,
                        process_one,
                        cookies_from=None,
                        whisper_model="tiny",
                        chunk_size=12000,
                        no_transcribe=False,
                        max_transcribe_min=20) -> dict:
    """
    返回 {
        digest_name, items_processed, weekly_prompt_path,
        sub_bundle_paths, sub_notes (if processed), epub_candidates
    }
    no_transcribe: True 完全不转写（最快）
    max_transcribe_min: 智能模式下，超过此时长的视频跳过转写（默认 20 分钟）
    """
    from save_output import safe_filename
    from build_prompt import save_bundle

    digest_name = f"weekly-{datetime.now().strftime('%Y-W%V-%Y%m%d')}"
    out_dir = root / "output" / "digest" / digest_name
    out_dir.mkdir(parents=True, exist_ok=True)

    items = scan_result.get("items", [])
    if not items:
        return {"digest_name": digest_name, "items_processed": 0,
                "weekly_prompt_path": None, "sub_bundle_paths": [],
                "epub_candidates": []}

    if no_transcribe:
        print(f"\n📝 处理本周 {len(items)} 条内容（不转写，仅用元信息）...\n")
    else:
        print(f"\n📝 处理本周 {len(items)} 条内容（智能转写：≤{max_transcribe_min}分钟走 Whisper）...\n")
    processed = []
    for i, it in enumerate(items, 1):
        print(f"━━━━━━ [{i}/{len(items)}] {it['title'][:60]} ━━━━━━")
        try:
            r = process_one(it["url"], cookies_from, False,
                            whisper_model=whisper_model,
                            chunk_size=chunk_size,
                            no_transcribe=no_transcribe,
                            max_transcribe_min=max_transcribe_min)
            if r.get("ok"):
                r["url"] = it["url"]
                r["source_name"] = it["source_name"]
                r["published"] = it.get("published")
                processed.append(r)
            else:
                # 即使字幕没抓到/转写失败，也保留视频元信息，让周报至少能展示标题+链接
                processed.append({
                    "ok": False,
                    "url": it["url"],
                    "title": it.get("title"),
                    "source_name": it["source_name"],
                    "platform": it.get("source_type", "unknown"),
                    "source": "metadata-only",
                    "chars": 0,
                    "bundle_path": None,
                    "published": it.get("published"),
                    "error": r.get("error", "no-content"),
                })
        except Exception as e:
            print(f"   ⚠️ {e}")
            # 异常也保留元信息
            processed.append({
                "ok": False,
                "url": it["url"],
                "title": it.get("title"),
                "source_name": it["source_name"],
                "platform": it.get("source_type", "unknown"),
                "source": "metadata-only",
                "chars": 0,
                "bundle_path": None,
                "published": it.get("published"),
                "error": str(e)[:100],
            })

    ok_count = sum(1 for r in processed if r.get("ok"))
    print(f"\n✅ 有完整笔记的：{ok_count}/{len(items)}（其余只有元信息）")

    # 构造周报投喂包
    weekly_meta = {
        "title": f"周报 {datetime.now().strftime('%Y-%m-%d')}",
        "author": scan_result.get("newsletter", {}).get("name", "我的周报"),
        "uploader": scan_result.get("newsletter", {}).get("name", "我的周报"),
        "url": f"digest://{digest_name}",
    }
    # 把每条内容做摘要拼起来
    sections = []
    for r in processed:
        bundle_path = r.get("bundle_path")
        excerpt = ""
        if bundle_path and Path(bundle_path).exists():
            content = Path(bundle_path).read_text(encoding="utf-8")
            if "## 📜 原文" in content:
                after = content.split("## 📜 原文", 1)[1]
                if "```" in after:
                    excerpt = after.split("```", 2)[1].strip()[:1500]

        # 区分有完整笔记 vs 仅元信息
        if r.get("ok"):
            sections.append(
                f"### {r.get('source_name')} | {r.get('title')}\n"
                f"- 链接：{r.get('url')}\n"
                f"- 平台：{r.get('platform')}\n"
                f"- 字数：{r.get('chars')}\n\n"
                f"原文摘录：\n```\n{excerpt}\n```\n"
            )
        else:
            # 没字幕的视频，只放元信息
            sections.append(
                f"### {r.get('source_name')} | {r.get('title')}\n"
                f"- 链接：{r.get('url')}\n"
                f"- 平台：{r.get('platform')}\n"
                f"- ⚠️ 状态：仅元信息（{r.get('error','无字幕未转写')}）\n"
                f"- 编辑提示：基于标题猜测内容主题，简短点评，吸引读者点开看\n"
            )

    weekly_template = (root / "templates" / "weekly_digest.md").read_text(encoding="utf-8")
    parts = weekly_template.split("## Prompt", 1)
    instruction = parts[1].split("\n", 1)[1].strip() if len(parts) > 1 else weekly_template

    weekly_prompt = f"""# 任务：把本周新内容编辑成 Newsletter

## 📌 本期信息
- **刊物名**：{weekly_meta['author']}
- **日期**：{datetime.now().strftime('%Y-%m-%d')}
- **共 {len(processed)} 条内容**

---

## 📋 你的任务

{instruction}

---

## 📜 本周内容资料

{chr(10).join(sections)}

---

请直接输出最终的周报 Markdown，不要任何前言。
"""

    weekly_path = out_dir / f"{digest_name}.WEEKLY.prompt.md"
    weekly_path.write_text(weekly_prompt, encoding="utf-8")
    print(f"\n📦 周报投喂包：{weekly_path}")

    return {
        "digest_name": digest_name,
        "items_processed": len(processed),
        "weekly_prompt_path": weekly_path,
        "sub_bundle_paths": [r.get("bundle_path") for r in processed if r.get("bundle_path")],
        "epub_candidates": processed,
        "out_dir": out_dir,
        "raw_items": items,
    }


def auto_generate_weekly(root: Path, weekly_prompt_path: Path) -> Path | None:
    """如果配置了 LLM key，自动跑出周报正文。"""
    from run_llm import run_llm, is_available
    if not is_available():
        return None
    prompt = weekly_prompt_path.read_text(encoding="utf-8")
    print(f"\n🤖 调 LLM 生成周报...")
    result, provider = run_llm(prompt)
    if not result:
        return None
    final = weekly_prompt_path.parent / f"{weekly_prompt_path.stem.replace('.WEEKLY.prompt','')}.FINAL.md"
    final.write_text(result, encoding="utf-8")
    print(f"   ✅ {provider} 已生成：{final}")
    return final


def build_epub_if_many(root: Path, bundle: dict, threshold: int = 5) -> Path | None:
    """如果本周内容 >= threshold，把所有处理过的内容打包成 EPUB。"""
    if bundle["items_processed"] < threshold:
        return None
    try:
        from export_epub import export_epub
    except ImportError:
        return None

    chapters = []
    for r in bundle.get("epub_candidates", []):
        bp = r.get("bundle_path")
        if not bp or not Path(bp).exists():
            continue
        content = Path(bp).read_text(encoding="utf-8")
        # 直接把 prompt md 内容当章节
        chapters.append((r.get("title", "未命名"), content))

    if not chapters:
        return None

    out = bundle["out_dir"] / f"{bundle['digest_name']}.epub"
    export_epub(
        title=f"周报 {datetime.now().strftime('%Y-%m-%d')}",
        author="content-catcher",
        chapters=chapters,
        out_path=out,
    )
    print(f"\n📚 已生成 EPUB：{out}")
    return out


def send_weekly_email(scan_result: dict, weekly_md: Path,
                      attachments: list[Path] | None = None) -> tuple[bool, str]:
    """根据 newsletter 配置发邮件。"""
    from email_sender import send_email
    nl = scan_result.get("newsletter", {})
    if not nl.get("email_to") or not nl.get("smtp"):
        return False, "newsletter 配置缺 email_to 或 smtp"

    subject = f"📬 {nl.get('name', '本周周报')} - {datetime.now().strftime('%Y-%m-%d')}"
    body = weekly_md.read_text(encoding="utf-8")

    print(f"\n📧 发送邮件到 {nl['email_to']}...")
    ok, info = send_email(
        smtp_cfg=nl["smtp"],
        from_addr=nl.get("email_from") or nl["smtp"]["user"],
        to_addr=nl["email_to"],
        subject=subject,
        md_body=body,
        attachments=attachments or [],
    )
    if ok:
        print(f"   ✅ 邮件已发送")
    else:
        print(f"   ❌ {info}")
    return ok, info
