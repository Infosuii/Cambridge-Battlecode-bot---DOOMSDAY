#!/bin/bash
# Staging-ring fix and the 3-champion gate job on the gated-altar maps (02guardians, 01boss-battle; both sides),
# seeds 23-30 against the league. Output research/v75/gate2.txt
cd "/c/projects/cambridge battlecode/work/neural-full-stack"
P=../neural-gameplay/.venv/Scripts/python.exe
S="23 24 25 26 27 28 29 30"
J="base=bots/v78 stagering=artifacts/tmp/v67/q-stagering gate400=artifacts/tmp/v67/q-gate400 gate600=artifacts/tmp/v67/q-gate600"
args() { for j in $J; do echo "$1-${j%%=*}=${j#*=}"; done; }
for o in v65 v61 v58; do $P tools/v67/c_batch.py --seeds $S --workers 2 --opponent $o --plan research/v71/gate_plan.json $(args G2-$o); done
$P tools/v67/c_batch.py --seeds $S --workers 2 --opponent proxy --per-team --plan research/v71/gate_plan_teams.json $(args G2-proxy)
for n in stagering gate400 gate600; do for o in v65 v61 v58 proxy; do
  echo "$n $o: $($P tools/v67/c_paired.py G2-$o-$n G2-$o-base | grep -E 'margin difference|deaths per' | tr '\n' ' ')"
done; done
