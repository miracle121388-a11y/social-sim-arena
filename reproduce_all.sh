#!/usr/bin/env bash
# Tested with Git for Windows Bash and Windows Python. No downloads or uploads.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "$SCRIPT_DIR"
if [[ -n "${RESEARCH_PYTHON:-}" ]]; then
  PYTHON_BIN="$RESEARCH_PYTHON"
elif [[ -x .venv-research/Scripts/python.exe ]]; then
  PYTHON_BIN=.venv-research/Scripts/python.exe
else
  PYTHON_BIN=python
fi
export PYTHONDONTWRITEBYTECODE=1
export PYTHONIOENCODING=utf-8
exec "$PYTHON_BIN" -B reproduce.py "$@"
