"""验证 build_epub_if_many 优先用代笔成品，找不到就放占位章节，
而不是把投喂包（LLM prompt + 原始字幕）塞进 EPUB。

跑法：
    python tests/test_build_epub_polished.py
"""
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from digest import build_epub_if_many, _find_polished_chapter, _slugify_title  # noqa: E402


def _make_bundle(out_dir: Path, items_processed: int, candidates: list[dict]) -> dict:
    return {
        "digest_name": out_dir.name,
        "items_processed": items_processed,
        "out_dir": out_dir,
        "epub_candidates": candidates,
    }


# ---------- 测试 1：阈值未达不出 EPUB ----------
def test_below_threshold_returns_none():
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "weekly-test-low"
        out_dir.mkdir()
        bundle = _make_bundle(out_dir, items_processed=2, candidates=[])
        result = build_epub_if_many(Path(tmp), bundle, threshold=5)
        assert result is None, "未达阈值应返回 None"
    print("✅ 未达阈值时不生成 EPUB")


# ---------- 测试 2：有代笔单章 → 章节内容来自 chapter-<slug>.md，不是投喂包 ----------
def test_polished_chapter_used():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out_dir = root / "output" / "digest" / "weekly-test-polished"
        out_dir.mkdir(parents=True)

        # 准备投喂包（模拟 Whisper 转写 + LLM 任务说明）
        bundle_md = out_dir / "fake.prompt.md"
        bundle_md.write_text(
            "# 任务：把以下内容转成笔记\n\n"
            "## 📋 你的任务\n请基于...\n\n"
            "## 📜 原文\n```\n这里是 Whisper 转写的字幕原文，不该出现在 EPUB 里\n```\n",
            encoding="utf-8",
        )

        # 写一份代笔单章
        record = {
            "title": "测试视频标题",
            "url": "https://example.com/v",
            "source_name": "测试频道",
            "platform": "test",
            "bundle_path": str(bundle_md),
        }
        slug = _slugify_title(record["title"])
        chapter = out_dir / f"chapter-{slug}.md"
        chapter.write_text(
            "# 优美的代笔正文\n\n这是经过 LLM 整理的优美文章，**不含**字幕原文。\n\n"
            "## 一句话总结\n\n这是一段已经蒸馏过的内容。\n",
            encoding="utf-8",
        )

        bundle = _make_bundle(out_dir, items_processed=1, candidates=[record])
        result = build_epub_if_many(root, bundle, threshold=1)
        assert result is not None
        assert result.exists()

        with zipfile.ZipFile(result) as z:
            chap_content = z.read("EPUB/chap_01.xhtml").decode("utf-8")
            # 必须包含代笔正文的关键词
            assert "优美的代笔正文" in chap_content, "代笔标题没进 EPUB"
            assert "已经蒸馏过" in chap_content, "代笔正文没进 EPUB"
            # ❌ 必须不包含投喂包里的标志性内容
            assert "Whisper 转写的字幕原文" not in chap_content, \
                "❌ 投喂包内容不该出现在 EPUB"
            assert "请基于" not in chap_content, \
                "❌ LLM 任务说明不该出现在 EPUB"
    print("✅ 有代笔单章时，EPUB 章节使用代笔正文（非投喂包）")


# ---------- 测试 3：没有代笔单章 → 占位章节，且不包含投喂包内容 ----------
def test_placeholder_chapter_when_no_polished():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out_dir = root / "output" / "digest" / "weekly-test-placeholder"
        out_dir.mkdir(parents=True)

        bundle_md = out_dir / "fake.prompt.md"
        bundle_md.write_text(
            "# LLM 任务\n\n## 📜 原文\n```\n这是 Whisper 转写，不该出现\n```\n",
            encoding="utf-8",
        )
        record = {
            "title": "未代笔的视频",
            "url": "https://example.com/v2",
            "source_name": "测试频道",
            "platform": "test",
            "bundle_path": str(bundle_md),
        }

        bundle = _make_bundle(out_dir, items_processed=1, candidates=[record])
        result = build_epub_if_many(root, bundle, threshold=1)
        assert result is not None

        with zipfile.ZipFile(result) as z:
            chap = z.read("EPUB/chap_01.xhtml").decode("utf-8")
            assert "未代笔的视频" in chap, "占位章节应保留视频标题"
            assert "https://example.com/v2" in chap, "占位章节应保留链接"
            assert "尚未代笔" in chap, "占位章节应有提示"
            # ❌ 关键：投喂包内容不能漏进来
            assert "Whisper 转写" not in chap, \
                "❌ 占位章节不该包含投喂包字幕"
            assert "LLM 任务" not in chap, \
                "❌ 占位章节不该包含 LLM 任务说明"
    print("✅ 无代笔单章时，EPUB 用占位章节（不漏投喂包内容）")


# ---------- 测试 4：require_polished=False 时退回旧行为（debug 模式） ----------
def test_legacy_mode_includes_bundle():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out_dir = root / "output" / "digest" / "weekly-test-legacy"
        out_dir.mkdir(parents=True)

        bundle_md = out_dir / "fake.prompt.md"
        bundle_md.write_text("# Legacy\n\nFAKE_BUNDLE_MARKER", encoding="utf-8")
        record = {
            "title": "Legacy 视频",
            "bundle_path": str(bundle_md),
        }

        bundle = _make_bundle(out_dir, items_processed=1, candidates=[record])
        result = build_epub_if_many(root, bundle, threshold=1, require_polished=False)
        assert result is not None
        with zipfile.ZipFile(result) as z:
            chap = z.read("EPUB/chap_01.xhtml").decode("utf-8")
            assert "FAKE_BUNDLE_MARKER" in chap, \
                "legacy 模式应该把投喂包当章节"
    print("✅ legacy 模式（require_polished=False）行为兼容")


if __name__ == "__main__":
    test_below_threshold_returns_none()
    test_polished_chapter_used()
    test_placeholder_chapter_when_no_polished()
    test_legacy_mode_includes_bundle()
    print("\n🎉 所有 build_epub polished 行为测试通过")
