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

# --virtual-time-budget is known to hang the headless process on some
# environments (chromium issue 40219957, intermittent / environment-dependent
# rather than macOS-specific): the virtual clock never advances, so dump /
# screenshot / print never fire and the call hits the timeout. We cache the
# first hang and retry without the budget flag from then on.
_budget_ok = None  # None = untested; True = works; False = hangs

# Hard-disable the budget path (CI coverage of the fallback path).
if os.environ.get("OVS_NO_VIRTUAL_TIME", "").lower() in ("1", "true", "yes"):
    _budget_ok = False

# Injected into shot/pdf pages when the budget path hangs: forces CSS
# animations/transitions to complete instantly, so the captured frame equals
# the post-animation state without virtual-time fast-forwarding.
ANIM_COMPRESS_CSS = (
    "*{animation-duration:0.01s !important;animation-delay:0s !important;"
    "transition-duration:0.01s !important}"
)

# print-to-pdf is a synchronous snapshot taken at t=0, so even a compressed
# animation still captures the first keyframe (fill-mode:both from{opacity:0}
# renders blank). For PDFs we instead drop animations entirely so elements
# render their static (post-animation) styles.
ANIM_STATIC_CSS = "*{animation:none !important;transition:none !important}"


def detect_browser():
    override = os.environ.get("OVS_BROWSER", "").strip()
    if override:
        candidate = Path(override)
        if candidate.exists():
            return candidate
        found = shutil.which(override)
        if found:
            return Path(found)
        raise SystemExit(
            "OVS_BROWSER 未找到：" + override
            + "。命令名未在 PATH 中时，请改用浏览器完整路径，例如 "
            + "Windows: C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe；"
            + "macOS: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome；"
            + "Linux: /usr/bin/google-chrome"
        )
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
    if sys.platform == "darwin":
        # Fresh headless profiles on macOS can pop a "Chrome Safe Storage"
        # keychain prompt (a system dialog an agent cannot click), which
        # stalls rendering until timeout. Mock the keychain instead, and use
        # incognito (in-memory profile) as isolation: a --user-data-dir
        # pointing at a fresh directory hangs headless on macOS
        # (chromium issue 40133981).
        base.append("--use-mock-keychain")
        base.append("--incognito")
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


def _run_probe_direct(browser, args_fn, budget_ms, timeout=15):
    """Like run_headless_budget_safe but bypasses the sandbox probe (used
    inside _sandbox_supported itself to avoid recursion).

    Only a hang (TimeoutExpired) marks the budget path as broken. A nonzero
    exit code is a real failure of this particular run and must NOT poison the
    process-wide _budget_ok cache, otherwise every later export silently skips
    the budget path (no animation fast-forward) on a macOS/CI run.
    """
    global _budget_ok
    if _budget_ok is not False:
        try:
            r = subprocess.run([str(browser)] + flags(*args_fn("--virtual-time-budget=%d" % budget_ms)), capture_output=True, timeout=timeout)
            if r.returncode == 0:
                return r
            return r
        except subprocess.TimeoutExpired:
            _budget_ok = False
    return subprocess.run([str(browser)] + flags(*args_fn(None)), capture_output=True, timeout=timeout)


def _sandbox_supported(browser):
    global _sandbox_state
    if _sandbox_state is not None:
        return _sandbox_state

    def _probe(extra):
        # Fresh profile per attempt: a crashed first run poisons its
        # user-data-dir (singleton locks, partial files) and can crash a
        # retry that reuses it.
        with tempfile.TemporaryDirectory(prefix="ovs-sandbox-probe-", ignore_cleanup_errors=True) as td:
            def args_fn(budget):
                a = list(extra) + ["--dump-dom", "about:blank"]
                if budget:
                    a.insert(1, budget)
                # --user-data-dir hangs headless on macOS (issue 40133981);
                # incognito (from flags()) provides isolation there.
                if sys.platform != "darwin":
                    a.insert(1, "--user-data-dir=" + td)
                return a
            try:
                r = _run_probe_direct(browser, args_fn, 1500)
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


def run_headless_budget_safe(browser, args_fn, budget_ms, timeout, extra_flags=(), prepare_fallback=None):
    """Run headless Chrome, retrying without --virtual-time-budget on hang.

    args_fn(budget_flag_or_None) builds the full argument list (minus the
    common flags). Only a hang (TimeoutExpired) triggers the no-budget retry:
    a nonzero exit code is a real rendering error and is returned as-is, so a
    genuine failure is never masked by a fallback rerun. prepare_fallback() may
    rebuild the input page (e.g. inject ANIM_COMPRESS_CSS / ANIM_STATIC_CSS)
    before the no-budget retry.
    """
    global _budget_ok
    if _budget_ok is not False and budget_ms:
        try:
            r = run_headless(
                browser,
                list(extra_flags) + args_fn("--virtual-time-budget=%d" % budget_ms),
                timeout=timeout,
            )
            if r.returncode == 0:
                return r
            return r
        except subprocess.TimeoutExpired:
            pass
        _budget_ok = False
        if prepare_fallback:
            prepare_fallback()
    return run_headless(browser, list(extra_flags) + args_fn(None), timeout=timeout)
