/**
 * 生成 content-catcher v0.8.0 项目说明文档 docx
 * 中文友好（PingFang SC / 微软雅黑 fallback），含封面、目录、表格、分章节。
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
const FONT_CN = "PingFang SC"; // macOS 默认中文字体；Win 上 fallback 到雅黑
const FONT_EN = "Helvetica Neue";
const FONT_MONO = "Menlo";

const COLOR_PRIMARY = "0071e3";   // Apple blue
const COLOR_TEXT = "1d1d1f";
const COLOR_MUTED = "6e6e73";
const COLOR_TABLE_HEAD = "E8F1FC";
const COLOR_BORDER = "DDDDDD";
const COLOR_CODE_BG = "F5F5F7";

const border = { style: BorderStyle.SINGLE, size: 4, color: COLOR_BORDER };
const allBorders = { top: border, bottom: border, left: border, right: border };

// ─── 帮助函数 ──────────────────────────────────────────
const p = (text, opts = {}) => new Paragraph({
  children: [new TextRun({ text, font: FONT_CN, color: COLOR_TEXT, size: 22, ...opts })],
  spacing: { before: 80, after: 80, line: 360 },
  ...(opts._para || {}),
});

const h1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  children: [new TextRun({ text, font: FONT_CN, bold: true, size: 36, color: COLOR_PRIMARY })],
  spacing: { before: 480, after: 240 },
  pageBreakBefore: true,
});

const h2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  children: [new TextRun({ text, font: FONT_CN, bold: true, size: 28, color: COLOR_TEXT })],
  spacing: { before: 360, after: 160 },
});

const h3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  children: [new TextRun({ text, font: FONT_CN, bold: true, size: 24, color: COLOR_TEXT })],
  spacing: { before: 280, after: 140 },
});

const bullet = (text, opts = {}) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  children: [new TextRun({ text, font: FONT_CN, color: COLOR_TEXT, size: 22, ...opts })],
  spacing: { before: 40, after: 40, line: 340 },
});

const numbered = (text, opts = {}) => new Paragraph({
  numbering: { reference: "numbers", level: 0 },
  children: [new TextRun({ text, font: FONT_CN, color: COLOR_TEXT, size: 22, ...opts })],
  spacing: { before: 40, after: 40, line: 340 },
});

const code = (text) => new Paragraph({
  children: [new TextRun({ text, font: FONT_MONO, size: 20, color: COLOR_TEXT })],
  spacing: { before: 40, after: 40, line: 280 },
  shading: { type: ShadingType.CLEAR, fill: COLOR_CODE_BG, color: "auto" },
  border: {
    top:    { style: BorderStyle.SINGLE, size: 1, color: COLOR_BORDER, space: 4 },
    bottom: { style: BorderStyle.SINGLE, size: 1, color: COLOR_BORDER, space: 4 },
    left:   { style: BorderStyle.SINGLE, size: 1, color: COLOR_BORDER, space: 4 },
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

// 引言用浅底色 + 左缩进表达，避免 docx-js 生成 <w:pBdr> 时把 left 写在 bottom 之后导致 schema 不合规
const quote = (text) => new Paragraph({
  children: [new TextRun({ text, font: FONT_CN, size: 22, color: COLOR_MUTED, italics: true })],
  spacing: { before: 120, after: 120, line: 340 },
  indent: { left: 720, right: 360 },
  shading: { type: ShadingType.CLEAR, fill: "F0F7FF", color: "auto" },
});

const cell = (text, opts = {}) => {
  const isHeader = opts.head;
  return new TableCell({
    borders: allBorders,
    width: { size: opts.width || 4680, type: WidthType.DXA },
    shading: isHeader ? { type: ShadingType.CLEAR, fill: COLOR_TABLE_HEAD, color: "auto" } : undefined,
    margins: { top: 80, bottom: 80, left: 140, right: 140 },
    children: [new Paragraph({
      children: [new TextRun({
        text, font: FONT_CN, size: 20, color: COLOR_TEXT,
        bold: isHeader || opts.bold,
      })],
      spacing: { before: 0, after: 0 },
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
    children: [new TextRun({ text: "项目说明文档", font: FONT_CN, size: 36, color: COLOR_TEXT })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 80 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Personal Information Distillery + Newsletter Engine", font: FONT_EN, italics: true, size: 24, color: COLOR_MUTED })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 1200 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "v0.8.0", font: FONT_EN, bold: true, size: 32, color: COLOR_PRIMARY })],
    alignment: AlignmentType.CENTER,
  }),
  new Paragraph({
    children: [new TextRun({ text: "2026 年 6 月 2 日", font: FONT_CN, size: 22, color: COLOR_MUTED })],
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
    children: [new TextRun({ text: "目录", font: FONT_CN, bold: true, size: 36, color: COLOR_PRIMARY })],
    pageBreakBefore: true,
    spacing: { after: 240 },
  }),
  new TableOfContents("Table of Contents", {
    hyperlink: true,
    headingStyleRange: "1-3",
  }),
);

// === 第 1 章：项目概述 ===
children.push(
  h1("1. 项目概述"),

  h2("1.1 一句话定义"),
  p("content-catcher 是一个本地优先的「信息蒸馏 + Newsletter」基础设施——把任何长内容（音视频 / 图文 / 播客）变成可读的结构化笔记，既可以单条按需调用，也可以订阅式自动推送到邮箱。"),

  h2("1.2 它的形态"),
  bullet("内容处理 CLI：一行命令拿到笔记（中文 / 英文 / 双语 / 小红书 / 精装等多种风格）"),
  bullet("Newsletter 引擎：订阅一批频道，每周自动扫近 7 天新内容、打包成 EPUB 电子书、邮件推送"),
  bullet("Agent 友好：所有 LLM 撰写步骤都是「投喂包 .prompt.md」形态，可以接 Claude / GPT 自动跑，也可以让对话方人工代笔"),
  bullet("本地优先：默认不上传任何内容到第三方 API；Whisper 转写跑在你电脑 CPU 上"),

  h2("1.3 它不是什么"),
  bullet("不是一个开了就 7×24 自动跑的服务（没有 daemon）"),
  bullet("不是万能 AI 摘要器——蒸馏层质量取决于你接的 LLM 或代笔人"),
  bullet("不是开箱即用的商业 Newsletter 平台——你是它的唯一作者也是唯一读者"),

  h2("1.4 适合谁用"),
  bullet("信息密度敏感，不想被算法推送的人"),
  bullet("愿意用对话方（Claude / GPT）做编辑判断而不是依赖通用模型自动摘要的人"),
  bullet("中文圈友好——抓取层完整覆盖 B 站 / 小宇宙 / 苹果播客 / 小红书"),
);

// === 第 2 章：整体架构 ===
children.push(
  h1("2. 整体架构"),

  h2("2.1 四层模型"),
  p("项目按从下到上的四层来组织：基础设施 → 抓取层 → CLI / Skill 形态 → Newsletter 系统。"),
  tbl(
    ["层级", "职责", "关键模块"],
    [
      ["Layer 4 · Newsletter", "订阅扫描 → 周报组装 → 邮件 / EPUB 推送", "subscribe.py / digest.py / email_sender.py / export_epub.py"],
      ["Layer 3 · CLI / Skill", "单条整理、批量、专题、跨平台对比", "catch.py / batch.py / build_prompt.py"],
      ["Layer 2 · 抓取层", "YouTube / B 站 / 播客 RSS / 小红书 + Whisper 转写", "detect_platform.py / fetch_subtitle.py / transcribe.py"],
      ["Layer 1 · 基础设施", "yt-dlp / faster-whisper / feedparser / EbookLib / smtplib", "_bin.py / cache.py"],
    ],
    [2400, 2960, 4000],
  ),

  h2("2.2 关键设计原则"),
  numbered("「投喂包」 (.prompt.md) 是统一中介——抓取层只负责出投喂包，蒸馏层可以是 LLM API、对话方 Claude、或人手写"),
  numbered("代笔成品和投喂包严格分离——EPUB 只装代笔成品 chapter-*.md，绝不装投喂包字幕原文"),
  numbered("用户的数据物理隔离：单条整理（output/notes/）和订阅周报（output/digest/）互不干扰"),
  numbered("失败优雅降级：YouTube fetcher / 邮件 / 转写每一步都有 fallback 路径"),
);

// === 第 3 章：快速开始 ===
children.push(
  h1("3. 快速开始（5 分钟）"),

  h2("3.1 前提"),
  bullet("macOS / Linux（Windows 未正式测试）"),
  bullet("Python 3.10+"),
  bullet("git"),
  bullet("约 3 GB 磁盘（其中大头是 faster-whisper 模型）"),

  h2("3.2 一键安装"),
  ...codeBlock([
    "git clone https://github.com/zczxd1118/content-catcher.git",
    "cd content-catcher",
    "./install.sh",
  ]),
  p("install.sh 会自动："),
  numbered("检查 Python 版本"),
  numbered("建 .venv/ 虚拟环境"),
  numbered("装所有依赖（requirements.txt）"),
  numbered("拷出 channels.yaml 和 .smtp_secret 占位文件"),
  numbered("跑 catch --help 和 EPUB 烟雾测试"),

  h2("3.3 跑第一条"),
  ...codeBlock([
    "source .venv/bin/activate",
    "catch.py https://www.bilibili.com/video/BV1xxxxxx --cookies-from chrome",
  ]),
  p("产出会在 output/notes/<标题>.md（结构化笔记）+ output/bundles/<标题>.prompt.md（投喂 LLM 用）。"),
);

// === 第 4 章：命令速查 ===
children.push(
  h1("4. 核心命令速查"),

  h2("4.1 单条 / 批量"),
  tbl(
    ["命令", "用途"],
    [
      ["catch.py <URL>", "整理单条"],
      ["catch.py <URL> --cookies-from chrome", "带浏览器 cookies（B 站常用）"],
      ["catch.py --batch urls.txt", "批量整理"],
      ["catch.py --batch urls.txt --mode topic --batch-name \"主题名\"", "批量做专题合集"],
      ["catch.py --batch urls.txt --mode compare", "批量做跨平台对比"],
      ["catch.py <URL> --raw", "只抓原文不做笔记"],
    ],
    [4800, 4560],
  ),

  h2("4.2 订阅周报"),
  tbl(
    ["命令", "用途"],
    [
      ["catch.py --subscribe channels.yaml", "扫近一周新内容 → 投喂包 + 占位 EPUB"],
      ["catch.py --subscribe channels.yaml --finalize-epub <dir>", "用代笔单章重新生成 EPUB"],
      ["catch.py --subscribe channels.yaml --send-only <dir>", "把现成 digest 发邮件"],
      ["catch.py --subscribe channels.yaml --auto --send-email", "带 LLM API 时一气呵成"],
      ["catch.py --subscribe channels.yaml --days 14 --epub-threshold 1", "调时间窗 + EPUB 阈值"],
    ],
    [5600, 3760],
  ),

  h2("4.3 常用参数"),
  tbl(
    ["参数", "用途"],
    [
      ["--cookies-from chrome/safari/firefox/edge", "从浏览器读 cookies"],
      ["--no-transcribe", "无字幕时不走 Whisper（节省时间）"],
      ["--max-transcribe-min N", "超过 N 分钟跳过 Whisper（默认 20）"],
      ["--whisper-model tiny/base/small/medium/large-v3", "Whisper 模型大小（默认 tiny）"],
      ["--chunk-size N", "长文本分段大小"],
      ["--no-cache", "强制重抓"],
      ["--deep", "精装电子书风格（叙事体长文）"],
      ["--full", "完整版（逐字稿 + 导读）"],
      ["--epub-threshold N", "自动 EPUB 的最低条目数（默认 5）"],
    ],
    [3960, 5400],
  ),
);

// === 第 5 章：配置 ===
children.push(
  h1("5. 配置文件"),

  h2("5.1 channels.yaml 结构"),
  p("订阅相关的唯一入口。最小骨架："),
  ...codeBlock([
    "newsletter:",
    "  name: \"我的 AI 周报\"",
    "  email_to: \"you@example.com\"",
    "  email_from: \"you@example.com\"",
    "  smtp:",
    "    host: \"smtp.qq.com\"",
    "    port: 465",
    "    use_ssl: true",
    "    user: \"you@example.com\"",
    "",
    "defaults:",
    "  days: 7",
    "  max_per_channel: 3",
    "",
    "channels:",
    "  - type: bilibili_uploader",
    "    name: \"大牙大-\"",
    "    mid: \"25752587\"",
    "    cookies_from: chrome",
    "    enabled: true",
  ]),

  h2("5.2 三种 source type"),
  tbl(
    ["type", "必填字段", "用途"],
    [
      ["bilibili_uploader", "mid", "B 站 UP 主（需登录 cookies）"],
      ["youtube_channel", "channel_id（UC 开头）或 handle", "YouTube 频道（v0.7.3+ 带 fetcher chain）"],
      ["rss", "url", "通用 RSS（小宇宙 / Substack / Megaphone / 博客）"],
    ],
    [2400, 2960, 4000],
  ),

  h2("5.3 .smtp_secret"),
  p("邮件授权码文件，永远不要 commit 进 git。格式："),
  ...codeBlock([
    "SMTP_PASS=你的SMTP授权码",
  ]),
  p("⚠️ 不要 export SMTP_PASS=\"$(cat .smtp_secret)\" ——会把整个文件（含注释）当 token，登录失败。脚本会自己读，无需手动 export。"),

  h2("5.4 各邮箱授权码申请入口"),
  tbl(
    ["邮箱", "申请路径"],
    [
      ["QQ 邮箱", "mail.qq.com → 设置 → 账户 → IMAP/SMTP → 申请授权码"],
      ["Gmail", "myaccount.google.com → 安全性 → 应用专用密码"],
      ["163 邮箱", "mail.163.com → 设置 → POP3/SMTP → 客户端授权密码"],
    ],
    [2000, 7360],
  ),
);

// === 第 6 章：人机分工工作流 ===
children.push(
  h1("6. 人机分工工作流（推荐）"),

  h2("6.1 为什么这样设计"),
  p("很多人不想给 ANTHROPIC / OPENAI 充值，想用自己日常对话的 Claude / GPT 来代笔——content-catcher 就是为这个场景设计的。"),
  quote("机器做工程活，人 / 对话方 LLM 做判断和蒸馏。"),

  h2("6.2 完整 4 步链"),
  numbered("catch.py --subscribe channels.yaml —— 抓取 + 投喂包 + 占位 EPUB"),
  numbered("你 / Claude 读投喂包，在 digest 目录写代笔单章 chapter-<slug>.md"),
  numbered("catch.py --subscribe channels.yaml --finalize-epub <本期目录> —— 用代笔重做 EPUB"),
  numbered("catch.py --subscribe channels.yaml --send-only <本期目录> —— 发邮件"),

  h2("6.3 在对话里怎么跟 Claude 说"),
  p("最常用的触发短语："),
  quote("「按 skill 流程跑本周 content-catcher 订阅，重要的几条帮我代笔」"),
  p("Claude 会自动跑完上面 4 步，你只负责看邮箱。"),

  h2("6.4 EPUB 章节优先级"),
  p("v0.7.2+ 设计：EPUB 章节内容按以下顺序查找，绝不再装投喂包原文："),
  numbered("output/digest/<本期>/chapter-<slug>.md —— 本期代笔单章（首选）"),
  numbered("output/final/<slug>/笔记.md —— 长期保留的精装版"),
  numbered("占位章节（仅标题 + 链接 + 「尚未代笔」提示）"),
);

// === 第 7 章：常见问题 FAQ ===
children.push(
  h1("7. 常见问题 FAQ"),

  h3("Q1. install.sh 报 Python too old"),
  p("升级到 Python 3.10+。macOS 推荐 brew install python@3.12，或者用 pyenv。"),

  h3("Q2. B 站抓取失败，提示「Sign in to confirm」"),
  p("B 站需要登录 cookies。在 Chrome / Safari 里手动登录一次 B 站，然后命令里加 --cookies-from chrome 或 safari。"),

  h3("Q3. YouTube 订阅扫到 0 条"),
  p("YouTube 自家 RSS endpoint 自 2025 年起间歇 5xx/404。v0.7.3+ 已加 fetcher chain 自动 fallback。若仍 0 条：浏览器直接打开 https://www.youtube.com/feeds/videos.xml?channel_id=<UCxxx> 验证 YouTube 当下是否正常。"),

  h3("Q4. SMTP 报 'ascii' codec can't encode characters"),
  p("v0.7.1 已修。如果重现，检查 scripts/email_sender.py 是不是被退回了旧版（构造 EmailMessage 时必须传 policy=SMTP_POLICY + charset='utf-8'）。"),

  h3("Q5. SMTP 密码总是错"),
  bullet("检查 .smtp_secret 格式：SMTP_PASS=xxx，一行，等号两边无空格"),
  bullet("用的是 SMTP 授权码而不是邮箱登录密码"),
  bullet("不要 export SMTP_PASS=\"$(cat .smtp_secret)\" ——让脚本自己读"),

  h3("Q6. Whisper 转写太慢"),
  p("默认 tiny 模型在 CPU 上约 1x 实时速度。三个解决方案："),
  bullet("--max-transcribe-min 10：超过 10 分钟的视频直接跳过"),
  bullet("--whisper-model small：更准但慢 2-3 倍"),
  bullet("--no-transcribe：完全跳过，只用元信息 fallback"),

  h3("Q7. EPUB 章节里全是字幕原文 / LLM 任务说明"),
  p("你装的是 v0.7.0–0.7.1。升级到 v0.7.2+："),
  ...codeBlock([
    "git pull && pip install -r requirements.txt",
  ]),
  p("新版本只用 chapter-*.md 代笔单章 + output/final/ 精装版；找不到就用占位章节，绝不会再把投喂包塞进去。"),

  h3("Q8. 长任务被 shell 切了"),
  p("用 nohup 真正脱离会话："),
  ...codeBlock([
    "nohup ./catch.py --subscribe channels.yaml > /tmp/catch.log 2>&1 &",
    "disown",
    "tail -f /tmp/catch.log",
  ]),

  h3("Q9. 想完全清掉重跑"),
  ...codeBlock([
    "rm -rf output/   # 删所有产出（包括缓存）",
    "rm -rf .venv/    # 删 venv 重装",
  ]),
);

// === 第 8 章：版本与许可 ===
children.push(
  h1("8. 版本与许可"),

  h2("8.1 当前版本：v0.8.0"),
  p("发布日期：2026-06-02"),
  p("关键变化："),
  bullet("可分发：新增 pyproject.toml + requirements.txt + install.sh"),
  bullet("可代笔：EPUB 章节按代笔优先级查找，绝不再装投喂包"),
  bullet("可订阅 YouTube：fetcher chain（原生 → UULF → RSSHub/Invidious 三级 fallback）"),
  bullet("中文邮件无障碍：修了 EmailMessage 默认 policy 的中文编码 bug"),
  bullet("完整文档：MANUAL.md + SUBSCRIPTION_GUIDE.md + CHANGELOG.md"),

  h2("8.2 链接"),
  link("GitHub 仓库：https://github.com/zczxd1118/content-catcher", "https://github.com/zczxd1118/content-catcher"),
  link("v0.8.0 Release：https://github.com/zczxd1118/content-catcher/releases/tag/v0.8.0", "https://github.com/zczxd1118/content-catcher/releases/tag/v0.8.0"),
  link("完整 Markdown 手册：docs/MANUAL.md", "https://github.com/zczxd1118/content-catcher/blob/main/docs/MANUAL.md"),
  link("订阅源管理指南：docs/SUBSCRIPTION_GUIDE.md", "https://github.com/zczxd1118/content-catcher/blob/main/docs/SUBSCRIPTION_GUIDE.md"),
  link("CHANGELOG：CHANGELOG.md", "https://github.com/zczxd1118/content-catcher/blob/main/CHANGELOG.md"),

  h2("8.3 许可"),
  p("MIT License。可自由用于商业、个人、修改、分发，仅需保留版权声明。"),

  h2("8.4 致谢"),
  bullet("yt-dlp —— 视频抓取事实标准"),
  bullet("faster-whisper —— PyTorch-free 的 Whisper"),
  bullet("trafilatura —— 网页正文提取"),
  bullet("feedparser —— 宽容的 RSS 解析"),
  bullet("EbookLib —— EPUB 生成"),
  bullet("RSSHub / Invidious —— YouTube 备用 feed 代理"),

  // 收尾
  new Paragraph({
    children: [new TextRun({ text: "— 文档结束 —", font: FONT_CN, italics: true, size: 22, color: COLOR_MUTED })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 480, after: 240 },
  }),
);

// ─── 构建文档 ────────────────────────────────────────────
const doc = new Document({
  creator: "content-catcher × Claude",
  title: "content-catcher v0.8.0 项目说明",
  description: "Personal Information Distillery + Newsletter Engine — 项目说明文档",
  styles: {
    default: {
      document: { run: { font: FONT_CN, size: 22 } },
    },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: FONT_CN, color: COLOR_PRIMARY },
        paragraph: { spacing: { before: 480, after: 240 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: FONT_CN, color: COLOR_TEXT },
        paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: FONT_CN, color: COLOR_TEXT },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 }, // US Letter
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          children: [
            new TextRun({ text: "content-catcher v0.8.0 项目说明", font: FONT_CN, size: 18, color: COLOR_MUTED }),
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
    children,
  }],
});

const OUT = "/Users/zoezczhou/.workbuddy/skills/content-catcher/output/manual/content-catcher-v0.8.0-项目说明.docx";
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(OUT, buffer);
  const size = fs.statSync(OUT).size;
  console.log(`✅ 生成 docx: ${OUT}`);
  console.log(`   大小: ${(size/1024).toFixed(1)} KB`);
});
