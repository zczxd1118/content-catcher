# 📡 订阅管理手册

> content-catcher v0.7.2+ · 最后更新：2026-06-02
>
> 这份手册告诉你如何修改 `channels.yaml` —— 改主题、加源、删源、暂时关源、查 ID。
> 所有订阅相关的配置都集中在**一个文件**：`channels.yaml`（仓库根目录）。

---

## 🗺 文件结构总览

```yaml
newsletter:        # 周报元信息：刊名、邮箱、SMTP
defaults:          # 全局默认参数：每周抓多少天、每个频道最多几条
channels:          # 订阅源列表（核心）
  - type: ...      # 每个源是一个块
```

---

## 1️⃣ 改"周报主题/刊名/邮箱"

`channels.yaml` 顶部的 `newsletter:` 块控制：

```yaml
newsletter:
  name: "周小丁的 AI + Vibe Coding 周报"   # ← 刊名（出现在邮件标题、EPUB 标题、卷首语）
  email_to: "170665060@qq.com"            # ← 收件邮箱
  email_from: "170665060@qq.com"          # ← 发件邮箱
  smtp:
    host: "smtp.qq.com"                   # ← 用 QQ 邮箱就 smtp.qq.com，163 就 smtp.163.com
    port: 465
    use_ssl: true
    user: "170665060@qq.com"              # ← SMTP 用户名（一般等于发件邮箱）
```

> 🔑 SMTP 密码（授权码）放在仓库根目录的 `.smtp_secret` 里（已 gitignore），格式：
> ```
> SMTP_PASS=你的SMTP授权码
> ```
> **不要**手动 `export SMTP_PASS`，让脚本自己从文件读。

### 改完之后

直接保存就行，下次跑订阅会自动读新配置。

---

## 2️⃣ 调"全局默认参数"

```yaml
defaults:
  days: 7              # 每次扫描抓近 N 天的新内容
  max_per_channel: 3   # 每个频道最多取 N 条（避免周报过长）
  cookies_from: null   # 默认不从浏览器读 cookies；某个源需要 cookies 在该源下单独写
```

### 单次想改怎么办？

不用改 yaml，命令行覆盖就行：

```bash
catch.py --subscribe channels.yaml --days 14         # 抓近两周（追新订源时常用）
catch.py --subscribe channels.yaml --epub-threshold 1   # EPUB 阈值临时调到 1（测试用）
```

---

## 3️⃣ 加一个新订阅源

`channels:` 列表里**复制一个同类型的块**改一下就行。三种 type：

### 类型 A：B 站 UP 主

```yaml
- type: bilibili_uploader
  name: "大牙大-"           # ← 显示名（任意），周报里看到的
  mid: "25752587"          # ← B 站个人空间的数字 ID（必填）
  cookies_from: chrome     # ← 一定要从浏览器读 cookies（B 站反爬）
  enabled: true
```

#### 怎么找 mid？

1. 浏览器登录 B 站，打开 UP 主主页
2. URL 长这样：`https://space.bilibili.com/25752587/...`
3. `space.bilibili.com/` 后面那串数字就是 mid（这里是 `25752587`）

#### cookies 怎么准备？

第一次跑前在 Chrome / Safari 里**登录 B 站**就行，`cookies_from: chrome` 会自动从 Chrome 里读。

### 类型 B：YouTube 频道

```yaml
- type: youtube_channel
  name: "Lex Fridman"
  channel_id: "UCSHZKyawb77ixDdsGog4iWA"   # ← UC 开头 24 字符
  enabled: true
```

#### 怎么找 channel_id？

最快的两个方法：

**A. 用 yt-dlp（命令行）**

```bash
~/.workbuddy/binaries/python/envs/content-catcher/bin/yt-dlp \
    --print "%(channel_id)s" --playlist-end 1 \
    "https://www.youtube.com/@latentspacepod"
```

**B. 直接抓页面源**

