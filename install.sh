#!/usr/bin/env sh
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.10 or newer is required."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

. .venv/bin/activate
python -m pip install --upgrade pip
if [ -n "$OVS_PIP_INDEX" ]; then
  python -m pip install -r requirements.txt --index-url "$OVS_PIP_INDEX"
elif ! python -m pip install -r requirements.txt --timeout 30; then
  echo "First attempt failed. Retrying with Tsinghua mirror..."
  python -m pip install -r requirements.txt --timeout 60 --index-url https://pypi.tuna.tsinghua.edu.cn/simple
fi

echo "Setup complete. Running environment doctor..."
python scripts/doctor.py
