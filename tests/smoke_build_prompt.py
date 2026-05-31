"""自检：用假数据测投喂包生成（不依赖网络）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_prompt import save_bundle, build_prompt
from detect_language import detect_language


def main():
    # 假数据 1：中文字幕
    meta_zh = {
        "title": "测试视频 - 中文播客示例",
        "uploader": "测试频道",
        "duration_sec": 1800,
        "url": "https://example.com/zh",
    }
    text_zh = (
        "大家好，今天我们来聊一聊 AI 时代下的产品经理转型问题。"
        "首先，我想谈谈传统产品经理面临的三大挑战。"
        "第一是技术理解的门槛在升高，第二是用户预期在变化，"
        "第三是产品迭代周期被压缩到极致。"
    ) * 5

    # 假数据 2：英文字幕
    meta_en = {
        "title": "Test Video - English Podcast Example",
        "uploader": "Test Channel",
        "duration_sec": 1800,
        "url": "https://example.com/en",
    }
    text_en = (
        "Today we're talking about agentic AI and the future of work. "
        "The first key idea is that AI agents are not just tools, they're collaborators. "
        "The second insight is about delegation - we need to learn when to trust them. "
        "Third, the economics of this technology will reshape entire industries."
    ) * 5

    out_dir = ROOT / "output" / "bundles"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== 中文样本 ===")
    lang_zh = detect_language(text_zh)
    print(f"语言判断：{lang_zh}")
    p1, c1 = save_bundle(meta_zh, text_zh, lang_zh, "fake-source", out_dir)
    print(f"prompt: {p1.name} ({p1.stat().st_size} bytes)")
    print(f"ctx:    {c1.name}")

    print("\n=== 英文样本 ===")
    lang_en = detect_language(text_en)
    print(f"语言判断：{lang_en}")
    p2, c2 = save_bundle(meta_en, text_en, lang_en, "fake-source", out_dir)
    print(f"prompt: {p2.name} ({p2.stat().st_size} bytes)")
    print(f"ctx:    {c2.name}")

    # 抽样看一下中文 prompt 头部
    print("\n=== 中文 prompt 文件前 800 字预览 ===")
    print(p1.read_text(encoding="utf-8")[:800])

    print("\n✅ 自检通过")


if __name__ == "__main__":
    main()
