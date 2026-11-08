#!/usr/bin/env bash
# Final paired evaluation of retrain checkpoints (and other candidates) against v112 on the 53-map held-out panel.
# usage (repo root, Git Bash): bash tools/rl_env_1104/train/final_eval.sh OUT RUN "4 8 12 16" [extra name=dir ...]
set -euo pipefail
OUT="$1"; RUN="$2"; ITS="$3"; shift 3
R=artifacts/tmp/rl_env_1104
A=artifacts/tmp/agentic_restore/training
PY=C:/Users/info/.venvs/rlenv/Scripts/python
CANDS=(--candidate v112=$R/v112/x)
for it in $ITS; do
  W="$A/runs/$RUN/student_w_$it.h"
  [ -f "$W" ] || { echo "missing $W"; exit 1; }
  $PY -I tools/rl_env_1104/train/checkpoint_bot.py "$A/v4/bots/$(cat $A/runs/$RUN/base.txt)/src" "$W" "$R/ck_${RUN}_$it"
  CANDS+=(--candidate "${RUN}i$it=$R/ck_${RUN}_$it")
done
for x in "$@"; do CANDS+=(--candidate "$x"); done
EVAL_MAP_DIR=artifacts/tmp/final_maps CAMBC=/c/Users/info/.venvs/cambc5/Scripts/cambc.exe $PY tools/rl_env_1104/eval/run_eval.py \
  --manifest research/rl_env_1104/candidates/manifests/final53_1108.json --split development "${CANDS[@]}" --reference v112 \
  --opponent v112opp=$R/eval-bots/v112opp --opponent nnfinal=$R/v111base/nnfinal/nnfinal.wasm \
  --opponent v86h=bots/v86h --opponent x3inv=bots/x3inv --opponent x3mf2=bots/x3mf2 --opponent x3ctr3=bots/x3ctr3 \
  --release --jobs 7 --out "runs/rl_env_1104/eval/$OUT"
