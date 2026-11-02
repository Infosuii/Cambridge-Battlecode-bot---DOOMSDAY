#!/bin/bash
# Per-map plan search for x3 on the competition maps v92's ladder fit does not cover (the 03 maps).
# Each config (plan id x start round) plays every map, both sides, vs each opponent; results.json per run.
#   bash tools/x3_mapplan_search.sh            env: OPPS, MAPS, WORKERS
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}
MAPS=${MAPS:-"03ambush-field 03colosseum 03contours 03fan 03homonoliths 03honeycomb 03membrane 03one-gem 03reef 03riverbed 03showdown 03shrines 03the-front 03twisty 03ultrastarvation 00happy-halloween"}
for opp in ${OPPS:-v92 v86h x1bru}; do
  for cfg in base p1r0 p2r0 p3r0 p4r0 p5r0 p6r0 p7r0 p8r0 p1r150 p2r150 p3r150 p4r150 p5r150 p6r150 p7r150 p8r150; do
    name=mp-$cfg-$opp-01
    [ -f artifacts/tmp/dz/$name/results.json ] && continue
    if [ $cfg = base ]; then SET=""; else
      id=${cfg:1:1}; r=${cfg#*r}; SET="--set X1_PLAN=1 --set X1_PLAN_ROUND=$r --set X1_PLAN_ID=$id"; fi
    "$PY" tools/dz.py smoke --name $name --map-dir maps/ladder-pool --maps $MAPS --opponent $opp --candidate-bot x3 \
      --workers ${WORKERS:-7} $SET > artifacts/tmp/$name.log 2>&1
    echo "$name: $(grep -o '"wins": [0-9]*' artifacts/tmp/$name.log | head -1)"
  done
done
echo MAPPLAN_DONE
