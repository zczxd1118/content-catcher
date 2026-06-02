---
name: content-catcher
description: Capture and structure long-form content (audio/video/posts) from YouTube, Bilibili, Xiaohongshu, Apple Podcasts, Xiaoyuzhou — supports single-link, batch with topic/cross-platform digest, and subscription-based weekly newsletter with EPUB export and email delivery. Subtitle-first with Whisper local transcription fallback, cookie injection, and long-content auto-chunking.
description_zh: 内容捕手 - 多平台音视频图文转结构化笔记 + Newsletter 订阅
description_en: Content Catcher - Multi-platform Skill
disable: false
agent_created: true
---

# 内容捕手 content-catcher

## When to use

Use this skill when the user:
- 粘贴 YouTube / B 站 / 小宇宙 / 苹果播客 / 小红书 链接
- 说"把这个播客/视频转成笔记"
- 说"把这几个视频做成专题笔记 / 跨平台对比报告"
- 说"帮我订阅这些 YouTuber/UP 主，每周推送周报"
- 想把音视频/图文长内容快速变成可读、可分享的结构化笔记

Typical triggers:
- "帮我整理这个 B 站视频"
- "对比一下这几个 KOL 对 XX 的看法"
- "做一个 vibe coding 主题的专题合集"
- "每周自动给我发一份关注的 up 主新视频周报"

## 🎯 五大场景

| 场景 | 输入 | 输出 |
|------|------|------|
| 中文音视频 | B 站 / 小宇宙 / 中文 YouTube | 结构化中文笔记 |
| 英文音视频 | Lex Fridman / Latent Space | 中英双语对照笔记 |
| 小红书图文 | 小红书笔记 | 二创素材包 |
| 批量+合集 | 多链接（多平台亦可） | 索引 / 专题合集 / 跨平台对比 |
| 订阅周报 | channels.yaml + 定时 | 每周新内容 → 邮箱周报 + 可选 EPUB |

| 场景 | 输入 | 输出 |
|------|------|------|
| 中文音视频 | B 站 / 小宇宙 / 中文 YouTube | 结构化中文笔记 |
| 英文音视频 | Lex Fridman / Latent Space | 中英双语对照笔记 |
| 小红书图文 | 小红书笔记 | 二创素材包 |
| 批量+合集 | 多链接（多平台亦可） | 索引 / 专题合集 / 跨平台对比 |
| **订阅周报** | channels.yaml + 定时 | **每周新内容 → 邮箱周报 + 可选 EPUB** |

## 📦 使用模式

### 单条
```bash
python catch.py URL
```

### 批量
```bash
python catch.py --batch urls.txt
python catch.py --batch urls.txt --mode topic --batch-name "AI Agent 学习专题"
python catch.py --batch urls.txt --mode compare --batch-name "AutoGLM 竞品分析"
```

### ⭐ 订阅周报（M5 新增）
```bash
# 1. 拷贝配置模板
cp channels.example.yaml channels.yaml

# 2. 编辑 channels.yaml：填你关注的 YouTuber / B 站 up 主 / RSS

# 3. 跑订阅扫描，生成本周新内容的投喂包（不发邮件）
python catch.py --subscribe channels.yaml

# 4. 自动跑 LLM 出周报正文（需 ANTHROPIC_API_KEY / OPENAI_API_KEY）
python catch.py --subscribe channels.yaml --auto

# 5. 发到邮箱（需 SMTP_PASS 环境变量，YAML 配 SMTP）
export SMTP_PASS=你的SMTP授权码
python catch.py --subscribe channels.yaml --auto --send-email

# 6. 自定义时间范围
python catch.py --subscribe channels.yaml --days 3
```

### 定时跑（macOS launchd）
```bash
# 编辑 ~/Library/LaunchAgents/com.you.weekly-digest.plist 添加：
# 每周一早上 9 点跑订阅周报并发邮件
```

### 📧 SMTP 踩坑提示

