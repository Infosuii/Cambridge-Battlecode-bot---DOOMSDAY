#!/bin/bash
# DZ_EARLY_JOBS screens (on top of DZ_FAST_BOOT; pairs: dz-fastboot-*-01) with the fuel set (fast fight, late field gate, field meter), from the frozen snapshot
# research/dz/fastboot-2026-11-01/source. Controls: dz-fuelctl4-v76-01 / -v65-01 are the identical binary with
# DZ_FAST_BOOT=0 (00596bf3819d, checked); dz-fuelctl4-idle81-01 is run here. Exit V-E3: R100 gold +10% vs idle.
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; S=research/dz/fastboot-2026-11-01/source_ej
F="--set DZ_FAST_FIGHT=1 --set DZ_LATE_FIELD_GATE=1 --set DZ_FIELD_METER=1"
for job in "earlyjobs idle81 1" "earlyjobs v76 1" "earlyjobs v65 1"; do
  set -- $job; name=dz-$1-$2-01
  [ -f research/dz/runs/$name/results.json ] && continue
  [ -e artifacts/tmp/dz/$name ] && continue
  "$PY" tools/dz.py smoke --name $name --pool --opponent $2 --workers ${WORKERS:-2} $F --set DZ_FAST_BOOT=1 --set DZ_EARLY_JOBS=$3 --source $S > artifacts/tmp/ej_$name.log 2>&1
  echo "$name: $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/ej_$name.log | tail -1) $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/fb_$name.log | head -1)"
done
echo EARLYJOBS_DONE
