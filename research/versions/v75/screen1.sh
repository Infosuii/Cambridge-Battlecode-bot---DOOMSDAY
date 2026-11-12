#!/bin/bash
# Screen V75_RACE / V75_LONE against the proxy and v65 on fresh seed 23 (baseline v74).
cd "/c/projects/cambridge battlecode/work/neural-full-stack"
P=../neural-gameplay/.venv/Scripts/python.exe
J="base=bots/v74 race=artifacts/tmp/v67/v75r-race lone=artifacts/tmp/v67/v75r-lone both=artifacts/tmp/v67/v75r-both"
args() { for j in $J; do echo "$1-${j%%=*}=${j#*=}"; done; }
$P tools/v67/c_batch.py --seeds 23 --workers 4 --opponent proxy --per-team --plan research/v70/pool_plan_teams.json $(args V-proxy)
$P tools/v67/c_batch.py --seeds 23 --workers 4 --opponent v65 $(args V-v65)
for o in proxy v65; do for v in race lone both; do $P tools/v67/c_paired.py V-$o-$v V-$o-base; done; done
