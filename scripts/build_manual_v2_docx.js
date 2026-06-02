/**
 * 生成 content-catcher v0.8.0 项目说明书 v2（详细版）
 *
 * 设计：保留 v0.7 旧版的 10 章骨架（用户已经习惯），但内容全面升级到 v0.8.0。
 * 新增：packaging、installer、新 CLI、EPUB 重构、YouTube fetcher chain、Claude 代笔工作流。
 */
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, PageOrientation, LevelFormat, ExternalHyperlink,
  TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType,
  VerticalAlign, PageNumber, PageBreak, TabStopType, TabStopPosition,
} = require('/Users/zoezczhou/.workbuddy/binaries/node/workspace/node_modules/docx');

// ─── 通用样式 ───────────────────────────────────────────
const FONT_CN = "PingFang SC";
const FONT_EN = "Helvetica Neue";
const FONT_MONO = "Menlo";

const COLOR_PRIMARY = "0071e3";
const COLOR_ACCENT = "1F4E79";
const COLOR_TEXT = "1d1d1f";
const COLOR_MUTED = "6e6e73";
const COLOR_TABLE_HEAD = "1F4E79";
const COLOR_TABLE_HEAD_TEXT = "FFFFFF";
const COLOR_BORDER = "BFBFBF";
const COLOR_CODE_BG = "F5F5F7";
const COLOR_QUOTE_BG = "F0F7FF";
const COLOR_WARN_BG = "FFF8E5";

const border = { style: BorderStyle.SINGLE, size: 4, color: COLOR_BORDER };
const allBorders = { top: border, bottom: border, left: border, right: border };

// ─── 帮助函数 ──────────────────────────────────────────
const p = (text, opts = {}) => new Paragraph({
  children: [new TextRun({ text, font: FONT_CN, color: COLOR_TEXT, size: 22, ...opts })],
  spacing: { before: 80, after: 80, line: 360 },
  ...(opts._para || {}),
});

// 富文本段落：mixed runs（粗体强调等）
const pRich = (...runs) => new Paragraph({
  children: runs.map(r => {
    if (typeof r === 'string') return new TextRun({ text: r, font: FONT_CN, color: COLOR_TEXT, size: 22 });
    return new TextRun({ font: FONT_CN, color: COLOR_TEXT, size: 22, ...r });
  }),
  spacing: { before: 80, after: 80, line: 360 },
});

const h1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  children: [new TextRun({ text, font: FONT_CN, bold: true, size: 36, color: COLOR_PRIMARY })],
  spacing: { before: 480, after: 240 },
  pageBreakBefore: true,
});

const h2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  children: [new TextRun({ text, font: FONT_CN, bold: true, size: 28, color: COLOR_ACCENT })],
  spacing: { before: 360, after: 160 },
});

const h3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  children: [new TextRun({ text, font: FONT_CN, bold: true, size: 24, color: COLOR_TEXT })],
  spacing: { before: 280, after: 140 },
});

const h4 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_4,
  children: [new TextRun({ text, font: FONT_CN, bold: true, size: 22, color: COLOR_MUTED })],
  spacing: { before: 200, after: 100 },
});

const bullet = (text, opts = {}) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  children: [new TextRun({ text, font: FONT_CN, color: COLOR_TEXT, size: 22, ...opts })],
  spacing: { before: 40, after: 40, line: 340 },
});

const bulletRich = (...runs) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  children: runs.map(r => {
    if (typeof r === 'string') return new TextRun({ text: r, font: FONT_CN, color: COLOR_TEXT, size: 22 });
    return new TextRun({ font: FONT_CN, color: COLOR_TEXT, size: 22, ...r });
  }),
  spacing: { before: 40, after: 40, line: 340 },
});

const numbered = (text, opts = {}) => new Paragraph({
  numbering: { reference: "numbers", level: 0 },
  children: [new TextRun({ text, font: FONT_CN, color: COLOR_TEXT, size: 22, ...opts })],
  spacing: { before: 40, after: 40, line: 340 },
});

const code = (text) => new Paragraph({
  children: [new TextRun({ text, font: FONT_MONO, size: 20, color: COLOR_TEXT })],
  spacing: { before: 30, after: 30, line: 280 },
  shading: { type: ShadingType.CLEAR, fill: COLOR_CODE_BG, color: "auto" },
  border: {
    top:    { style: BorderStyle.SINGLE, size: 1, color: COLOR_BORDER, space: 4 },
    left:   { style: BorderStyle.SINGLE, size: 1, color: COLOR_BORDER, space: 4 },
    bottom: { style: BorderStyle.SINGLE, size: 1, color: COLOR_BORDER, space: 4 },
    right:  { style: BorderStyle.SINGLE, size: 1, color: COLOR_BORDER, space: 4 },
  },
});

const codeBlock = (lines) => lines.map(code);

const link = (text, url) => new Paragraph({
  children: [new ExternalHyperlink({
    children: [new TextRun({ text, font: FONT_CN, size: 22, color: COLOR_PRIMARY, underline: {} })],
    link: url,
  })],
  spacing: { before: 60, after: 60 },
});

const quote = (text) => new Paragraph({
  children: [new TextRun({ text, font: FONT_CN, size: 22, color: COLOR_MUTED, italics: true })],
  spacing: { before: 120, after: 120, line: 340 },
  indent: { left: 720, right: 360 },
  shading: { type: ShadingType.CLEAR, fill: COLOR_QUOTE_BG, color: "auto" },
});

const warn = (text) => new Paragraph({
  children: [
    new TextRun({ text: "⚠️ ", font: FONT_EN, size: 22 }),
    new TextRun({ text, font: FONT_CN, size: 22, color: COLOR_TEXT, bold: true }),
  ],
  spacing: { before: 120, after: 120, line: 340 },
  indent: { left: 360, right: 360 },
  shading: { type: ShadingType.CLEAR, fill: COLOR_WARN_BG, color: "auto" },
});

