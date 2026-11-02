#!/bin/bash
# Per-map knob fit for x3 (like v92's ladfit): one ES per map over ladfit's 24 dimensions, both sides vs each opponent.
#   bash tools/x3_mapfit.sh            env: MAPS (default: the 16 pool maps without a ladder table), OPPS, ITERS, PAIRS
set -u
cd "$(dirname "$0")/.."
MAPS=${MAPS:-"03ambush-field 03colosseum 03contours 03fan 03homonoliths 03honeycomb 03membrane 03one-gem 03reef 03riverbed 03showdown 03shrines 03the-front 03twisty 03ultrastarvation 00happy-halloween"}
K=0,1,2,3,4,5,8,9,10,11,12,22,23,43,45,46,55,57,60,61,64,65,50,49
for m in $MAPS; do
  python tools/x3_knob_es.py --name mapfit-$m --knobs $K --map-dir maps/ladder-pool --maps $m --maps-per-iter 1 \
    --opps ${OPPS:-v92,v86h,x1bru} --scope 0 --iters ${ITERS:-6} --pairs ${PAIRS:-3} --sigma 0.5 --lr 1.0 \
    --workers ${WORKERS:-6} | tail -1 | sed "s/^/$m: /"
done
echo MAPFIT_DONE
