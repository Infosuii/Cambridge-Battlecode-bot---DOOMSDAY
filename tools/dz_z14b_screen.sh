#!/bin/bash
# Z14b exact screen: every config of research/dz/z-integration-2026-10-31/z14b_configs.json as a uniform 70-row table
# under DZ_PLAN_TABLE=1 (same code as the final table; only table data differs), vs v76 and v65, base first.
# Builds from the frozen snapshot z14b_source (edits to bots/dz never mix in). Resumable: skips finished runs and names whose raw folder exists. Usage: PY=python bash tools/dz_z14b_screen.sh
# [WORKERS=3] [REVERSE=1]  (two copies, one with REVERSE=1, split the queue).
set -u
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1
PY=${PY:-python}; W=${WORKERS:-3}
SPEC=research/dz/z-integration-2026-10-31/z14b_configs.json
NAMES="base $("$PY" -c "import json;print(' '.join(json.load(open('$SPEC'))['configs']))")"
[ -n "${REVERSE:-}" ] && NAMES=$(echo $NAMES | tr ' ' '\n' | tac | tr '\n' ' ')
mkdir -p artifacts/tmp/z14b
for n in $NAMES; do
  for opp in v76 v65; do
    name=dz-z14b-$n-$opp-02
    [ -f research/dz/runs/$name/results.json ] && continue
    [ -e artifacts/tmp/dz/$name ] && continue
    rows=artifacts/tmp/z14b/$n.inc
    "$PY" tools/dz_plan_select.py --configs $SPEC --uniform $n --out $rows
    "$PY" tools/dz.py smoke --name $name --pool --opponent $opp --workers $W --set DZ_PLAN_TABLE=1 --plan-rows $rows --source research/dz/z-integration-2026-10-31/z14b_source > artifacts/tmp/z14b/$name.log 2>&1
    echo "$name done: $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/z14b/$name.log | tail -1) $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/z14b/$name.log | head -1)"
  done
done
echo Z14B_SCREEN_DONE
