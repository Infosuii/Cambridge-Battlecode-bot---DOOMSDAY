#!/bin/bash
# Batch-1 code fixes on bots/v78 (v76 + v75 switches ported, all off) against the league on seeds 24/25; the v76 runs
# W-<opp>-v76 from its validation are the comparison. Output research/v75/fixes1.txt
cd "/c/projects/cambridge battlecode/work/neural-full-stack"
P=../neural-gameplay/.venv/Scripts/python.exe
J="v78=bots/v78 huntguard=artifacts/tmp/v67/q-huntguard fleeally=artifacts/tmp/v67/q-fleeally join=artifacts/tmp/v67/q-join bag300=artifacts/tmp/v67/q-bag300"
args() { for j in $J; do echo "$1-${j%%=*}=${j#*=}"; done; }
for o in v65 v61 v58; do $P tools/v67/c_batch.py --seeds 24 25 --workers 4 --opponent $o $(args Q-$o); done
$P tools/v67/c_batch.py --seeds 24 25 --workers 4 --opponent proxy --per-team --plan research/v70/pool_plan_teams.json $(args Q-proxy)
for n in v78 huntguard fleeally join bag300; do for o in v65 v61 v58 proxy; do
  echo "$n vs v76, $o: $($P tools/v67/c_paired.py Q-$o-$n W-$o-v76 | grep -E 'margin difference|deaths per' | tr '\n' ' ')"
done; done
