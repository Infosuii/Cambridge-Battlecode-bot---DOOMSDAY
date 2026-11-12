#!/bin/bash
# Greedy combination of stage-2 winners on the fast-siege base, all 70 maps vs v81hl (pair x1-fastsiege-v81hl-01).
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}
rm -rf bots/x1-sweep && mkdir -p bots/x1-sweep && cp -r research/x1/snapshots/sweep1/src bots/x1-sweep/src
run() { local name=$1; shift
  [ -f research/dz/runs/$name/results.json ] && return; [ -e artifacts/tmp/dz/$name ] && return
  "$PY" tools/dz.py smoke --name $name --pool --opponent v81hl --candidate-bot x1-sweep --workers ${WORKERS:-4} --set X1_FAST_SIEGE=1 "$@" > artifacts/tmp/$name.log 2>&1
  echo "$name: $(grep -o '"wins": [0-9]*' artifacts/tmp/$name.log | head -1) $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/$name.log | tail -1)"
}
run x1-g2-v81hl-01 --set A2_CAMPWATCH=1 --set APEX_FLEE_ALLY=1 &
run x1-g3-v81hl-01 --set A2_CAMPWATCH=1 --set APEX_FLEE_ALLY=1 --set APEX_SNIPE=1 &
wait
run x1-g4-v81hl-01 --set A2_CAMPWATCH=1 --set APEX_FLEE_ALLY=1 --set APEX_SNIPE=1 --set APEX_PAIR=1 &
run x1-g2b-v81hl-01 --set A2_CAMPWATCH=1 --set APEX_SNIPE=1 &
wait
echo X1_GREEDY_DONE
