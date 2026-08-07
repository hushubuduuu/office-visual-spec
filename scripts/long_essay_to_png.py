# -*- coding: utf-8 -*-
"""Render a long-essay HTML file to a cropped mobile long PNG.

Usage:
  python long_essay_to_png.py input.html output.png [--width 1080] [--window-height 30000] [--top-pad 160] [--bottom-pad 180]
"""
import argparse
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

from chrome_common import find_browser, run_headless
from cli import run_main


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--window-height", type=int, default=30000)
    parser.add_argument("--top-pad", type=int, default=160)
    parser.add_argument("--bottom-pad", type=int, default=180)
    args = parser.parse_args()

    html = args.input.resolve()
    if not html.exists():
        raise SystemExit("找不到输入文件：" + str(html) + "，请检查路径是否正确。")
    out = args.output.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        shot = Path(tmp.name)

    try:
        r = run_headless(
            find_browser(),
            [
                "--hide-scrollbars",
                "--window-size=%d,%d" % (args.width, args.window_height),
                "--screenshot=" + str(shot),
                html.as_uri(),
            ],
            timeout=120,
        )
        if r.returncode != 0:
            raise SystemExit("浏览器渲染失败：" + r.stderr.decode("utf-8", "ignore")[-300:])

        img = Image.open(shot).convert("RGB")
        bg = Image.new("RGB", img.size, (253, 253, 251))
        diff = ImageChops.difference(img, bg)
        bbox = diff.getbbox()
        if bbox is None:
            raise SystemExit("截图内容为空，请检查 HTML 是否正常渲染。")
        if bbox[3] >= img.height - 1:
            print("WARN: 内容可能超出截图高度，已按当前窗口裁剪；如内容不完整，请增大 --window-height 或分屏导出。", flush=True)
        top = max(0, bbox[1] - args.top_pad)
        bottom = min(img.height, bbox[3] + args.bottom_pad)
        final = img.crop((0, top, img.width, bottom))
        final.save(out)
        print("saved", out)
        print("size", final.size)
    finally:
        shot.unlink(missing_ok=True)


if __name__ == "__main__":
    run_main(main, next_step="请根据上面的提示处理；缺少依赖时运行 install.bat（Windows）或 install.sh（macOS/Linux）")
