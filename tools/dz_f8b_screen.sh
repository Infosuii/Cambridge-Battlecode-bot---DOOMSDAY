#!/bin/bash
# Mastery draft vs v85 (unseen) and idle (V-E3), with fast-boot pairs, snapshot research/dz/f8-2026-11-01/source.
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; S=research/dz/f8-2026-11-01/source
F="--set DZ_FAST_FIGHT=1 --set DZ_LATE_FIELD_GATE=1 --set DZ_FIELD_METER=1 --set DZ_FAST_BOOT=1"
for job in "fastboot v85 0" "mastery v85 1" "mastery idle81 1"; do
  set -- $job; name=dz-$1-$2-01
  [ -f research/dz/runs/$name/results.json ] && continue
  [ -e artifacts/tmp/dz/$name ] && continue
  X=""; [ $3 = 1 ] && X="--set DZ_DRAFT_MASTERY=1 --set DZ_GEAR_SURVIVE=1 --set DZ_GEAR_PROSPECT=1"
  "$PY" tools/dz.py smoke --name $name --pool --opponent $2 --workers ${WORKERS:-2} $F $X --source $S > artifacts/tmp/f8b_$name.log 2>&1
  echo "$name: $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/f8b_$name.log | tail -1)"
done
echo F8B_DONE
