# -*- coding: utf-8 -*-
"""Isolate: is the hang caused by the template content, the setTimeout probe
script, or the dump-dom/pdf mode itself?"""
import subprocess
import tempfile
import time
from pathlib import Path

CHROME = r"C:\Users\Mangetout\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe"
REPO = Path(__file__).resolve().parent
TEMPLATE = REPO / "templates" / "a4-summary.html"

PROBE_SCRIPT = """<script>
setTimeout(function(){
  document.title='PROFILE|H100|W100';
}, 1600);
</script></body>"""


def write_html(name, content):
    td = tempfile.mkdtemp(prefix="ovs-iso-")
    p = Path(td) / "p.html"
    p.write_text(content, encoding="utf-8")
    return p


def run_case(name, args, real_to=15):
    t0 = time.time()
    try:
        r = subprocess.run([CHROME, "--headless=new", "--disable-gpu"] + args,
                           capture_output=True, timeout=real_to)
        out = r.stdout.decode("utf-8", "replace")
        print("%-52s rc=%d  %4.1fs  title-set=%s" % (name, r.returncode, time.time() - t0, "PROFILE|" in out))
    except subprocess.TimeoutExpired:
        print("%-52s TIMEOUT after %ds" % (name, real_to))


if __name__ == "__main__":
    udd = tempfile.mkdtemp(prefix="ovs-iso-udd-")
    tpl_raw = TEMPLATE.read_text(encoding="utf-8")
    tpl_no_script = tpl_raw  # template untouched (it has no probe script)
    tiny = "<html><head><title>t</title></head><body>" + PROBE_SCRIPT
    tiny_no_script = "<html><head><title>t</title></head><body><h1>hi</h1></body></html>"

    p_tpl = write_html("tpl", tpl_raw)
    p_tiny = write_html("tiny", tiny)
    p_tiny_ns = write_html("tiny-ns", tiny_no_script)

    run_case("F dump-dom a4 template (no script)", ["--dump-dom", p_tpl.as_uri(), "--user-data-dir=" + udd, "--virtual-time-budget=6000"])
    run_case("G dump-dom tiny html + setTimeout", ["--dump-dom", p_tiny.as_uri(), "--user-data-dir=" + udd, "--virtual-time-budget=6000"])
    run_case("H dump-dom tiny html no script", ["--dump-dom", p_tiny_ns.as_uri(), "--user-data-dir=" + udd, "--virtual-time-budget=6000"])
    run_case("I print-to-pdf tiny + setTimeout", ["--print-to-pdf=" + str(REPO / "iso.pdf"), "--no-pdf-header-footer", p_tiny.as_uri(), "--user-data-dir=" + udd, "--virtual-time-budget=6000"])
    run_case("J print-to-pdf tiny no script", ["--print-to-pdf=" + str(REPO / "iso2.pdf"), "--no-pdf-header-footer", p_tiny_ns.as_uri(), "--user-data-dir=" + udd, "--virtual-time-budget=6000"])
    run_case("K dump-dom about:blank full flags", ["--disable-dev-shm-usage", "--disable-background-networking", "--disable-component-update", "--disable-default-apps", "--disable-sync", "--metrics-recording-only", "--no-first-run", "--disable-features=OptimizationHints,MediaRouter,Translate,ClientSidePhishingDetection", "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost", "--user-data-dir=" + udd, "--dump-dom", "about:blank"])
