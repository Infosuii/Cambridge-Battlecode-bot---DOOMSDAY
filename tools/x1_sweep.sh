#!/bin/bash
# Stage 1 of the x1 feature sweep: each switched-off v81hl feature on 19 development maps vs v81hl, on top of the
# fast-siege base, from one frozen snapshot. Pair: the same cells of x1-fastsiege-v81hl-01 (deterministic).
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; SPEC=research/x1/sweep1.json
MAPS=$("$PY" -c "import json;print(' '.join(json.load(open('$SPEC'))['maps']))")
FLAGS=$("$PY" -c "import json;print(' '.join(json.load(open('$SPEC'))['flags']))")
SNAP=research/x1/snapshots/sweep1; [ -d $SNAP/src ] || { mkdir -p $SNAP && cp -r bots/x1/src $SNAP/src; }
rm -rf bots/x1-sweep && mkdir -p bots/x1-sweep && cp -r $SNAP/src bots/x1-sweep/src
for f in $FLAGS; do
  name=x1-sw-$(echo $f | tr 'A-Z_' 'a-z-')-v81hl-01
  [ -f research/dz/runs/$name/results.json ] && continue
  [ -e artifacts/tmp/dz/$name ] && continue
  "$PY" tools/dz.py smoke --name $name --maps $MAPS --opponent v81hl --candidate-bot x1-sweep --workers ${WORKERS:-3} --set X1_FAST_SIEGE=1 --set $f=1 > artifacts/tmp/$name.log 2>&1
  echo "$f: $(grep -o '"wins": [0-9]*' artifacts/tmp/$name.log | head -1) $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/$name.log | tail -1) $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/$name.log | head -1)"
done
echo X1_SWEEP1_DONE
