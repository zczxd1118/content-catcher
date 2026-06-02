"""SMTP 邮件发送（支持 HTML 正文 + 附件）。"""
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.policy import SMTP as SMTP_POLICY
from pathlib import Path


def markdown_to_html(md_text: str) -> str:
    """极简 Markdown → HTML（不依赖 markdown 库）。"""
    try:
        import markdown as md_lib
        return md_lib.markdown(md_text, extensions=["tables", "fenced_code"])
    except ImportError:
        # 退而求其次：用 <pre> 包起来
        from html import escape
        return f"<pre style='font-family:ui-monospace,Menlo,monospace;white-space:pre-wrap'>{escape(md_text)}</pre>"


def send_email(smtp_cfg: dict,
               from_addr: str, to_addr: str,
               subject: str,
               md_body: str,
               attachments: list[Path] | None = None,
               password_env: str = "SMTP_PASS") -> tuple[bool, str]:
    """
    返回 (是否成功, 状态信息)。
    smtp_cfg: {host, port, use_ssl, user}
    """
    password = os.getenv(password_env)

    # Fallback 1：从项目根目录的 .smtp_secret 文件读取
    if not password:
        from pathlib import Path
        secret_file = Path(__file__).resolve().parent.parent / ".smtp_secret"
        if secret_file.exists():
            for line in secret_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith(f"{password_env}=") and not line.startswith("#"):
                    password = line.split("=", 1)[1].strip().strip("'\"")
                    break

    if not password:
        return False, f"未设置 {password_env}（既没在环境变量、也没在 .smtp_secret 文件里）"

    # 显式使用 email.policy.SMTP（默认 compat32 是 ASCII-only，
    # 中文 Subject / From 显示名 / 附件名会触发 'ascii' codec can't encode）。
    # SMTP policy 会自动按 RFC 2047 编码 header，并按 RFC 6532 处理 UTF-8 正文。
    msg = EmailMessage(policy=SMTP_POLICY)
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject

    msg.set_content(md_body, charset="utf-8")
    html = markdown_to_html(md_body)
    msg.add_alternative(
        f"<html><body style='font-family:-apple-system,BlinkMacSystemFont,sans-serif;"
        f"max-width:680px;margin:0 auto;padding:16px;line-height:1.7'>"
        f"{html}</body></html>", subtype="html", charset="utf-8"
    )

    if attachments:
        for p in attachments:
            if not p.exists():
                continue
            data = p.read_bytes()
            mime_main, mime_sub = guess_mime(p)
            msg.add_attachment(data, maintype=mime_main, subtype=mime_sub, filename=p.name)

    try:
        if smtp_cfg.get("use_ssl"):
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_cfg["host"], smtp_cfg.get("port", 465), context=ctx, timeout=30) as s:
                s.login(smtp_cfg["user"], password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(smtp_cfg["host"], smtp_cfg.get("port", 587), timeout=30) as s:
                s.starttls()
                s.login(smtp_cfg["user"], password)
                s.send_message(msg)
        return True, "ok"
    except Exception as e:
        return False, f"SMTP 失败：{e}"


def guess_mime(p: Path) -> tuple[str, str]:
    ext = p.suffix.lower()
    if ext == ".epub":
        return ("application", "epub+zip")
    if ext == ".pdf":
        return ("application", "pdf")
    if ext == ".md" or ext == ".txt":
        return ("text", "plain")
    if ext == ".html":
        return ("text", "html")
    return ("application", "octet-stream")
