"""把抓到的字幕 + 元信息 + 占位的 LLM 笔记 拼成 Markdown 文件落盘。"""
import re
from pathlib import Path
from datetime import datetime


def safe_filename(text: str, max_len: int = 60) -> str:
    """把标题转成可作文件名的安全字符串。"""
    text = re.sub(r"[\\/:*?\"<>|\n\r\t]", "", text or "untitled")
    text = text.strip()[:max_len]
    return text or "untitled"


def render_markdown(meta: dict, subtitle_text: str, lang: str, source: str,
                    llm_notes: str | None = None) -> str:
    """生成 Markdown 内容。"""
    title = meta.get("title", "未知标题")
    uploader = meta.get("uploader", "未知作者")
    duration = meta.get("duration_sec")
    duration_str = f"{duration // 60}分{duration % 60}秒" if duration else "未知"
    url = meta.get("url", "")
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    md = f"""# {title}

> 📌 **来源**：[{url}]({url})
> 👤 **作者**：{uploader}
> ⏱️ **时长**：{duration_str}
> 🌐 **原文语言**：{lang}
> 🔧 **字幕来源**：{source}
> 📅 **抓取时间**：{today}

---

## 📝 笔记

{llm_notes or "_（待 LLM 结构化：把下方原文交给 AI，套用对应模板生成笔记）_"}

---

## 📜 原文字幕

```
{subtitle_text}
```
"""
    return md


def save(meta: dict, subtitle_text: str, lang: str, source: str,
         out_dir: Path, llm_notes: str | None = None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = safe_filename(meta.get("title", "untitled")) + ".md"
    path = out_dir / fname
    md = render_markdown(meta, subtitle_text, lang, source, llm_notes)
    path.write_text(md, encoding="utf-8")
    return path