```bash
python3 -c "
import urllib.request, re
req = urllib.request.Request('https://www.youtube.com/@latentspacepod',
                              headers={'User-Agent':'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8','ignore')
m = re.search(r'\"channelId\":\"(UC[\w-]{22})\"', html) or \\
    re.search(r'(UC[\w-]{22})', html)
print(m.group(1) if m else 'NOT FOUND')
"
```

> 🛠 **YouTube fetcher chain（v0.7.3 起）**：
> 由于 YouTube 在 2025 年起让原生 `videos.xml` endpoint 间歇 5xx/404，
> v0.7.3 版本的 `subscribe.scan_youtube_channel` 改成多级 fetcher：
>
> 1. 原生 `videos.xml?channel_id=` —— 带 2 次重试（指数退避）
> 2. `videos.xml?playlist_id=UULF...` —— 替换 UC 前缀，可过滤 Shorts
> 3. 第三方代理 —— RSSHub / Invidious 公共实例逐个试
>
> **任何一路返回非空 items 立即停止**，全失败时打印明确日志并返回 []。
>
> 实际效果：稳定网络下原生大概率第 1 步就成；遇到 YouTube 端临时挂掉时自动降级。
> 如果某频道连续多周扫不到内容，**先在浏览器试一下原 URL 看是不是 YouTube 端正在维护**。

### 类型 C：通用 RSS（播客 / Substack / 博客）

```yaml
- type: rss
  name: "张小珺Jùn 商业访谈录"
  url: "https://feed.xyzfm.space/dk4yh3pkpjp3"
  enabled: true
```

#### 怎么找 RSS URL？

