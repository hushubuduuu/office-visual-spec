# -*- coding: utf-8 -*-
"""Friendly CLI wrapper for office-visual-spec scripts."""
import os
import sys
import traceback


def run_main(fn, next_step=""):
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
