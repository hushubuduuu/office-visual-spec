# -*- coding: utf-8 -*-
"""Environment doctor for office-visual-spec."""
import importlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from chrome_common import detect_browser, run_headless
from cli import run_main

CHECKS = []


def check(name, ok, detail, hint="", warn=False):
    """Record one check. warn=True downgrades a failure to a warning:
    it is printed with ⚠ and does not affect the exit code."""
    CHECKS.append((name, ok, detail, hint, warn))


def main():
    py_ok = sys.version_info >= (3, 10)
    py_hint = "请安装 Python 3.10 或更高版本"
    if sys.platform == "darwin":
        py_hint += "（macOS: brew install python@3.12；Apple Silicon 先执行 eval \"$(/opt/homebrew/bin/brew shellenv)\" 再重跑）"
    check("Python 3.10+", py_ok, sys.version.split()[0], py_hint)

    for mod in ["PIL", "pptx"]:
        try:
            importlib.import_module(mod)
            check(mod, True, "已安装", "")
        except Exception:
            check(mod, False, "未安装", "请运行 install.bat 或 install.sh 安装依赖")
    try:
        importlib.import_module("pymupdf")  # PyMuPDF >= 1.24 提供顶层 pymupdf 包
        check("PyMuPDF", True, "已安装", "")
    except Exception:
        try:
            importlib.import_module("fitz")  # 旧版 PyMuPDF 兼容层
            check("PyMuPDF", True, "已安装（fitz 兼容层）", "")
        except Exception:
            check("PyMuPDF", False, "未安装", "请运行 install.bat 或 install.sh 安装依赖")

    node = shutil.which("node")
    if node:
        try:
            r = subprocess.run([node, "--version"], capture_output=True, timeout=10, text=True)
            version = (r.stdout or r.stderr).strip()
            ok = version.startswith("v") and len(version) > 1 and version[1:2].isdigit() and int(version[1:].split(".")[0]) >= 18
            check("Node.js 18+", ok, version, "Node 仅用于 validate-html 结构自检，不影响渲染导出；可忽略，或安装 Node.js 18+", warn=True)
        except Exception as e:
            check("Node.js 18+", False, str(e), "Node 仅用于 validate-html 结构自检，不影响渲染导出；可忽略，或安装 Node.js 18+", warn=True)
    else:
        check("Node.js 18+", False, "未找到 node", "Node 仅用于 validate-html 结构自检，不影响渲染导出；可忽略，或安装 Node.js 18+", warn=True)

    safari_hint = ""
    if sys.platform == "darwin" and Path("/Applications/Safari.app").exists():
        safari_hint = "；仅检测到 Safari，它不支持 headless 渲染，请安装 Chrome/Chromium/Edge"
    try:
        browser = detect_browser()
        check("Chrome/Edge 浏览器", browser is not None, str(browser) if browser else "未找到", "请安装 Chrome/Edge" + safari_hint + "，或设置 OVS_BROWSER")
    except SystemExit as e:
        check("Chrome/Edge 浏览器", False, str(e), "请安装浏览器" + safari_hint + "，或设置 OVS_BROWSER")
        browser = None

    try:
        with tempfile.TemporaryFile(prefix="ovs-doctor-"):
            pass
        check("临时目录可写", True, tempfile.gettempdir(), "")
    except Exception as e:
        check("临时目录可写", False, str(e), "请检查系统临时目录权限")

    if browser:
        try:
            r = run_headless(browser, ["--dump-dom", "about:blank"], timeout=20)
            ok = r.returncode == 0
            detail = "可以启动" if ok else r.stderr.decode("utf-8", "ignore")[-160:]
            check("浏览器可启动", ok, detail, "请检查浏览器安装或运行环境，必要时设置 OVS_BROWSER")
        except Exception as e:
            check("浏览器可启动", False, str(e), "请检查浏览器安装或运行环境，必要时设置 OVS_BROWSER")

    print("office-visual-spec 环境自检")
    print("-" * 40)
    failed = 0
    warned = 0
    for name, ok, detail, hint, warn in CHECKS:
        if ok:
            print("✅ " + name + ": " + str(detail))
        elif warn:
            warned += 1
            print("⚠️ " + name + ": " + str(detail))
            if hint:
                print("    说明：" + hint)
        else:
            failed += 1
            print("❌ " + name + ": " + str(detail))
            if hint:
                print("    请处理：" + hint)
    print("-" * 40)
    if warned:
        print("共 %d 项警告（不影响渲染导出，可忽略）。" % warned)
    if failed:
        print("共 %d 项未通过（参考项，不阻塞开工；渲染/导出失败时按提示补齐依赖后回查 doctor）。" % failed)
        raise SystemExit(1)
    print("全部通过，可以开始使用。")


if __name__ == "__main__":
    run_main(main, next_step="缺少依赖时请运行 install.bat（Windows）或 install.sh（macOS/Linux）")
