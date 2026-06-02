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

## ⚡ 5 秒上手

> v0.8.0 起提供**三种安装方式**，全部都在 [Release 页面](https://github.com/zczxd1118/content-catcher/releases/tag/v0.8.0)。

### 方式 A：完整版 ZIP（macOS 推荐，零配置）

下载 [`content-catcher-v0.8.0-bundle.zip`](https://github.com/zczxd1118/content-catcher/releases/download/v0.8.0/content-catcher-v0.8.0-bundle.zip)（**202 MB**，含预装的 Python venv + Whisper tiny 模型）。

```
1. 解压 → 双击 启动.command
2. 第一次启动会自动检测环境 / 必要时重建 venv（2-3 分钟）
3. 看到「✅ 环境就绪」就开干，无需联网下模型
```

### 方式 B：源码 + 一键安装（推荐给所有平台）

```bash
git clone https://github.com/zczxd1118/content-catcher.git
cd content-catcher
./install.sh                                       # 自动建 venv + 装依赖 + 准备配置
source .venv/bin/activate

# 单条整理
catch.py https://www.bilibili.com/video/BV1xxxxxx --cookies-from chrome

# 跑订阅周报
cp channels.example.yaml channels.yaml             # 改成你自己的订阅源
catch.py --subscribe channels.yaml
```

### 方式 C：pip 安装（想当库用）

```bash
pip install https://github.com/zczxd1118/content-catcher/releases/download/v0.8.0/content_catcher-0.8.0-py3-none-any.whl
catch --help
```

📖 **完整文档**：[`项目说明书.docx`](./项目说明书.docx) · [`docs/MANUAL.md`](./docs/MANUAL.md) · 📡 [`docs/SUBSCRIPTION_GUIDE.md`](./docs/SUBSCRIPTION_GUIDE.md) · 📝 [`CHANGELOG.md`](./CHANGELOG.md)

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
- 当你 `catch.py URL` —— 你在用 **Layer 3（工具）**
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
| 🎬 单条转笔记 | `catch.py URL` | 结构化中文/双语笔记 |
| 📚 单条精装版 | `catch.py URL --deep` | 1500-15000 字叙事长文 |
| 📜 单条完整版 | `catch.py URL --full` | 逐字稿+导读+章节索引 |
| 🗂️ 批量+合集/对比 | `catch.py --batch urls.txt --mode topic/compare` | 专题书/跨平台对比报告 |
| 📬 订阅周报 | `catch.py --subscribe channels.yaml --send-email` | 邮件周报+EPUB 附件 |

---

## 🎯 三种 AI 调用模式

| 模式 | 命令 | 谁出 AI 算力 | 适合 |
|------|------|------------|------|
| **🥇 投喂包**（默认） | `catch.py URL` | 复制投喂包丢给 AI（WorkBuddy/Claude/GPT）| 所有人 |
| **🥈 全自动** | `catch.py URL --auto` | 你的 API key（DeepSeek/Claude/GPT）| 重度用户 |
| **🥉 仅原文** | `catch.py URL --raw` | 不调 AI | 归档需求 |

---

## 📬 订阅周报（v0.7.2+ 推荐 4 步工作流）

```bash
# Step 1：抓取 → 出投喂包（人机协作的「准备」步骤）
catch.py --subscribe channels.yaml

# Step 2：用对话方 Claude / GPT 读投喂包，写代笔单章到 digest 目录：
#   output/digest/<本期>/chapter-<slug>.md

# Step 3：用代笔单章重做 EPUB（绝不再塞投喂包原文，纯优美文章）
catch.py --subscribe channels.yaml --finalize-epub <本期目录名>

# Step 4：发邮件（EPUB 自动作为附件）
catch.py --subscribe channels.yaml --send-only <本期目录名>
```

### 给对话方 Claude 的触发短语

> 「按 skill 流程跑本周 content-catcher 订阅，重要的几条帮我代笔」

详细教程：[`docs/SUBSCRIPTION_GUIDE.md`](./docs/SUBSCRIPTION_GUIDE.md)

---

## 📡 修改订阅清单

### 方法 A：用 `manage_channels.py` 工具（推荐，无需手编 YAML）

```bash
# 看现在订了什么
python scripts/manage_channels.py list

# 加 B 站 up 主（mid 在 space.bilibili.com/XXXXXXX 的 URL 里）
python scripts/manage_channels.py add-bili 25752587 "大牙大-"

# 加 YouTube 频道（channel_id 是 UC 开头那一串）
python scripts/manage_channels.py add-youtube UCJIfeSCssxSC_Dhc5s7woww "Lex Fridman"

# 加 RSS 播客（小宇宙 / 苹果播客 / Substack）
python scripts/manage_channels.py add-rss "https://feed.xyzfm.space/dk4yh3pkpjp3" "张小珺商业访谈录"

# 临时关闭某个频道（不删除）
python scripts/manage_channels.py disable "Lex Fridman"
```

### 方法 B：直接编辑 `channels.yaml`

```yaml
channels:
  - type: bilibili_uploader
    name: "大牙大-"
    mid: "25752587"
    cookies_from: chrome
    enabled: true       # ← 改成 false 即可临时关闭

  - type: youtube_channel
    name: "Lex Fridman"
    channel_id: "UCSHZKyawb77ixDdsGog4iWA"
    enabled: true

  - type: rss
    name: "张小珺商业访谈录"
    url: "https://feed.xyzfm.space/dk4yh3pkpjp3"
    enabled: true
```

### 各平台 ID 怎么找

| 平台 | ID 在哪里 | 例子 |
|------|---------|------|
| **B 站 up 主** | `space.bilibili.com/XXXXXXX` URL 里的数字 | `25752587` |
| **YouTube 频道** | 频道主页源码里搜 `"channelId":"UC..."` | `UCSHZKyawb77ixDdsGog4iWA` |
| **小宇宙节目** | 用 podstatus / xyzfm.space 找 RSS | `https://feed.xyzfm.space/xxxxxx` |
| **Substack 播客** | `<站名>.substack.com/feed/podcast/<id>.rss` | 自动探测，也可手动 |
| **苹果播客** | 用 castro.fm/itunes 转换 | RSS URL |

> 📌 修改 `channels.yaml` 后**下次跑 `--subscribe` 自动用新清单**。
> `output/digest/history.json` 存"已发过的视频"，**改清单不会重置历史** —— 老视频不会重发。

---

## 🛠️ 技术栈

- **Python 3.10+**
- **yt-dlp**：万能下载器（B 站 / YouTube / 苹果播客等多平台）
- **faster-whisper**：本地语音转写（Mac 友好，CPU + int8）
- **ebooklib**：EPUB 导出
- **feedparser / trafilatura**：RSS / HTML 抓取
- **PyYAML**：订阅配置
- **smtplib**：邮件推送（QQ/Gmail/网易等通用 SMTP）

---

## 🧪 测试

v0.8.0 含 4 套回归测试，跑之前 `source .venv/bin/activate`：

```bash
python tests/test_email_sender_unicode.py     # 中文邮件编码不再 ASCII 错
python tests/test_export_epub.py              # EPUB 结构 + 中文 Markdown
python tests/test_build_epub_polished.py     # 投喂包绝不漏进 EPUB
python tests/test_youtube_fetcher_chain.py   # YouTube 多级 fallback
```

---

## 🗺️ 路线图

### v0.8.0 已完成（2026-06-02）
- [x] M0–M4：单条 / 批量 / 跨平台 / 长内容分段
- [x] M5：订阅 + 周报 + 邮件 + EPUB
- [x] M6：播客主站 RSS 整合（latent.space / acquired.fm / lexfridman.com / substack）
- [x] **v0.7.1 中文邮件编码修复**（EmailMessage policy + UTF-8 charset）
- [x] **v0.7.2 EPUB 重构**：`chapter-<slug>.md` 优先级查找，绝不再塞投喂包
- [x] **v0.7.2 新 CLI**：`--send-only` / `--finalize-epub` / `--epub-threshold`
- [x] **v0.7.3 YouTube fetcher chain**：原生重试 → UULF playlist → RSSHub/Invidious 代理
- [x] **v0.8.0 打包**：pyproject.toml + install.sh + 完整版 zip（含 venv + 模型）
- [x] **v0.8.0 文档**：10 章项目说明书 docx + 完整用户手册 + 订阅管理指南

### 接下来（v0.8.x / v0.9.x）
- [ ] launchd / cron 定时任务模板（目前手动跑）
- [ ] Whisper 模型自动按需切换（短视频 tiny / 长视频 small）
- [ ] EPUB 自动加封面图
- [ ] Windows 一键安装脚本
- [ ] 升级为 Agent（基于此项目的 [content-curator](https://github.com/zczxd1118/content-curator)）

---

## 📂 目录结构

```
content-catcher/
├── catch.py                  # 主入口（CLI）
├── install.sh                # v0.8.0：一键安装
├── 启动.command              # v0.8.0：macOS 完整版双击入口
├── pyproject.toml            # v0.8.0：可 pip install
├── requirements.txt          # v0.8.0：依赖清单
├── 项目说明书.docx           # v0.8.0：10 章完整说明书
├── SKILL.md                  # WorkBuddy Skill 描述
├── channels.example.yaml     # 订阅配置模板
├── scripts/
│   ├── _bin.py               # v0.8.0：统一查 yt-dlp 等二进制
│   ├── detect_platform.py
│   ├── get_metadata.py
│   ├── fetch_subtitle.py
│   ├── fetch_xiaohongshu.py
│   ├── fetch_podcast_rss.py
│   ├── transcribe.py
│   ├── chunker.py
│   ├── build_prompt.py
│   ├── run_llm.py
│   ├── batch.py
│   ├── subscribe.py          # v0.7.3：YouTube fetcher chain
│   ├── digest.py             # v0.7.2：build_epub_if_many 重构
│   ├── digest_history.py
│   ├── email_sender.py       # v0.7.1：中文编码修复
│   ├── export_epub.py
│   ├── manage_channels.py
│   ├── build_manual_docx.py  # v0.8.0：项目说明书 docx 生成
│   └── ...
├── templates/                # Prompt 模板（5 种产物形态）
│   ├── chinese_notes.md
│   ├── english_bilingual.md
│   ├── xiaohongshu_note.md
│   ├── deep_book.md
│   ├── full_transcript.md
│   ├── topic_collection.md
│   ├── cross_platform_compare.md
│   ├── weekly_digest.md
│   └── chapter_polished.md   # v0.7.2+ 代笔单章模板
├── docs/                     # v0.7.3+ 完整文档
│   ├── MANUAL.md             # 10 章用户手册
│   └── SUBSCRIPTION_GUIDE.md # 订阅源管理详解
└── tests/                    # v0.7.1+ 回归测试
    ├── test_email_sender_unicode.py
    ├── test_export_epub.py
    ├── test_build_epub_polished.py
    └── test_youtube_fetcher_chain.py
```

---

## 💡 使用建议

- **隐私**：本工具不上传任何内容到外部服务器，转写完全本地（faster-whisper）
- **成本**：默认模式零 API 费（投喂包丢给你已有的 AI），自动模式按 API 计费（DeepSeek 极便宜）
- **国内网络**：HuggingFace 模型走 hf-mirror.com 镜像（已自动处理）
- **B 站抓取**：需要 Chrome 登录 B 站，工具读 cookies 自动注入
- **完整版 zip 跨机器**：venv 是 macOS Apple Silicon 构建，其他平台首次跑 `启动.command` 会自动重建 venv（约 2-3 分钟）；Whisper 模型纯数据，跨平台直接用

---

## ⚠️ 已知限制

- YouTube 在国内 IP 可能反爬（建议改用 Apple Podcasts / B 站；v0.7.3 已加 fetcher chain 改善）
- 小红书需公开笔记（私密笔记暂不支持）
- 长视频 Whisper 转写慢（30 分钟视频约 5-10 分钟，可用 `--no-transcribe` 走 metadata fallback）
- YouTube `videos.xml` endpoint 在 2025 起间歇 5xx（行业问题，已加 3 级 fallback 缓解）

---

## 📜 License

MIT · © 2026 周小丁