const cell = (text, opts = {}) => {
  const isHeader = opts.head;
  return new TableCell({
    borders: allBorders,
    width: { size: opts.width || 4680, type: WidthType.DXA },
    shading: isHeader ? { type: ShadingType.CLEAR, fill: COLOR_TABLE_HEAD, color: "auto" } : undefined,
    margins: { top: 100, bottom: 100, left: 140, right: 140 },
    children: [new Paragraph({
      children: [new TextRun({
        text, font: FONT_CN, size: 20,
        color: isHeader ? COLOR_TABLE_HEAD_TEXT : COLOR_TEXT,
        bold: isHeader || opts.bold,
      })],
      spacing: { before: 0, after: 0, line: 280 },
    })],
    verticalAlign: VerticalAlign.CENTER,
  });
};

const tbl = (headers, rows, columnWidths) => {
  const totalWidth = columnWidths.reduce((a,b) => a+b, 0);
  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((h, i) => cell(h, { head: true, width: columnWidths[i] })),
      }),
      ...rows.map(row => new TableRow({
        children: row.map((c, i) => cell(c, { width: columnWidths[i] })),
      })),
    ],
  });
};

// ─── 文档内容 ──────────────────────────────────────────
const children = [];

// === 封面 ===
children.push(
  new Paragraph({
    children: [new TextRun({ text: "📡", font: FONT_EN, size: 96 })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 2400, after: 240 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "content-catcher", font: FONT_EN, bold: true, size: 56, color: COLOR_PRIMARY })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 160 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "多平台音视频/图文转结构化笔记 Skill", font: FONT_CN, size: 28, color: COLOR_TEXT })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 80 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "项目说明书", font: FONT_CN, size: 36, color: COLOR_TEXT })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 80 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Personal Information Distillery + Newsletter Engine", font: FONT_EN, italics: true, size: 22, color: COLOR_MUTED })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 1000 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "v0.8.0", font: FONT_EN, bold: true, size: 40, color: COLOR_PRIMARY })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "作者：周小丁", font: FONT_CN, size: 22, color: COLOR_TEXT })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 60 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "更新日期：2026 年 6 月 2 日", font: FONT_CN, size: 22, color: COLOR_MUTED })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "https://github.com/zczxd1118/content-catcher", font: FONT_MONO, size: 20, color: COLOR_PRIMARY })],
    alignment: AlignmentType.CENTER,
  }),
);

// === 目录 ===
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text: "📋 目录", font: FONT_CN, bold: true, size: 36, color: COLOR_PRIMARY })],
    pageBreakBefore: true,
    spacing: { after: 240 },
  }),
  new TableOfContents("Table of Contents", {
    hyperlink: true,
    headingStyleRange: "1-3",
  }),
);

// === 1. 项目概览 ===
children.push(
  h1("一、项目概览"),

  h2("1.1 一句话定位"),
  p("content-catcher 是一个本地优先的「信息蒸馏 + Newsletter」基础设施——把任何平台的长内容（音视频 / 播客 / 图文），10 分钟内自动变成一份结构化的可读笔记 / 周报 / EPUB 电子书。"),
  quote("它不只是字幕转笔记工具，而是把「抓取 → 转写 → LLM 蒸馏 → 邮件 / EPUB 推送」整条链路打通的个人 Newsletter 引擎。"),

  h2("1.2 它能做什么"),
  bullet("粘一个 YouTube / B 站 / 苹果播客 / 小宇宙 / 小红书链接，5 分钟产出结构化笔记"),
  bullet("自动从英文播客 RSS 抓 show notes，写出 5000-15000 字中文 / 英文精装版长文"),
  bullet("批量处理多个链接，输出索引、专题合集或跨平台对比报告（适合做竞品分析）"),
  bullet("订阅式 Newsletter：扫描你关注的 KOL，每周自动生成周报，支持邮件 + EPUB 推送"),
  bullet("无字幕 / 长视频 / 国内反爬等场景全部自动降级处理（5 层 fallback 策略）"),
  bullet("v0.8.0 新增：一键安装脚本 ./install.sh，从 git clone 到能跑只需 5 分钟"),

  h2("1.3 谁适合用"),
  tbl(
    ["类型", "适配度", "典型场景"],
    [
      ["AI 产品 / 设计研究者", "★★★★★", "跨平台对标分析、产品案例库构建"],
      ["KOL 重度阅读者", "★★★★★", "订阅 N 个 UP 主 / 播客主，每周自动收集精华"],
      ["内容创作者", "★★★★☆", "把自己看过的视频整理成可检索的素材库"],
      ["技术 / 行业从业者", "★★★★☆", "技术博客笔记、竞品调研、信息周报"],
      ["普通用户", "★★★☆☆", "如果只是偶尔整理一两条，门槛偏高（需要 macOS + 命令行基础）"],
    ],
    [2200, 1400, 5760],
  ),

  h2("1.4 与同类产品对比"),
  tbl(
    ["维度", "ChatGPT 网页版", "Notion AI", "content-catcher"],
    [
      ["本地化", "❌", "❌", "✅ 数据全在本地"],
      ["批量 / 订阅", "❌", "❌", "✅ Newsletter 引擎"],
      ["LLM 中立", "❌（仅 OpenAI）", "❌（仅 Anthropic / GPT）", "✅ 可接任何对话方"],
      ["输出格式", "对话框文本", "Notion 页面", "Markdown / EPUB / 邮件 / docx"],
      ["反爬适配", "❌", "❌", "✅ B 站 cookies、小红书 token、yt-dlp"],
      ["免费", "受限", "$ /月", "✅ 完全免费"],
    ],
    [1800, 2400, 2400, 2760],
  ),
);

