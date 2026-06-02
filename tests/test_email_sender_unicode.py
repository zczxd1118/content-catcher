"""验证 email_sender 在中文 Subject / 中文正文 / Emoji 下不会触发
'ascii' codec can't encode characters 错误。

这是 v0.7.1 hotfix 的回归测试。

跑法（在仓库根目录）：
    python tests/test_email_sender_unicode.py

期望：
    返回值: False，且错误信息是 'Connection refused' / SMTP 协议错误，
    而不是 'ascii' codec ... 这种字符集错误。
"""
import sys
from pathlib import Path

# 让脚本在仓库任意位置都能跑
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from email_sender import send_email  # noqa: E402


def test_chinese_subject_and_body():
    # 故意指向不可达端口，让它真正构造完 EmailMessage 再 SMTP 失败
    ok, info = send_email(
        smtp_cfg={
            "host": "127.0.0.1",
            "port": 1,
            "use_ssl": False,
            "user": "fake@example.com",
        },
        from_addr="fake@example.com",
        to_addr="test@example.com",
        subject="测试中文标题：周小丁的 AI 周报 W23 🚀",
        md_body=(
            "# 中文正文\n\n"
            "这是一个**中文测试**，包含 emoji 🚀 和破折号 — 中文逗号，全部要 UTF-8 编码。\n\n"
            "## 列表测试\n"
            "- 大牙大-（B 站）\n"
            "- 张小珺商业访谈录（小宇宙）\n"
        ),
        # 用一个一定不存在的 env，强制走 .smtp_secret fallback
        # 跑测试的人需要项目根目录有 .smtp_secret 才能拿到密码
        password_env="SMTP_PASS",
    )
    print(f"返回: ok={ok}, info={info!r}")

    assert ok is False, "网络不可达时应该返回失败"
    err = info.lower()
    assert "ascii" not in err, (
        f"❌ 仍出现 ASCII 编码错误，hotfix 失败：{info}"
    )
    assert "codec" not in err, (
        f"❌ 仍出现编码 codec 错误，hotfix 失败：{info}"
    )
    print("✅ 中文 / Emoji 不再触发 ASCII 编码错误，仅卡在 SMTP 网络层。")


if __name__ == "__main__":
    test_chinese_subject_and_body()
