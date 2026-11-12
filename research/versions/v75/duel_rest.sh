#!/bin/bash
# Continue the ladder duels: v74 (platform 68, already submitted), then submit v75 and run it. Retries the submit.
cd "/c/projects/cambridge battlecode/work/neural-full-stack"
PY=../neural-gameplay/.venv/Scripts/python.exe
export PYTHONIOENCODING=utf8
PLAN=research/v59/duel_top1.json
arm() {  # version name
  $PY tools/replay/await_active.py "$1" --timeout-min 90 || exit 1
  $PY tools/replay/ladder_duel.py run --plan $PLAN --version "$1" --arm "$2"
  $PY tools/replay/ladder_duel.py report --plan $PLAN --arms v67-1028 "$2" --margins
}
arm 68 v74
for i in 1 2 3 4 5 6; do
  out=$(./tools/vendor/cambc.exe submit bots/v75 --note "v75 ladder duel candidate" 2>&1)
  ver=$(echo "$out" | sed -n 's/.*Submitted bot version \([0-9]*\).*/\1/p')
  [ -n "$ver" ] && break
  echo "submit attempt $i failed: $out"; sleep 30
done
[ -n "$ver" ] || exit 1
echo "v75 submitted as platform $ver"
arm "$ver" v75
$PY tools/replay/ladder_duel.py report --plan $PLAN --arms v74 v75 --margins
