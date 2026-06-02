# 📦 content-catcher 部署指南

> 适用于 **任何新电脑 / 任何 AI 助手**（WorkBuddy / Claude Code / Cursor / 自己跑）。

---

## 🎯 部署目标

按照本指南，30 分钟内你能在新电脑上跑通：

```bash
python catch.py "https://www.bilibili.com/video/BVxxxxx" --deep
# → 拿到一份完整的精装版 Markdown 文章
```

---

## 📋 部署清单（10 步）

| # | 步骤 | 估时 |
|---|------|------|
| 1 | 装 Homebrew（仅 macOS） | 5-15 分钟 |
| 2 | 装 Python 3.10+ | 1-3 分钟 |
| 3 | 装 ffmpeg | 1-3 分钟 |
| 4 | 解压 / 克隆项目 | 30 秒 |
| 5 | 创建 venv 虚拟环境 | 30 秒 |
| 6 | 装 Python 依赖 | 2-5 分钟 |
| 7 | 装 Whisper 模型（手动下载） | 3-5 分钟 |
| 8 | 配置 Chrome cookies（B 站用） | 2 分钟 |
| 9 | 配置 SMTP（发邮件用） | 5 分钟 |
| 10 | 跑 doctor.py 验证 | 30 秒 |

**总耗时：约 25-45 分钟**（首次）。

---

## 🖥️ 系统兼容性

| 系统 | 兼容性 | 说明 |
|------|--------|------|
| **macOS Intel** | ✅ 已验证（开发机） | 推荐 |
| **macOS Apple Silicon (M1/M2/M3)** | ✅ 兼容 | 注意 brew 路径变成 `/opt/homebrew` |
| **Linux (Ubuntu/Debian)** | ✅ 兼容 | 把 brew 换成 apt-get |
| **Windows** | ⚠️ 部分兼容 | 建议用 WSL2 |

---

## 🍎 macOS 详细部署步骤

### Step 1：装 Homebrew

终端跑：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

中途会要求输入登录密码（屏幕不显示是正常的，按回车确认）。

装完后**按提示设置 PATH**（重要，否则 brew 命令找不到）：

**Intel Mac**：
```bash
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/usr/local/bin/brew shellenv)"
```

**Apple Silicon Mac**：
```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

验证：
```bash
brew --version  # 看到版本号即 OK
```

---

### Step 2：装 Python 3.10+

```bash
brew install python@3.12
```

验证：
```bash
# Intel Mac
/usr/local/bin/python3.12 --version

# Apple Silicon
/opt/homebrew/bin/python3.12 --version
```

应输出 `Python 3.12.x`。

⚠️ **不要用系统自带的 `/usr/bin/python3`**（macOS 自带版本是 3.9，本项目要 3.10+ 才支持 `str | None` 语法）。

---

### Step 3：装 ffmpeg

```bash
brew install ffmpeg
```

验证：
```bash
ffmpeg -version | head -1
```

---

### Step 4：解压项目

如果你用 zip 包：
```bash
cd ~/Downloads
unzip content-catcher-v0.7-*.zip -d ~/content-catcher
cd ~/content-catcher
```

如果你用 Git：
```bash
cd ~
git clone https://github.com/zczxd1118/content-catcher.git
cd content-catcher
```

---

### Step 5：创建 Python 虚拟环境

**强烈建议**用单独的 venv，避免污染系统 Python：

**Intel Mac**：
```bash
/usr/local/bin/python3.12 -m venv ~/content-catcher-venv
```

**Apple Silicon Mac**：
```bash
/opt/homebrew/bin/python3.12 -m venv ~/content-catcher-venv
```

之后所有命令都用这个 venv 里的 python：
```bash
~/content-catcher-venv/bin/python --version
# → Python 3.12.x
```

---

### Step 6：装 Python 依赖

一行命令装齐：

```bash
~/content-catcher-venv/bin/pip install \
  yt-dlp \
  youtube-transcript-api \
  langdetect \
  charset-normalizer \
  chardet \
  PyYAML \
  ebooklib \
  lxml \
  faster-whisper \
  markdown
