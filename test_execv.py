# -*- coding: utf-8 -*-
"""Verify whether cli.py's os.execv relaunch preserves exit codes on Windows,
and what exit code the empty-sheet failure path really produces."""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.abspath(__file__))


def run(cmd, cwd=None):
    r = subprocess.run(cmd, capture_output=True, cwd=cwd or REPO, timeout=120)
    return r


# 1) raw os.execv exit-code preservation
code = ("import os, sys; "
        "os.execv(sys.executable, [sys.executable, '-c', 'import sys; sys.exit(7)'])")
r1 = run([sys.executable, "-c", code])
print("os.execv exit-code test: RC =", r1.returncode, "(7 = preserved, 0 = lost)")

# 2) empty-sheet failure via system python (relaunch path)
r2 = run([sys.executable, "scripts/render-html.py", "a4", "no-sheet.html", "--check-only"])
print("empty-sheet (relaunch path) RC =", r2.returncode)
print("  OUT tail:", r2.stdout.decode("utf-8", "replace")[-100:].strip())

# 3) empty-sheet failure via venv python directly (no relaunch)
venv_py = os.path.join(REPO, ".venv", "Scripts", "python.exe")
if os.path.exists(venv_py):
    r3 = run([venv_py, "scripts/render-html.py", "a4", "no-sheet.html", "--check-only"])
    print("empty-sheet (venv direct) RC =", r3.returncode)
    print("  OUT tail:", r3.stdout.decode("utf-8", "replace")[-100:].strip())
