#!/bin/bash
# Duel set (top 12, 24 groups): arm live68 = platform 68 as it is, then v74h submitted and played on the same plan.
set -e
cd "$(dirname "$0")/../.."
export PYTHONIOENCODING=utf8 PY=/c/Users/info/nnbc-venv/Scripts/python.exe
P=research/v72/duel_top1_v74.json
"$PY" tools/replay/ladder_duel.py run --plan "$P" --version 68 --arm live68
bash tools/replay/duel_pipeline.sh "$P" live68 bots/v74h
