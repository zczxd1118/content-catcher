# 🎯 content-catcher

> 多平台音视频/图文转结构化笔记的 Skill —— **链接进，精装文/周报/对比报告出**。

支持 **YouTube / B 站 / 小红书 / 苹果播客 / Spotify / 小宇宙 / Substack 播客** 等 7+ 平台，**1 行命令**或 `@skill` 调用，**1-15 分钟**拿到产物。

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

```bash
# 1. 配 channels.yaml（参考 channels.example.yaml）
cp channels.example.yaml channels.yaml
# 用 manage_channels.py 加订阅源
python scripts/manage_channels.py add-bili 25752587 "你关注的 up 主"

# 2. 配 SMTP（持久化）
echo "SMTP_PASS=你的QQ邮箱授权码" > .smtp_secret  # 已加进 .gitignore

# 3. 跑订阅 + 发邮件
python catch.py --subscribe channels.yaml --send-email
```

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
