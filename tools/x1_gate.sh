#!/bin/bash
# Full gate for an x1 candidate (research/x1/RETRY_QUEUE.md step R1): every map kind, both sides, vs v88 (bots/x2)
# and its seed-2 build (bots/x2-s2). Maze-style maps run once maps/x1-maze exists (Agent 2's maze-test + real200b).
#   bash tools/x1_gate.sh BOT TAG ["--set X1_FLAG=1 ..."]       env: OPPS, WORKERS, SETS
# Run names: x1g-TAG-SET-OPP-01 (research/dz/runs/<name>/results.json). Prints wins per cell and the total.
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; BOT=$1; TAG=${2:-$1}; EXTRA=${3:-}
SETS=${SETS:-"ladder styled maze"}
for opp in ${OPPS:-x2 x2-s2}; do
  for set in $SETS; do
    case $set in
      ladder) M="" ;;
      styled) M="--map-dir maps/x1-unseen" ;;
      pool) M="--map-dir maps/ladder-pool" ;;  # current competition map pool (cambc maps pull, 2 Nov)
      maze) [ -d maps/x1-maze ] || { echo "skip maze (maps/x1-maze missing)"; continue; }; M="--map-dir maps/x1-maze" ;;
    esac
    name=x1g-$TAG-$set-$opp-01
    if [ ! -f research/dz/runs/$name/results.json ]; then
      rm -rf artifacts/tmp/dz/$name
      "$PY" tools/dz.py smoke --name $name --pool $M --opponent $opp --candidate-bot $BOT --workers ${WORKERS:-6} $EXTRA > artifacts/tmp/$name.log 2>&1
    fi
    "$PY" - "$name" <<'EOF'
import json, sys
r = json.load(open(f'research/dz/runs/{sys.argv[1]}/results.json'))
print(f"{sys.argv[1]}: {r['wins']}/{r['games']} fuel_outs {r['fuel_outs']} sha {r['per_game'][0]['candidate_sha256'][:12]}")
EOF
  done
done
echo X1G_${TAG}_DONE