// === 2. 核心功能 ===
children.push(
  h1("二、核心功能"),

  h2("2.1 五大产物形态"),
  p("一条 catch.py 命令可以产出五种形态的笔记，对应不同使用场景："),
  tbl(
    ["形态", "命令", "适用场景"],
    [
      ["标准笔记", "catch.py <url>", "单条内容快速消化，3-5 分钟生成"],
      ["精装版长文", "catch.py <url> --premium", "把 1 小时播客写成 5000-15000 字深度长文"],
      ["完整版", "catch.py <url> --full", "不删减、保留所有原文，适合做长期素材库"],
      ["批量索引 / 合集", "catch.py --batch urls.txt", "把多条链接合成一本可检索目录"],
      ["订阅周报", "catch.py --subscribe channels.yaml", "每周自动扫订阅源 → EPUB + 邮件"],
    ],
    [1800, 3200, 4360],
  ),

  h2("2.2 三种 AI 调用模式"),
  p("v0.8.0 优雅地把「AI 怎么参与」拆成三种模式，用户按自身工作流挑一种："),
  tbl(
    ["模式", "怎么用", "适合谁"],
    [
      ["人机协作（推荐）", "catch.py 出投喂包 .prompt.md → 用户/Claude 读后写正文 → catch.py --send-only 发邮件", "重度对话方用户（不接 LLM API）"],
      ["全自动（--auto）", "catch.py --auto 直接调用 LLM API 写正文", "已购 OpenAI / Anthropic API 的用户"],
      ["纯手动", "catch.py 出 .prompt.md → 自己粘到 ChatGPT 网页版手动写", "完全不想配置 API 的用户"],
    ],
    [1700, 4500, 3160],
  ),

  h2("2.3 五层降级策略（核心智能）"),
  p("不同平台的反爬程度、字幕完整度、网络可达性各异。v0.8.0 的抓取层会按下列顺序自动降级："),
  numbered("✅ 平台原生字幕 / show notes（YouTube CC、播客 RSS description）—— 最快，无需 LLM"),
  numbered("✅ 音频下载 + Whisper 本地转写（B 站、苹果播客）—— 慢但准"),
  numbered("✅ HTML 全文提取（trafilatura，适合小红书 / 公众号）"),
  numbered("✅ 元信息 fallback（标题 + 简介 + 章节 timestamps）—— 即使字幕全无也有产出"),
  numbered("✅ YouTube fetcher chain（v0.7.3+）：原生 → UULF playlist → RSSHub/Invidious 代理"),

  h2("2.4 平台覆盖"),
  tbl(
    ["平台", "抓取方式", "v0.8.0 状态"],
    [
      ["B 站", "yt-dlp + chrome cookies → 音频 → Whisper", "✅ 稳定"],
      ["YouTube", "videos.xml RSS + fetcher chain（v0.7.3+）", "✅ 多级 fallback"],
      ["苹果播客 / 小宇宙", "RSS show notes + 音频 Whisper", "✅ 稳定"],
      ["Substack / Megaphone 等 RSS", "feedparser + 全文 description", "✅ 稳定"],
      ["小红书", "trafilatura HTML 提取", "⚠️ 需登录 cookies"],
      ["微信公众号", "RSSHub 代理", "⚠️ 实例可用性飘忽"],
    ],
    [1700, 4500, 3160],
  ),
);

// === 3. 技术架构 ===
children.push(
  h1("三、技术架构"),

  h2("3.1 四层架构图"),
  p("项目按从下到上的四层来组织："),
  codeBlock([
    "┌────────────────────────────────────────────────────────────┐",
    "│  Layer 4：Newsletter 系统                                   │",
    "│  catch.py --subscribe / --finalize-epub / --send-only       │",
    "│  → subscribe.py / digest.py / email_sender.py / export_epub │",
    "├────────────────────────────────────────────────────────────┤",
    "│  Layer 3：CLI 入口                                          │",
    "│  catch.py（单条 / 批量 / 订阅 / 直发 三合一入口）             │",
    "├────────────────────────────────────────────────────────────┤",
    "│  Layer 2：抓取与转写层                                       │",
    "│  fetch_subtitle / download_audio / transcribe_whisper /     │",
    "│  fetch_show_notes / fetch_html / get_metadata               │",
    "├────────────────────────────────────────────────────────────┤",
    "│  Layer 1：基础设施                                          │",
    "│  Python venv / yt-dlp / faster-whisper / trafilatura /      │",
    "│  ebooklib / feedparser / markdown / PyYAML                  │",
    "└────────────────────────────────────────────────────────────┘",
  ]),

  h2("3.2 关键模块"),
  tbl(
    ["模块", "职责", "依赖"],
    [
      ["catch.py", "主入口 CLI，所有功能从这里调用", "—"],
      ["scripts/_bin.py", "v0.8.0 新增：统一查找 yt-dlp 等二进制", "—"],
      ["scripts/subscribe.py", "订阅扫描，含 v0.7.3 YouTube fetcher chain", "feedparser"],
      ["scripts/digest.py", "周报组装 + EPUB 章节查找", "—"],
      ["scripts/download_audio.py", "yt-dlp 下载音频（仅音轨）", "yt-dlp"],
      ["scripts/transcribe_whisper.py", "本地 Whisper 转写", "faster-whisper"],
      ["scripts/fetch_subtitle.py", "yt-dlp 拉平台原生字幕", "yt-dlp"],
      ["scripts/fetch_show_notes.py", "RSS / 网页抓 show notes", "feedparser / trafilatura"],
      ["scripts/email_sender.py", "v0.7.1 修了中文编码 bug", "smtplib"],
      ["scripts/export_epub.py", "Markdown → EPUB（ebooklib）", "ebooklib / lxml"],
      ["scripts/build_manual_docx.py", "v0.8.0 新增：项目说明 docx 生成", "docx-js（node）"],
    ],
    [3200, 4400, 1760],
  ),

  h2("3.3 Prompt 模板（核心壁垒）"),
  p("每种笔记风格都对应 prompts/ 目录下的一份模板。LLM 看到投喂包后按对应模板生成正文。"),
  bullet("prompts/note-standard.md：标准笔记模板（默认）"),
  bullet("prompts/note-premium.md：精装版长文模板（5000-15000 字深度）"),
  bullet("prompts/note-bilingual.md：中英双语模板"),
  bullet("prompts/note-xhs.md：小红书风格（碎片化、口语化）"),
  bullet("templates/chapter_polished.md：v0.7.2+ 新增的「代笔单章」模板，写给 EPUB 章节用"),

  warn("v0.7.2 重要变更：EPUB 章节不再塞投喂包（含 LLM 任务说明 + Whisper 原文），改为按 chapter-<slug>.md → output/final/<slug>/笔记.md → 占位章节 三级查找。"),
);

