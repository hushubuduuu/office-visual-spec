# -*- coding: utf-8 -*-
"""Isolate Blocker 1: does doctor.py / emoji print crash when stdout is a pipe
on a GBK Windows system (no PYTHONUTF8)?"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.abspath(__file__))


def clean_env():
    return {k: v for k, v in os.environ.items()
            if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}


def run(cmd, cwd=REPO):
    r = subprocess.run(cmd, capture_output=True, cwd=cwd,
                       env=clean_env(), timeout=120)
    print("CMD:", " ".join(cmd))
    print("RC:", r.returncode)
    out = r.stdout.decode("utf-8", "replace")
    err = r.stderr.decode("utf-8", "replace")
    print("STDOUT (%d bytes):" % len(out))
    print(out[:800])
    if len(out) > 800:
        print("... [truncated]")
    print("STDERR (%d bytes):" % len(err))
    print(err[:400])
    print("-" * 60)


if __name__ == "__main__":
    print("PYTHONUTF8 in clean env:", clean_env().get("PYTHONUTF8", "<unset>"))
    # 1. minimal repro
    run([sys.executable, "-c", "print('\u2705 ok')"])
    # 2. doctor via system python (relaunch path)
    run([sys.executable, "scripts/doctor.py"])
    # 3. doctor via venv python directly (no relaunch)
    venv_py = os.path.join(REPO, ".venv", "Scripts", "python.exe")
    if os.path.exists(venv_py):
        run([venv_py, "scripts/doctor.py"])
    else:
        print("no venv python, skip #3")