- **`.smtp_secret` 是 KEY=VAL 格式（含注释行）**，不要用 `export SMTP_PASS="$(cat .smtp_secret)"` 整段塞环境变量——会把注释也当 token，登录失败。`email_sender.py` 自带 fallback 解析，让脚本自己读就行（直接 `python catch.py --send-email`，**不要**预先 export）。
- **中文标题/中文附件名/中文正文**：v0.7.1+ 已修。`EmailMessage` 默认 policy 是 `compat32`（ASCII-only），所以构造时强制传 `policy=SMTP_POLICY` 并给 `set_content`/`add_alternative` 加 `charset="utf-8"`。如果再次出现 `'ascii' codec can't encode characters`，先检查 `email_sender.py` 是不是被退回了旧版。

## ⚙️ 参数速查

| 参数 | 用途 |
|------|------|
| `--batch <file>` | 批量模式 |
| `--mode {index,topic,compare}` | 批量产物形态 |
| `--subscribe <yaml>` | 订阅周报模式 ⭐ |
| `--days <n>` | 订阅模式抓近 N 天 |
| `--send-email` | 订阅模式发邮件 |
| `--auto` | LLM 全自动 |
| `--cookies-from <browser>` | 浏览器 cookies |
| `--no-transcribe` | 不走 Whisper |
| `--whisper-model {...}` | 转写模型 |
| `--chunk-size <n>` | 长文本分段大小 |
| `--no-cache` | 强制重抓 |
| `--raw` | 只抓原文 |

## 🔁 订阅周报数据流（M5）

```
channels.yaml
   ↓
subscribe.scan_all     ← RSS 抓 YouTube/B站/小宇宙近 N 天新内容
   ↓
digest_history.filter_new  ← 剔除已发过的
   ↓
逐个跑 process_one     ← 抓字幕/转写
   ↓
digest.build_weekly_bundle  ← 拼周报投喂包
   ↓
(可选) run_llm 自动生成周报正文
   ↓
(若内容 ≥ 5 条) export_epub  ← 打包 EPUB 附件
   ↓
(若 --send-email) email_sender  ← SMTP 发到你邮箱
   ↓
digest_history.mark_sent  ← 标记已发，下次不重复
```

## 📁 项目结构

```
content-catcher/
├── SKILL.md / README.md / catch.py
├── channels.example.yaml      ← M5 订阅配置模板
├── scripts/
│   ├── detect_platform.py / get_metadata.py
│   ├── fetch_subtitle.py / fetch_xiaohongshu.py
│   ├── download_audio.py / transcribe.py
│   ├── detect_language.py / chunker.py
│   ├── build_prompt.py / run_llm.py / save_output.py
│   ├── cache.py / batch.py / doctor.py
│   ├── subscribe.py           ← M5：频道扫描（YouTube/B站/RSS）
│   ├── digest.py              ← M5：周报主调度
│   ├── digest_history.py      ← M5：增量记忆
│   ├── email_sender.py        ← M5：SMTP 邮件
│   └── export_epub.py         ← M5：EPUB 导出
├── templates/
│   ├── chinese_notes.md / english_bilingual.md
│   ├── xiaohongshu_note.md
│   ├── topic_collection.md / cross_platform_compare.md
│   └── weekly_digest.md       ← M5：Newsletter 周报模板
├── tests/                      多个 smoke test
└── output/
    ├── subs / audio / notes / bundles / final
    ├── cache/ / batches/
    └── digest/<digest_name>/   ← M5：周报产物（含 EPUB）
        └── history.json        ← M5：增量记忆
```

## 🆚 能力矩阵

| 维度 | 一般 Newsletter Skill | content-catcher v0.6 |
|------|--------------------|---------------------|
| 订阅式 | ✅ | ✅ |
| 邮件推送 | ✅ | ✅ |
| EPUB 附件 | ✅ | ✅ |
| YouTube | ✅ | ✅ |
| **B 站** | ❌ | ✅ |
| **小宇宙** | ❌ | ✅（RSS） |
| **苹果播客** | ❌ | ✅ |
| **小红书** | ❌ | ✅ |
| 单次/批量/对比 | ❌ | ✅ |
| 跨平台分析 | ❌ | ✅ |

## 🗺️ 路线图

- [x] M0–M4
- [x] **M5：订阅 + 周报 + 邮件 + EPUB**
- [x] **M6：播客主站 RSS 整合**（latent.space / acquired.fm / lexfridman.com / substack 自动抓 show notes）
- [ ] M7：launchd / cron 定时任务模板（一行装好定时跑）
- [ ] M8：并行处理（多链接同时跑）
- [ ] M9：上架 WorkBuddy Skill 市场
