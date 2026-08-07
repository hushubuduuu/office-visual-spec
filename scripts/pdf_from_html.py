# -*- coding: utf-8 -*-
"""Print the responsive HTML template to a copyable-text PDF.

Usage:
  python pdf_from_html.py [output.pdf] [a4|slide]
"""
import argparse
import tempfile
from pathlib import Path

import fitz

from chrome_common import find_browser, run_headless
from cli import run_main

PAGE_SIZES = {
    "a4": "A4",
    "slide": "13.333in 7.5in",
    "mobile": "3.89in 8.4in",
}


def make_temp_html(source: Path, page_size: str) -> Path:
    text = source.read_text(encoding="utf-8")
    marker = "size: A4;"
    replacement = "size: %s;" % PAGE_SIZES[page_size]
    if marker in text:
        text = text.replace(marker, replacement, 1)
    if page_size == "slide":
        text = text.replace('<html lang="zh-CN">', '<html lang="zh-CN" class="print-slide">', 1)
    if page_size == "mobile":
        text = text.replace('<html lang="zh-CN">', '<html lang="zh-CN" class="print-mobile">', 1)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".html", prefix="office-visual-spec-print-", delete=False) as f:
        f.write(text)
        tmp = Path(f.name)
    return tmp


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", default="\u793a\u4f8b-\u8bfe\u7a0b\u7eaa\u8981.pdf")
    parser.add_argument("size", nargs="?", choices=list(PAGE_SIZES), default="a4")
    parser.add_argument("--input", type=Path, default=None)
    args = parser.parse_args()

    source = args.input or (Path(__file__).resolve().parent.parent / "templates" / "a4-summary.html")
    if not source.exists():
        raise SystemExit("找不到输入文件：" + str(source) + "，请检查路径是否正确。")
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = make_temp_html(source, args.size)
    try:
        r = run_headless(
            find_browser(),
            [
                "--print-to-pdf=" + str(out),
                "--no-pdf-header-footer",
                "--virtual-time-budget=3000",
                tmp.as_uri(),
            ],
            timeout=120,
        )
        if r.returncode != 0:
            raise SystemExit("浏览器渲染失败：" + r.stderr.decode("utf-8", "ignore")[-300:])
        doc = fitz.open(str(out))
        try:
            text = "".join(page.get_text() for page in doc)
            if len(text.strip()) <= 100:
                raise SystemExit("生成的 PDF 没有可复制文字，请检查 HTML 内容。")
            page_count = doc.page_count
        finally:
            doc.close()
        print("saved", out)
        print("pages", page_count, "size", args.size)
        print("copyable text: OK")
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    run_main(main, next_step="请根据上面的提示处理；缺少依赖时运行 install.bat（Windows）或 install.sh（macOS/Linux）")
