#!/bin/bash
# Generalist check after Z14c: uniform dvg7 (and the geometric selector table, ridge 100) on all 70 maps vs the
# unseen opponents v74 and v81hl, paired with dz-z14c-base-<opp>-01. Holdout maps included (G6 for a generalist).
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; Z=research/dz/z14c-2026-11-01; SNAP=$Z/source
FUEL="--set DZ_PLAN_TABLE=1 --set DZ_FAST_FIGHT=1 --set DZ_LATE_FIELD_GATE=1 --set DZ_FIELD_METER=1"
while ! grep -q Z14C_ALL_DONE artifacts/tmp/z14c_a.log 2>/dev/null; do sleep 120; done
"$PY" tools/dz_plan_select.py --configs $Z/z14c_configs.json --uniform dvg7 --out artifacts/tmp/z14c/dvg7.inc
/c/Users/info/nnbc-venv/Scripts/python.exe tools/dz_geo_select.py --configs $Z/z14c_configs.json --features dz-diag-mapfeat-03 --ridge 100 \
  --out $Z/geo_table.inc --results $Z/geo_RESULTS.json > /dev/null
for opp in v74 v81hl; do
  for kind in dvg7 geo; do
    name=dz-z14c-$kind-$opp-01; rows=artifacts/tmp/z14c/dvg7.inc; [ $kind = geo ] && rows=$Z/geo_table.inc
    [ -f research/dz/runs/$name/results.json ] && continue
    "$PY" tools/dz.py smoke --name $name --pool --opponent $opp --workers ${WORKERS:-3} $FUEL --plan-rows $rows --source $SNAP > artifacts/tmp/z14c/$name.log 2>&1 &
  done
  wait
  echo "$opp done"
done
echo GENERALIST_DONE
