"""验证 _fetch_youtube_feed 在 YouTube 原生 endpoint 不可靠时能 fallback。

YouTube 在 2025 年起让 videos.xml 间歇性 5xx/404，必须有 fallback 链。
这些测试用 mock 替换 http_get + _parse_youtube_atom，保证逻辑正确性
（不依赖真实网络，沙箱里也能跑）。

跑法：
    python tests/test_youtube_fetcher_chain.py
"""
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import subscribe  # noqa: E402

CID = "UCSHZKyawb77ixDdsGog4iWA"

# 一段最小的合法 YouTube Atom feed，含 1 个 entry（够 _parse_youtube_atom 解析出 1 item）
SAMPLE_ATOM = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
      xmlns:media="http://search.yahoo.com/mrss/"
      xmlns="http://www.w3.org/2005/Atom">
  <title>Sample Channel</title>
  <entry>
    <id>yt:video:abc12345678</id>
    <yt:videoId>abc12345678</yt:videoId>
    <title>Test Video</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc12345678"/>
    <published>2026-06-01T00:00:00+00:00</published>
  </entry>
</feed>
"""


def test_native_succeeds_no_fallback():
    """原生 channel_id endpoint 成功 → 不应触发任何 fallback。"""
    calls = []

    def fake_http_get(url, **kw):
        calls.append(url)
        if "channel_id=" in url:
            return SAMPLE_ATOM
        return None

    with mock.patch.object(subscribe, "http_get", fake_http_get):
        items = subscribe._fetch_youtube_feed(CID, "Test")

    assert len(items) == 1, f"应抓到 1 条，实际 {len(items)}"
    assert items[0]["url"] == "https://www.youtube.com/watch?v=abc12345678"
    assert len(calls) == 1, f"原生成功不该 fallback，实际调用 {len(calls)} 次"
    assert "channel_id=" in calls[0]
    print("✅ 原生 channel_id 成功时不触发 fallback")


def test_native_fails_uulf_succeeds():
    """原生失败 → UULF playlist_id 成功。"""
    calls = []

    def fake_http_get(url, **kw):
        calls.append(url)
        if "channel_id=" in url:
            return None  # 原生失败
        if "playlist_id=UULF" in url:
            return SAMPLE_ATOM
        return None

    with mock.patch.object(subscribe, "http_get", fake_http_get):
        items = subscribe._fetch_youtube_feed(CID, "Test")

    assert len(items) == 1, f"UULF fallback 应抓到 1 条，实际 {len(items)}"
    assert any("channel_id=" in c for c in calls), "应该先试原生"
    assert any("playlist_id=UULF" + CID[2:] in c for c in calls), "UULF 替换错误"
    assert len(calls) == 2, f"原生失败后只该试 UULF 一次，实际 {len(calls)} 次"
    print("✅ 原生失败 → UULF 后备生效")


def test_native_returns_empty_falls_back():
    """原生返回 200 但 0 item（YouTube 的"假成功"）→ 仍触发 fallback。"""
    calls = []

    def fake_http_get(url, **kw):
        calls.append(url)
        if "channel_id=" in url:
            # 返回合法 XML 但 0 entry
            return b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>Empty</title></feed>'
        if "playlist_id=UULF" in url:
            return SAMPLE_ATOM
        return None

    with mock.patch.object(subscribe, "http_get", fake_http_get):
        items = subscribe._fetch_youtube_feed(CID, "Test")

    assert len(items) == 1, "0-item 假成功也该 fallback"
    assert len(calls) == 2, "应触发 1 次 fallback"
    print("✅ 原生 200-but-empty 也会 fallback")


def test_all_native_fail_uses_proxy():
    """原生 + UULF 都失败 → 走第三方代理。"""
    calls = []

    def fake_http_get(url, **kw):
        calls.append(url)
        # 原生和 UULF 都失败
        if "youtube.com/feeds/videos.xml" in url:
            return None
        # 第一个代理（rsshub.app）成功
        if "rsshub.app" in url:
            return SAMPLE_ATOM
        return None

    with mock.patch.object(subscribe, "http_get", fake_http_get):
        items = subscribe._fetch_youtube_feed(CID, "Test")

    assert len(items) == 1, "代理应抓到 1 条"
    proxy_calls = [c for c in calls if "rsshub" in c or "invidious" in c or "yewtu" in c]
    assert len(proxy_calls) >= 1, "应至少试一次代理"
    print("✅ 原生全失败 → 代理后备生效")


def test_everything_fails():
    """所有 fetcher 全失败 → 返回空 list，不抛异常。"""
    with mock.patch.object(subscribe, "http_get", lambda *a, **kw: None):
        items = subscribe._fetch_youtube_feed(CID, "Test")

    assert items == [], "全失败应返回 []"
    print("✅ 全失败时优雅返回空 list，不抛异常")


def test_parse_handles_missing_videoId():
    """openrss / 一些代理可能没有 yt:videoId namespace，从 <link href> 解析。"""
    # 无 yt:videoId，只有 link href
    xml = b"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Proxy Style Entry</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=xyz98765432"/>
    <published>2026-06-01T00:00:00Z</published>
  </entry>
</feed>"""
    items = subscribe._parse_youtube_atom(xml, "Test")
    assert len(items) == 1, "应能从 link href 解析 videoId"
    assert items[0]["url"] == "https://www.youtube.com/watch?v=xyz98765432"
    print("✅ 无 yt:videoId 时能从 <link href> 解析")


def test_http_retry_recovers():
    """http_get 加重试后，第一次 502 第二次成功也能拿到内容。"""
    attempts = {"n": 0}

    class FakeErr(Exception):
        pass

    def fake_urlopen(req, timeout):
        attempts["n"] += 1
        if attempts["n"] < 2:
            raise FakeErr("simulated 502")
        return mock.MagicMock(
            __enter__=lambda self: self,
            __exit__=lambda *a: None,
            read=lambda: b"hello",
        )

    with mock.patch.object(subscribe.urllib.request, "urlopen", side_effect=fake_urlopen):
        body = subscribe.http_get("https://example.com", quiet=True, retries=2, backoff=0.01)

    assert body == b"hello", f"重试后应拿到 hello，实际 {body}"
    assert attempts["n"] == 2, f"应重试 1 次（共 2 次尝试），实际 {attempts['n']}"
    print("✅ http_get 重试机制生效")


if __name__ == "__main__":
    test_native_succeeds_no_fallback()
    test_native_fails_uulf_succeeds()
    test_native_returns_empty_falls_back()
    test_all_native_fail_uses_proxy()
    test_everything_fails()
    test_parse_handles_missing_videoId()
    test_http_retry_recovers()
    print("\n🎉 所有 YouTube fetcher chain 测试通过")
