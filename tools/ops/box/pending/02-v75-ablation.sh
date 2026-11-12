#!/bin/bash
# v75 ablations vs v74h (120 maps, both sides, seeds 1-3; 720 games each). Results: ops/box/results/02-*.json
W=$(( $(nproc) - 2 ))
"$PY" tools/lab/screen120.py --name s2-v75-fixes-only --cand "bots/v75:V70_DRAFT_TABLE=0;V71_MAP_KNOBS=0" --base bots/v74h --workers $W | tail -1 > ops/box/results/02-fixes-only.json
"$PY" tools/lab/screen120.py --name s3-v75-tables-only --cand "bots/v75:V68_SIEGE_FIX=0;V69_ISLAND=0;V69_CAPTURE_STALL=0" --base bots/v74h --workers $W | tail -1 > ops/box/results/02-tables-only.json
cat ops/box/results/02-*.json
