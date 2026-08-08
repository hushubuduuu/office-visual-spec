# -*- coding: utf-8 -*-
"""Shared headless Chrome/Edge flags, browser detection and launcher."""
import os
import shutil
import sys
import subprocess
import tempfile
from pathlib import Path

BROWSER_CANDIDATES = [
    # Windows
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    # macOS
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
    Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    Path("/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"),
    # Linux common paths
    Path("/usr/bin/google-chrome"),
    Path("/usr/bin/google-chrome-stable"),
    Path("/usr/bin/chromium"),
    Path("/usr/bin/chromium-browser"),
    Path("/usr/bin/microsoft-edge"),
    Path("/usr/bin/microsoft-edge-stable"),
    Path("/snap/bin/chromium"),
]

BROWSER_COMMANDS = [
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "microsoft-edge",
    "microsoft-edge-stable",
    "chrome",
]

_sandbox_state = None
_sandbox_warned = False


def detect_browser():
    override = os.environ.get("OVS_BROWSER", "").strip()
    if override:
        candidate = Path(override)
        if candidate.exists():
            return candidate
        found = shutil.which(override)
        if found:
            return Path(found)
        raise SystemExit("OVS_BROWSER 指向的浏览器不存在：" + override)
    for candidate in BROWSER_CANDIDATES:
        if candidate.exists():
            return candidate
    for name in BROWSER_COMMANDS:
        found = shutil.which(name)
        if found:
            return Path(found)
    return None


def safari_hint():
    if sys.platform == "darwin" and Path("/Applications/Safari.app").exists():
        return "；检测到 Safari，但它不支持 headless 渲染，请安装 Chrome、Chromium 或 Edge"
    return ""


def find_browser():
    browser = detect_browser()
    if browser is None:
        raise SystemExit("未找到 Chrome/Edge/Chromium。" + safari_hint() + "。请安装浏览器，或设置 OVS_BROWSER 指定浏览器路径。")
    return browser


def flags(*extra):
    base = ["--headless=new", "--disable-gpu", "--disable-dev-shm-usage"]
    if os.environ.get("OVS_NO_SANDBOX", "").lower() in ("1", "true", "yes"):
        base.append("--no-sandbox")
    if os.environ.get("OVS_ALLOW_NETWORK", "").lower() not in ("1", "true", "yes"):
        base += [
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-default-apps",
            "--disable-sync",
            "--metrics-recording-only",
            "--no-first-run",
            "--disable-features=OptimizationHints,MediaRouter,Translate,ClientSidePhishingDetection",
            "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost",
        ]
    return base + list(extra)


def _sandbox_supported(browser):
    global _sandbox_state
    if _sandbox_state is not None:
        return _sandbox_state

    def _probe(extra):
        # Fresh profile per attempt: a crashed first run poisons its
        # user-data-dir (singleton locks, partial files) and can crash a
        # retry that reuses it.
        with tempfile.TemporaryDirectory(prefix="ovs-sandbox-probe-", ignore_cleanup_errors=True) as td:
            args = [
                "--user-data-dir=" + td,
                "--virtual-time-budget=1500",
                "--dump-dom",
                "about:blank",
            ]
            try:
                r = subprocess.run([str(browser)] + extra + flags(*args), capture_output=True, timeout=15)
                return r.returncode == 0
            except subprocess.TimeoutExpired:
                return False

    if _probe([]):
        _sandbox_state = True
        return True
    if _probe(["--no-sandbox"]):
        _sandbox_state = False
        return False
    _sandbox_state = None
    return True


def run_headless(browser, args, timeout=None):
    global _sandbox_warned
    force_no_sandbox = os.environ.get("OVS_NO_SANDBOX", "").lower() in ("1", "true", "yes")
    if force_no_sandbox:
        # flags() already appends --no-sandbox when OVS_NO_SANDBOX is set.
        return subprocess.run([str(browser)] + flags(*args), capture_output=True, timeout=timeout)
    if not _sandbox_supported(browser):
        if not _sandbox_warned:
            print("WARN: 当前环境无法使用浏览器沙箱，已自动改用无沙箱模式；如不希望降级，请更换运行环境。", flush=True)
            _sandbox_warned = True
        return subprocess.run([str(browser), "--no-sandbox"] + flags(*args), capture_output=True, timeout=timeout)
    return subprocess.run([str(browser)] + flags(*args), capture_output=True, timeout=timeout)
