#!/usr/bin/env bash
# Cumulative chain on v139, one feature per step: each step is paired against the previous step on both panels
# (final53 x 6 pool opponents, new83 x 3 held-out opponents). usage: seq.sh RUN PREV_RUN_PREFIX PREV_NAME A=dir B=dir
#   A is tested against PREV (stored runs PREV_RUN_PREFIX-final53/-new83, candidate PREV_NAME); B (speculative) against A.
set -u
cd /c/Users/info/neural-networkk-battlecode || exit 1
R=artifacts/tmp/rl_env_1104
E=runs/rl_env_1104/eval
PY=C:/Users/info/.venvs/rlenv/Scripts/python
CAMBC=/c/Users/info/.venvs/cambc5/Scripts/cambc.exe
RUN=$1; PREV=$2; PNAME=$3; A=$4; B=${5:-}
AN=${A%%=*}; BN=${B%%=*}
CANDS="--candidate $A"
[ -n "$B" ] && CANDS="$CANDS --candidate $B"
EVAL_MAP_DIR=artifacts/tmp/final_maps CAMBC=$CAMBC $PY tools/rl_env_1104/eval/run_eval.py \
  --manifest research/rl_env_1104/candidates/manifests/final53_1108.json --split development $CANDS --reference $AN \
  --opponent v112opp=$R/eval-bots/v112opp --opponent nnfinal=$R/v111base/nnfinal/nnfinal.wasm --opponent v86h=bots/v86h \
  --opponent x3inv=bots/x3inv --opponent x3mf2=bots/x3mf2 --opponent x3ctr3=bots/x3ctr3 \
  --release --jobs 7 --out $E/$RUN-final53 > $E/$RUN-final53.log 2>&1
EVAL_MAP_DIR=artifacts/tmp/ladderpool_maps CAMBC=$CAMBC $PY tools/rl_env_1104/eval/run_eval.py \
  --manifest research/rl_env_1104/candidates/manifests/new83_1108.json --split development $CANDS --reference $AN \
  --opponent x3inv=bots/x3inv --opponent x3mf2=bots/x3mf2 --opponent x3ctr3=bots/x3ctr3 \
  --release --jobs 7 --out $E/$RUN-new83 > $E/$RUN-new83.log 2>&1
for p in final53 new83; do
  echo "== $AN vs $PNAME ($p)"; $PY -I tools/rl_env_1104/eval/pair_runs.py --ref $E/$PREV-$p:$PNAME --cand $E/$RUN-$p:$AN 2>&1 | grep -E "COMPLETE|INCOMPLETE" | sed -E 's/ci95.*//'
  [ -n "$B" ] && { echo "== $BN vs $AN ($p)"; $PY -I tools/rl_env_1104/eval/pair_runs.py --ref $E/$RUN-$p:$AN --cand $E/$RUN-$p:$BN 2>&1 | grep -E "COMPLETE|INCOMPLETE" | sed -E 's/ci95.*//'; }
done
echo SEQ_DONE $RUN
