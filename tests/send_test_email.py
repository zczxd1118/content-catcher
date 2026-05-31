"""
一次性测试：把已写好的周报 Markdown 发到 170665060@qq.com

运行前：
  export SMTP_PASS='你的QQ邮箱16位授权码'
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from email_sender import send_email

MD_FILE = ROOT / "output/digest/weekly-2026-W22-20260528/周小丁的-AI-Vibe-Coding-周报-2026W22.md"

if not MD_FILE.exists():
    print(f"❌ 找不到周报文件：{MD_FILE}")
    sys.exit(1)

if not os.getenv("SMTP_PASS"):
    # 看看 .smtp_secret 文件有没有
    secret_file = ROOT / ".smtp_secret"
    if not secret_file.exists():
        print("❌ SMTP_PASS 未设置。在终端先跑：export SMTP_PASS='你的授权码'")
        print("   或创建 .smtp_secret 文件（参考 .smtp_secret.template）")
        sys.exit(1)
    # 文件存在，email_sender 会自己读，跳过这里的检查
    print("📁 用 .smtp_secret 文件里的密码")

md_content = MD_FILE.read_text(encoding="utf-8")

print(f"📧 准备发送...")
print(f"   收件人：170665060@qq.com")
print(f"   主题：📬 周小丁的 AI + Vibe Coding 周报 - 2026W22（v2 完整内容版）")
print(f"   正文长度：{len(md_content)} 字符")
print()

ok, msg = send_email(
    smtp_cfg={
        "host": "smtp.qq.com",
        "port": 465,
        "use_ssl": True,
        "user": "170665060@qq.com",
    },
    from_addr="170665060@qq.com",
    to_addr="170665060@qq.com",
    subject="📬 周小丁的 AI + Vibe Coding 周报 - 2026W22（v2 完整内容版）",
    md_body=md_content,
    attachments=None,
)

if ok:
    print("✅ 邮件发送成功！去 QQ 邮箱收件箱看（如果没有，翻一下垃圾邮件）")
else:
    print(f"❌ 发送失败：{msg}")
    sys.exit(2)
