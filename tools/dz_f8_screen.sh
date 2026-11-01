#!/bin/bash
# F8 mastery draft (DZ_DRAFT_MASTERY + survive/prospect gear) with the fuel set + fast boot, snapshot
# research/dz/f8-2026-11-01/source; pairs: dz-fastboot-<opp>-01 (v76, v65, v74, v81hl).
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; S=research/dz/f8-2026-11-01/source
F="--set DZ_FAST_FIGHT=1 --set DZ_LATE_FIELD_GATE=1 --set DZ_FIELD_METER=1 --set DZ_FAST_BOOT=1"
for opp in v81hl v74 v76 v65; do
  name=dz-mastery-$opp-01
  [ -f research/dz/runs/$name/results.json ] && continue
  [ -e artifacts/tmp/dz/$name ] && continue
  "$PY" tools/dz.py smoke --name $name --pool --opponent $opp --workers ${WORKERS:-2} $F --set DZ_DRAFT_MASTERY=1 --set DZ_GEAR_SURVIVE=1 --set DZ_GEAR_PROSPECT=1 --source $S > artifacts/tmp/f8_$name.log 2>&1
  echo "$name: $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/f8_$name.log | tail -1) $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/f8_$name.log | head -1)"
done
echo F8_DONE
