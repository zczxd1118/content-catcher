"""M4 完整自检：批量 / 缓存 / 索引 / 合集 / 对比。"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from batch import run_batch, read_urls_from_file
from cache import save as cache_save, load as cache_load, clear as cache_clear


def fake_process(url, cookies_from, raw, **kwargs):
    """假的单链路处理函数：直接编造结果，用于测试批量调度。"""
    if "fail" in url:
        return {"ok": False, "error": "fake-failure"}
    title = url.split("/")[-1] or "fake-title"
    platform = "xiaohongshu" if "xiaohongshu" in url else \
               "bilibili" if "bilibili" in url else \
               "youtube" if "youtube" in url else "unknown"
    # 模拟生成一个 bundle 文件
    bundles_dir = ROOT / "output" / "bundles"
    bundles_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = bundles_dir / f"fake-{abs(hash(url)) % 100000}.prompt.md"
    bundle_path.write_text(
        f"# 假的投喂包 for {title}\n\n## 📜 原文\n\n```\n模拟内容来自 {url}\n```\n",
        encoding="utf-8"
    )
    return {
        "ok": True, "title": title, "platform": platform,
        "source": "fake-source", "chars": 1234,
        "bundle_path": str(bundle_path), "chunks": 1,
    }


def main():
    print("=" * 60)
    print("M4 完整自检")
    print("=" * 60)

    # 清空测试缓存
    cache_clear(ROOT)

    # ----- Test 1: URL 文件解析 -----
    print("\n[1] URL 文件解析：")
    urls_file = ROOT / "tests" / "fixtures_urls.txt"
    urls_file.parent.mkdir(parents=True, exist_ok=True)
    urls_file.write_text("""# 这是注释
https://www.bilibili.com/video/BV1xxx --cookies-from safari
https://www.youtube.com/watch?v=abc
https://www.xiaohongshu.com/explore/note1

# 中间空行
https://example.com/should-fail-test
""", encoding="utf-8")
    items = read_urls_from_file(urls_file)
    print(f"   解析到 {len(items)} 个链接")
    for u, c in items:
        print(f"   - {u[:60]:60s} cookies={c}")
    assert len(items) == 4

    # ----- Test 2: 批量处理 + index 模式 -----
    print("\n[2] 批量 index 模式：")
    s1 = run_batch(ROOT, items[:3], fake_process, "test-batch-index",
                   mode="index", use_cache=True)
    assert s1["ok"] == 3
    assert s1["total"] == 3
    print(f"   ✅ index 模式：{s1['ok']}/{s1['total']} 成功")
    print(f"   ✅ 索引文件：{s1['index'].relative_to(ROOT)}")

    # ----- Test 3: 缓存命中 -----
    print("\n[3] 缓存命中复测：")
    t0 = time.time()
    s2 = run_batch(ROOT, items[:3], fake_process, "test-batch-cached",
                   mode="index", use_cache=True)
    t1 = time.time()
    print(f"   ✅ 第二次跑耗时 {(t1-t0)*1000:.1f}ms（应该很快，因为缓存命中）")

    # ----- Test 4: 失败容错 -----
    print("\n[4] 失败容错（混入 fail URL）：")
    s3 = run_batch(ROOT, items, fake_process, "test-batch-with-fail",
                   mode="index", use_cache=False)
    assert s3["ok"] == 3 and s3["total"] == 4
    print(f"   ✅ {s3['ok']}/{s3['total']} 成功，1 个失败但不影响整体")

    # ----- Test 5: topic 专题合集模式 -----
    print("\n[5] 专题合集模式：")
    s4 = run_batch(ROOT, items[:3], fake_process, "test-topic",
                   mode="topic", use_cache=False)
    out_dir = ROOT / "output" / "batches" / "test-topic"
    collection = out_dir / "test-topic.COLLECTION.prompt.md"
    assert collection.exists()
    print(f"   ✅ 专题合集 prompt：{collection.relative_to(ROOT)}")

    # ----- Test 6: compare 跨平台对比模式 -----
    print("\n[6] 跨平台对比模式：")
    s5 = run_batch(ROOT, items[:3], fake_process, "test-compare",
                   mode="compare", use_cache=False)
    compare = ROOT / "output" / "batches" / "test-compare" / "test-compare.COMPARE.prompt.md"
    assert compare.exists()
    print(f"   ✅ 跨平台对比 prompt：{compare.relative_to(ROOT)}")

    # ----- Test 7: 抽样查看产物 -----
    print("\n[7] 跨平台对比投喂包前 600 字预览：")
    print(compare.read_text(encoding="utf-8")[:600])

    print("\n" + "=" * 60)
    print("✅ M4 自检全部通过")
    print("=" * 60)


if __name__ == "__main__":
    main()
