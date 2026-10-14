#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
research_python="${RESEARCH_PYTHON:-./.venv-research/Scripts/python.exe}"
"$research_python" -I -B tests/test_v2.py
"$research_python" -B evaluate.py --campaign v2 --method-version v1 --split test --mode full_paper_ablation
"$research_python" -B evaluate.py --campaign v2 --split test --mode full_paper_ablation
"$research_python" -I -B paper/update_round2.py
"$research_python" -I -B paper/build.py
"$research_python" -I -B paper/build_zh.py
