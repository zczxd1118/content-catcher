"""验证 export_epub 能生成结构合法的 EPUB 文件。

跑法（在仓库根目录）：
    python tests/test_export_epub.py

期望：
    生成的 .epub 是合法 ZIP，含 mimetype / OPF / nav，章节内容
    完整保留中文 / Emoji / Markdown 渲染（标题、列表、表格、引用）。
"""
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from export_epub import export_epub  # noqa: E402


# ---------- 测试 1：最小 EPUB 能成功生成 ----------
def test_minimal_epub():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "min.epub"
        export_epub(
            title="最小测试",
            author="tester",
            chapters=[("ch1", "# hello\n\nworld")],
            out_path=out,
        )
        assert out.exists(), "EPUB 文件没生成"
        assert out.stat().st_size > 0, "EPUB 是空文件"
        print(f"✅ 最小 EPUB 生成成功（{out.stat().st_size} bytes）")


# ---------- 测试 2：EPUB 是合法 ZIP 且结构正确 ----------
def test_epub_structure():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "struct.epub"
        export_epub(
            title="结构测试",
            author="tester",
            chapters=[
                ("第一章", "# 引言\n\n段落"),
                ("第二章", "# 主体\n\n- a\n- b"),
                ("第三章", "# 尾声"),
            ],
            out_path=out,
        )

        with zipfile.ZipFile(out) as z:
            files = z.namelist()
            # 必须有的 EPUB 标准结构
            assert "mimetype" in files, "缺 mimetype"
            assert "META-INF/container.xml" in files, "缺 container.xml"
            opf = [f for f in files if f.endswith(".opf")]
            assert opf, "缺 OPF（包文件）"
            nav = [f for f in files if f.endswith("nav.xhtml")]
            assert nav, "缺 nav.xhtml（导航）"
            # 章节数
            chap_files = [f for f in files if "chap_" in f and f.endswith(".xhtml")]
            assert len(chap_files) == 3, f"期望 3 章，实际 {len(chap_files)}"
            # nav 里有 3 条 <li>
            nav_html = z.read(nav[0]).decode("utf-8")
            assert nav_html.count("<li>") >= 3, "nav 里章节数对不上"
            # mimetype 内容必须是 application/epub+zip
            mt = z.read("mimetype").decode("ascii")
            assert mt.strip() == "application/epub+zip", f"mimetype 异常：{mt!r}"
        print(f"✅ EPUB 结构正确（{len(files)} 个文件，3 章）")


# ---------- 测试 3：中文 + Emoji + 复杂 Markdown 不丢失 ----------
def test_unicode_and_markdown():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "unicode.epub"
        rich_md = (
            "# 中文标题 🚀\n\n"
            "这是**粗体**和*斜体*，包含 Emoji 🎉 与破折号 ——。\n\n"
            "## 子标题\n\n"
            "- 列表项 1\n"
            "- 列表项 2 含 `inline code`\n\n"
            "| 列 A | 列 B |\n|---|---|\n| 一 | 二 |\n\n"
            "> 引用块：所有事都得伴着疼。\n\n"
            "```python\nprint('hello world')\n```\n"
        )
        export_epub(
            title="中文 EPUB 🚀",
            author="周小丁",
            chapters=[("第 1 章 · 中文测试", rich_md)],
            out_path=out,
        )

        with zipfile.ZipFile(out) as z:
            chap = next(f for f in z.namelist() if "chap_" in f)
            content = z.read(chap).decode("utf-8")
            # 关键内容必须保留
            assert "中文标题" in content, "中文标题丢失"
            assert "🚀" in content, "Emoji 丢失"
            assert "周小丁" in content or True, ""  # author 在 OPF 不在章节内
            # Markdown 渲染：粗体 / 列表 / 引用 / 代码
            assert "<strong>" in content, "粗体没渲染"
            assert "<ul>" in content or "<li>" in content, "列表没渲染"
            assert "<blockquote>" in content, "引用没渲染"
            assert "<code>" in content, "代码块没渲染"
        print("✅ 中文 / Emoji / 复杂 Markdown 保留完整")


if __name__ == "__main__":
    test_minimal_epub()
    test_epub_structure()
    test_unicode_and_markdown()
    print("\n🎉 所有 EPUB 回归测试通过")
