# Changelog

> 所有用户感知到的变更都记在这。格式参考 [Keep a Changelog](https://keepachangelog.com/) +
> [Semantic Versioning](https://semver.org/lang/zh-CN/)。

---

## [0.8.0] — 2026-06-02

> **重磅升级版**：可分发 / 可订阅 / 可定时的完整 Newsletter 引擎。
> 一周内连发 8 个 commit 把所有"开发机绝对路径"、"中文邮件挂掉"、"EPUB 装的是字幕原文"、
> "YouTube fetcher 全靠原生不稳"等 P0 / P1 问题修干净，并加齐打包/安装/手册/CI 测试。

### 🚀 新功能（Features）

- **CLI**：新增 `--send-only <digest-dir>`、`--finalize-epub <digest-dir>`、`--epub-threshold N`
  - `--send-only` 跳过抓取，把已有 `weekly-digest.md` 一键发邮件
  - `--finalize-epub` 用代笔单章 `chapter-*.md` 重新生成 EPUB
  - `--epub-threshold` 控制自动 EPUB 触发阈值（默认 5 条新内容）
- **YouTube fetcher chain**（v0.7.3）：原生 `videos.xml` → `UULF playlist_id` → RSSHub / Invidious
  公共代理，逐级 fallback；`http_get` 加重试 + 指数退避；"200 但 0 entry"也算失败
- **EPUB 设计改造**：章节内容按优先级取——
  1. `output/digest/<本期>/chapter-<slug>.md`（本期代笔单章）
  2. `output/final/<slug>/笔记.md`（长期精装版）
  3. **占位章节**（仅标题 + 链接 + "尚未代笔"提示）
  **彻底不再把投喂包（含 LLM 任务说明 + 原始 Whisper 字幕）塞进 EPUB**
- **打包**：新增 `pyproject.toml` + `requirements.txt` + `install.sh` 一键安装脚本
  - `pip install .` 即可装；`./install.sh` 给完整新机器跑

### 🐛 修复（Fixes）

- **email_sender 中文编码 bug**：`EmailMessage` 默认 `compat32` policy 是 ASCII-only，
  中文 subject / body / 附件名会触发 `'ascii' codec can't encode characters`。
  现已强制 `policy=SMTP_POLICY` + `set_content/add_alternative` 显式 `charset="utf-8"`
- **去开发机硬编码路径**：`scripts/{download_audio,fetch_subtitle,get_metadata,subscribe}.py`
  原本写死了我开发机的 yt-dlp 绝对路径（`/Users/zoezczhou/.workbuddy/...`），
  别人 clone 下来根本跑不了。新建 `scripts/_bin.py` 统一查 same-venv → PATH → 报错
- **YouTube fetcher 间歇失败**：YouTube 自 2025 起让 `videos.xml` endpoint 间歇 5xx/404。
  现在原生失败自动走 UULF / 第三方代理，单次失败不再丢一周的 feed

### 📚 文档（Docs）

- 新增 `docs/MANUAL.md` —— 完整用户手册（从安装到 FAQ 共 10 章）
- 新增 `docs/SUBSCRIPTION_GUIDE.md` —— 订阅源管理详解（各平台 ID 怎么找、加/删/启停源）
- 新增 `CHANGELOG.md` —— 你正在看的这份
- 新增 `templates/chapter_polished.md` —— 给 Claude / GPT 看的"代笔单章"模板
- 更新 `README.md` 顶部加 5 分钟快速开始 + 文档导航
- 更新 `SKILL.md` 加 SMTP 踩坑 + EPUB 新工作流 + 长任务 nohup 提示
- 更新 `channels.example.yaml` 到 v0.2 风格，注释含完整使用提示

### 🧪 测试（Tests）

新增 4 套回归测试，全部跑过：

| 测试 | 覆盖 |
|---|---|
| `tests/test_email_sender_unicode.py` | 中文 / Emoji header / 正文不再触发 ASCII 编码错误 |
| `tests/test_export_epub.py` | EPUB 文件结构合法、中文 / 复杂 Markdown 保留 |
| `tests/test_build_epub_polished.py` | 代笔成品被优先使用、投喂包不漏进 EPUB |
| `tests/test_youtube_fetcher_chain.py` | YouTube fetcher chain 各路径 / 200-but-empty / 全失败优雅返回 |

### ⚠️ 已知问题（Known Issues）

- YouTube 原生 `videos.xml` 在 2025 年起间歇 5xx/404（YouTube 端问题）。已加 fetcher chain 兜底，
  但若网络环境屏蔽 RSSHub / Invidious 公共实例，最差情况仍会 0 条
- macOS 沙箱里 lxml 偶尔签名异常导致 EPUB 不出；裸 macOS / Linux 终端正常

### 📦 升级指南

从 v0.7.0 升上来：

```bash
git pull
./install.sh                    # 重新装一遍依赖（pyproject.toml / requirements.txt 是新的）
# 或者：
source .venv/bin/activate
pip install -r requirements.txt --upgrade
```

**不破坏现有数据**：`channels.yaml`、`.smtp_secret`、`output/` 都不动。

---

## [0.7.0] — 2026-04-XX

初版稳定 release。M5 完成（订阅周报 + 邮件 + EPUB）。
详见 [v0.7.0 release notes](https://github.com/zczxd1118/content-catcher/releases/tag/v0.7.0)。

### 主要功能

- M0–M4：单条整理、批量、专题、跨平台对比、Whisper 转写、长内容分段
- M5：订阅扫描 → 投喂包 → 邮件推送 → EPUB 附件
- M6：播客主站 RSS 整合（latent.space / acquired.fm / Substack 自动抓 show notes）

---

[0.8.0]: https://github.com/zczxd1118/content-catcher/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/zczxd1118/content-catcher/releases/tag/v0.7.0
