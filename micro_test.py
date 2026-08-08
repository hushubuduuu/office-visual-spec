# -*- coding: utf-8 -*-
"""Micro-tests: isolate whether dump-dom+file:// hangs, and whether the real
render paths (screenshot / print-to-pdf) work with this chromium build."""
import os
import subprocess
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


def make_probe(with_script=True):
    td = tempfile.mkdtemp(prefix="ovs-micro-")
    if with_script:
        html = TEMPLATE.read_text(encoding="utf-8").replace("</body>", PROBE)
    else:
        html = "<html><head><title>plain</title></head><body><h1>hi</h1></body></html>"
    p = Path(td) / "probe.html"
    p.write_text(html, encoding="utf-8")
    return p


def run_case(name, args, real_to=20):
    t0 = time.time()
    try:
        r = subprocess.run([CHROME, "--headless=new", "--disable-gpu"] + args,
                           capture_output=True, timeout=real_to)
        out = r.stdout.decode("utf-8", "replace")
        ok = "PROFILE|" in out
        print("%-52s rc=%d  %4.1fs  PROFILE=%s" % (name, r.returncode, time.time() - t0, ok))
    except subprocess.TimeoutExpired:
        print("%-52s TIMEOUT after %ds" % (name, real_to))


if __name__ == "__main__":
    udd = tempfile.mkdtemp(prefix="ovs-micro-udd-")
    p_script = make_probe(True)
    p_plain = make_probe(False)

    run_case("A dump-dom about:blank", ["--dump-dom", "about:blank", "--user-data-dir=" + udd])
    run_case("B dump-dom file:// (plain, no script)", ["--dump-dom", p_plain.as_uri(), "--user-data-dir=" + udd])
    run_case("C dump-dom file:// (with probe script)", ["--dump-dom", p_script.as_uri(), "--user-data-dir=" + udd, "--virtual-time-budget=6000"])
    run_case("D screenshot file:// (render path)", ["--screenshot=" + str(REPO / "shot-test.png"), "--window-size=794,1123", "--force-device-scale-factor=1", "--virtual-time-budget=12000", p_script.as_uri(), "--user-data-dir=" + udd])
    run_case("E print-to-pdf file:// (pdf path)", ["--print-to-pdf=" + str(REPO / "pdf-test.pdf"), "--no-pdf-header-footer", "--virtual-time-budget=12000", p_script.as_uri(), "--user-data-dir=" + udd])
    print("shot exists:", (REPO / "shot-test.png").exists(), " pdf exists:", (REPO / "pdf-test.pdf").exists())
