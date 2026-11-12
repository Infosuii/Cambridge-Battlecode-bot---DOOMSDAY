#!/usr/bin/env bash
# Per-map profile selection on the 83 maps v112 does not recognise: v112 + one research/v71 profile (new maps only) per
# candidate, paired against v112 on identical cells. usage: bash tools/rl_env_1104/train/profile_select.sh OUT "p1 p2 ..."
set -euo pipefail
OUT="$1"; PROFS="$2"
R=artifacts/tmp/rl_env_1104
CANDS=(--candidate v112=$R/v112/x)
for p in $PROFS; do CANDS+=(--candidate "$p=$R/prof_$p"); done
EVAL_MAP_DIR=artifacts/tmp/ladderpool_maps CAMBC=/c/Users/info/.venvs/cambc5/Scripts/cambc.exe C:/Users/info/.venvs/rlenv/Scripts/python \
  tools/rl_env_1104/eval/run_eval.py --manifest research/rl_env_1104/candidates/manifests/new83_1108.json --split development \
  "${CANDS[@]}" --reference v112 --opponent v112opp=$R/eval-bots/v112opp --opponent nnfinal=$R/v111base/nnfinal/nnfinal.wasm \
  --opponent v86h=bots/v86h --release --jobs 7 --out "runs/rl_env_1104/eval/$OUT"
