#!/usr/bin/env bash
# Fill the robust counter search (tools/x3_counter.py robust): for each opponent, play variants from k29 down,
# skipping any run already here or posted by a helper on comms (g3 L007, g5070 / g5060 ctr3).
#   bash tools/x3_counter_fill.sh "x1bru v86h x3inv" [WORKERS]
set -u
cd "$(dirname "$0")/.."
C=../x1-comms
for opp in $1; do
  for k in $(seq 29 -1 0); do
    git -C $C pull -q 2>/dev/null
    n=ctr3-$opp-k$k
    for f in research/dz/runs/$n/results.json $C/g3/results/L007/$n.json $C/g5070/results/ctr3/$n.json $C/g5060/results/ctr3/$n.json; do
      [ -f $f ] && { echo "$n done ($f)"; continue 2; }
    done
    PFX=ctr3 EXTRA="--set X1_MAPFIT=1" bash tools/x3_counter_run.sh "$k" $opp ${2:-12}
  done
done
echo FILL_DONE
