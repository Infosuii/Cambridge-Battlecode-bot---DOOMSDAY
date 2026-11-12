#!/bin/bash
# Round 5 continued: the same ten builds on seeds 5/6, then reselect from all four seeds (runs pooled per opponent).
cd "/c/projects/cambridge battlecode/work/neural-full-stack"
P=../neural-gameplay/.venv/Scripts/python.exe
N="spread solo needplus nohunt calm wait nowait shopmore shopless"
J="base=bots/v74"; for n in $N; do J="$J $n=artifacts/tmp/v67/r5-$n"; done
args() { for j in $J; do echo "$1-${j%%=*}=${j#*=}"; done; }
for o in v65 v61 v58; do $P tools/v67/c_batch.py --seeds 5 6 --workers 2 --opponent $o $(args R5b-$o); done
$P tools/v67/c_batch.py --seeds 5 6 --workers 2 --opponent proxy --per-team --plan research/v70/pool_plan_teams.json $(args R5b-proxy)
A=""; for o in v65 v61 v58 proxy; do A="$A --base $o=R5-$o-base,R5b-$o-base"; done
for n in $N; do for o in v65 v61 v58 proxy; do A="$A --option $n:$o=R5-$o-$n,R5b-$o-$n"; done; done
$P tools/v67/c_draft_league.py $A --keys artifacts/tmp/v67/map_keys_full.json --out research/v75/knob_table_r5x.json --min-gain 100 --max-loss 250
echo "round 5b finished $(date -u +%FT%TZ)"
