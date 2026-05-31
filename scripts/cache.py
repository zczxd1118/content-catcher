"""
简单的链接级缓存：抓过的链接结果存 JSON，下次跳过抓取。
按 URL 的 hash 命名，存入 output/cache/。
"""
import hashlib
import json
from pathlib import Path
from datetime import datetime


CACHE_DIR_NAME = "cache"


def cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def cache_path(root: Path, url: str) -> Path:
    cache_dir = root / "output" / CACHE_DIR_NAME
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{cache_key(url)}.json"


def load(root: Path, url: str) -> dict | None:
    p = cache_path(root, url)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def save(root: Path, url: str, payload: dict) -> Path:
    payload = {**payload, "_cached_at": datetime.now().isoformat()}
    p = cache_path(root, url)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def clear(root: Path, url: str | None = None):
    cache_dir = root / "output" / CACHE_DIR_NAME
    if not cache_dir.exists():
        return
    if url:
        p = cache_path(root, url)
        if p.exists():
            p.unlink()
    else:
        for f in cache_dir.glob("*.json"):
            f.unlink()
