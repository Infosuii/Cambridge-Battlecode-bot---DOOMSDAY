#!/bin/bash
# League baseline for a candidate bot (default v81hl): 70 maps x 2 sides vs each opponent. Usage: BOT=v81hl bash tools/x1_league.sh
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; BOT=${BOT:-v81hl}
for opp in v81hl v85 v76 v65 dz; do
  name=x1-base-$BOT-$opp-01
  [ -f research/dz/runs/$name/results.json ] && continue
  [ -e artifacts/tmp/dz/$name ] && continue
  "$PY" tools/dz.py smoke --name $name --pool --opponent $opp --candidate-bot $BOT --workers ${WORKERS:-2} > artifacts/tmp/x1_$name.log 2>&1
  echo "$name: $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/x1_$name.log | tail -1) $(grep -o '"wins": [0-9]*' artifacts/tmp/x1_$name.log | head -1) $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/x1_$name.log | head -1)"
done
echo X1_LEAGUE_DONE