| 平台 | 方法 |
|---|---|
| **小宇宙** | https://podstatus.com → 搜节目名 → 看 "Feed" 字段（一般是 `feed.xyzfm.space/...`） |
| **Apple Podcasts** | 看 podstatus.com 上的 `Feed` 字段（多数 = Megaphone / Acast / Substack 原始 feed） |
| **Substack** | `https://<sitename>.substack.com/feed`（如 `latent.space/feed`），或者播客 feed `https://api.substack.com/feed/podcast/<podcast_id>.rss`（podcast_id 在 Substack 后台或 feed XML 里能找到） |
| **公众号** | 没原生 RSS，可以用 [RSSHub](https://docs.rsshub.app/) 反代：`https://rsshub.app/wechat/...` |
| **B 站专栏** | 同上，RSSHub：`https://rsshub.app/bilibili/user/article/<uid>` |
| **其他博客** | 一般 `<网址>/feed`、`<网址>/rss` 或 `<网址>/atom.xml` 试一遍 |

#### 验证 RSS 是不是真的活着

```bash
python3 -c "
import urllib.request, re
url = 'https://feed.xyzfm.space/dk4yh3pkpjp3'
xml = urllib.request.urlopen(url, timeout=10).read().decode('utf-8','ignore')
titles = re.findall(r'<title>(.*?)</title>', xml)
print('频道:', titles[0] if titles else '?')
print('最近 3 条:')
for t in titles[1:4]: print(' -', t[:80])
"
```

如果输出空 / 404 / SSL 错误，feed 多半挂了，换一个。

---

## 4️⃣ 暂时关闭/启用某个源

不用删，改一行就行：

```yaml
- type: bilibili_uploader
  name: "马克的技术工作坊"
  mid: "1815948385"
  cookies_from: chrome
  enabled: false        # ← 改成 false 即关，true 即开
```

> 💡 推荐**关而不删**——这样以后想恢复时一行改回 `true` 就行，不用重查 ID。

---

## 5️⃣ 永久删除一个源

直接把整个 channel 块从 `channels:` 列表里删掉。注意 YAML 缩进，别误删别的。

如果不放心，先把它注释掉测一周：

```yaml
  # - type: bilibili_uploader
  #   name: "已退订的 UP 主"
  #   mid: "..."
  #   enabled: false
```

---

## 6️⃣ 调整周报和 EPUB 的触发条件

### 改自动 EPUB 阈值

默认 ≥ 5 条新内容才出 EPUB（避免一周一条也出一本电子书）。可以全局改：

直接修改 `scripts/digest.py` 里 `build_epub_if_many` 的 `threshold` 参数，或者在命令行上覆盖：

```bash
catch.py --subscribe channels.yaml --epub-threshold 1   # 1 条起就出 EPUB
catch.py --subscribe channels.yaml --epub-threshold 8   # 8 条起才出 EPUB
```

### 改抓取的时间窗

```bash
catch.py --subscribe channels.yaml --days 3   # 只看近 3 天（适合每天跑）
catch.py --subscribe channels.yaml --days 14  # 近两周（适合"补订阅"或第一次跑新源）
```

---

## 7️⃣ 完整工作流速查表

```bash
# A. 抓取（生成投喂包 + 默认 EPUB）
catch.py --subscribe channels.yaml

# B. 写代笔单章到 digest 目录（让 Claude 帮你写）
#    output/digest/<本期>/chapter-<某条标题>.md
#    模板：templates/chapter_polished.md

# C. 重做 EPUB（用代笔章节替换占位）
catch.py --subscribe channels.yaml --finalize-epub <本期目录名>

# D. 发邮件
catch.py --subscribe channels.yaml --send-only <本期目录名>
```

---

## 🆘 常见问题

### Q: B 站源扫到 0 条？

- **首先**：确认浏览器（Chrome / Safari）里**已登录 B 站**
- **其次**：确认 `cookies_from: chrome` 这一行写对了
- **再不行**：试试 `cookies_from: safari`（看你常用哪个浏览器）
- **B 站近 7 天没有新内容也是正常的**——某些 UP 主一周就发 1–2 条，扫到 0 条不是 bug

### Q: 修改 channels.yaml 后跑订阅没反应？

- 你的 yaml 缩进可能错了。**用 4 空格缩进**，不要混 tab
- 验证：`python3 -c "import yaml; yaml.safe_load(open('channels.yaml'))"`，没输出就是 OK

### Q: SMTP 报 'ascii' codec can't encode characters？

- 这是 v0.7.0 老版本的 bug，v0.7.1 已修。如果还遇到，看 `scripts/email_sender.py` 是不是被退回了旧版

### Q: 加了一堆 YouTube 源都扫不到？

- v0.7.3 已经加了 fetcher chain（原生 → UULF playlist → RSSHub/Invidious 代理），多数情况都能 fallback 到结果
- 若仍然 0 条：
  1. 看日志最后那行 `❌ 所有 YouTube fetcher 全部失败` —— 说明所有路径都被网络挡了
  2. 浏览器打开 `https://www.youtube.com/feeds/videos.xml?channel_id=<你的UC...>` 直接看（YouTube 端可能短暂维护）
  3. 检查 RSSHub / Invidious 公共实例是否被你所在网络环境屏蔽（中国大陆访问会比较挑实例）

### Q: 一次跑订阅时间超久（被前台 shell 切了）？

- 长视频走 Whisper 转写比较慢，建议**用 `nohup` 跑**：
  ```bash
  cd ~/.workbuddy/skills/content-catcher
  nohup ~/.workbuddy/binaries/python/envs/content-catcher/bin/python \
      catch.py --subscribe channels.yaml \
      > /tmp/curio_subscribe.log 2>&1 &
  disown
  ```
  然后 `tail -f /tmp/curio_subscribe.log` 看进度。

---

## 📚 相关文件

| 文件 | 作用 |
|---|---|
| `channels.yaml` | 唯一的订阅配置入口（**本手册的主角**） |
| `.smtp_secret` | SMTP 密码（已 gitignore） |
| `output/digest/<本期>/weekly-digest.md` | 每期周报正文（你/Claude 代笔的） |
| `output/digest/<本期>/chapter-*.md` | 每条内容的代笔单章 |
| `templates/chapter_polished.md` | 代笔单章模板 |
| `output/digest/history.json` | 已发送内容的去重记录（增量扫描用） |
| `SKILL.md` | skill 总览（含 `--send-only` / `--finalize-epub` 等命令说明） |

---

> 这份手册随 channels.yaml 同步演进。如果你新增了一种平台 / 一种 source type / 一种工作流约定，别忘了在这里也加一段。
