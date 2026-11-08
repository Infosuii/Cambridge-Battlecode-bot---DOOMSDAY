#!/usr/bin/env bash
# Claude's CPU PPO retrain of the v112 target network on top of a patched base bot.
# usage: bash cl_train.sh RUN_NAME ITERS GAMES EVAL_EVERY [BASE_BOT]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
RUN="$1"; ITERS="$2"; GAMES="$3"; EVERY="$4"; BASE="${5:-cl112}"
export TRAIN_CPU=1
export TRAIN_JOBS="${TRAIN_JOBS:-6}"
export TRAIN_MIN_FREE_GB="${TRAIN_MIN_FREE_GB:-0.6}"
export TRAIN_GAME_MIN_FREE_GB="${TRAIN_GAME_MIN_FREE_GB:-0.4}"
export TRAIN_TORCH_THREADS="${TRAIN_TORCH_THREADS:-6}"
export TRAIN_RUN="$RUN"
export TRAIN_BOT_PREFIX="${RUN}_"
export TRAIN_BASE="$BASE"
export TRAIN_INITIAL="$HERE/training/runs/release-es/auto_es_g12_parent.pt"
export TRAIN_CRITIC="$HERE/reference/nn-rl6-original/nn_rl6/value_10.pt"
export TRAIN_LEAGUE="${TRAIN_LEAGUE:-[[\"v112\",0.2],[\"nnfinal\",0.15],[\"v86h\",0.1],[\"x3inv\",0.1],[\"v111\",0.1],[\"nnm4\",0.1],[\"v92\",0.05],[\"ref_x1\",0.05],[\"ref_x3ctr\",0.05],[\"ref_p65pack\",0.1]]}"
export TRAIN_MAPSETS='[["maps_ladder96",0.8],["maps_pooltrain",0.2]]'
export TRAIN_EVAL_MAPS="${TRAIN_EVAL_MAPS:-maps_sel12}"
export TRAIN_EVAL_OPP="${TRAIN_EVAL_OPP:-v112,nnfinal,v86h,x3inv}"
PY="${PY:-C:/Users/info/.venvs/rlenv/Scripts/python}"
cd "$HERE/training"
exec "$PY" -P agent2/lab/train.py "runs/$RUN" "$TRAIN_INITIAL" "$ITERS" --games "$GAMES" --eval-every "$EVERY"
