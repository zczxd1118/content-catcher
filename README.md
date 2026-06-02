# 📡 content-catcher

> **Personal Information Distillery + Newsletter Engine**
>
> 一个"信息蒸馏 + Newsletter"基础设施 —— 把任何长内容（音视频 / 图文 / 播客）
> 变成"被精选过"的笔记。既能单条按需调用（Skill 形态），
> 也能订阅式自动推送到邮箱（Newsletter 形态）。

[![GitHub release](https://img.shields.io/github/v/release/zczxd1118/content-catcher)](https://github.com/zczxd1118/content-catcher/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## ⚡ 5 分钟跑起来

```bash
git clone https://github.com/zczxd1118/content-catcher.git
cd content-catcher
./install.sh                                       # 一键建 venv + 装依赖 + 准备配置
source .venv/bin/activate

# 单条整理
catch.py https://www.bilibili.com/video/BV1xxxxxx --cookies-from chrome

# 跑订阅周报
cp channels.example.yaml channels.yaml             # 改成你自己的订阅源
catch.py --subscribe channels.yaml
```

📖 **完整文档**：[`docs/MANUAL.md`](./docs/MANUAL.md) · 📡 订阅源管理：[`docs/SUBSCRIPTION_GUIDE.md`](./docs/SUBSCRIPTION_GUIDE.md) · 📝 变更记录：[`CHANGELOG.md`](./CHANGELOG.md)

---

## 🎯 它不只是一个 Skill

很多人第一眼会以为这是"链接转笔记的小工具"，但实际上它是个**4 层架构**的内容基础设施：

```
                    👁️ 用户感知层
                         │
┌────────────────────────┼────────────────────────┐
│ Layer 4: Newsletter 系统（产品形态）              │
│   订阅源 → 抓取 → 蒸馏 → 邮件推送 → EPUB 附件      │
│   类比：Refind / Substack / Snipd                │
└────────────────────────┬────────────────────────┘
                         │ 由这一层支撑
┌────────────────────────┼────────────────────────┐
│ Layer 3: 内容处理工具（CLI / Skill 形态）         │
│   一行命令 / @skill → 拿到笔记                   │
│   类比：yt-dlp / faster-whisper / 单一 AI Skill  │
└────────────────────────┬────────────────────────┘
                         │ 由这一层支撑
┌────────────────────────┼────────────────────────┐
│ Layer 2: Prompt 工程库（核心壁垒）⭐             │
│   8 个精心打磨的模板：中文/英文/小红书/精装/批量/对比 │
│   这才是真正的"产品 know-how"                    │
└────────────────────────┬────────────────────────┘
                         │ 由这一层支撑
┌────────────────────────┴────────────────────────┐
│ Layer 1: 技术管线（基础设施）                     │
│   字幕抓取 + Whisper 转写 + RSS 探测 +            │
│   Cookies 注入 + 长内容分段 + 缓存 + 失败容错      │
└─────────────────────────────────────────────────┘
```

**所以**：
- 当你 `python catch.py URL` —— 你在用 **Layer 3（工具）**
- 当你 `@content-catcher` 调它 —— 你在用 **Layer 3（Skill）**
- 当你 `--subscribe + --send-email` —— 你在用 **Layer 4（Newsletter）**
- 当你看到产物质量惊艳 —— 那是 **Layer 2 的功劳**

---

## 🆚 跟同类产品的差异

| 同类产品 | 它的定位 | content-catcher 的差异 |
|---------|---------|---------------------|
| **Snipd / Podwise** | 播客转笔记 SaaS | 多平台 + 多形态 + 用户掌控成本 |
| **Refind** | AI 推荐 Newsletter | 用户掌控订阅源 + 中文圈友好 |
| **yt-dlp** | 纯下载工具 | 之上加 AI 蒸馏层 + Newsletter 形态 |
| **单一 AI Skill** | 一个 Prompt 包 | 8 模板 + 完整管线 + 订阅闭环 |

---

## ✨ 五大场景

| 场景 | 命令 | 产物 |
|------|------|------|
| 🎬 单条转笔记 | `python catch.py URL` | 结构化中文/双语笔记 |
| 📚 单条精装版 | `python catch.py URL --deep` | 1500-15000 字叙事长文 |
| 📜 单条完整版 | `python catch.py URL --full` | 逐字稿+导读+章节索引 |
| 🗂️ 批量+合集/对比 | `python catch.py --batch urls.txt --mode topic/compare` | 专题书/跨平台对比报告 |
| 📬 订阅周报 | `python catch.py --subscribe channels.yaml --send-email` | 邮件周报+EPUB 附件 |

---

## 🚀 快速开始

### 1. 克隆 & 装环境

```bash
git clone https://github.com/zczxd1118/content-catcher.git
cd content-catcher

# 用本机 Python 3.10+ 建 venv（macOS 用 brew install python@3.12）
/usr/local/bin/python3.12 -m venv ~/.workbuddy/binaries/python/envs/content-catcher

# 装依赖
~/.workbuddy/binaries/python/envs/content-catcher/bin/pip install \
  yt-dlp youtube-transcript-api langdetect charset-normalizer chardet \
  PyYAML ebooklib lxml faster-whisper markdown
```

### 2. 装 ffmpeg（Whisper 转写依赖）

```bash
brew install ffmpeg
```

### 3. 验证环境

```bash
~/.workbuddy/binaries/python/envs/content-catcher/bin/python scripts/doctor.py
```

### 4. 跑第一个 demo

```bash
# 小红书图文（最快，5 秒）
python catch.py "https://www.xiaohongshu.com/explore/xxxxx"

# B 站视频（要 Chrome 登录 B 站）
python catch.py "https://www.bilibili.com/video/BVxxxxx" --cookies-from chrome

# 英文 AI 播客（自动从 RSS 抓 show notes）
python catch.py "https://www.latent.space/p/daytona" --deep
```

---

## 🎯 三种 AI 调用模式

| 模式 | 命令 | 谁出 AI 算力 | 适合 |
|------|------|------------|------|
| **🥇 投喂包**（默认） | `python catch.py URL` | 复制投喂包丢给 AI（WorkBuddy/Claude/GPT）| 所有人 |
| **🥈 全自动** | `python catch.py URL --auto` | 你的 API key（DeepSeek/Claude/GPT）| 重度用户 |
| **🥉 仅原文** | `python catch.py URL --raw` | 不调 AI | 归档需求 |

---

## 📡 订阅周报

### 1️⃣ 初次配置

```bash
# A. 复制订阅模板
cp channels.example.yaml channels.yaml
# B. 编辑 email_to / email_from / smtp.user 改成你的邮箱
# C. 配 SMTP 授权码（持久化，不用每次 export）
echo "SMTP_PASS=你的QQ邮箱授权码" > .smtp_secret  # 已加进 .gitignore
```

### 2️⃣ 跑订阅

```bash
# 仅生成投喂包（不发邮件，调试时用）
python catch.py --subscribe channels.yaml

# 全自动 + 发邮件（每周一次）
python catch.py --subscribe channels.yaml --auto --send-email
```

### 3️⃣ 修改订阅清单（重点 ⭐）

**两种方法,任选其一:**

#### 方法 A：用 `manage_channels.py` 工具（推荐，无需手编 YAML）

```bash
# 看现在订了什么
python scripts/manage_channels.py list

# 加 B 站 up 主（mid 在 space.bilibili.com/XXXXXXX 的 URL 里）
python scripts/manage_channels.py add-bili 25752587 "大牙大-"

# 加 YouTube 频道（channel_id 是 UC 开头那一串）
python scripts/manage_channels.py add-youtube UCJIfeSCssxSC_Dhc5s7woww "Lex Fridman"

# 加 RSS 播客（小宇宙 / 苹果播客 / Substack）
python scripts/manage_channels.py add-rss "https://www.xiaoyuzhoufm.com/podcast/xxx/feed.xml" "张小珺"

# 临时关闭某个频道（不删除）
python scripts/manage_channels.py disable "Lex Fridman"

# 重新启用
python scripts/manage_channels.py enable "Lex Fridman"

# 彻底删除
python scripts/manage_channels.py remove "Lex Fridman"
```

#### 方法 B：直接编辑 `channels.yaml`

```yaml
channels:
  - type: bilibili_uploader
    name: "大牙大-"
    mid: "25752587"
    cookies_from: chrome
    enabled: true       # ← 改成 false 即可临时关闭

  - type: youtube_channel
    name: "Lex Fridman"
    channel_id: "UCJIfeSCssxSC_Dhc5s7woww"
    enabled: true

  - type: rss
    name: "张小珺商业访谈录"
    rss_url: "https://feed.xyz/zhangxiaojun"
    enabled: true
```

### 4️⃣ 各平台 ID 怎么找

| 平台 | ID 在哪里 | 例子 |
|------|---------|------|
| **B 站 up 主** | `space.bilibili.com/XXXXXXX` URL 里的数字 | `25752587` |
| **YouTube 频道** | 频道主页源码里搜 `"channelId":"UC..."` | `UCJIfeSCssxSC_Dhc5s7woww` |
| **小宇宙节目** | 节目页源码搜 `feed.xml` | `https://www.xiaoyuzhoufm.com/podcast/xxx/feed.xml` |
| **Substack 播客** | `<站名>.substack.com/feed` | 自动探测，也可手动 |
| **苹果播客** | 用 castro.fm/itunes 转换 | RSS URL |

### 5️⃣ 修改订阅后立即生效

修改完 `channels.yaml` 后**下次跑 `--subscribe` 自动用新清单**，不需要重启什么。

📌 提示：`output/digest/history.json` 存"已发过的视频"，**改订阅清单不会重置历史** —— 避免你换 up 主后老视频又重发。

---

## 🛠️ 技术栈

- **Python 3.10+**
- **yt-dlp**：万能下载器
- **faster-whisper**：本地语音转写（Mac 友好，CPU + int8）
- **ebooklib**：EPUB 导出
- **PyYAML**：订阅配置
- **smtplib**：邮件推送（QQ/Gmail/网易等通用 SMTP）

---

## 🗺️ 路线图

- [x] M0–M4：单条 / 批量 / 跨平台 / 长内容分段
- [x] **M5：订阅 + 周报 + 邮件 + EPUB**
- [x] **M6：播客主站 RSS 整合**（latent.space / acquired.fm / lexfridman.com / substack）
- [ ] M7：launchd / cron 定时任务模板
- [ ] M8：并行处理（多链接同时跑）
- [ ] M9：升级为 Agent（基于此项目的 [content-curator](https://github.com/zczxd1118/content-curator) ）

---

## 📂 目录结构

```
content-catcher/
├── catch.py                  # 主入口（CLI）
├── SKILL.md                  # WorkBuddy Skill 描述
├── channels.example.yaml     # 订阅配置模板
├── scripts/
│   ├── detect_platform.py    # 平台识别
│   ├── get_metadata.py       # 抓元信息
│   ├── fetch_subtitle.py     # 字幕抓取
│   ├── fetch_xiaohongshu.py  # 小红书图文
│   ├── fetch_podcast_rss.py  # 播客 RSS
│   ├── transcribe.py         # Whisper 转写
│   ├── chunker.py            # 长内容分段
│   ├── build_prompt.py       # 投喂包生成
│   ├── run_llm.py            # LLM 自动模式
│   ├── batch.py              # 批量调度
│   ├── subscribe.py          # 订阅扫描
│   ├── digest.py             # 周报生成
│   ├── digest_history.py     # 增量记忆
│   ├── email_sender.py       # SMTP 推送
│   ├── export_epub.py        # EPUB 导出
│   ├── manage_channels.py    # 订阅管理
│   ├── save_output.py        # 落盘
│   ├── detect_language.py    # 语言识别
│   ├── doctor.py             # 环境体检
│   └── cache.py              # 链接缓存
├── templates/                # Prompt 模板（5 种产物形态）
│   ├── chinese_notes.md
│   ├── english_bilingual.md
│   ├── xiaohongshu_note.md
│   ├── deep_book.md          # 精装电子书风格
│   ├── full_transcript.md    # 逐字稿+导读
│   ├── topic_collection.md   # 专题合集
│   ├── cross_platform_compare.md  # 跨平台对比
│   └── weekly_digest.md      # Newsletter 周报
└── tests/                    # 自检脚本
```

---

## 💡 使用建议

- **隐私**：本工具不上传任何内容到外部服务器，转写完全本地（faster-whisper）
- **成本**：默认模式零 API 费（投喂包丢给你已有的 AI），自动模式按 API 计费（DeepSeek 极便宜）
- **国内网络**：HuggingFace 模型走 hf-mirror.com 镜像（已自动处理）
- **B 站抓取**：需要 Chrome 登录 B 站，工具读 cookies 自动注入

---

## ⚠️ 已知限制

- YouTube 在国内 IP 可能反爬（建议改用 Apple Podcasts / B 站）
- 小红书需公开笔记（私密笔记暂不支持）
- 长视频 Whisper 转写慢（30 分钟视频约 5-10 分钟，可用 `--no-transcribe` 走 metadata fallback）

---

## 📜 License

MIT
