"""
M3 完整回归自检：
  1. 分段器正常工作
  2. 短文本仍走单段投喂包
  3. 长文本走多段 + 汇总投喂包
  4. 小红书图文模板可加载
  5. 三种 template_key（zh/en/xhs）都能生成投喂包
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from chunker import chunk_text, need_chunking
from build_prompt import save_bundle, load_template


def main():
    print("=" * 60)
    print("M3 完整自检")
    print("=" * 60)

    # ----- Test 1: 模板加载 -----
    print("\n[1] 三种模板都能加载：")
    for key in ["zh", "en", "xhs"]:
        tpl = load_template(key)
        print(f"   ✅ {key}: {len(tpl)} bytes")

    # ----- Test 2: 短文本 → 单段 -----
    print("\n[2] 短文本 → 单段投喂包：")
    short_meta = {"title": "短文本测试", "uploader": "tester", "url": "https://test/short"}
    short_text = "这是一段很短的测试内容。" * 20  # 240 字符
    out_dir = ROOT / "output" / "bundles"
    r1 = save_bundle(short_meta, short_text, "zh", "test", out_dir, chunk_size=12000)
    print(f"   chunks={r1['chunks']}（应为 1）")
    assert r1["chunks"] == 1
    assert r1["merge"] is None
    print(f"   ✅ {r1['prompts'][0].name}")

    # ----- Test 3: 长文本 → 多段 + 汇总 -----
    print("\n[3] 长文本 → 多段投喂包 + 汇总：")
    long_meta = {"title": "长文本测试 - 三小时访谈", "uploader": "tester",
                 "url": "https://test/long", "duration_sec": 10800}
    long_text = "这是一段很长的测试内容。" * 5000  # ~60000 字符
    r2 = save_bundle(long_meta, long_text, "en", "test", out_dir, chunk_size=12000)
    print(f"   chunks={r2['chunks']}（应 >= 4）")
    assert r2["chunks"] >= 4
    assert r2["merge"] is not None
    for p in r2["prompts"]:
        print(f"   ✅ {p.name}")
    print(f"   ✅ MERGE: {r2['merge'].name}")

    # ----- Test 4: 小红书模板 -----
    print("\n[4] 小红书图文投喂包：")
    xhs_meta = {
        "title": "vibe coding 把播客变 ebook 的工作流",
        "author": "张咋啦",
        "url": "https://xhs/test",
        "tags": ["vibecoding", "claudecode", "播客"],
    }
    xhs_text = "之前把 Acquired 变成纸质书的后续，成功把工作流自动化了 🎉 全程纯自然语言。"
    r3 = save_bundle(xhs_meta, xhs_text, "xhs", "test", out_dir, chunk_size=12000)
    print(f"   chunks={r3['chunks']}")
    print(f"   ✅ {r3['prompts'][0].name}")

    # ----- Test 5: 抽样查看小红书投喂包内容 -----
    print("\n[5] 小红书投喂包内容预览：")
    content = r3["prompts"][0].read_text(encoding="utf-8")
    print(content[:600])

    print("\n" + "=" * 60)
    print("✅ M3 自检全部通过")
    print("=" * 60)


if __name__ == "__main__":
    main()
