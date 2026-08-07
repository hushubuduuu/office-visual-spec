#!/usr/bin/env sh
cd "$(dirname "$0")"
if [ -x ".venv/bin/python" ]; then
  .venv/bin/python scripts/doctor.py
else
  python3 scripts/doctor.py
fi
