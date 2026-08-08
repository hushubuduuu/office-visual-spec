#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""office-visual-spec standard render pipeline: HTML -> PNG / PDF

Mirrors the local html-editor export architecture:
- PNG: one complete long image at the device logical width.
- PDF: paginated multi-page PDF (same page slicing as the editor).
- mobile-long PDF: single long page, rendered from the full PNG.
- pages/: per-page PNG image set.

Usage:
  python render-html.py <type> <input.html> <outdir> [--scale 2] [--width 1080] [--check-only]
  python render-html.py <type> <input.html> --check-only

Types: a4 | html-ppt | ppt-web | html-page | xhs | mobile-long | infographic
"""
import argparse
import re
import shutil
import tempfile
import time
from pathlib import Path

# NOTE: no third-party imports at module level on purpose. The venv bootstrap
# lives in cli.run_main(); if a system python without deps imports this module,
# a top-level third-party import would crash before the bootstrap can re-exec
# under .venv. PIL is only needed for the mobile-long PDF branch below.

from chrome_common import find_browser, flags as chrome_flags, run_headless
from cli import run_main

# "sheet" is the logical CSS canvas. "png" is the same logical size;
# actual output pixels are logical size * --scale.
TYPES = {
    "a4": {"sheet": (794, 1123), "png": (794, 1123), "page": True, "pdf": "A4"},
    "html-ppt": {"sheet": (1280, 720), "png": (1280, 720), "page": True, "pdf": "1280x720"},
    "ppt-web": {"sheet": (1280, 720), "png": (1280, 720), "page": True, "pdf": "1280x720", "web": True},
    "html-page": {"sheet": None, "png": None, "page": False, "pdf": "A4", "dynamic": True, "width": 860},
    "xhs": {"sheet": (1080, 1440), "png": (1080, 1440), "page": True, "pdf": "1080x1440"},
    "mobile-long": {"sheet": None, "png": None, "page": False, "pdf": "A4", "dynamic": True, "width": 1080, "default_scale": 3},
    "infographic": {"sheet": (1080, 1215), "png": (1080, 1215), "page": False, "pdf": "1080x1215"},
}

# Long PNGs stretch the page, so vh changes. Override vh-based variables with fixed px.
LONG_PNG_VH_FIXES = {"a4": ":root{--m-top:87.3px;--m-bottom:71.4px}"}


def read(path):
    return Path(path).read_text(encoding="utf-8")


def write(path, text):
    Path(path).write_text(text, encoding="utf-8")


def cleanup_dir(path):
    for _ in range(3):
        try:
            shutil.rmtree(path)
            return
        except OSError:
            time.sleep(0.2)
    shutil.rmtree(path, ignore_errors=True)


def cleanup_file(path):
    for _ in range(3):
        try:
            Path(path).unlink(missing_ok=True)
            return
        except OSError:
            time.sleep(0.2)


def chrome(args, timeout=120):
    result = run_headless(find_browser(), ["--hide-scrollbars"] + args, timeout=timeout)
    if result.returncode != 0:
        print("浏览器渲染失败，错误信息：" + result.stderr.decode("utf-8", "ignore")[-300:], flush=True)
    return result.returncode


def profile(html_path, web=False, width=None):
    """Return (sheet_rows, page_height, page_width).

    width: when set, the probe runs in a viewport of that width (needed for
    dynamic types like html-page/mobile-long whose layout depends on the
    content width; the default headless viewport is 800px and would measure
    a different height than the target-width screenshot).
    """
    delay = 1600 if web else 1200
    probe = """<script>
    setTimeout(function(){
      var out = Array.from(document.querySelectorAll('.sheet, .canvas')).map(function(s,i){
        return (i+1)+':' + Math.round(s.scrollHeight) + '/' + Math.round(s.clientHeight);
      }).join(',');
      var h = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
      var w = Math.max(document.body.scrollWidth, document.documentElement.scrollWidth);
      document.title='PROFILE|' + out + '|H' + h + '|W' + w;
    }, %d);
    </script></body>""" % delay
    s = read(html_path).replace("</body>", probe)
    tmpdir = tempfile.mkdtemp(prefix="ovs-probe-html-")
    tmp = Path(tmpdir) / "probe.html"
    write(tmp, s)
    udd = tempfile.mkdtemp(prefix="ovs-probe-")
    args = ["--user-data-dir=" + udd, "--virtual-time-budget=6000", "--dump-dom"]
    if width:
        args.insert(2, "--window-size=%d,1200" % width)
    args.append(Path(tmp).resolve().as_uri())
    try:
        result = run_headless(
            find_browser(),
            args,
            timeout=60,
        )
        if result.returncode != 0:
            raise SystemExit("浏览器渲染失败，错误信息：" + result.stderr.decode("utf-8", "ignore")[-300:])
        dom = result.stdout.decode("utf-8", "ignore")
    finally:
        cleanup_dir(udd)
        cleanup_dir(tmpdir)
    if "PROFILE|" not in dom:
        raise SystemExit("无法读取页面尺寸，请检查 HTML 文件是否完整，或用 OVS_DEBUG=1 查看详细错误。")
    m = re.search(r"<title>(PROFILE\|[^<]*)</title>", dom)
    if not m:
        raise SystemExit("无法读取页面尺寸，请检查 HTML 文件是否完整，或用 OVS_DEBUG=1 查看详细错误。")
    parts = m.group(1).split("|")
    rows = []
    if len(parts) > 1 and parts[1]:
        for part in parts[1].split(","):
            if ":" in part:
                idx, dims = part.split(":")
                sh, ch = dims.split("/")
                rows.append((int(idx), int(sh), int(ch)))
    height = int(parts[2][1:]) if len(parts) > 2 and parts[2].startswith("H") else 0
    width = int(parts[3][1:]) if len(parts) > 3 and parts[3].startswith("W") else 0
    return rows, height, width


def check_overflow(html_path, web=False):
    rows, _, _ = profile(html_path, web=web)
    bad = []
    for idx, sh, ch in rows:
        if ch == 0:
            bad.append("sheet %d 高度为 0（可能被 CSS 隐藏，请检查 display/height）" % idx)
        elif sh > ch + 1:
            bad.append("sheet %d: %d > %d" % (idx, sh, ch))
    if bad:
        raise SystemExit("页面内容超出画布，请精简内容后重试。详情：" + "; ".join(bad))
    return rows


def shot(html_path, out_png, w, h, scale, extra_css="", extra_js="", budget=12000):
    s = read(html_path)
    css = "<style>" + extra_css + "</style>"
    js = "<script>" + extra_js + "</script>"
    s = s.replace("</head>", css + "</head>")
    if extra_js:
        s = s.replace("</body>", js + "</body>")
    tmpdir = tempfile.mkdtemp(prefix="ovs-shot-html-")
    tmp = Path(tmpdir) / "shot.html"
    write(tmp, s)
    udd = tempfile.mkdtemp(prefix="ovs-shot-")
    args = ["--user-data-dir=" + udd, "--window-size=%d,%d" % (w, h),
            "--force-device-scale-factor=%d" % scale,
            "--virtual-time-budget=%d" % budget,
            "--screenshot=" + str(out_png), Path(tmp).resolve().as_uri()]
    try:
        rc = chrome(args)
    finally:
        cleanup_dir(udd)
        cleanup_dir(tmpdir)
    return rc


def to_pdf(html_path, out_pdf, budget=15000, extra_css=""):
    target = html_path
    tmpdir = None
    if extra_css:
        s = read(html_path).replace("</head>", "<style>" + extra_css + "</style></head>")
        tmpdir = tempfile.mkdtemp(prefix="ovs-pdf-html-")
        tmp = Path(tmpdir) / "pdf-extra.html"
        write(tmp, s)
        target = tmp
    udd = tempfile.mkdtemp(prefix="ovs-pdf-")
    args = ["--user-data-dir=" + udd, "--print-to-pdf=" + str(out_pdf),
            "--print-to-pdf-no-header", "--no-pdf-header-footer",
            "--virtual-time-budget=%d" % budget,
            Path(target).resolve().as_uri()]
    try:
        rc = chrome(args, timeout=180)
    finally:
        cleanup_dir(udd)
        if tmpdir:
            cleanup_dir(tmpdir)
    return rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("type", choices=list(TYPES))
    ap.add_argument("input")
    ap.add_argument("outdir", nargs="?")
    ap.add_argument("--scale", type=int, default=None)
    ap.add_argument("--width", type=int, default=None)
    ap.add_argument("--check-only", action="store_true", help="只运行内置 check_overflow，不导出")
    args = ap.parse_args()

    if not args.check_only and not args.outdir:
        raise SystemExit("缺少输出目录参数。完整命令示例：python scripts/render-html.py <type> <input.html> <outdir>")

    cfg = TYPES[args.type]
    scale = args.scale if args.scale is not None else cfg.get("default_scale", 2)
    src = Path(args.input).resolve()
    if not src.exists():
        raise SystemExit("找不到输入文件：" + str(src) + "，请检查路径是否正确。")
    if args.check_only:
        if cfg["page"] or args.type == "infographic":
            check_overflow(str(src), web=args.type == "ppt-web")
            print("PASS: overflow check")
        else:
            w = args.width or cfg.get("width", 1280)
            _, height, _ = profile(str(src), web=args.type == "ppt-web", width=w)
            if not height:
                raise SystemExit("无法读取页面高度，请检查 HTML 文件是否完整，或用 OVS_DEBUG=1 查看详细错误。")
            print("PASS: profile height", height)
        return
    out = Path(args.outdir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "png").mkdir(exist_ok=True)
    (out / "pdf").mkdir(exist_ok=True)

    if cfg["page"] or args.type == "infographic":
        check_overflow(str(src), web=args.type == "ppt-web")

    hide = ".sheet{display:none!important}"
    show_n = lambda n: ".sheet:nth-of-type(%d){display:block!important}" % n
    no_margin = "body{margin:0}.sheet{margin:0!important;box-shadow:none!important}"

    failed = False

    def report(rc, *parts):
        nonlocal failed
        if rc != 0:
            failed = True
        print(("OK " if rc == 0 else "FAIL "), *parts)

    count = 0
    if cfg["page"]:
        rows, _, _ = profile(str(src), web=args.type == "ppt-web")
        count = len(rows)

        if args.type == "ppt-web":
            # Interactive deck: keep per-page PNGs because it is a horizontal deck.
            for i in range(1, count + 1):
                png = out / "png" / ("page-%02d.png" % i)
                css = "[data-anim]{opacity:1!important;transform:none!important}"
                js = 'document.getElementById("deck").style.transition="none";setTimeout(function(){try{go(%d);}catch(e){}},800);' % (i - 1)
                rc = shot(str(src), str(png), cfg["png"][0], cfg["png"][1], scale, css, js)
                report(rc, "png", i)
        else:
            # Editor architecture: PNG = full long image; pages/ = image set.
            pages_dir = out / "png" / "pages"
            pages_dir.mkdir(exist_ok=True)
            for i in range(1, count + 1):
                png = pages_dir / ("page-%02d.png" % i)
                css = no_margin + hide + show_n(i)
                rc = shot(str(src), str(png), cfg["png"][0], cfg["png"][1], scale, css)
                report(rc, "pages", i)
            long_h = count * cfg["sheet"][1]
            full_png = out / "png" / ("%s-full.png" % args.type)
            long_css = no_margin + ".sheet{page-break-after:auto!important;break-after:auto!important}"
            long_css += LONG_PNG_VH_FIXES.get(args.type, "")
            rc = shot(str(src), str(full_png), cfg["png"][0], long_h, scale, extra_css=long_css)
            report(rc, "png full", full_png.name)
    else:
        png = out / "png" / ("%s-full.png" % args.type)
        if cfg.get("dynamic"):
            w = args.width or cfg.get("width", 1280)
            _, height, _ = profile(str(src), web=args.type == "ppt-web", width=w)
            if not height:
                raise SystemExit("无法获取页面高度，已停止渲染，避免输出尺寸错误的图片。")
            h = height
            print("profile height:", h)
        else:
            w, h = cfg["sheet"] or (1280, 800)
        css = "" if cfg.get("dynamic") else "body{margin:0}.canvas{margin:0!important;box-shadow:none!important}"
        rc = shot(str(src), str(png), w, h, scale, extra_css=css)
        report(rc, "png full")

    pdf = out / "pdf" / ("%s.pdf" % args.type)
    if args.type == "mobile-long":
        if rc != 0 or not png.exists():
            raise SystemExit("PNG 截图失败，已跳过 PDF 生成。请先处理上面的截图错误。")
        from PIL import Image  # deferred import: keeps the import-time chain third-party-free
        with Image.open(str(png)) as im:
            im.convert("RGB").save(str(pdf), "PDF", resolution=96.0)
        print("OK", "pdf long")
    else:
        rc = to_pdf(str(src), str(pdf))
        report(rc, "pdf")

    if failed:
        raise SystemExit(1)
    print("output:", out)


if __name__ == "__main__":
    run_main(main, next_step="请根据上面的提示处理；缺少依赖时运行 install.bat（Windows）或 install.sh（macOS/Linux）")