```

⏰ **耐心等 2-5 分钟**（部分包要编译，比如 lxml）。

如果遇到 `pip install` 慢/超时，用国内镜像：
```bash
~/content-catcher-venv/bin/pip install \
  -i https://pypi.tuna.tsinghua.edu.cn/simple \
  yt-dlp youtube-transcript-api langdetect charset-normalizer chardet \
  PyYAML ebooklib lxml faster-whisper markdown
```

---

### Step 7：装 Whisper 模型（关键 ⚠️）

⚠️ **国内网络访问 HuggingFace 会超时**。**手动下载模型**到本地是最稳的方式：

#### 7.1 创建模型目录
```bash
cd ~/content-catcher
mkdir -p models/models--Systran--faster-whisper-tiny/snapshots/main
cd models/models--Systran--faster-whisper-tiny/snapshots/main
```

#### 7.2 用 curl 从国内镜像下载 6 个文件
```bash
BASE=https://hf-mirror.com/Systran/faster-whisper-tiny/resolve/main
for f in config.json model.bin tokenizer.json vocabulary.txt preprocessor_config.json README.md; do
  echo "下载 $f..."
  curl -sL "$BASE/$f" -o "$f"
done
ls -lh
# 应该看到 6 个文件，model.bin 约 72MB
```

#### 7.3（可选）想要更高准确率，下 `small` 模型（480MB）
重复 7.1-7.2，路径换成 `models/models--Systran--faster-whisper-small/snapshots/main`，URL 里 `tiny` 换成 `small`。

---

### Step 8：配置 Chrome cookies（抓 B 站用）

如果你要用本工具抓 **B 站** / **YouTube** 等需要登录的平台：

1. 在系统中装 **Chrome 浏览器**（如果还没装）
2. 用 Chrome 登录目标平台一次（B 站、YouTube 等）
3. 不需要导出 cookies —— 工具会自动从 Chrome 的本地 cookies 数据库读取

⚠️ macOS 12+ **不能读 Safari 的 cookies**（被隐私保护拦了）。**必须用 Chrome**（或 Firefox）。

---

### Step 9：配置 SMTP（发邮件用）

#### 9.1 拿邮箱授权码（**不是登录密码**）

**QQ 邮箱**：
1. 打开 https://mail.qq.com → 设置 → 账号
2. 找 "POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV 服务"
3. 开启 **IMAP/SMTP 服务**
4. 用手机发短信验证 → 拿到 **16 位授权码**

**Gmail**：
1. 开启账号"两步验证"
2. 创建 App Password
3. 用生成的 16 位密码

**网易 163**：流程类似 QQ。

#### 9.2 把授权码存到 `.smtp_secret` 文件
```bash
cd ~/content-catcher
echo "SMTP_PASS=你的16位授权码" > .smtp_secret
```

⚠️ 这个文件**已加进 `.gitignore`**，不会被提交到 GitHub。

#### 9.3 修改 `channels.yaml`（如果用订阅功能）
```bash
cp channels.example.yaml channels.yaml
# 用文本编辑器打开 channels.yaml，把 email_to / email_from / smtp.user 改成你的邮箱
```

---

### Step 10：跑 doctor.py 验证

```bash
cd ~/content-catcher
~/content-catcher-venv/bin/python scripts/doctor.py
```

理想输出：

```
🩺 content-catcher 环境体检

📦 Python 包：
  ✅ yt-dlp
  ✅ youtube-transcript-api
  ✅ langdetect
  ✅ charset-normalizer
  ✅ PyYAML（订阅配置）
  ✅ faster-whisper（可选，转写兜底）
  ✅ ebooklib（可选，EPUB 导出）
  ✅ markdown（可选，邮件 HTML 美化）

🔧 系统工具：
  ✅ ffmpeg

🔑 LLM API（自动模式可选）：
  ❌ ANTHROPIC_API_KEY
  ❌ OPENAI_API_KEY

