#!/usr/bin/env bash
# Counter search (tools/x3_counter.py): play x3 with variant k forced on every map, against OPP, on the whole pool,
# both sides. Run names PFX-OPP-kK (PFX default ctr2). Usage: bash tools/x3_counter_run.sh "0 1 2 ... 29" [OPP] [WORKERS]
# env EXTRA: more --set flags for every variant (e.g. "--set X1_MAPFIT=1" for the x3mf base)
set -u
KS=${1:-$(seq 0 29)}; OPP=${2:-v92}; WORKERS=${3:-6}
MAPS=$(ls maps/ladder-pool/*.map26a | xargs -n1 basename | sed 's/\.map26a$//')
for k in $KS; do
  name=${PFX:-ctr2}-$OPP-k$k
  [ -f artifacts/tmp/dz/$name/results.json ] && { echo "$name cached"; continue; }
  git checkout -q -- research/dz/SEED_LEDGER.md 2>/dev/null
  python tools/dz.py smoke --name $name --map-dir maps/ladder-pool --maps $MAPS --opponent $OPP --candidate-bot x3 \
    --workers $WORKERS --set X1_COUNTER=1 --set X1_COUNTER_FORCE=$k ${EXTRA:-} > artifacts/tmp/$name.log 2>&1
  python -c "import json;r=json.load(open('artifacts/tmp/dz/$name/results.json'));print('$name', sum(g['outcome']==('teamA' if g['side']=='A' else 'teamB') for g in r['per_game']), '/', len(r['per_game']))"
done
