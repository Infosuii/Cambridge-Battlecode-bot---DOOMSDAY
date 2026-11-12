#!/bin/bash
# B1 EE3 v4 (surplus-only gate, DZ_FAST_FIGHT, DZ_LATE_FIELD_GATE, DZ_FIELD_METER; no local fight) and its fuel-only control
# (DZ_FAST_FIGHT + DZ_LATE_FIELD_GATE + DZ_FIELD_METER), vs v76 and v65, from snapshot research/dz/b1-2026-11-01/source_ee3v4.
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; S=research/dz/b1-2026-11-01/source_ee3v4
F="--set DZ_FAST_FIGHT=1 --set DZ_LATE_FIELD_GATE=1 --set DZ_FIELD_METER=1"
for opp in v76 v65; do
  for kind in fuelctl4 ee3v4; do
    name=dz-$kind-$opp-01
    [ -f research/dz/runs/$name/results.json ] && continue
    [ -e artifacts/tmp/dz/$name ] && continue
    extra=""; [ $kind = ee3v4 ] && extra="--set DZ_EE3=1"
    "$PY" tools/dz.py smoke --name $name --pool --opponent $opp --workers ${WORKERS:-2} $F $extra --source $S > artifacts/tmp/b1v4_$name.log 2>&1
    echo "$name: $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/b1v4_$name.log | tail -1) $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/b1v3_$name.log | head -1) $(grep -o '"fuel_p99": [0-9]*' artifacts/tmp/b1v3_$name.log | head -1)"
  done
done
echo B1V4_DONE
