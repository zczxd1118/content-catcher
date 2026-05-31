"""
订阅管理小工具

用法：
  # 列出所有订阅
  python scripts/manage_channels.py list

  # 加 B 站 up 主（自动处理）
  python scripts/manage_channels.py add-bili 25752587 "大牙大-"

  # 加 YouTube 频道
  python scripts/manage_channels.py add-youtube UCJIfeSCssxSC_Dhc5s7woww "Lex Fridman"

  # 加小宇宙 / 苹果播客（提供 RSS）
  python scripts/manage_channels.py add-rss "https://www.xiaoyuzhoufm.com/podcast/xxx/feed.xml" "张小珺"

  # 关闭某个频道
  python scripts/manage_channels.py disable "大牙大-"

  # 启用某个频道
  python scripts/manage_channels.py enable "大牙大-"

  # 删除某个频道
  python scripts/manage_channels.py remove "大牙大-"
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = ROOT / "channels.yaml"


def load_yaml():
    import yaml
    return yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))


def save_yaml(data):
    import yaml
    YAML_PATH.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False, indent=2),
        encoding="utf-8",
    )


def cmd_list():
    data = load_yaml()
    chs = data.get("channels", [])
    print(f"\n📡 当前订阅列表（共 {len(chs)} 个）\n")
    for i, ch in enumerate(chs, 1):
        status = "✅" if ch.get("enabled") else "⏸️ "
        type_short = ch["type"].replace("_uploader", "").replace("_channel", "")
        ident = ch.get("mid") or ch.get("channel_id") or ch.get("rss_url", "")[:50]
        print(f"  {status} [{i}] [{type_short:10}] {ch.get('name','?'):20} -> {ident}")
    print()


def cmd_add_bili(mid, name):
    data = load_yaml()
    data.setdefault("channels", []).append({
        "type": "bilibili_uploader",
        "name": name,
        "mid": str(mid),
        "cookies_from": "chrome",
        "enabled": True,
    })
    save_yaml(data)
    print(f"✅ 已添加 B 站 up 主：{name} (mid={mid})")


def cmd_add_youtube(cid, name):
    data = load_yaml()
    data.setdefault("channels", []).append({
        "type": "youtube_channel",
        "name": name,
        "channel_id": cid,
        "enabled": True,
    })
    save_yaml(data)
    print(f"✅ 已添加 YouTube 频道：{name} (cid={cid})")


def cmd_add_rss(rss, name):
    data = load_yaml()
    data.setdefault("channels", []).append({
        "type": "rss",
        "name": name,
        "rss_url": rss,
        "enabled": True,
    })
    save_yaml(data)
    print(f"✅ 已添加 RSS：{name}")


def cmd_toggle(name, enabled):
    data = load_yaml()
    found = False
    for ch in data.get("channels", []):
        if ch.get("name") == name:
            ch["enabled"] = enabled
            found = True
            break
    if found:
        save_yaml(data)
        action = "启用" if enabled else "关闭"
        print(f"✅ 已{action}：{name}")
    else:
        print(f"❌ 找不到：{name}")
        sys.exit(1)


def cmd_remove(name):
    data = load_yaml()
    chs = data.get("channels", [])
    new_chs = [c for c in chs if c.get("name") != name]
    if len(new_chs) == len(chs):
        print(f"❌ 找不到：{name}")
        sys.exit(1)
    data["channels"] = new_chs
    save_yaml(data)
    print(f"✅ 已删除：{name}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "list":
        cmd_list()
    elif cmd == "add-bili" and len(args) >= 2:
        cmd_add_bili(args[0], args[1])
    elif cmd == "add-youtube" and len(args) >= 2:
        cmd_add_youtube(args[0], args[1])
    elif cmd == "add-rss" and len(args) >= 2:
        cmd_add_rss(args[0], args[1])
    elif cmd == "disable" and args:
        cmd_toggle(args[0], False)
    elif cmd == "enable" and args:
        cmd_toggle(args[0], True)
    elif cmd == "remove" and args:
        cmd_remove(args[0])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
