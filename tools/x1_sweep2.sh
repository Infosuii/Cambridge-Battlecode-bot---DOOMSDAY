#!/bin/bash
# Stage 2 of the x1 feature sweep: stage-1 survivors (and all of them combined) on all 70 maps vs v81hl, fast-siege
# base, snapshot research/x1/snapshots/sweep1. Pair: x1-fastsiege-v81hl-01.
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}
F="APEX_RECALL_TRAVEL APEX_FLEE_ALLY A2_CAMPWATCH APEX_POSITION NOVA_CI_LINK APEX_SNIPE APEX_GOLD_TAPER APEX_PAIR NOVA_RACE_BANK"
COMBO=""; for f in $F; do COMBO="$COMBO --set $f=1"; done
rm -rf bots/x1-sweep && mkdir -p bots/x1-sweep && cp -r research/x1/snapshots/sweep1/src bots/x1-sweep/src
run() { local name=$1; shift
  [ -f research/dz/runs/$name/results.json ] && return; [ -e artifacts/tmp/dz/$name ] && return
  "$PY" tools/dz.py smoke --name $name --pool --opponent v81hl --candidate-bot x1-sweep --workers ${WORKERS:-4} --set X1_FAST_SIEGE=1 "$@" > artifacts/tmp/$name.log 2>&1
  echo "$name: $(grep -o '"wins": [0-9]*' artifacts/tmp/$name.log | head -1) $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/$name.log | tail -1) $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/$name.log | head -1)"
}
run x1-s2-combo-v81hl-01 $COMBO
for f in $F; do run x1-s2-$(echo $f | tr 'A-Z_' 'a-z-')-v81hl-01 --set $f=1; done
echo X1_SWEEP2_DONE
