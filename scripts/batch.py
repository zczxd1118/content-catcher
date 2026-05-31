"""
批量处理器：一次跑多个 URL，生成：
  1. 每个 URL 的独立笔记（复用单链路管线）
  2. 一份 index.md 目录
  3. （可选）一份"专题合集"或"跨平台对比"汇总投喂包
"""
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Callable


def read_urls_from_file(path: Path) -> list[tuple[str, str | None]]:
    """
    读 URL 文件，每行一个 URL。支持：
      # 注释
      URL
      URL --cookies-from safari      ← 行内参数（暂只支持 --cookies-from）
    返回 [(url, cookies_from), ...]
    """
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        url = parts[0]
        cookies_from = None
        if "--cookies-from" in parts:
            i = parts.index("--cookies-from")
            if i + 1 < len(parts):
                cookies_from = parts[i + 1]
        items.append((url, cookies_from))
    return items


def write_index(root: Path, batch_name: str, results: list[dict]) -> Path:
    """生成批量索引 index.md。"""
    out_dir = root / "output" / "batches" / batch_name
    out_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# 批量索引：{batch_name}",
        "",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> 共处理 {len(results)} 个链接，"
        f"成功 {sum(1 for r in results if r.get('ok'))} 个，"
        f"失败 {sum(1 for r in results if not r.get('ok'))} 个",
        "",
        "## 链接列表",
        "",
        "| # | 状态 | 标题 | 平台 | 来源 | 字数 | 链接 |",
        "|---|------|------|------|------|------|------|",
    ]
    for i, r in enumerate(results, 1):
        status = "✅" if r.get("ok") else "❌"
        title = r.get("title") or "(未知)"
        platform = r.get("platform") or "-"
        src = r.get("source") or "-"
        nchars = r.get("chars") or "-"
        url = r.get("url") or ""
        # 表格里的 | 会断格，做转义
        title_safe = title.replace("|", "丨")
        lines.append(f"| {i} | {status} | {title_safe} | {platform} | {src} | {nchars} | [link]({url}) |")

    lines.append("")
    lines.append("## 产物文件")
    lines.append("")
    for i, r in enumerate(results, 1):
        if not r.get("ok"):
            continue
        bundle = r.get("bundle_path")
        if bundle:
            lines.append(f"- [{i}] [{Path(bundle).name}](../../bundles/{Path(bundle).name})")

    # 失败原因
    failed = [r for r in results if not r.get("ok")]
    if failed:
        lines.append("")
        lines.append("## 失败原因")
        lines.append("")
        for i, r in enumerate(failed, 1):
            lines.append(f"- {r.get('url')} → {r.get('error', '未知错误')}")

    index_path = out_dir / "index.md"
    index_path.write_text("\n".join(lines), encoding="utf-8")
    return index_path


