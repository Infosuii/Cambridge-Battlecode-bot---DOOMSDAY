#!/bin/bash
# Round 5 of per-map knob profiles (v74 base): nine profiles over knobs earlier rounds never varied (need pool, wait,
# stage timeout, shop gold, hunt switch, danger ttd), selection seeds 1/2 against the league, per-map choice by
# c_draft_league (gain > 100, no opponent below -250). Output research/v75/round5.txt; table research/v75/knob_table_r5.json.
cd "/c/projects/cambridge battlecode/work/neural-full-stack"
P=../neural-gameplay/.venv/Scripts/python.exe
N="spread solo needplus nohunt calm wait nowait shopmore shopless"
J="base=bots/v74"; for n in $N; do J="$J $n=artifacts/tmp/v67/r5-$n"; done
args() { for j in $J; do echo "$1-${j%%=*}=${j#*=}"; done; }
echo "round 5 started $(date -u +%FT%TZ)"
for o in v65 v61 v58; do $P tools/v67/c_batch.py --seeds 1 2 --workers 2 --opponent $o $(args R5-$o); done
$P tools/v67/c_batch.py --seeds 1 2 --workers 2 --opponent proxy --per-team --plan research/v70/pool_plan_teams.json $(args R5-proxy)
A=""; for o in v65 v61 v58 proxy; do A="$A --base $o=R5-$o-base"; done
for n in $N; do for o in v65 v61 v58 proxy; do A="$A --option $n:$o=R5-$o-$n"; done; done
$P tools/v67/c_draft_league.py $A --keys artifacts/tmp/v67/map_keys_full.json --out research/v75/knob_table_r5.json --min-gain 100 --max-loss 250
echo "round 5 selection finished $(date -u +%FT%TZ)"
