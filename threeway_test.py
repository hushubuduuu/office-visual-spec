# -*- coding: utf-8 -*-
"""Clean 3-way comparison on the exact CI probe command:
playwright chromium vs playwright headless-shell vs Google Chrome."""
import subprocess
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent
TEMPLATE = REPO / "templates" / "a4-summary.html"

BROWSERS = {
    "pw-chromium": r"C:\Users\Mangetout\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe",
    "pw-headless-shell": r"C:\Users\Mangetout\AppData\Local\ms-playwright\chromium_headless_shell-1234\chrome-headless-shell-win64\chrome-headless-shell.exe",
    "google-chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
}

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


def run_case(browser, name, real_to=20):
    td = tempfile.mkdtemp(prefix="ovs-cmp-")
    udd = tempfile.mkdtemp(prefix="ovs-cmp-udd-")
    p = Path(td) / "probe.html"
    p.write_text(TEMPLATE.read_text(encoding="utf-8").replace("</body>", PROBE), encoding="utf-8")
    args = [browser, "--headless=new", "--disable-gpu", "--disable-dev-shm-usage",
            "--disable-background-networking", "--disable-component-update",
            "--disable-default-apps", "--disable-sync", "--metrics-recording-only",
            "--no-first-run",
            "--disable-features=OptimizationHints,MediaRouter,Translate,ClientSidePhishingDetection",
            "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost",
            "--user-data-dir=" + udd, "--virtual-time-budget=6000", "--dump-dom", p.as_uri()]
    t0 = time.time()
    try:
        r = subprocess.run(args, capture_output=True, timeout=real_to)
        out = r.stdout.decode("utf-8", "replace")
        print("%-18s %-34s rc=%d %4.1fs PROFILE=%s" % (name, browser.split("\\")[-1], r.returncode, time.time() - t0, "PROFILE|" in out))
    except subprocess.TimeoutExpired:
        print("%-18s %-34s TIMEOUT %ds" % (name, browser.split("\\")[-1], real_to))


if __name__ == "__main__":
    for name, path in BROWSERS.items():
        run_case(path, name)
