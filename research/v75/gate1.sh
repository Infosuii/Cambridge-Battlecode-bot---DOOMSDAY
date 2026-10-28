#!/bin/bash
# V75_GATE from rounds 150 / 300 / 450 against bots/v75 on the gated-altar maps (02guardians, 01boss-battle; both sides),
# seeds 23-30 against the league.
cd "/c/projects/cambridge battlecode/work/neural-full-stack"
P=../neural-gameplay/.venv/Scripts/python.exe
S="23 24 25 26 27 28 29 30"
J="base=bots/v75 g150=artifacts/tmp/v67/v75g-150 g300=artifacts/tmp/v67/v75g-300 g450=artifacts/tmp/v67/v75g-450"
args() { for j in $J; do echo "$1-${j%%=*}=${j#*=}"; done; }
for o in v65 v61 v58; do $P tools/v67/c_batch.py --seeds $S --workers 4 --opponent $o --plan research/v71/gate_plan.json $(args GT-$o); done
$P tools/v67/c_batch.py --seeds $S --workers 4 --opponent proxy --per-team --plan research/v71/gate_plan_teams.json $(args GT-proxy)
for o in v65 v61 v58 proxy; do for v in g150 g300 g450; do $P tools/v67/c_paired.py GT-$o-$v GT-$o-base; done; done