def build_collection_prompt(root: Path, batch_name: str, results: list[dict],
                            mode: str = "topic") -> Path | None:
    """
    根据多个子笔记生成"专题合集"或"跨平台对比"的汇总投喂包。
    mode: "topic" → topic_collection.md
          "compare" → cross_platform_compare.md
    """
    if not results:
        return None

    templates_dir = root / "templates"
    template_name = {
        "topic": "topic_collection.md",
        "compare": "cross_platform_compare.md",
    }.get(mode, "topic_collection.md")
    template_md = (templates_dir / template_name).read_text(encoding="utf-8")
    parts = template_md.split("## Prompt", 1)
    instruction = parts[1].split("\n", 1)[1].strip() if len(parts) > 1 else template_md

    out_dir = root / "output" / "batches" / batch_name
    out_dir.mkdir(parents=True, exist_ok=True)

    # 收集每个 ok 的 bundle 内容
    sources_block = []
    for i, r in enumerate(results, 1):
        if not r.get("ok"):
            continue
        title = r.get("title") or "(未知)"
        platform = r.get("platform") or "-"
        url = r.get("url") or ""
        bundle_path = r.get("bundle_path")
        excerpt = ""
        if bundle_path and Path(bundle_path).exists():
            content = Path(bundle_path).read_text(encoding="utf-8")
            # 把原文部分摘出来当摘要喂给 AI（避免重复整个 prompt 模板）
            if "## 📜 原文" in content:
                excerpt = content.split("## 📜 原文", 1)[1]
                excerpt = excerpt.split("```", 2)[1] if "```" in excerpt else excerpt
                excerpt = excerpt.strip()[:3000]
        sources_block.append(
            f"### 来源 {i}\n"
            f"- 标题：{title}\n"
            f"- 平台：{platform}\n"
            f"- 链接：{url}\n\n"
            f"**该来源的核心笔记（已由 AI 生成或原文摘录）**：\n\n"
            f"<在此粘贴第 {i} 份子笔记 / 或直接保留下方原文摘要>\n\n"
            f"原文摘要：\n```\n{excerpt}\n```\n"
        )

    mode_label = {"topic": "专题合集", "compare": "跨平台对比"}.get(mode, mode)

    prompt = f"""# 任务：把以下多份内容做{mode_label}

## 📌 批次信息
- **批次名**：{batch_name}
- **共 {len(sources_block)} 份内容**
- **合并模式**：{mode_label}

---

## 📋 你的任务

{instruction}

---

## 📜 各来源资料

{chr(10).join(sources_block)}

---

请直接输出最终的 Markdown {mode_label}笔记，不要任何前言。
"""
    suffix = "COLLECTION" if mode == "topic" else "COMPARE"
    p = out_dir / f"{batch_name}.{suffix}.prompt.md"
    p.write_text(prompt, encoding="utf-8")
    return p


def run_batch(root: Path,
              urls: list[tuple[str, str | None]],
              process_one: Callable,
              batch_name: str,
              mode: str = "index",     # index / topic / compare
              use_cache: bool = True,
              raw: bool = False,
              extra_args: dict | None = None) -> dict:
    """
    主批量调度。process_one 是单链路处理函数，签名：
        process_one(url, cookies_from, raw, **extra_args) -> dict
    返回 {ok: bool, title, platform, source, chars, bundle_path, url, error?}
    """
    extra_args = extra_args or {}
    results = []
    total = len(urls)
    start_time = time.time()

    print(f"\n🚀 启动批量模式")
    print(f"   批次名：{batch_name}")
    print(f"   待处理：{total} 个链接")
    print(f"   合并模式：{mode}")
    print(f"   使用缓存：{use_cache}\n")

    from cache import load as cache_load, save as cache_save

    for i, (url, cookies_from) in enumerate(urls, 1):
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📦 [{i}/{total}] {url[:80]}{'...' if len(url) > 80 else ''}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        if use_cache:
            cached = cache_load(root, url)
            if cached and cached.get("ok"):
                print(f"   ⚡ 命中缓存，跳过抓取")
                results.append({**cached, "url": url})
                continue

        try:
            result = process_one(url, cookies_from or extra_args.get("cookies_from"),
                                 raw, **{k: v for k, v in extra_args.items() if k != "cookies_from"})
            result["url"] = url
            cache_save(root, url, result)
            results.append(result)
        except SystemExit as e:
            # 单链路里调用 sys.exit 时，包装成失败结果
            r = {"ok": False, "url": url, "error": f"SystemExit code={e.code}"}
            results.append(r)
            print(f"   ❌ 失败：SystemExit({e.code})")
        except Exception as e:
            r = {"ok": False, "url": url, "error": str(e)[:200]}
            results.append(r)
            print(f"   ❌ 异常：{e}")

    elapsed = time.time() - start_time
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    ok_n = sum(1 for r in results if r.get("ok"))
    print(f"✅ 批量完成：{ok_n}/{total} 成功，耗时 {elapsed:.1f}s\n")

    # 写索引
    index = write_index(root, batch_name, results)
    print(f"📋 批量索引：{index}")

    # 写合集（如需）
    if mode in ("topic", "compare") and ok_n > 0:
        merge_path = build_collection_prompt(root, batch_name, results, mode)
        if merge_path:
            mode_label = {"topic": "专题合集", "compare": "跨平台对比"}[mode]
            print(f"📚 {mode_label}投喂包：{merge_path}")

    return {"results": results, "index": index, "ok": ok_n, "total": total}
