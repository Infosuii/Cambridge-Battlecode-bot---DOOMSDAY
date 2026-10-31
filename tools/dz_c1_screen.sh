#!/bin/bash
# C1 market claims (DZ_MARKET) full-pool screens from the frozen snapshot research/dz/c1-2026-11-01/source.
# Exit V-E1: idle income +10% vs dz-carrier-priority-idle-01; contested pairs: -v76-check-01, -v65-full-01.
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; S=research/dz/c1-2026-11-01/source
for opp in idle81 v76 v65; do
  name=dz-market-$opp-01
  [ -f research/dz/runs/$name/results.json ] && continue
  [ -e artifacts/tmp/dz/$name ] && continue
  "$PY" tools/dz.py smoke --name $name --pool --opponent $opp --workers ${WORKERS:-2} --set DZ_MARKET=1 --source $S > artifacts/tmp/c1_$name.log 2>&1
  echo "$name: $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/c1_$name.log | tail -1) $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/c1_$name.log | head -1)"
done
echo C1_DONE
