#!/bin/bash
# Resume round 6: run only the (stage, opponent, profile) runs that have no complete games.json, ten jobs at a time with
# two workers each (32 single-worker jobs at once oversubscribe the machine and run 3x slower), then select.
# Usage: bash research/v75/round6_resume.sh bots/v76
cd "/c/projects/cambridge battlecode/work/neural-full-stack"
P=../neural-gameplay/.venv/Scripts/python.exe
BASE=${1:-bots/v76}
echo "round 6 resume on $(basename $BASE) started $(date -u +%FT%TZ)"
NAMES=$($P -c "import sys; sys.path.insert(0,'tools/v67'); from c_profiles import PROFILES; print(' '.join(PROFILES))")
J="base=$BASE"; for n in $NAMES; do J="$J $n=artifacts/tmp/v67/r6-$n"; done
missing() {  # prefix -> job args for runs without games.json
  for j in $J; do r="$1-${j%%=*}"; [ -f artifacts/evaluations/v67/$r/games.json ] || echo "$r=${j#*=}"; done
}
chunks() {  # seeds opponent extra-args... ; reads jobs on stdin, runs ten at a time
  local seeds="$1" opp="$2"; shift 2
  local batch=()
  while read -r job; do
    batch+=("$job")
    if [ ${#batch[@]} -ge 10 ]; then $P tools/v67/c_batch.py --seeds $seeds --workers 2 --opponent $opp "$@" "${batch[@]}"; batch=(); fi
  done
  [ ${#batch[@]} -gt 0 ] && $P tools/v67/c_batch.py --seeds $seeds --workers 2 --opponent $opp "$@" "${batch[@]}"
}
for stage in s:26,27,28 c:29,30,31; do
  tag=${stage%%:*}; seeds=$(echo ${stage#*:} | tr ',' ' ')
  for o in v65 v61 v58; do missing R6$tag-$o | chunks "$seeds" $o; done
  missing R6$tag-proxy | chunks "$seeds" proxy --per-team --plan research/v70/pool_plan_teams.json
done
A=""; for o in v65 v61 v58 proxy; do A="$A --base $o=R6s-$o-base --confirm-base $o=R6c-$o-base"; done
for n in $NAMES; do for o in v65 v61 v58 proxy; do A="$A --option $n:$o=R6s-$o-$n --confirm-option $n:$o=R6c-$o-$n"; done; done
$P tools/v67/c_draft_league.py $A --keys artifacts/tmp/v67/map_keys_full.json --out research/v75/knob_table_r6.json --min-gain 100 --max-loss 250
echo "round 6 selection finished $(date -u +%FT%TZ)"
