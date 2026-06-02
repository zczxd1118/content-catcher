#!/usr/bin/env python3
"""一键生成项目说明 docx 的便利脚本。

依赖：
  - Node 22+（用来跑 docx 库）
  - 已 npm install docx 到 ~/.workbuddy/binaries/node/workspace/node_modules
  - Python 3.10+

跑法：
  python scripts/build_manual_docx.py

输出：
  output/manual/content-catcher-v0.8.0-项目说明.docx
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output" / "manual"
OUT_DOCX = OUT_DIR / "content-catcher-v0.8.0-项目说明.docx"

# 我们假设这个脚本附近有 .js 源（同名同目录，扩展名 .js）
# 实际工程上：脚本和 .js 都放 scripts/ 下
JS_SOURCE = ROOT / "scripts" / "build_manual_docx.js"
NODE_MODULES = Path.home() / ".workbuddy/binaries/node/workspace/node_modules"
NODE_BIN = Path.home() / ".workbuddy/binaries/node/versions/22.22.2/bin/node"


def reorder_pbdr_children(xml_path: Path) -> int:
    """docx-js 9.7.x 把 <w:pBdr> 子元素写成 top→bottom→left→right，
    但 OOXML schema 要求 top→left→bottom→right。批量修。"""
    xml = xml_path.read_text(encoding="utf-8")
    pattern = re.compile(r"(<w:pBdr>)(.*?)(</w:pBdr>)", re.DOTALL)
    order = ["top", "left", "bottom", "right", "between", "bar"]
    count = 0

    def reorder(m):
        nonlocal count
        count += 1
        body = m.group(2)
        elems = re.findall(r"<w:(?:top|left|bottom|right|between|bar)\s+[^/]*/>", body)
        by_name = {re.match(r"<w:(\w+)", el).group(1): el for el in elems}
        new = "\n          ".join(by_name[n] for n in order if n in by_name)
        return f"{m.group(1)}\n          {new}\n        {m.group(3)}"

    xml_path.write_text(pattern.sub(reorder, xml), encoding="utf-8")
    return count


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 用 docx-js 生成（如果 .js 源存在）
    if JS_SOURCE.exists():
        print(f"📝 跑 docx-js 生成器：{JS_SOURCE.name}")
        env = os.environ.copy()
        env["NODE_PATH"] = str(NODE_MODULES)
        r = subprocess.run([str(NODE_BIN), str(JS_SOURCE)],
                           env=env, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"❌ Node 执行失败：{r.stderr[:300]}")
            sys.exit(1)
        print(r.stdout.strip())

    if not OUT_DOCX.exists():
        print(f"❌ 找不到 {OUT_DOCX}")
        sys.exit(1)

    # 2. unpack → 修 pBdr 顺序 → repack
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        print(f"🔧 修复 <w:pBdr> schema 顺序...")
        # 简单 unzip（避免依赖 docx skill 的 unpack.py）
        with zipfile.ZipFile(OUT_DOCX) as z:
            z.extractall(tmp)
        doc_xml = tmp / "word" / "document.xml"
        n = reorder_pbdr_children(doc_xml)
        print(f"   修了 {n} 个 <w:pBdr>")
        # 重新打包
        tmp_zip = OUT_DOCX.with_suffix(".tmp.docx")
        with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(tmp):
                for f in files:
                    full = Path(root) / f
                    z.write(full, full.relative_to(tmp))
        shutil.move(str(tmp_zip), str(OUT_DOCX))

    size_kb = OUT_DOCX.stat().st_size / 1024
    print(f"✅ {OUT_DOCX} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
