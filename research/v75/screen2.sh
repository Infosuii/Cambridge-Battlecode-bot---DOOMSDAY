#!/bin/bash
# Screen 2: stand-and-fight switches and the neutral-case lone guard, same seed/opponents as screen 1 (base cached).
cd "/c/projects/cambridge battlecode/work/neural-full-stack"
P=../neural-gameplay/.venv/Scripts/python.exe
J="base=bots/v74 lone2=artifacts/tmp/v67/v75r-lone2 stand=artifacts/tmp/v67/v75r-stand stand2=artifacts/tmp/v67/v75r-stand2"
args() { for j in $J; do echo "$1-${j%%=*}=${j#*=}"; done; }
$P tools/v67/c_batch.py --seeds 23 --workers 4 --opponent proxy --per-team --plan research/v70/pool_plan_teams.json $(args V-proxy)
$P tools/v67/c_batch.py --seeds 23 --workers 4 --opponent v65 $(args V-v65)
for o in proxy v65; do for v in lone2 stand stand2; do $P tools/v67/c_paired.py V-$o-$v V-$o-base; done; done
