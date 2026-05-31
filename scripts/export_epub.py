"""
把 Markdown 笔记导出为 EPUB 电子书（适合 Kindle / iPad / Apple Books）。
"""
import re
from pathlib import Path
from datetime import datetime


def markdown_to_html(md_text: str) -> str:
    try:
        import markdown as md_lib
        return md_lib.markdown(md_text, extensions=["tables", "fenced_code", "toc"])
    except ImportError:
        from html import escape
        # 简陋兜底
        html = escape(md_text)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.M)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.M)
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.M)
        return f"<pre style='white-space:pre-wrap'>{html}</pre>"


def export_epub(title: str,
                author: str,
                chapters: list[tuple[str, str]],   # [(章节名, Markdown 内容), ...]
                out_path: Path,
                language: str = "zh") -> Path:
    """
    生成 EPUB。chapters 顺序就是电子书的章节顺序。
    依赖 ebooklib + lxml。沙箱里可能因 lxml 签名问题失败，本机环境正常。
    """
    try:
        from ebooklib import epub
    except ImportError as e:
        raise RuntimeError(
            f"EPUB 导出依赖 ebooklib + lxml 不可用：{e}。"
            f"在 macOS 沙箱里 lxml 可能签名异常；本机环境跑 "
            f"`pip install ebooklib lxml` 即可。"
        ) from e

    book = epub.EpubBook()
    book.set_identifier(f"content-catcher-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    book.set_title(title)
    book.set_language(language)
    book.add_author(author or "content-catcher")

    epub_chapters = []
    css_content = """
        body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
               line-height: 1.75; font-size: 1em; }
        h1 { font-size: 1.6em; margin-top: 1.2em; }
        h2 { font-size: 1.3em; margin-top: 1em; border-bottom: 1px solid #eee;
             padding-bottom: 0.2em; }
        h3 { font-size: 1.1em; margin-top: 0.8em; }
        p, li { margin: 0.6em 0; }
        blockquote { border-left: 3px solid #888; padding-left: 1em; color: #555;
                     margin: 1em 0; }
        code { background: #f4f4f4; padding: 0.1em 0.3em; border-radius: 3px; }
        pre { background: #f7f7f7; padding: 1em; overflow: auto; border-radius: 4px; }
        table { border-collapse: collapse; margin: 1em 0; }
        th, td { border: 1px solid #ddd; padding: 0.5em 0.8em; }
        th { background: #f7f7f7; }
    """
    style = epub.EpubItem(uid="style_default", file_name="style/main.css",
                          media_type="text/css", content=css_content)
    book.add_item(style)

    for i, (ch_title, ch_md) in enumerate(chapters, 1):
        html = markdown_to_html(ch_md)
        ch = epub.EpubHtml(title=ch_title, file_name=f"chap_{i:02d}.xhtml",
                           lang=language)
        ch.content = f"<html><head><title>{ch_title}</title>" \
                     f'<link rel="stylesheet" type="text/css" href="style/main.css"/></head>' \
                     f"<body>{html}</body></html>"
        ch.add_item(style)
        book.add_item(ch)
        epub_chapters.append(ch)

    book.toc = tuple(epub_chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + epub_chapters

    out_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(out_path), book)
    return out_path


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "output" / "epub" / "test.epub"
    p = export_epub(
        title="测试电子书",
        author="content-catcher",
        chapters=[
            ("第一章 引言", "# 引言\n\n这是一本测试 EPUB。\n\n## 章节小节\n\n正文..."),
            ("第二章 主体", "# 主体\n\n- 要点 1\n- 要点 2\n- 要点 3"),
        ],
        out_path=out,
    )
    print(f"✅ 生成 EPUB：{p}（{p.stat().st_size} bytes）")
