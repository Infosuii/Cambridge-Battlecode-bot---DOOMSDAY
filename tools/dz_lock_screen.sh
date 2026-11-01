#!/bin/bash
# DZ_ALTAR_LOCK screens (fuel set + fast boot), snapshot research/dz/lock-2026-11-01/source; pairs dz-fastboot-*-01
# (the same binary with the lock compiled out). Then the unseen opponents v74 and v81hl, paired with fastboot runs
# made here.
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; S=research/dz/lock-2026-11-01/source
F="--set DZ_FAST_FIGHT=1 --set DZ_LATE_FIELD_GATE=1 --set DZ_FIELD_METER=1 --set DZ_FAST_BOOT=1"
for job in "lock v76 1" "lock v65 1" "lock v74 1" "fastboot v74 0" "lock v81hl 1" "fastboot v81hl 0"; do
  set -- $job; name=dz-$1-$2-01
  [ -f research/dz/runs/$name/results.json ] && continue
  [ -e artifacts/tmp/dz/$name ] && continue
  "$PY" tools/dz.py smoke --name $name --pool --opponent $2 --workers ${WORKERS:-2} $F --set DZ_ALTAR_LOCK=$3 --source $S > artifacts/tmp/lock_$name.log 2>&1
  echo "$name: $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/lock_$name.log | tail -1) $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/lock_$name.log | head -1)"
done
echo LOCK_DONE
