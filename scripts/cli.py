# -*- coding: utf-8 -*-
"""Friendly CLI wrapper for office-visual-spec scripts."""
import os
import sys
import traceback
from pathlib import Path


def _relaunch_in_venv():
    """If a .venv exists and we are not already running inside it, re-exec
    under the venv interpreter so the dependencies installed there become
    visible. This is the safety net that prevents the classic dead loop:
    doctor/render run with the system python, fail on missing deps, tell the
    user to run install (which installs into .venv), then fail again.

    Returns True when the process was replaced (caller should stop), False
    when continuing with the current interpreter is fine.
    """
    root = Path(__file__).resolve().parent.parent
    if os.name == "nt":
        venv_py = root / ".venv" / "Scripts" / "python.exe"
    else:
        venv_py = root / ".venv" / "bin" / "python"
    if not venv_py.exists():
        return False
    current = Path(sys.executable).resolve()
    if current == venv_py.resolve():
        return False
    argv = [str(venv_py), str(Path(sys.argv[0]).resolve())] + sys.argv[1:]
    try:
        os.execv(str(venv_py), argv)
    except OSError:
        # venv interpreter is broken; fall back to the current interpreter so
        # doctor can still report the problem instead of dying silently.
        return False
    return True


def run_main(fn, next_step=""):
    if _relaunch_in_venv():
        return  # process was replaced by the venv interpreter
    try:
        fn()
    except SystemExit as e:
        if isinstance(e.code, int):
            raise SystemExit(e.code)
        if e.code is None:
            return
        message = str(e.code)
        print()
        print("出错了：" + message)
        if next_step:
            print("下一步：" + next_step)
        if os.environ.get("OVS_DEBUG", "").lower() in ("1", "true", "yes"):
            traceback.print_exc()
        raise SystemExit(1)
    except Exception as e:
        print()
        print("出错了：" + str(e))
        if next_step:
            print("下一步：" + next_step)
        if os.environ.get("OVS_DEBUG", "").lower() in ("1", "true", "yes"):
            traceback.print_exc()
        raise SystemExit(1)
