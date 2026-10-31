#!/bin/bash
# B1 EE3 v2 (additive engagements only; provisional enemy model, 56 v76 games) full-pool screens, from the frozen snapshot
# research/dz/b1-2026-11-01/source_ee3v2. Paired baselines: dz-carrier-priority-v76-check-01, -v65-full-01.
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; S=research/dz/b1-2026-11-01/source_ee3v2
for opp in v76 v65; do
  name=dz-ee3v2-$opp-01
  [ -f research/dz/runs/$name/results.json ] && continue
  "$PY" tools/dz.py smoke --name $name --pool --opponent $opp --workers ${WORKERS:-2} --set DZ_EE3=1 --source $S > artifacts/tmp/b1_$name.log 2>&1
  echo "$name: $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/b1_$name.log | tail -1) $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/b1_$name.log | head -1)"
done
echo B1_DONE