// === 4. 五大场景使用指南 ===
children.push(
  h1("四、五大场景使用指南"),

  h2("场景 1：单条音视频转笔记（最常用）"),
  p("用户案例：刚看到一个 1 小时的 B 站访谈，想 5 分钟内消化主要观点。"),
  h4("命令"),
  codeBlock([
    "# 标准笔记（默认）",
    "catch.py 'https://www.bilibili.com/video/BV1xxxxxxxx' --cookies-from chrome",
    "",
    "# 精装版长文（适合干货密度高的内容）",
    "catch.py 'https://...' --cookies-from chrome --premium",
    "",
    "# 双语版（适合英文播客 / YouTube）",
    "catch.py 'https://...' --bilingual",
  ]),
  h4("产物位置"),
  codeBlock([
    "output/notes/<视频标题>.md           ← 投喂包（送给 LLM 蒸馏的输入）",
    "output/bundles/<视频标题>.prompt.md  ← 等同上，仅命名约定",
    "output/audio/<视频标题>.m4a          ← 下载的音频缓存",
  ]),
  h4("流程"),
  numbered("yt-dlp 拉视频元信息（标题、时长、作者、章节）"),
  numbered("尝试拉平台原生字幕；失败则下载音频 → Whisper 转写"),
  numbered("生成投喂包 .prompt.md（含元信息 + 任务说明 + 原文字幕）"),
  numbered("如果加了 --auto + 有 LLM API：直接调 API 写正文输出 .md"),
  numbered("如果走对话方代笔：把 .prompt.md 内容发给 Claude，让它按 prompts/ 模板写"),

  h2("场景 2：精装版长文"),
  p("用户案例：Latent Space 一期 Daytona 访谈，原文 9 万字、8 个 chapter，想要写成 1.5 万字深度长文。"),
  codeBlock([
    "catch.py 'https://lex.fridman.com/daytona' --premium",
    "→ output/notes/Daytona-Vibe-Coding.md（投喂包）",
    "→ Claude 按 prompts/note-premium.md 模板写 → 5000-15000 字成品",
    "→ 用户把成品挪到 output/final/<slug>/笔记.md",
    "→ 下次跑订阅周报时 build_epub_if_many 会自动捡起来当章节",
  ]),

  h2("场景 3：完整版（不删减）"),
  p("用户案例：技术访谈，每一句都可能是关键信息，需要保留完整原文。"),
  codeBlock([
    "catch.py 'https://...' --full",
    "→ 不做摘要 / 删减，输出完整字幕分段 + 时间码",
    "→ 适合做长期可检索素材库",
  ]),

  h2("场景 4：批量 + 跨平台对比（竞品分析神器）"),
  p("用户案例：做 AI Coding 产品研究，想一次抓 10 个 KOL 对 Cursor / Claude Code / Windsurf 的评测。"),
  codeBlock([
    "# 创建 urls.txt，一行一个链接",
    "cat > urls.txt <<EOF",
    "https://www.bilibili.com/video/BV111...  # 大牙大- 评测 Cursor",
    "https://www.youtube.com/watch?v=...      # AI Engineer 演示 Claude Code",
    "https://feeds.megaphone.fm/nopriors/...  # No Priors 聊 Coding Agent",
    "EOF",
    "",
    "catch.py --batch urls.txt --premium",
    "→ output/batch/<时间戳>/index.md          ← 一本可检索目录",
    "→ output/batch/<时间戳>/<title>.prompt.md ← 每条投喂包",
    "→ output/batch/<时间戳>/对比.prompt.md    ← 跨平台对比专用 prompt",
  ]),

  h2("场景 5：订阅周报（终极闭环）"),
  p("用户案例：固定订阅 6 个频道（3 B 站 + 3 中英播客），每周一收到一封带 EPUB 附件的优美 Newsletter。"),
  h4("4 步工作流（v0.7.2+ 推荐）"),
  numbered("Step 1：catch.py --subscribe channels.yaml —— 抓取本周 7 天新内容，出投喂包 + 占位 EPUB"),
  numbered("Step 2：Claude 读投喂包，写代笔单章 → output/digest/<本期>/chapter-<slug>.md"),
  numbered("Step 3：catch.py --subscribe channels.yaml --finalize-epub <本期> —— 用代笔单章重做 EPUB"),
  numbered("Step 4：catch.py --subscribe channels.yaml --send-only <本期> —— 发邮件（EPUB 自动作为附件）"),

  h4("跟 Claude 的标准触发短语"),
  quote("「按 skill 流程跑本周 content-catcher 订阅，重要的几条帮我代笔」"),
  p("Claude 看到这句话会自动跑完 4 步，你只需要等邮件到。"),

  h4("EPUB 章节查找优先级（v0.7.2+）"),
  numbered("①  output/digest/<本期>/chapter-<slug>.md —— 本期临时代笔（首选）"),
  numbered("②  output/final/<slug>/笔记.md —— 长期收藏的精装版（自动捡）"),
  numbered("③  占位章节 —— 只放标题 + 链接 + 「该集尚未代笔」提示（绝不再塞投喂包原文）"),
);

