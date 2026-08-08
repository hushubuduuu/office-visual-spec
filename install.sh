#!/usr/bin/env sh
set -e
cd "$(dirname "$0")"

# Find a Python 3.10+ interpreter. Prefer "python3"; fall back to versioned
# names and Homebrew's prefix. On Apple Silicon /opt/homebrew/bin is not on
# PATH by default, and the system /usr/bin/python3 is 3.9 on many macOS
# versions, so a plain "python3" probe can loop forever after the user
# installs a newer Homebrew Python.
find_python() {
  for candidate in \
    "python3" \
    "python3.13" \
    "python3.12" \
    "/opt/homebrew/bin/python3.13" \
    "/opt/homebrew/bin/python3.12" \
    "/usr/local/bin/python3.13" \
    "/usr/local/bin/python3.12"; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
      echo "$candidate"
      return 0
    fi
  done
  # Last resort: let brew tell us its prefix.
  if command -v brew >/dev/null 2>&1; then
    prefix="$(brew --prefix 2>/dev/null || true)"
    if [ -n "$prefix" ]; then
      for minor in 13 12; do
        candidate="$prefix/bin/python3.$minor"
        if [ -x "$candidate" ] && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
          echo "$candidate"
          return 0
        fi
      done
    fi
  fi
  return 1
}

PYTHON_BIN="$(find_python || true)"
if [ -z "$PYTHON_BIN" ]; then
  echo "Python 3.10 or newer is required."
  echo "  macOS: brew install python@3.12"
  echo "         Apple Silicon 需先让 brew 进入 PATH：eval \"\$(/opt/homebrew/bin/brew shellenv)\"，再重跑本脚本"
  echo "  Linux: use your package manager, e.g. sudo apt install python3 python3-venv"
  echo "Then run this script again."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  "$PYTHON_BIN" -m venv .venv
fi

. .venv/bin/activate
# pip upgrade failure is non-fatal: fall through to the dependency install,
# which retries via the Tsinghua mirror if the first attempt fails.
python -m pip install --upgrade pip --quiet || echo "警告：pip 升级失败，继续尝试安装依赖"
if [ -n "$OVS_PIP_INDEX" ]; then
  python -m pip install -r requirements.txt --index-url "$OVS_PIP_INDEX"
elif ! python -m pip install -r requirements.txt --timeout 30; then
  echo "First attempt failed. Retrying with Tsinghua mirror..."
  python -m pip install -r requirements.txt --timeout 60 --index-url https://pypi.tuna.tsinghua.edu.cn/simple
fi

echo "Setup complete. Running environment doctor..."
python scripts/doctor.py || {
  echo
  echo "doctor 有未通过项（参考项，不阻塞开工；渲染/导出失败时按提示补齐依赖后回查 doctor）。"
  echo "未找到浏览器时：可设置 OVS_BROWSER 指向 Chrome/Edge/Chromium 完整路径，"
  echo "  例如 macOS: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome；Linux: /usr/bin/google-chrome。"
  exit 1
}
