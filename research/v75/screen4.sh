#!/bin/bash
# Big-bag rule alone and the full caution package (bag + lone2 + race) against the league, seed 23 (bases cached).
cd "/c/projects/cambridge battlecode/work/neural-full-stack"
P=../neural-gameplay/.venv/Scripts/python.exe
$P tools/v67/c_batch.py --seeds 23 --workers 5 --opponent proxy --per-team --plan research/v70/pool_plan_teams.json V-proxy-bag=artifacts/tmp/v67/v75r-bag V-proxy-pack=artifacts/tmp/v67/v75r-pack
for o in v65 v61 v58; do $P tools/v67/c_batch.py --seeds 23 --workers 5 --opponent $o V-$o-bag=artifacts/tmp/v67/v75r-bag V-$o-pack=artifacts/tmp/v67/v75r-pack; done
for o in proxy v65 v61 v58; do for v in bag pack; do $P tools/v67/c_paired.py V-$o-$v V-$o-base; done; done
