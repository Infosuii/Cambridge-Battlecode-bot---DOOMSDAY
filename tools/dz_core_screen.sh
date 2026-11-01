#!/bin/bash
# Experiments on top of the candidate core (mastery draft + survive/prospect gear + fuel set + fast boot), snapshot
# research/dz/core-2026-11-01/source; pairs: dz-mastery-<opp>-01 (identical core binary 24d36aa56b12).
# Usage: bash tools/dz_core_screen.sh TAG "--set DZ_X=1 ..."
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; S=research/dz/core-2026-11-01/source; TAG=$1; EXTRA=$2
CORE="--set DZ_FAST_FIGHT=1 --set DZ_LATE_FIELD_GATE=1 --set DZ_FIELD_METER=1 --set DZ_FAST_BOOT=1 --set DZ_DRAFT_MASTERY=1 --set DZ_GEAR_SURVIVE=1 --set DZ_GEAR_PROSPECT=1"
for opp in v81hl v85 v76 v65; do
  name=dz-core-$TAG-$opp-01
  [ -f research/dz/runs/$name/results.json ] && continue
  [ -e artifacts/tmp/dz/$name ] && continue
  "$PY" tools/dz.py smoke --name $name --pool --opponent $opp --workers ${WORKERS:-2} $CORE $EXTRA --source $S > artifacts/tmp/core_$name.log 2>&1
  echo "$name: $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/core_$name.log | tail -1) $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/core_$name.log | head -1)"
done
echo CORE_${TAG}_DONE
