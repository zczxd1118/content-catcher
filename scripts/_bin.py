"""统一定位 yt-dlp / ffmpeg 等外部二进制的工具函数。

为什么需要：
- 之前各 script 里硬编码了一份开发机绝对路径，别人 clone 跑不了
- 现在按"和当前 Python 同 venv → PATH → 报错"的顺序查
"""
import os
import shutil
import sys
from pathlib import Path


def find_bin(name: str) -> str | None:
    """按下面的顺序找一个二进制：

    1. 跟当前 Python 同 venv（最稳——pip install 的 console_scripts 会落在这）
       eg. /path/to/venv/bin/yt-dlp
    2. 系统 PATH（shutil.which）
    3. 返回 None（调用方负责报友好错）
    """
    # 1) 同 venv
    venv_bin = Path(sys.executable).parent / name
    if venv_bin.is_file() and os.access(venv_bin, os.X_OK):
        return str(venv_bin)
    # Windows 后缀
    if sys.platform == "win32":
        venv_exe = venv_bin.with_suffix(".exe")
        if venv_exe.is_file():
            return str(venv_exe)

    # 2) PATH
    found = shutil.which(name)
    if found:
        return found

    return None


def require_bin(name: str, install_hint: str = "") -> str:
    """找不到就抛 RuntimeError，带友好的安装提示。"""
    path = find_bin(name)
    if path:
        return path
    msg = f"找不到 {name}。"
    if install_hint:
        msg += f" 请先安装：{install_hint}"
    raise RuntimeError(msg)


# 常用：导入即用的 YTDLP_BIN
YTDLP_BIN = find_bin("yt-dlp")  # None 表示没装；运行时具体功能再 raise