// === 5. 部署步骤（详细版）===
children.push(
  h1("五、部署步骤（详细版）"),

  h2("5.1 系统兼容性"),
  tbl(
    ["平台", "兼容度", "备注"],
    [
      ["macOS（Apple Silicon / Intel）", "★★★★★", "首要支持平台，install.sh 默认走 macOS 路径"],
      ["Linux（Ubuntu / Debian）", "★★★★☆", "需自己装 ffmpeg；其他完全通用"],
      ["Windows", "★★★☆☆", "WSL2 推荐；原生 Windows 需用 install.bat（计划中）"],
      ["Python 版本", "≥ 3.10", "已用 pyproject.toml 强制约束"],
      ["磁盘空间", "≥ 5 GB", "Whisper tiny 模型 ~75MB；base ~150MB；缓存音频按需"],
      ["网络", "需访问 youtube.com / bilibili.com", "国内可访问 B 站 / 小宇宙；YouTube 需代理"],
    ],
    [3200, 1400, 4760],
  ),

  h2("5.2 macOS 一键部署（v0.8.0 推荐路径）"),
  p("v0.8.0 全新的 install.sh 把以下 10 步全部封装："),
  codeBlock([
    "git clone https://github.com/zczxd1118/content-catcher.git",
    "cd content-catcher",
    "./install.sh",
    "source .venv/bin/activate",
  ]),
  p("install.sh 内部做了什么："),
  numbered("检查 Python 3.10+ 是否可用"),
  numbered("检查 ffmpeg；缺则提示 brew install ffmpeg"),
  numbered("在 ./.venv/ 建独立 venv"),
  numbered("pip install -r requirements.txt（yt-dlp / faster-whisper / trafilatura / ebooklib 等）"),
  numbered("如果不存在则 cp channels.example.yaml → channels.yaml"),
  numbered("如果不存在则建空 .smtp_secret + 提示填密码"),
  numbered("跑 python -c \"import faster_whisper; ...\" 烟雾测试"),
  numbered("打印 next steps 给用户"),

  h2("5.3 Whisper 模型说明"),
  p("v0.8.0 不再强制要求手动下载——首次跑 catch.py 时 faster-whisper 会自动下载所需模型。"),
  tbl(
    ["模型", "大小", "速度", "中文质量", "用途"],
    [
      ["tiny", "75 MB", "极快", "★★☆☆☆", "默认；订阅扫描批量转写"],
      ["base", "150 MB", "快", "★★★☆☆", "希望略提升中文质量时"],
      ["small", "490 MB", "中", "★★★★☆", "精装版单条整理推荐"],
      ["medium", "1.5 GB", "慢", "★★★★★", "高质量、不在乎时间"],
    ],
    [1200, 1400, 1400, 1700, 3660],
  ),
  p("切换模型：编辑 channels.yaml 的 defaults.whisper_model 或者命令行加 --whisper-model small"),

  h2("5.4 验证部署"),
  codeBlock([
    "# 1. CLI 起得来",
    "catch.py --help",
    "",
    "# 2. 跑回归测试",
    "python tests/test_email_sender_unicode.py",
    "python tests/test_export_epub.py",
    "python tests/test_build_epub_polished.py",
    "python tests/test_youtube_fetcher_chain.py",
    "",
    "# 3. 跑一条真实链接（B 站需要 chrome cookies）",
    "catch.py 'https://www.bilibili.com/video/BV1xxxxxx' --cookies-from chrome",
  ]),

  h2("5.5 配置邮件发送（QQ 邮箱示例）"),
  numbered("登录 QQ 邮箱 web 端 → 设置 → 账户 → 开启 IMAP/SMTP 服务"),
  numbered("发短信生成 16 位授权码"),
  numbered("把授权码写入 .smtp_secret："),
  codeBlock([
    "# .smtp_secret（已在 .gitignore，不会被推到 GitHub）",
    "SMTP_PASS=你的16位授权码",
  ]),
  numbered("修改 channels.yaml 顶部 newsletter.email_to / email_from / smtp 字段"),
  numbered("跑发件测试：catch.py --subscribe channels.yaml --send-only <已有 digest 目录>"),

  warn("不要用 export SMTP_PASS=\"$(cat .smtp_secret)\" 整段塞环境变量——会把注释行也当 token 用，登录失败。让脚本自己读 .smtp_secret 即可。"),
);

// === 6. 跨电脑迁移 ===
children.push(
  h1("六、复用到其他 AI / 其他电脑"),

  h2("6.1 给其他 AI 用（让它帮你部署）"),
  p("v0.8.0 的 SKILL.md + docs/MANUAL.md + docs/SUBSCRIPTION_GUIDE.md 三份文档对所有 LLM 友好。把项目目录给 Claude / GPT，它能自己读完文档并开始执行。"),
  codeBlock([
    "# 给 Claude 看的最小上下文（复制粘贴即可）",
    "我有一个叫 content-catcher 的项目，主要功能：",
    "1. 单条音视频转笔记：catch.py <url>",
    "2. 订阅周报：catch.py --subscribe channels.yaml",
    "请读 ./SKILL.md 和 ./docs/MANUAL.md 了解细节。",
    "",
    "现在我想 [具体任务]，请按 skill 流程帮我跑。",
  ]),

  h2("6.2 跨电脑迁移"),
  h4("方式 A：通过 GitHub（推荐）"),
  numbered("旧电脑：git push 所有改动（注意 .smtp_secret / channels.yaml 已 gitignore，不会上去）"),
  numbered("新电脑：git clone https://github.com/zczxd1118/content-catcher.git"),
  numbered("新电脑：./install.sh 一键装齐"),
  numbered("把旧电脑的 channels.yaml + .smtp_secret 通过 iCloud / 安全方式拷过来"),

  h4("方式 B：tar 包整体备份"),
  codeBlock([
    "# 在旧电脑打包（含 output 历史缓存）",
    "tar -czvf content-catcher-backup.tar.gz \\",
    "  --exclude='.venv' --exclude='__pycache__' \\",
    "  ~/.workbuddy/skills/content-catcher",
    "",
    "# 新电脑解压后",
    "cd content-catcher && ./install.sh",
  ]),

  h2("6.3 最佳实践：用 Git + 私人配置覆盖"),
  bullet("公开源码 → push 到 GitHub（任何人可 clone）"),
  bullet("私人订阅清单 channels.yaml → 仅本地（已 gitignore）"),
  bullet("个人偏好（不接 LLM API / Claude 代笔等）→ 放 LOCAL_NOTES.md（已 gitignore）"),
  bullet("SMTP 密码 → .smtp_secret（已 gitignore）"),
  quote("这套分层方案让 v0.8.0 真正做到「开源 + 个人化共存」——其他人 clone 你的 repo 看不到任何隐私信息，自己 install.sh 后立刻能用。"),
);

