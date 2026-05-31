"""周报历史记忆：记录已发过的内容，避免重复推送。"""
import json
from pathlib import Path
from datetime import datetime


def history_path(root: Path) -> Path:
    p = root / "output" / "digest" / "history.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load(root: Path) -> dict:
    p = history_path(root)
    if not p.exists():
        return {"sent_urls": {}, "digests": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"sent_urls": {}, "digests": []}


def mark_sent(root: Path, urls: list[str], digest_name: str):
    h = load(root)
    now = datetime.now().isoformat()
    for u in urls:
        h["sent_urls"][u] = {"sent_at": now, "digest": digest_name}
    h["digests"].append({
        "name": digest_name,
        "sent_at": now,
        "url_count": len(urls),
    })
    history_path(root).write_text(
        json.dumps(h, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def filter_new(root: Path, items: list[dict]) -> list[dict]:
    """剔除已经发过的 url。"""
    h = load(root)
    sent = h.get("sent_urls", {})
    return [it for it in items if it["url"] not in sent]
