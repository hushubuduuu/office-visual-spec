# -*- coding: utf-8 -*-
"""Flag-matrix test: find which flag combination makes playwright chromium
complete the PROFILE probe (virtual-time-budget + dump-dom + file://)."""
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CHROME = r"C:\Users\Mangetout\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe"
REPO = Path(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = REPO / "templates" / "a4-summary.html"

PROBE = """<script>
setTimeout(function(){
  var out = Array.from(document.querySelectorAll('.sheet, .canvas')).map(function(s,i){
    return (i+1)+':' + Math.round(s.scrollHeight) + '/' + Math.round(s.clientHeight);
  }).join(',');
  var h = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
  var w = Math.max(document.body.scrollWidth, document.documentElement.scrollWidth);
  document.title='PROFILE|' + out + '|H' + h + '|W' + w;
}, 1600);
</script></body>"""

NET_FLAGS = [
    "--disable-background-networking", "--disable-component-update",
    "--disable-default-apps", "--disable-sync", "--metrics-recording-only",
    "--no-first-run",
    "--disable-features=OptimizationHints,MediaRouter,Translate,ClientSidePhishingDetection",
    "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost",
]


def make_probe():
    td = tempfile.mkdtemp(prefix="ovs-matrix-probe-")
    html = TEMPLATE.read_text(encoding="utf-8").replace("</body>", PROBE)
    p = Path(td) / "probe.html"
    p.write_text(html, encoding="utf-8")
    return p


def run_case(name, extra, use_net=True, budget="6000", use_dump=True, headless="--headless=new", timeout_flag=None, real_to=25):
    probe = make_probe()
    udd = tempfile.mkdtemp(prefix="ovs-matrix-udd-")
    args = [CHROME] + extra + [headless, "--disable-gpu", "--disable-dev-shm-usage"]
    if use_net:
        args += NET_FLAGS
    args += ["--user-data-dir=" + udd]
    if budget:
        args.append("--virtual-time-budget=" + budget)
    if timeout_flag:
        args.append(timeout_flag)
    if use_dump:
        args += ["--dump-dom", probe.as_uri()]
    t0 = time.time()
    try:
        r = subprocess.run(args, capture_output=True, timeout=real_to)
        out = r.stdout.decode("utf-8", "replace")
        ok = "PROFILE|" in out
        print("%-46s rc=%d  %4.1fs  PROFILE=%s" % (name, r.returncode, time.time() - t0, ok))
    except subprocess.TimeoutExpired:
        print("%-46s TIMEOUT after %ds" % (name, real_to))
    finally:
        try:
            import shutil
            shutil.rmtree(udd, ignore_errors=True)
            shutil.rmtree(str(probe.parent), ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    print("CHROME:", CHROME)
    run_case("1 full CI flags (reproduce)", ["--no-sandbox"], real_to=30)
    run_case("2 no --no-sandbox", [], real_to=30)
    run_case("3 no network flags", ["--no-sandbox"], use_net=False, real_to=30)
    run_case("4 no net, no no-sandbox", [], use_net=False, real_to=30)
    run_case("5 budget=0 (no virtual time)", ["--no-sandbox"], use_net=False, budget="0", real_to=30)
    run_case("6 --timeout=15000 real", ["--no-sandbox"], use_net=False, budget=None, timeout_flag="--timeout=15000", real_to=30)
    run_case("7 old --headless", ["--no-sandbox"], use_net=False, headless="--headless", real_to=30)
