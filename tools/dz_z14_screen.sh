#!/bin/bash
# Z14 screening batch: every candidate in research/dz/z-integration-2026-10-31/z14_configs.json, vs v76 and v65.
# Resumable: skips runs whose results exist. If a run was interrupted, its raw folder artifacts/tmp/dz/<name> blocks
# the name (the runner refuses reuse); delete that one folder, or finish it with `python tools/dz.py recover`.
# Usage (repo root, Git Bash): PY=python bash tools/dz_z14_screen.sh   (two copies with REVERSE=1 on one share 8 threads)
set -u
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1
PY=${PY:-python}
G="--set DZ_GEAR_SURVIVE=1 --set DZ_GEAR_PROSPECT=1"
declare -A CFG=(
 [gs]="--set DZ_GEAR_SURVIVE=1" [gsp]="$G" [gp]="--set DZ_GEAR_PROSPECT=1" [ee1]="--set DZ_EE=1"
 [eerg]="--set DZ_EE=1 --set DZ_EE_REGROUP=1" [rg]="--set DZ_EE_REGROUP=1" [gates4]="--set DZ_RING_GATES=1"
 [bb]="--set DZ_BANK_BIG=1" [bn]="--set DZ_BANK_NEAR_MIN=1" [ghp]="--set DZ_GEAR_HEALTH=1" [crew1]="--set DZ_CREWS=1"
 [crewall]="--set DZ_CREWS=1 --set DZ_CREW_ALL=1" [int1]="$G --set DZ_EE=1 --set DZ_RING_GATES=1"
 [int1b]="$G --set DZ_RING_GATES=1" [int1c]="$G --set DZ_EE=1")
for k in 1 2 3 4 5 6 7; do CFG[dv$k]="--set DZ_DRAFT_VARIANT=$k"; CFG[dvg$k]="--set DZ_DRAFT_VARIANT=$k $G"; done
ORDER=$(for k in "${!CFG[@]}"; do echo "$k"; done | sort ${REVERSE:+-r})
for n in $ORDER; do
  for opp in v76 v65; do
    name=dz-$n-$opp-01; [ $opp = v65 ] && name=dz-$n-v65-z14-01
    [ "$n" = gsp ] && [ $opp = v65 ] && continue   # dz-gsp-v65-confirm-01
    [ "$n" = int1 ] && [ $opp = v65 ] && continue  # dz-int1-v65-confirm-01
    [ -f research/dz/runs/$name/results.json ] && continue
    [ -e artifacts/tmp/dz/$name ] && { echo "skip $name: raw folder exists (running elsewhere or interrupted)"; continue; }
    "$PY" tools/dz.py smoke --name $name --pool --opponent $opp ${CFG[$n]} > artifacts/tmp/z14_$name.log 2>&1
    echo "$name done: $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/z14_$name.log | tail -1)"
  done
done
echo Z14_SCREEN_DONE
