#!/usr/bin/env bash
# Independent check of a per-map profile table: the 83 unrecognised maps, opponents NOT used in selection
# (x3inv, x3mf2, x3ctr3), both sides, paired with v112. usage: bash tools/rl_env_1104/train/table_validate.sh OUT name=dir [name=dir ...]
set -euo pipefail
OUT="$1"; shift
R=artifacts/tmp/rl_env_1104
CANDS=(--candidate v112=$R/v112/x)
for x in "$@"; do CANDS+=(--candidate "$x"); done
EVAL_MAP_DIR=artifacts/tmp/ladderpool_maps CAMBC=/c/Users/info/.venvs/cambc5/Scripts/cambc.exe C:/Users/info/.venvs/rlenv/Scripts/python \
  tools/rl_env_1104/eval/run_eval.py --manifest research/rl_env_1104/candidates/manifests/new83_1108.json --split development \
  "${CANDS[@]}" --reference v112 --opponent x3inv=bots/x3inv --opponent x3mf2=bots/x3mf2 --opponent x3ctr3=bots/x3ctr3 \
  --release --jobs 7 --out "runs/rl_env_1104/eval/$OUT"