// === 7. FAQ ===
children.push(
  h1("七、常见问题（FAQ）"),

  h3("Q1. install.sh 报「找不到 ffmpeg」怎么办？"),
  p("macOS 执行：brew install ffmpeg；Linux 执行：sudo apt install ffmpeg。这是 yt-dlp / Whisper 的依赖。"),

  h3("Q2. 跑 B 站 URL 报「需要登录」怎么办？"),
  p("加 --cookies-from chrome（或 firefox / safari），yt-dlp 会自动从浏览器读 cookies。注意 macOS 上首次会弹窗要钥匙串访问权限。"),

  h3("Q3. YouTube 源订阅扫到 0 条？"),
  bulletRich(
    "v0.7.3+ 已加 fetcher chain（原生 + 重试 → UULF playlist → RSSHub/Invidious 代理），多数情况会 fallback 到结果",
  ),
  bulletRich("看日志最后一行 ", { text: "❌ 所有 YouTube fetcher 全部失败", bold: true, font: FONT_MONO }, " 说明所有路径都被网络挡了"),
  bulletRich("浏览器打开 ", { text: "https://www.youtube.com/feeds/videos.xml?channel_id=<UC...>", font: FONT_MONO }, " 直接看是不是 YouTube 端临时维护"),

  h3("Q4. 邮件发送报「'ascii' codec can't encode characters」？"),
  p("v0.7.1+ 已修。如果你跑了旧版，pip install --upgrade 或者 git pull 拿新版即可。代码修复是给 EmailMessage 加 policy=SMTP_POLICY + set_content/add_alternative 加 charset=\"utf-8\"。"),

  h3("Q5. EPUB 里看到的全是字幕原文 + 「请你做...」，不是优美文章？"),
  p("v0.7.2+ 已修。新流程要求你写代笔单章 chapter-<slug>.md 放进 digest 目录，然后跑 --finalize-epub 重做 EPUB。详见第四章场景 5。"),

  h3("Q6. Whisper 转写中文时把专有名词音译错了（vibe coding → 「扣的」）？"),
  bullet("升级到 small 或 medium 模型：catch.py <url> --whisper-model small"),
  bullet("如果是订阅扫描，编辑 channels.yaml 的 defaults.whisper_model: small"),
  bullet("代笔阶段对照术语表手工还原（VS Code / Claude Code / Plan Mode / Xcode / token 等）"),

  h3("Q7. 跑订阅扫描时长内容（≥10 分钟视频）的 Whisper 转写会卡？"),
  bullet("默认 WorkBuddy / 命令行环境对前台任务有 2 分钟硬限"),
  bullet("用 nohup 真正脱离会话："),
  code("nohup catch.py --subscribe channels.yaml > /tmp/curio.log 2>&1 & disown"),
  bullet("再 tail -f /tmp/curio.log 看进度"),

  h3("Q8. 想完全自动化（每周一中午自动跑+发邮件），怎么搞？"),
  bullet("macOS launchd 或 cron 都能调度（写 plist / crontab）"),
  bullet("但要求那个时刻电脑开机且 catch.py --subscribe ... --send-email 跑完才能寄出邮件"),
  bullet("如果走「Claude 代笔」路线，automation 只能跑到出投喂包+占位 EPUB；剩下的代笔 + finalize-epub + send-only 仍需用户介入"),

  h3("Q9. 旧版（v0.7.0）能直接升级到 v0.8.0 吗？"),
  codeBlock([
    "cd content-catcher",
    "git pull",
    "./install.sh    # 或 pip install -r requirements.txt --upgrade",
  ]),
  p("不破坏现有数据 —— channels.yaml / .smtp_secret / output/ 全部保留。"),

  h3("Q10. 我能给其他人用这个项目吗？"),
  bullet("可以。MIT 协议，随便 fork / 二次开发 / 商用"),
  bullet("注意：项目里 channels.yaml / .smtp_secret 是 gitignore 的，别人 clone 你的 repo 看不到你的隐私订阅清单和邮箱密码"),
  bullet("如果发现 bug，欢迎提 issue / PR 到 https://github.com/zczxd1118/content-catcher"),
);

