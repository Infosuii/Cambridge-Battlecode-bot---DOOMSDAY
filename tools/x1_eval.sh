#!/bin/bash
# Anti-overfit evaluation for the x1 line (teammate findings 2026-11-01: ladder-map-only results overfit v81's tables,
# single builds hide chaos): a candidate bot on the 70 ladder maps AND 50 unseen generated maps (maps/x1-unseen),
# against v81hl and its seed-2/seed-3 builds. Usage: bash tools/x1_eval.sh BOT [TAG] ["--set ..."]
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; BOT=$1; TAG=${2:-$1}; EXTRA=${3:-}
for opp in v81hl v81hl-s2 v81hl-s3; do
  for set in ladder unseen; do
    name=x1e-$TAG-$set-$opp-01
    [ -f research/dz/runs/$name/results.json ] && continue
    [ -e artifacts/tmp/dz/$name ] && continue
    M=""; [ $set = unseen ] && M="--map-dir maps/x1-unseen"
    "$PY" tools/dz.py smoke --name $name --pool $M --opponent $opp --candidate-bot $BOT --workers ${WORKERS:-3} $EXTRA > artifacts/tmp/$name.log 2>&1
    echo "$name: $(grep -o '"wins": [0-9]*' artifacts/tmp/$name.log | head -1) $(grep -o '"games": [0-9]*' artifacts/tmp/$name.log | head -1)"
  done
done
echo X1E_${TAG}_DONE
