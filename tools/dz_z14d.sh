#!/bin/bash
# Z14d: screen every Z14c config vs v74 (same snapshot/fuel set, so v76/v65 screens stay exact), select on
# v76+v65+v74 (margin 100), confirm vs v81hl and v85 (unseen), paired with the uniform-base table. After the
# generalist check. Usage: PY=python WORKERS=3 bash tools/dz_z14d.sh [REVERSE=1 for a second screening copy]
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; W=${WORKERS:-3}
Z=research/dz/z14c-2026-11-01; SPEC=$Z/z14d_configs.json; SNAP=$Z/source
FUEL="--set DZ_PLAN_TABLE=1 --set DZ_FAST_FIGHT=1 --set DZ_LATE_FIELD_GATE=1 --set DZ_FIELD_METER=1"
while ! grep -q GENERALIST_DONE artifacts/tmp/generalist.log 2>/dev/null; do sleep 120; done
run() { local name=$1 rows=$2 opp=$3
  [ -f research/dz/runs/$name/results.json ] && return; [ -e artifacts/tmp/dz/$name ] && return
  "$PY" tools/dz.py smoke --name $name --pool --opponent $opp --workers $W $FUEL --plan-rows $rows --source $SNAP > artifacts/tmp/z14c/$name.log 2>&1
  echo "$name done: $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/z14c/$name.log | tail -1) $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/z14c/$name.log | head -1)"
}
NAMES=$("$PY" -c "import json;print(' '.join(json.load(open('$SPEC'))['configs']))")
[ -n "${REVERSE:-}" ] && NAMES=$(echo $NAMES | tr ' ' '\n' | tac | tr '\n' ' ')
for n in $NAMES; do
  rows=artifacts/tmp/z14c/$n.inc
  [ -f $rows ] || "$PY" tools/dz_plan_select.py --configs $SPEC --uniform $n --out $rows
  run dz-z14c-$n-v74-01 $rows v74
done
echo Z14D_SCREEN_DONE
[ -n "${REVERSE:-}" ] && exit 0
while ! grep -q Z14D_SCREEN_DONE artifacts/tmp/z14d_b.log 2>/dev/null; do sleep 120; done
"$PY" tools/dz_plan_select.py --configs $SPEC --margin 100 --out $Z/z14d_table.inc > $Z/z14d_selection.json; cat $Z/z14d_selection.json
run dz-z14d-table-v81hl-01 $Z/z14d_table.inc v81hl &
run dz-z14c-base-v85-01 artifacts/tmp/z14c/base.inc v85 &
wait
run dz-z14d-table-v85-01 $Z/z14d_table.inc v85 &
run dz-z14c-table-v85-01 $Z/z14c_table.inc v85 &
wait
echo Z14D_ALL_DONE