// === 8. 目录结构 ===
children.push(
  h1("八、目录结构"),

  p("v0.8.0 完整目录树（按重要性排序）："),
  codeBlock([
    "content-catcher/",
    "├── catch.py                    # 主入口 CLI（单条 / 批量 / 订阅 / 直发）",
    "├── install.sh                  # v0.8.0 新增：一键安装",
    "├── pyproject.toml              # v0.8.0 新增：可 pip install 的包配置",
    "├── requirements.txt            # v0.8.0 新增：依赖清单",
    "├── channels.example.yaml       # 订阅源样例（可拷贝改成 channels.yaml）",
    "├── README.md                   # 项目首页（带 5 分钟 quickstart）",
    "├── SKILL.md                    # 给 Claude/对话方读的工作指引",
    "├── CHANGELOG.md                # v0.8.0 新增：版本变更记录",
    "├── LICENSE                     # MIT",
    "│",
    "├── scripts/                    # 核心模块",
    "│   ├── _bin.py                 # v0.8.0：统一查 yt-dlp 等二进制",
    "│   ├── catch.py 各种子模块...",
    "│   ├── subscribe.py            # v0.7.3：YouTube fetcher chain",
    "│   ├── digest.py               # v0.7.2：build_epub_if_many 重构",
    "│   ├── email_sender.py         # v0.7.1：中文编码修复",
    "│   ├── export_epub.py          # ebooklib EPUB 生成",
    "│   ├── build_manual_docx.py    # v0.8.0：项目说明 docx 生成",
    "│   └── build_manual_docx.js    # v0.8.0：上面的 docx-js 实现",
    "│",
    "├── prompts/                    # 给 LLM 看的 prompt 模板",
    "│   ├── note-standard.md",
    "│   ├── note-premium.md",
    "│   ├── note-bilingual.md",
    "│   └── note-xhs.md",
    "│",
    "├── templates/                  # v0.7.2+ 新增",
    "│   └── chapter_polished.md     # 代笔单章模板",
    "│",
    "├── docs/                       # v0.7.3+ 完整文档",
    "│   ├── MANUAL.md               # 10 章手册",
    "│   └── SUBSCRIPTION_GUIDE.md   # 订阅源管理详解",
    "│",
    "├── tests/                      # v0.7.1+ 回归测试套件",
    "│   ├── test_email_sender_unicode.py",
    "│   ├── test_export_epub.py",
    "│   ├── test_build_epub_polished.py",
    "│   └── test_youtube_fetcher_chain.py",
    "│",
    "├── channels.yaml               # ⚠️ gitignored：你的私人订阅清单",
    "├── .smtp_secret                # ⚠️ gitignored：你的 SMTP 密码",
    "├── LOCAL_NOTES.md              # ⚠️ gitignored：本地偏好",
    "│",
    "└── output/                     # ⚠️ gitignored：所有产物",
    "    ├── notes/                  # 单条整理的笔记",
    "    ├── bundles/                # 投喂包 .prompt.md",
    "    ├── audio/                  # 下载的音频缓存",
    "    ├── digest/                 # 周报目录（weekly-YYYY-WXX-...）",
    "    ├── final/                  # 长期收藏的精装版（EPUB 自动捡）",
    "    ├── batch/                  # 批量任务产物",
    "    ├── epub/                   # EPUB 临时输出",
    "    └── manual/                 # docx 说明书输出",
  ]),
);

// === 9. 路线图 ===
children.push(
  h1("九、路线图"),

  h2("9.1 已完成（v0.8.0）"),
  bullet("✅ v0.7.1 - 邮件中文编码修复（'ascii' codec can't encode）"),
  bullet("✅ v0.7.1 - .gitignore LOCAL_NOTES.md 个人偏好不污染 repo"),
  bullet("✅ v0.7.1 - --send-only flag + smart body fallback（M5.1）"),
  bullet("✅ v0.7.1 - tests/test_email_sender_unicode.py + tests/test_export_epub.py 回归测试"),
  bullet("✅ v0.7.2 - EPUB 重构：只塞代笔成品，绝不再塞投喂包"),
  bullet("✅ v0.7.2 - --finalize-epub + --epub-threshold + chapter 模板"),
  bullet("✅ v0.7.2 - docs/SUBSCRIPTION_GUIDE.md 完整订阅管理文档"),
  bullet("✅ v0.7.3 - YouTube fetcher chain（原生 + 重试 → UULF playlist → 第三方代理）"),
  bullet("✅ v0.8.0 - 一键安装 install.sh + pyproject.toml + requirements.txt"),
  bullet("✅ v0.8.0 - scripts/_bin.py 修复硬编码 yt-dlp 路径（阻塞 release 的 P0 bug）"),
  bullet("✅ v0.8.0 - docs/MANUAL.md 10 章完整用户手册"),
  bullet("✅ v0.8.0 - 项目说明书 docx 生成器（本文档）"),
  bullet("✅ v0.8.0 - 发布 GitHub Release（sdist + wheel + docx 三个 asset）"),

  h2("9.2 短期（v0.8.x）"),
  bullet("⏳ 自动定时跑订阅（automation 调度 + 占位 EPUB 邮件）"),
  bullet("⏳ Windows 一键安装 install.bat"),
  bullet("⏳ Whisper 模型自动按需切换（短视频 tiny / 长视频 small）"),
  bullet("⏳ EPUB 自动加封面图（封面 = 周次 + 章节数 + 来源 logo）"),

  h2("9.3 中期（v0.9.x）"),
  bullet("⏳ 多语言 prompt 模板（增加日语 / 韩语 / 西语）"),
  bullet("⏳ Webhook 推送（除了邮件，也能推到 Telegram / Discord / 钉钉）"),
  bullet("⏳ 公众号自动抓（用 RSSHub 实例池 + 自动切换）"),
  bullet("⏳ 跨周报智能聚合（如果同一话题连续 N 周出现，自动生成专题）"),

  h2("9.4 长期（v1.0+）"),
  bullet("🔮 桌面 GUI（让非技术用户也能用）"),
  bullet("🔮 知识图谱可视化（你订阅了 N 个频道、产出了 M 篇笔记，可以看主题分布）"),
  bullet("🔮 团队 / 多人订阅（同一个订阅源，多个收件人不同模板）"),
);

