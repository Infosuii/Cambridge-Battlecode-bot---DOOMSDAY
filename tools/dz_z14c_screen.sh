#!/bin/bash
# Z14c exact screen (research/dz/z14c-2026-11-01): uniform 70-row tables under DZ_PLAN_TABLE=1 with the fuel set
# (DZ_FAST_FIGHT, DZ_LATE_FIELD_GATE, DZ_FIELD_METER), vs v76 and v65, from the frozen snapshot. Then (copy A only,
# once both copies finish) select on v76+v65 at margin 100 and confirm vs v74 and v81hl, paired with the base table.
# Resumable. Usage: PY=python WORKERS=3 bash tools/dz_z14c_screen.sh [REVERSE=1 for the second copy]
set -u
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1
PY=${PY:-python}; W=${WORKERS:-3}
Z=research/dz/z14c-2026-11-01; SPEC=$Z/z14c_configs.json; SNAP=$Z/source
FUEL="--set DZ_PLAN_TABLE=1 --set DZ_FAST_FIGHT=1 --set DZ_LATE_FIELD_GATE=1 --set DZ_FIELD_METER=1"
NAMES="base $("$PY" -c "import json;print(' '.join(json.load(open('$SPEC'))['configs']))")"
[ -n "${REVERSE:-}" ] && NAMES=$(echo $NAMES | tr ' ' '\n' | tac | tr '\n' ' ')
mkdir -p artifacts/tmp/z14c
run() { local name=$1 rows=$2 opp=$3
  [ -f research/dz/runs/$name/results.json ] && return; [ -e artifacts/tmp/dz/$name ] && return
  "$PY" tools/dz.py smoke --name $name --pool --opponent $opp --workers $W $FUEL --plan-rows $rows --source $SNAP > artifacts/tmp/z14c/$name.log 2>&1
  echo "$name done: $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/z14c/$name.log | tail -1) $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/z14c/$name.log | head -1)"
}
for n in $NAMES; do
  rows=artifacts/tmp/z14c/$n.inc
  "$PY" tools/dz_plan_select.py --configs $SPEC --uniform $n --out $rows
  for opp in v76 v65; do run dz-z14c-$n-$opp-01 $rows $opp; done
done
echo Z14C_SCREEN_DONE
[ -n "${REVERSE:-}" ] && exit 0
while ! grep -q Z14C_SCREEN_DONE artifacts/tmp/z14c_b.log 2>/dev/null; do sleep 120; done
"$PY" tools/dz_plan_select.py --configs $SPEC --margin 100 --out $Z/z14c_table.inc > $Z/z14c_selection.json; cat $Z/z14c_selection.json
for opp in v74 v81hl; do
  run dz-z14c-base-$opp-01 artifacts/tmp/z14c/base.inc $opp &
  run dz-z14c-table-$opp-01 $Z/z14c_table.inc $opp &
  wait
done
echo Z14C_ALL_DONE
