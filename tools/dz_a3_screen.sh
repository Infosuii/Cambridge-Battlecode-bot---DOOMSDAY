#!/bin/bash
# A3 DZ_GOLD_FIT screens (snapshot research/dz/a3-2026-11-01/source) after the ECONOMY_V2 league check.
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; S=research/dz/a3-2026-11-01/source
while ! grep -q ECON2_DONE artifacts/tmp/econ2.log 2>/dev/null; do sleep 120; done
for opp in v76 v65; do
  name=dz-goldfit-$opp-01
  [ -f research/dz/runs/$name/results.json ] && continue
  [ -e artifacts/tmp/dz/$name ] && continue
  "$PY" tools/dz.py smoke --name $name --pool --opponent $opp --workers ${WORKERS:-2} --set DZ_GOLD_FIT=1 --source $S > artifacts/tmp/a3_$name.log 2>&1
  echo "$name: $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/a3_$name.log | tail -1) $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/a3_$name.log | head -1)"
done
echo A3_DONE