// === 10. 附录 ===
children.push(
  h1("十、附录"),

  h2("10.1 命令行参数全集"),
  tbl(
    ["参数", "类型", "说明"],
    [
      ["<url>", "位置参数", "单条音视频/图文链接（B 站 / YouTube / 播客 / 小红书等）"],
      ["--batch <file>", "字符串", "批量模式；file 是一行一个 URL 的文本文件"],
      ["--subscribe <yaml>", "字符串", "订阅模式；yaml 是订阅源配置（默认 channels.yaml）"],
      ["--send-only <digest-dir>", "字符串", "v0.7.1+ 跳过抓取，直接把 digest 目录里 weekly-digest.md 发邮件"],
      ["--finalize-epub <digest-dir>", "字符串", "v0.7.2+ 用代笔 chapter-*.md 重做 EPUB"],
      ["--epub-threshold <N>", "整数", "v0.7.2+ EPUB 自动触发的最低条数（默认 5）"],
      ["--days <N>", "整数", "订阅时间窗（默认 7）"],
      ["--auto", "flag", "调 LLM API 自动写正文（需配 OPENAI_API_KEY 或 ANTHROPIC_API_KEY）"],
      ["--send-email", "flag", "扫完后直接发邮件（搭配 --subscribe）"],
      ["--premium", "flag", "精装版长文模板"],
      ["--bilingual", "flag", "中英双语模板"],
      ["--full", "flag", "完整版（不删减）"],
      ["--cookies-from <browser>", "字符串", "yt-dlp 用哪个浏览器的 cookies（chrome / firefox / safari）"],
      ["--whisper-model <name>", "字符串", "tiny / base / small / medium（默认 tiny）"],
      ["--help", "flag", "看所有参数"],
    ],
    [2600, 1100, 5660],
  ),

  h2("10.2 关键路径速查"),
  tbl(
    ["类别", "路径"],
    [
      ["项目根目录", "~/.workbuddy/skills/content-catcher/"],
      ["venv", "<项目根>/.venv/"],
      ["私人订阅清单", "<项目根>/channels.yaml（gitignored）"],
      ["SMTP 密码", "<项目根>/.smtp_secret（gitignored）"],
      ["本地偏好", "<项目根>/LOCAL_NOTES.md（gitignored）"],
      ["所有产物", "<项目根>/output/（gitignored）"],
      ["GitHub repo", "https://github.com/zczxd1118/content-catcher"],
      ["GitHub Release", "https://github.com/zczxd1118/content-catcher/releases/tag/v0.8.0"],
    ],
    [2400, 6960],
  ),

  h2("10.3 给面试官 / HR 的项目讲解（90 秒版）"),
  quote("content-catcher 是我自己做的一个本地优先的「信息蒸馏 + Newsletter」基础设施。一开始是为了解决「信息源太多看不过来」的个人痛点，写了大概 1500 行 Python，整合了 yt-dlp、faster-whisper、ebooklib、feedparser 等开源库，把 B 站 / YouTube / 播客 / 小红书等多平台内容统一变成可读笔记。"),
  quote("项目最大的特点是「人机协作」的设计——我没买任何 LLM API，所有 LLM 写正文的步骤都是输出投喂包 .prompt.md，由 Claude / GPT 在对话里完成，再用脚本组装成最终周报和 EPUB 电子书发邮件。这种设计让任何对话方都能复用，也避免了 API 成本。"),
  quote("v0.8.0 是首个真正可分发的 release，含一键安装脚本、完整文档、4 套回归测试，从 git clone 到能跑只要 5 分钟。中间踩过的坑——SMTP 中文编码 bug、EPUB 章节误塞 LLM 输入、YouTube RSS 间歇性 404——也都在 GitHub Issues 和 CHANGELOG 里有完整记录。"),

  h2("10.4 致谢"),
  bullet("yt-dlp / faster-whisper / trafilatura / ebooklib / feedparser / docx-js 等开源项目"),
  bullet("对话方 Claude（WorkBuddy / Anthropic）在多次重构、bug 排查和文档撰写中的协助"),
  bullet("所有提 Issue 和 PR 的潜在贡献者"),

  h2("10.5 反馈 / 联系"),
  link("GitHub Issues：https://github.com/zczxd1118/content-catcher/issues", "https://github.com/zczxd1118/content-catcher/issues"),
  link("GitHub Discussions：https://github.com/zczxd1118/content-catcher/discussions", "https://github.com/zczxd1118/content-catcher/discussions"),
  p(""),
  p(""),
  pRich(
    { text: "© 2026 周小丁  ·  ", color: COLOR_MUTED },
    { text: "MIT License", bold: true, color: COLOR_PRIMARY },
    { text: "  ·  v0.8.0 · 2026-06-02", color: COLOR_MUTED },
  ),
);

// ─── 文档组装 ──────────────────────────────────────────
const doc = new Document({
  creator: "content-catcher",
  title: "content-catcher v0.8.0 项目说明书",
  description: "完整的项目说明书：概览、功能、架构、使用场景、部署、迁移、FAQ、目录结构、路线图、附录",
  styles: {
    default: {
      document: { run: { font: FONT_CN, size: 22 } },
    },
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0,
          format: LevelFormat.BULLET,
          text: "•",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 360, hanging: 240 } } },
        }],
      },
      {
        reference: "numbers",
        levels: [{
          level: 0,
          format: LevelFormat.DECIMAL,
          text: "%1.",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 420, hanging: 280 } } },
        }],
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 },
      },
    },
    // codeBlock() 返回 Paragraph[]，要 flatten 避免 docx-js 输出 <0/> 之类的乱标签
    headers: {
      default: new Header({
        children: [new Paragraph({
          children: [
            new TextRun({ text: "content-catcher v0.8.0 项目说明书", font: FONT_CN, size: 18, color: COLOR_MUTED }),
            new TextRun({ text: "\thttps://github.com/zczxd1118/content-catcher", font: FONT_MONO, size: 16, color: COLOR_MUTED }),
          ],
          tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "第 ", font: FONT_CN, size: 18, color: COLOR_MUTED }),
            new TextRun({ children: [PageNumber.CURRENT], font: FONT_EN, size: 18, color: COLOR_MUTED }),
            new TextRun({ text: " 页 / 共 ", font: FONT_CN, size: 18, color: COLOR_MUTED }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT_EN, size: 18, color: COLOR_MUTED }),
            new TextRun({ text: " 页", font: FONT_CN, size: 18, color: COLOR_MUTED }),
          ],
        })],
      }),
    },
    children: children.flat(Infinity),
  }],
});

// ─── 输出 ────────────────────────────────────────────
const outPath = process.argv[2] || "/Users/zoezczhou/.workbuddy/skills/content-catcher/output/manual/content-catcher-v0.8.0-项目说明书.docx";
fs.mkdirSync(path.dirname(outPath), { recursive: true });

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  const kb = (buf.length / 1024).toFixed(1);
  console.log(`✅ 生成成功：${outPath}`);
  console.log(`   大小：${kb} KB · 章节：10 · 段落：${children.length}`);
}).catch(err => {
  console.error("❌ 生成失败：", err);
  process.exit(1);
});
