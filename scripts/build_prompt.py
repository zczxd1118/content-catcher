"""
投喂包构造器（M3 升级版）。

支持：
  - 三种模板：中文笔记 / 英文双语 / 小红书图文
  - 长内容自动分段：每段独立投喂包 + 一个汇总投喂包
"""
import json
from pathlib import Path
from datetime import datetime
from save_output import safe_filename
from chunker import chunk_text, need_chunking, DEFAULT_CHUNK_SIZE


TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

TEMPLATE_BY_TYPE = {
    "zh": "chinese_notes.md",
    "en": "english_bilingual.md",
    "xhs": "xiaohongshu_note.md",
    "deep": "deep_book.md",         # 深度模式：精装电子书风格（蒸馏改写）
    "full": "full_transcript.md",   # 完整版：逐字稿 + 导读（不删减）
}


def load_template(template_key: str) -> str:
    fname = TEMPLATE_BY_TYPE.get(template_key, "chinese_notes.md")
    return (TEMPLATES_DIR / fname).read_text(encoding="utf-8")


def extract_prompt_section(template_md: str) -> str:
    """从模板 md 中抽 '## Prompt' 后面的指令段。"""
    parts = template_md.split("## Prompt", 1)
    if len(parts) < 2:
        return template_md
    after = parts[1]
    # 跳过第一行（可能是"（给 AI 用）"小标题）
    if "\n" in after:
        return after.split("\n", 1)[1].strip()
    return after.strip()


def build_single_prompt(meta: dict, text: str, template_key: str,
                        source: str, chunk_info: str = "") -> str:
    """生成一个完整投喂包文本（单段或单 chunk）。"""
    template = load_template(template_key)
    instruction = extract_prompt_section(template)

    title = meta.get("title", "未知标题")
    uploader = meta.get("uploader") or meta.get("author") or "未知作者"
    duration = meta.get("duration_sec") or 0
    duration_str = f"{int(duration) // 60}分{int(duration) % 60}秒" if duration else "—"
    url = meta.get("url", "")
    lang_label = {"zh": "中文", "en": "英文", "xhs": "小红书图文"}.get(template_key, template_key)

    tags_line = ""
    if meta.get("tags"):
        tags_line = "- **话题标签**：" + " ".join(f"#{t}" for t in meta["tags"]) + "\n"

    return f"""# 任务：把以下内容转成结构化笔记

## 📌 内容信息
- **标题**：{title}
- **作者/频道**：{uploader}
- **时长**：{duration_str}
- **原文链接**：{url}
- **内容类型**：{lang_label}
- **字幕/原文来源**：{source}
{tags_line}{chunk_info}
---

## 📋 你的任务

{instruction}

---

## 📜 原文

```
{text}
```

---

请直接输出最终的 Markdown 笔记，不要任何前言。
"""


def build_merge_prompt(meta: dict, segment_count: int, template_key: str) -> str:
    """长内容场景：把 N 段单独生成的笔记，合并成一份完整笔记。"""
    title = meta.get("title", "未知标题")
    sections_hint = ""
    if template_key == "en":
        sections_hint = """
请合并时保留这些板块：
- Core Topics 核心议题（去重）
- Chapter Outline 章节大纲（按内容自然顺序）
- Key Quotes 金句摘录（精选最好的 8-12 句）
- Glossary 术语表（合并去重）
- Takeaways 行动启示（提炼最有价值的 5-7 条）
"""
    elif template_key == "xhs":
        sections_hint = """
请合并时保留这些板块：
- 笔记速览
- 信息提炼
- 二次创作钩子（精选最好的 5 条）
- 相关延伸方向
- 话题标签建议
"""
    else:
        sections_hint = """
请合并时保留这些板块：
- 一句话总结
- 核心议题（去重）
- 章节大纲（按内容自然顺序）
- 金句摘录（精选最好的 8-12 句）
- 关键人物/概念（合并去重）
- 行动清单（提炼最有价值的 5-7 条）
"""

    return f"""# 任务：合并多段笔记为一份完整笔记

## 📌 内容信息
- **标题**：{title}
- **原内容因为较长被切成了 {segment_count} 段**
- **下面会给你 {segment_count} 段笔记，请合并成一份完整、不重复、结构清晰的笔记**

## 📋 合并要求

{sections_hint}

合并原则：
- **不要简单堆叠**，要做去重 + 取最优
- **按内容自然顺序**而非按段落顺序排版
- 重复出现的观点 / 金句 / 术语 → 选最好的一条
- 同一主题被切到不同段 → 把它们合并起来

---

## 📜 各段笔记

(请把下面的占位符替换成各段笔记的内容)

{"".join(f"### 段 {i+1}/{segment_count}{chr(10)}<在此粘贴第 {i+1} 段笔记>{chr(10)}{chr(10)}" for i in range(segment_count))}

---

请直接输出合并后的最终 Markdown 笔记，不要任何前言。
"""


def build_context(meta: dict, text: str, template_key: str, source: str) -> dict:
    return {
        "version": "0.3.0",
        "generated_at": datetime.now().isoformat(),
        "meta": meta,
        "content": {
            "text_length": len(text),
            "template": template_key,
            "source": source,
        },
    }


def save_bundle(meta: dict, text: str, template_key: str, source: str,
                out_dir: Path,
                chunk_size: int = DEFAULT_CHUNK_SIZE) -> dict:
    """
    保存投喂包。返回 dict：
        {
          "prompts": [Path, ...],   # 单段或多段投喂包
          "merge": Path | None,     # 长内容场景的汇总投喂包
          "context": Path,
          "chunks": int,
        }
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    fname_base = safe_filename(meta.get("title", "untitled"))

    # 上下文 JSON
    ctx_path = out_dir / f"{fname_base}.context.json"
    ctx_path.write_text(
        json.dumps(build_context(meta, text, template_key, source),
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if not need_chunking(text, chunk_size):
        # 单段
        prompt_path = out_dir / f"{fname_base}.prompt.md"
        prompt_path.write_text(
            build_single_prompt(meta, text, template_key, source),
            encoding="utf-8",
        )
        return {"prompts": [prompt_path], "merge": None,
                "context": ctx_path, "chunks": 1}

    # 多段
    chunks = chunk_text(text, chunk_size=chunk_size)
    prompt_paths = []
    for c in chunks:
        chunk_info = (
            f"- **本段说明**：这是 {c.total} 段中的第 {c.idx} 段；"
            f"请先做本段笔记，最终会再做合并\n"
        )
        prompt_path = out_dir / f"{fname_base}.part{c.idx:02d}of{c.total:02d}.prompt.md"
        prompt_path.write_text(
            build_single_prompt(meta, c.text, template_key, source, chunk_info),
            encoding="utf-8",
        )
        prompt_paths.append(prompt_path)

    # 汇总投喂包
    merge_path = out_dir / f"{fname_base}.MERGE.prompt.md"
    merge_path.write_text(
        build_merge_prompt(meta, len(chunks), template_key),
        encoding="utf-8",
    )

    return {"prompts": prompt_paths, "merge": merge_path,
            "context": ctx_path, "chunks": len(chunks)}
