#!/bin/bash
# League check of the teammate's integrated DZ_ECONOMY_V2 candidate exactly as pushed at 6261950 (snapshot
# research/dz/econ2-league-2026-11-01/source; their code is not modified). Runs after the C1 screen.
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; S=research/dz/econ2-league-2026-11-01/source
while ! grep -q C1_DONE artifacts/tmp/c1.log 2>/dev/null; do sleep 120; done
for opp in v76 v65 v81hl; do
  name=dz-econ2-6261950-$opp-01
  [ -f research/dz/runs/$name/results.json ] && continue
  [ -e artifacts/tmp/dz/$name ] && continue
  "$PY" tools/dz.py smoke --name $name --pool --opponent $opp --workers ${WORKERS:-2} --set DZ_ECONOMY_V2=1 --source $S > artifacts/tmp/econ2_$name.log 2>&1
  echo "$name: $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/econ2_$name.log | tail -1) $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/econ2_$name.log | head -1)"
done
echo ECON2_DONE
