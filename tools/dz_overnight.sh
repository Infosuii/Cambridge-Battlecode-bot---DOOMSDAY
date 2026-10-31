#!/bin/bash
# Overnight queue after the Z14b screen (tools/dz_z14b_screen.sh, both copies). Resumable; skips finished runs.
# 1. Z14b table: select on v76+v65 (margin 100), confirm vs v74 and v81hl (never used to select), paired with the
#    uniform-base table run vs the same opponents. All from the z14b snapshot, so screened maps replay exactly.
# 2. A2 branches: from the base table, switch the team plan at round R (100/250/500) to HOME/HOARD/FIGHT/TURTLE,
#    vs v76 then v65 (snapshot research/dz/a2-2026-11-01/source; branches differ from baseline only in data).
set -u
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1
PY=${PY:-python}; W=${WORKERS:-3}
Z=research/dz/z-integration-2026-10-31; SPEC=$Z/z14b_configs.json; SNAP=$Z/z14b_source
while ! { grep -q Z14B_SCREEN_DONE artifacts/tmp/z14b_a.log && grep -q Z14B_SCREEN_DONE artifacts/tmp/z14b_b.log; }; do sleep 120; done
run() { # name, extra args...
  local name=$1; shift
  [ -f research/dz/runs/$name/results.json ] && return; [ -e artifacts/tmp/dz/$name ] && return
  "$PY" tools/dz.py smoke --name $name --pool --workers $W "$@" > artifacts/tmp/overnight_$name.log 2>&1
  echo "$name: $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/overnight_$name.log | tail -1) $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/overnight_$name.log | head -1)"
}
"$PY" tools/dz_plan_select.py --configs $SPEC --margin 100 --out $Z/z14b_table.inc > $Z/z14b_selection.json
cat $Z/z14b_selection.json
"$PY" tools/dz_plan_select.py --configs $SPEC --uniform base --out artifacts/tmp/z14b/base.inc
for opp in v74 v81hl; do
  run dz-z14b-base-$opp-02 --opponent $opp --set DZ_PLAN_TABLE=1 --plan-rows artifacts/tmp/z14b/base.inc --source $SNAP &
  run dz-z14b-table-$opp-01 --opponent $opp --set DZ_PLAN_TABLE=1 --plan-rows $Z/z14b_table.inc --source $SNAP &
  wait
done
A=research/dz/a2-2026-11-01; mkdir -p artifacts/tmp/a2
"$PY" tools/dz_plan_select.py --configs $SPEC --uniform base --out artifacts/tmp/a2/base.inc
declare -A BIT=([home]=16384 [hoard]=32768 [fight]=65536 [turtle]=131072)
for opp in v76 v65; do
  run dz-a2-base-$opp-01 --opponent $opp --set DZ_PLAN_TABLE=1 --plan-rows artifacts/tmp/a2/base.inc --source $A/source &
  wait
  jobs=()
  for r in 100 250 500; do for p in home fight turtle hoard; do jobs+=("$r:$p"); done; done
  for ((i=0;i<${#jobs[@]};i+=2)); do
    for j in "${jobs[@]:i:2}"; do
      r=${j%%:*}; p=${j##*:}
      run dz-a2-$p-r$r-$opp-01 --opponent $opp --set DZ_PLAN_TABLE=1 --plan-rows artifacts/tmp/a2/base.inc --source $A/source \
        --set DZ_SWITCH_ROUND=$r --set DZ_SWITCH_BITS=$((2147483648 + ${BIT[$p]})) &
    done
    wait
  done
done
echo OVERNIGHT_DONE