📧 SMTP 邮件（订阅模式 --send-email 需要）：
  ⚠️ SMTP_PASS（如果你存到 .smtp_secret 文件里就不用 export）

✨ 体检完成。
```

⚠️ ANTHROPIC/OPENAI key 是**可选**，不配也能用（默认模式）。

---

### 第一次跑 demo（验证）

```bash
# 用一个有 RSS 的英文 AI 播客（最稳）
~/content-catcher-venv/bin/python catch.py \
  "https://www.latent.space/p/daytona" \
  --deep

# 看产物
ls -lh output/bundles/
```

如果看到 `*.prompt.md` 文件 = ✅ 部署成功。

---

## 🐧 Linux 部署步骤（Ubuntu/Debian）

跟 macOS 几乎一样，**仅 Step 1-3 不同**：

```bash
# Step 1-3：装系统依赖
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3-pip ffmpeg

# Step 4 起：跟 macOS 完全相同
```

---

## 🪟 Windows 部署步骤

**强烈推荐用 WSL2**（Windows Subsystem for Linux），把 Windows 当成 Linux 跑：

1. 在 PowerShell（管理员）跑 `wsl --install`
2. 重启 → 装好 Ubuntu
3. 进 WSL → 按 Linux 部署步骤跑

如果不想用 WSL2，也可以直接在 Windows 跑，但要：
- 装 Python 3.12（python.org 下载）
- 装 ffmpeg（chocolatey: `choco install ffmpeg`）
- 路径全部改成 Windows 风格（`/` → `\`）

---

## 🤖 让 AI 助手帮你部署

如果你用 **WorkBuddy / Claude Code / Cursor**，**直接把这份文档发给 AI**，说：

```
请帮我按 DEPLOYMENT.md 一步步部署 content-catcher 到我电脑上。
我的系统是 [macOS Intel / macOS M1 / Linux / Windows]。
```

AI 会**逐步执行命令**，遇到报错会自动 debug。

---

## 🆘 常见问题速查

| 现象 | 原因 | 解决 |
|------|------|------|
| `command not found: python3.12` | Python 没装 | 重做 Step 2 |
| `command not found: brew` | PATH 没设 | 重做 Step 1 末尾的 echo + eval |
| `pip install` 卡住 | 网络问题 | 用 `-i https://pypi.tuna.tsinghua.edu.cn/simple` |
| `code signature` 错误 | venv 来自不同 Python | 删掉 venv 重建 |
| Whisper 加载模型失败 | HuggingFace 访问失败 | 按 Step 7 手动下载 |
| B 站抓不到字幕 | Chrome 没登录 | 用 Chrome 登录 B 站后重试 |
| `email send fail (535)` | 用了登录密码不是授权码 | 重新拿 SMTP 授权码 |
| YouTube "Sign in to confirm" | 国内 IP 反爬 | 改用 Apple Podcasts / RSS / B 站 |

---

## 🔄 跨电脑迁移

要换电脑用？带这 3 个东西：

1. **整个项目目录**（zip 或 git clone）
2. **`.smtp_secret`**（不要丢公网，私下传）
3. **`channels.yaml`**（你的订阅清单）

新电脑按 Step 1-7 部署 → 把这 3 个东西放回去 → 立刻能跑。

**Whisper 模型**可以选择性带（72MB，带过去省下载时间）。

---

## 📞 部署遇到问题

1. 先跑 `doctor.py` 看是哪步红叉
2. 看本文档"常见问题速查"
3. 把**完整终端报错**复制给 AI（WorkBuddy / Claude / GPT）问

---

## ✅ 部署完成检查清单

- [ ] `brew --version` 有输出
- [ ] `python3.12 --version` 显示 3.12.x
- [ ] `ffmpeg -version` 有输出
- [ ] `~/content-catcher-venv/bin/python scripts/doctor.py` 全绿
- [ ] `~/content-catcher-venv/bin/python catch.py "URL" --deep` 能跑通
- [ ] `output/bundles/` 里有 `.prompt.md` 文件

**全部打勾 = 部署完美** ✅
