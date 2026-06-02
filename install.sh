#!/usr/bin/env bash
# content-catcher 一键安装脚本
# 用法： bash install.sh   或  ./install.sh
# 需要：Python 3.10+ 已装，git 已装

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "📡 content-catcher 安装向导"
echo "═══════════════════════════════════════════"
echo

# ── 1. 检查 Python ──
echo "🔍 [1/5] 检查 Python 版本..."
if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "❌ 没找到 python3。请先装 Python 3.10+：https://www.python.org/downloads/"
    exit 1
fi

PY_VER=$($PY -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_OK=$($PY -c 'import sys; print(1 if sys.version_info >= (3, 10) else 0)')
if [ "$PY_OK" != "1" ]; then
    echo "❌ Python $PY_VER 太老了，需要 3.10+"
    echo "   建议：brew install python@3.12   /   或装个 pyenv"
    exit 1
fi
echo "   ✅ Python $PY_VER ($($PY -c 'import sys; print(sys.executable)'))"
echo

# ── 2. 建 venv ──
VENV="$ROOT/.venv"
if [ -d "$VENV" ]; then
    echo "📦 [2/5] 已有 venv（.venv/），跳过创建"
else
    echo "📦 [2/5] 创建 venv：$VENV"
    $PY -m venv "$VENV"
fi
PYBIN="$VENV/bin/python"
PIPBIN="$VENV/bin/pip"
echo

# ── 3. 装依赖 ──
echo "⬇️  [3/5] 安装依赖（需要几分钟，faster-whisper 包比较大）..."
"$PIPBIN" install --upgrade pip setuptools wheel >/dev/null
"$PIPBIN" install -r requirements.txt
echo "   ✅ 依赖安装完成"
echo

# ── 4. 准备配置文件 ──
echo "⚙️  [4/5] 准备配置文件..."
if [ -f "$ROOT/channels.yaml" ]; then
    echo "   ⏭  channels.yaml 已存在，跳过"
else
    cp "$ROOT/channels.example.yaml" "$ROOT/channels.yaml"
    echo "   ✅ 已从 channels.example.yaml 复制出 channels.yaml"
    echo "       ⚠️  下一步：编辑 channels.yaml 把订阅源换成你自己的（如果想用订阅周报）"
fi
if [ -f "$ROOT/.smtp_secret" ]; then
    echo "   ⏭  .smtp_secret 已存在，跳过"
else
    cat > "$ROOT/.smtp_secret" <<'EOF'
# SMTP 授权码（不是邮箱密码）：
#   - QQ 邮箱：mail.qq.com → 设置 → 账户 → IMAP/SMTP → 申请
#   - Gmail：myaccount.google.com → 安全性 → 应用专用密码
SMTP_PASS=替换成你的SMTP授权码
EOF
    chmod 600 "$ROOT/.smtp_secret"
    echo "   ✅ 已创建 .smtp_secret 占位文件（chmod 600）"
    echo "       ⚠️  下一步：用你的 SMTP 授权码替换里面的占位（仅在你想用邮件功能时）"
fi
echo

# ── 5. 烟雾测试 ──
echo "🧪 [5/5] 烟雾测试..."
"$PYBIN" "$ROOT/catch.py" --help >/dev/null && echo "   ✅ catch.py 跑通"
"$PYBIN" "$ROOT/scripts/export_epub.py" >/dev/null && echo "   ✅ EPUB 导出跑通"
echo "   （如果想跑完整测试集：cd $ROOT && $PYBIN tests/test_export_epub.py）"
echo

# ── 总结 ──
echo "═══════════════════════════════════════════"
echo "🎉 安装完成！"
echo
echo "📌 常用命令（先 activate venv 或者直接用绝对路径）："
echo "   source $VENV/bin/activate"
echo
echo "   # 整理单条链接"
echo "   catch.py https://www.bilibili.com/video/BVxxx --cookies-from chrome"
echo
echo "   # 跑订阅周报"
echo "   catch.py --subscribe channels.yaml"
echo
echo "📚 完整文档： docs/MANUAL.md"
echo "📡 订阅管理： docs/SUBSCRIPTION_GUIDE.md"
echo
