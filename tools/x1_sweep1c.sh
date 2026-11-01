#!/bin/bash
# Phase 1 completion: the 65 switched-off v81hl features (stage 1b list) on x1, vs the new benchmark v86h, scored on
# 19 ladder + 19 unseen maps (anti-overfit). Pairs: the same cells of x1e-cw-ladder-v86h-01 / x1e-cw-unseen-v86h-01.
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; SPEC=research/x1/sweep1c.json
LM=$("$PY" -c "import json;print(' '.join(json.load(open('$SPEC'))['maps']))")
UM=$("$PY" -c "import json;print(' '.join(json.load(open('$SPEC'))['unseen_maps']))")
FLAGS=$("$PY" -c "import json;print(' '.join(json.load(open('$SPEC'))['flags']))")
SNAP=research/x1/snapshots/sweep1c; [ -d $SNAP/src ] || { mkdir -p $SNAP && cp -r bots/x1-cw/src $SNAP/src; }
rm -rf bots/x1-sweepc && mkdir -p bots/x1-sweepc && cp -r $SNAP/src bots/x1-sweepc/src
for f in $FLAGS; do
  t=$(echo $f | tr 'A-Z_' 'a-z-')
  for set in ladder unseen; do
    name=x1-sc-$t-$set-v86h-01
    [ -f research/dz/runs/$name/results.json ] && continue
    [ -e artifacts/tmp/dz/$name ] && continue
    if [ $set = ladder ]; then M="--maps $LM"; else M="--map-dir maps/x1-unseen --maps $UM"; fi
    "$PY" tools/dz.py smoke --name $name $M --opponent v86h --candidate-bot x1-sweepc --workers ${WORKERS:-4} --set $f=1 > artifacts/tmp/$name.log 2>&1
  done
  echo "$f: ladder $(grep -o '"wins": [0-9]*' artifacts/tmp/x1-sc-$t-ladder-v86h-01.log | head -1) unseen $(grep -o '"wins": [0-9]*' artifacts/tmp/x1-sc-$t-unseen-v86h-01.log | head -1)"
done
echo X1_SWEEP1C_DONE
