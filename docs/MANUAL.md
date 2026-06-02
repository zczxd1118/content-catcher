# content-catcher 项目手册

> v0.8.0 · 完整用户指南
>
> 这份手册从"装上"讲到"用熟"——单条整理、订阅周报、邮件、EPUB、代笔工作流、踩坑全覆盖。

---

## 目录

1. [它是什么 / 不是什么](#1-它是什么--不是什么)
2. [快速开始（5 分钟）](#2-快速开始5-分钟)
3. [整体架构](#3-整体架构)
4. [核心命令速查](#4-核心命令速查)
5. [配置：channels.yaml + .smtp_secret](#5-配置channelsyaml--smtp_secret)
6. [使用模式](#6-使用模式)
   - 6.1 单条整理
   - 6.2 批量 / 专题
   - 6.3 订阅周报（含邮件 + EPUB）
   - 6.4 人机分工（不接 LLM API）
7. [文件目录在哪里](#7-文件目录在哪里)
8. [常见问题 FAQ](#8-常见问题-faq)
9. [开发与贡献](#9-开发与贡献)
10. [致谢与许可](#10-致谢与许可)

---

## 1. 它是什么 / 不是什么

### ✅ 它**是**

- **信息蒸馏 CLI**：把 YouTube / B 站 / 苹果播客 / 小宇宙 / 小红书 / 播客主站 等长内容→ 抓字幕 / 转写 / 结构化 → 可读的 Markdown 笔记
- **Newsletter 引擎**：订阅一批频道，每周自动扫近 7 天新内容、打包成 EPUB 电子书、邮件推送到你邮箱
- **Agent 友好**：所有 LLM 撰写步骤都是"投喂包 .prompt.md"形态，可以接 Claude / GPT 自动跑，也可以**让对话方（Claude）人工代笔**
- **本地优先**：默认不上传任何内容到第三方 API；Whisper 转写跑在你电脑 CPU 上

### ❌ 它**不是**

- 一个开了就自动 7×24 跑的服务（**没有 daemon**，要么手动跑、要么 cron / launchd / WorkBuddy automation 调度）
- 一个万能的"全能 AI 摘要器"——抓取层覆盖广，**蒸馏层质量取决于你接的 LLM**（或者代笔的 Claude）
- 一个开箱即用的"商业 Newsletter 平台"——你是它的**唯一作者也是唯一读者**（除非你自己改造）

---

## 2. 快速开始（5 分钟）

### 前提

- macOS / Linux（Windows 没正经测过）
- Python **3.10+**
- git
- ~3 GB 磁盘（其中大头是 faster-whisper 模型）

### 一键装

```bash
git clone https://github.com/zczxd1118/content-catcher.git
cd content-catcher
./install.sh
```

`install.sh` 会：
1. 检查 Python 版本
2. 建 `.venv/` 虚拟环境
3. 装所有依赖（`requirements.txt`）
4. 拷出 `channels.yaml` 和 `.smtp_secret` 占位
5. 跑 `catch --help` 和 EPUB 烟雾测试

### 跑第一条

```bash
source .venv/bin/activate
catch.py https://www.youtube.com/watch?v=xxxxxxx
```

输出会在 `output/notes/<标题>.md`（结构化笔记）+ `output/bundles/<标题>.prompt.md`（投喂 LLM 用）。

---

## 3. 整体架构

```
┌──────────────────────────────────────────────────────────┐
│ Layer 4：Newsletter（订阅周报 + 邮件 + EPUB 推送）         │
│   • channels.yaml 列出关注的 UP 主 / 频道 / 播客           │
│   • catch.py --subscribe 自动扫近 7 天新内容               │
│   • catch.py --finalize-epub 用代笔单章重做 EPUB          │
│   • catch.py --send-only 把成品发到邮箱                   │
└──────────────────────┬───────────────────────────────────┘
                       │ 由下层提供
┌──────────────────────┴───────────────────────────────────┐
│ Layer 3：内容处理 CLI（catch.py 主入口）                  │
│   • 单条 / 批量 / 跨平台对比 / 专题合集                    │
│   • 投喂包（.prompt.md）形态 → 任何 LLM 都能接             │
└──────────────────────┬───────────────────────────────────┘
                       │
┌──────────────────────┴───────────────────────────────────┐
│ Layer 2：抓取层                                            │
│   YouTube 字幕 ✓  B站字幕 ✓  播客 RSS ✓  小红书 ✓         │
│   Whisper 本地转写（无字幕时 fallback）                    │
└──────────────────────┬───────────────────────────────────┘
                       │
┌──────────────────────┴───────────────────────────────────┐
│ Layer 1：基础设施                                          │
│   yt-dlp（视频下载）+ faster-whisper（转写）              │
│   feedparser + trafilatura（RSS / web）                  │
│   EbookLib（EPUB）+ Markdown（HTML 渲染）+ smtplib（邮件） │
└──────────────────────────────────────────────────────────┘
```

---

## 4. 核心命令速查

> 所有命令都在仓库根目录跑（先 `source .venv/bin/activate` 或者用绝对路径）

### 单条 / 批量

```bash
# 单条
catch.py <URL>

# 单条带 cookies（B 站需要登录）
catch.py <URL> --cookies-from chrome

# 批量从文件
catch.py --batch urls.txt

# 批量做成专题
catch.py --batch urls.txt --mode topic --batch-name "AI Agent 学习专题"

# 批量做跨平台对比
catch.py --batch urls.txt --mode compare --batch-name "Claude vs Cursor"

# 只抓原文不做笔记
catch.py <URL> --raw
```

### 订阅周报

```bash
# 1. 抓取本周新内容（出投喂包 + 占位 EPUB）
catch.py --subscribe channels.yaml

# 2. 用代笔单章重做 EPUB（在 digest 目录写 chapter-*.md 后跑）
catch.py --subscribe channels.yaml --finalize-epub weekly-2026-W23-20260602

# 3. 把现成 digest 直接发邮件
catch.py --subscribe channels.yaml --send-only weekly-2026-W23-20260602

# 一气呵成（带 LLM API key 时用 --auto）
catch.py --subscribe channels.yaml --auto --send-email

# 调时间窗 + EPUB 阈值
catch.py --subscribe channels.yaml --days 14 --epub-threshold 1
```

### 常用参数

| 参数 | 用途 |
|---|---|
| `--cookies-from {chrome,safari,firefox,edge}` | 从浏览器读 cookies（B 站、付费 YouTube） |
| `--cookies-file <path>` | 直接传 cookies.txt 路径 |
| `--no-transcribe` | 无字幕时**不**走 Whisper（节省时间） |
| `--max-transcribe-min N` | 超过 N 分钟的视频跳过 Whisper（默认 20） |
| `--whisper-model {tiny,base,small,medium,large-v3}` | Whisper 模型大小（默认 tiny） |
| `--chunk-size N` | 长文本分段大小（投喂包切片用） |
| `--no-cache` | 强制重抓（默认会缓存链接结果） |
| `--deep` | 精装电子书风格（叙事体长文） |
| `--full` | 完整版（逐字稿 + 导读，不删减） |
| `--target-length "1500-3000"` | 深度模式下的目标字数 |
| `--days N` | 订阅模式抓近 N 天 |
| `--epub-threshold N` | 自动 EPUB 的最低条目数（默认 5） |
| `--auto` | 调 LLM API 自动写笔记 / 周报（需 ANTHROPIC/OPENAI key） |

---

## 5. 配置：channels.yaml + .smtp_secret

### 5.1 channels.yaml

订阅唯一入口，**完整的改源/加源/找 ID 指南**请看：[`docs/SUBSCRIPTION_GUIDE.md`](./SUBSCRIPTION_GUIDE.md)。

最小骨架：

```yaml
newsletter:
  name: "我的 AI 周报"
  email_to: "you@example.com"
  email_from: "you@example.com"
  smtp:
    host: "smtp.qq.com"
    port: 465
    use_ssl: true
    user: "you@example.com"

defaults:
  days: 7
  max_per_channel: 3

channels:
  - type: bilibili_uploader
    name: "大牙大-"
    mid: "25752587"
    cookies_from: chrome
    enabled: true
  - type: rss
    name: "Latent Space"
    url: "https://api.substack.com/feed/podcast/1084089.rss"
    enabled: true
```

### 5.2 .smtp_secret

> **永远不要把这个文件 commit 进 git**（仓库 `.gitignore` 默认会忽略）

```
SMTP_PASS=你的SMTP授权码
```

- **QQ 邮箱**：`mail.qq.com` → 设置 → 账户 → IMAP/SMTP/POP3 服务 → 申请授权码
- **Gmail**：`myaccount.google.com` → 安全性 → 应用专用密码
- **163 邮箱**：`mail.163.com` → 设置 → POP3/SMTP/IMAP → 客户端授权密码

> ⚠️ **不要** 用 `export SMTP_PASS="$(cat .smtp_secret)"`——会把整个文件（含注释）当 token，登录失败。脚本会自己读 `.smtp_secret`，无需手动 export。

---

## 6. 使用模式

### 6.1 单条整理

最常见用法：给一个链接，拿一份结构化笔记。

```bash
catch.py https://www.bilibili.com/video/BV1xxxxxx --cookies-from chrome
```

输出：

```
output/
├── notes/
│   └── <视频标题>.md           ← 你直接看 / 用 / 分享的笔记
└── bundles/
    └── <视频标题>.prompt.md    ← 把这个喂给 LLM 能拿到结构化笔记（如果你想让 LLM 写）
```

### 6.2 批量 / 专题

```bash
# urls.txt 一行一个 URL（# 开头是注释，行内可以写 --cookies-from chrome）
catch.py --batch urls.txt --mode topic --batch-name "Vibe Coding 实战合集"
```

模式：
- **`index`**（默认）：每条单独整理 + 一个总索引
- **`topic`**：让 LLM 把多条糅合成一份专题文章
- **`compare`**：让 LLM 做跨平台 / 跨 KOL 对比

### 6.3 订阅周报（含邮件 + EPUB）

完整 4 步工作流：

```bash
# Step 1：抓取
catch.py --subscribe channels.yaml
#   → output/digest/weekly-YYYY-WXX-YYYYMMDD/
#     ├── weekly-YYYY-WXX-YYYYMMDD.WEEKLY.prompt.md   ← 喂 LLM 写周报正文
#     └── weekly-YYYY-WXX-YYYYMMDD.epub                ← 占位 EPUB（≥ threshold 时）

# Step 2：写代笔正文（如果你不接 LLM API）
# 用对话方（Claude）读投喂包，写：
#   - output/digest/<本期>/weekly-digest.md          ← 周报邮件正文
#   - output/digest/<本期>/chapter-<slug>.md         ← 每条的精装单章（可选）

# Step 3：用代笔重做 EPUB（替换占位章节）
catch.py --subscribe channels.yaml --finalize-epub weekly-YYYY-WXX-YYYYMMDD

# Step 4：发邮件
catch.py --subscribe channels.yaml --send-only weekly-YYYY-WXX-YYYYMMDD
```

### 6.4 人机分工（不接 LLM API）

很多人**不想给 ANTHROPIC / OPENAI 充值**，想用自己日常对话的 Claude / GPT 来代笔——content-catcher 是**为这个场景设计的**：

```
catch.py 跑抓取 / 转写 / 切片 / 打包  ← 机器擅长的工程活
                  │
                  ↓
              投喂包.prompt.md
                  │
                  ↓
        你（或对话方 Claude）写正文   ← LLM 擅长的判断、蒸馏、改写
                  │
                  ↓
      catch.py --finalize-epub 重打包  ← 工程活
                  │
                  ↓
      catch.py --send-only 发邮件      ← 工程活
```

**触发短语**（在对话里跟 Claude 说）：

> "按 skill 流程跑本周 content-catcher 订阅，重要的几条帮我代笔"

Claude 会自动跑完 4 步，**你只负责看邮箱**。

---

## 7. 文件目录在哪里

```
content-catcher/
├── catch.py                     主入口 CLI
├── install.sh                   一键安装脚本
├── pyproject.toml               包元信息（pip install 用）
├── requirements.txt             运行时依赖清单
├── README.md                    项目首页
├── CHANGELOG.md                 版本变更记录
├── SKILL.md                     skill 元信息（agent 加载用）
├── LICENSE                      MIT 协议
│
├── channels.example.yaml        订阅配置模板（复制为 channels.yaml）
├── channels.yaml                ← 你的真实订阅清单（gitignored）
├── .smtp_secret                 ← 邮件授权码（gitignored）
│
├── scripts/                     业务模块
│   ├── _bin.py                  二进制定位（yt-dlp / ffmpeg）
│   ├── detect_platform.py      URL → 平台识别
│   ├── get_metadata.py         元信息抓取
│   ├── fetch_subtitle.py       字幕抓取
│   ├── download_audio.py       音频下载
│   ├── transcribe.py           Whisper 转写
│   ├── chunker.py / build_prompt.py / save_output.py
│   ├── subscribe.py            订阅扫描（含 YouTube fetcher chain）
│   ├── digest.py               周报组装 + EPUB 触发
│   ├── digest_history.py       去重记忆
│   ├── email_sender.py         SMTP 邮件
│   ├── export_epub.py          EPUB 导出
│   └── run_llm.py / batch.py / doctor.py / cache.py
│
├── templates/                   笔记 / 周报模板
│   ├── chinese_notes.md / english_bilingual.md
│   ├── xiaohongshu_note.md
│   ├── topic_collection.md / cross_platform_compare.md
│   ├── weekly_digest.md
│   └── chapter_polished.md
│
├── tests/                       回归测试
│   ├── test_email_sender_unicode.py
│   ├── test_export_epub.py
│   ├── test_build_epub_polished.py
│   ├── test_youtube_fetcher_chain.py
│   └── smoke_*.py
│
├── docs/
│   ├── MANUAL.md                ← 你正在看的这份
│   └── SUBSCRIPTION_GUIDE.md    订阅源管理详解
│
└── output/                      ← 全部产出（gitignored）
    ├── notes/                   单条整理后的 .md
    ├── bundles/                 投喂 LLM 的 .prompt.md
    ├── audio/                   下载的音频
    ├── subs/                    抓到的字幕
    ├── cache/                   链接级缓存
    ├── batches/                 批量产出
    ├── digest/                  周报产出
    │   ├── history.json         已发内容的去重记录
    │   └── weekly-YYYY-WXX-YYYYMMDD/
    │       ├── *.WEEKLY.prompt.md   投喂包
    │       ├── weekly-digest.md     周报正文（代笔）
    │       ├── chapter-*.md          单章代笔
    │       └── *.epub                成品电子书
    ├── epub/                    单独跑的 EPUB
    └── final/                   长期保留的精装版（EPUB 会自动捡）
```

---

## 8. 常见问题 FAQ

### Q1. `install.sh` 报 "Python too old"
升级到 Python 3.10+。macOS 推荐 `brew install python@3.12`，或者用 pyenv。

### Q2. B 站抓取失败，提示 "Sign in to confirm"
B 站要登录 cookies。在 Chrome / Safari 里**手动登录一次** B 站，然后命令里加 `--cookies-from chrome`（或 `safari`）。

### Q3. YouTube 订阅扫到 0 条
YouTube 自家 RSS endpoint 自 2025 年起间歇 5xx/404。v0.7.3+ 已加 fetcher chain（原生 → UULF playlist → RSSHub/Invidious 代理）自动 fallback。若仍 0 条：
- 浏览器直接打开 `https://www.youtube.com/feeds/videos.xml?channel_id=<UCxxx>` 验证 YouTube 是不是当下挂了
- 检查所在网络是否屏蔽了 RSSHub / Invidious 公共实例

### Q4. SMTP 报 `'ascii' codec can't encode characters`
v0.7.1 已修。如果重现，先检查 `scripts/email_sender.py` 是不是被退回了旧版（构造 `EmailMessage` 时必须传 `policy=SMTP_POLICY`）。

### Q5. SMTP 密码总是错
- 检查 `.smtp_secret` 格式：`SMTP_PASS=xxx`，**一行**，等号两边无空格
- 用的是 **SMTP 授权码** 而不是邮箱登录密码
- **不要** `export SMTP_PASS="$(cat .smtp_secret)"`——让脚本自己读

### Q6. Whisper 转写超慢
默认 `tiny` 模型，CPU 上 ~实时倍速。可调：
- 缩短：`--max-transcribe-min 10`（>10 分钟直接跳过）
- 加大：`--whisper-model small`（更准但慢 2-3 倍）
- 跳过：`--no-transcribe`（只用元信息 fallback）

### Q7. EPUB 章节里全是字幕原文 / LLM 任务说明
你装的是 v0.7.0—0.7.1。**升级到 v0.7.2+**：
```bash
git pull && pip install -r requirements.txt
```
新版本 EPUB 只用 `chapter-*.md` 代笔单章 + `output/final/` 精装版；找不到就用占位章节，**绝不**会再把投喂包塞进去。

### Q8. 中文专有名词转写错（"扣定" "Pen Mode" "DipSegre"）
Whisper tiny 对中文专有名词识别有限。两个方案：
- 升级模型：`--whisper-model small`
- 让 Claude 代笔时人工还原（推荐——tiny 速度优势保留）

### Q9. 长任务跑到一半被 shell 切了
用 `nohup` 真正脱离会话：
```bash
nohup ./catch.py --subscribe channels.yaml > /tmp/catch.log 2>&1 &
disown
tail -f /tmp/catch.log
```

### Q10. 想完全清掉重跑
```bash
rm -rf output/  # 删所有产出（包括缓存和已发记录）
rm -rf .venv/   # 删 venv 重装
```

---

## 9. 开发与贡献

### 跑测试

```bash
source .venv/bin/activate
for t in tests/test_*.py; do python "$t"; done
```

应该看到 4 个 ✅：email_sender_unicode / export_epub / build_epub_polished / youtube_fetcher_chain。

### 项目约定

- **不上 git**：`.smtp_secret`、`channels.yaml`、`output/`、`LOCAL_NOTES.md`、`my_videos.txt`
- **新 CLI flag** 写在 `catch.py` 的 `argparse` 块；记得同步加进 `docs/MANUAL.md` 的"参数速查"表
- **新 source type** 写在 `scripts/subscribe.py` 的 `scan_*` 函数；记得同步加进 `docs/SUBSCRIPTION_GUIDE.md`
- **新 LLM 模板** 放在 `templates/`，命名 `<场景>.md`
- 改动核心模块（subscribe / digest / email_sender / export_epub）必须**写对应的 `tests/test_*.py`**
- commit message 用 conventional commits 风格（`feat:` `fix:` `docs:` `test:` `chore:`）

### 提 issue / PR

去 https://github.com/zczxd1118/content-catcher/issues 描述清楚：
- 你用的版本（`git rev-parse HEAD` 或 release tag）
- 复现步骤
- 报错信息 / 期望行为

---

## 10. 致谢与许可

### 依赖致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) —— 视频抓取的事实标准
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) —— PyTorch-free Whisper
- [trafilatura](https://github.com/adbar/trafilatura) —— 网页正文提取
- [feedparser](https://github.com/kurtmckee/feedparser) —— RSS 解析
- [EbookLib](https://github.com/aerkalov/ebooklib) —— EPUB 生成
- [RSSHub](https://docs.rsshub.app/) / [Invidious](https://invidious.io/) —— YouTube 备用 feed 代理

### 许可

MIT License — 详见 [LICENSE](../LICENSE)。

---

> **最后**：这个项目是为"信息密度敏感、不想被算法推送、愿意用对话方做编辑判断"的人做的。如果你刚好是这种人，欢迎 fork、改造、分享。
