#!/bin/bash
# Round 6: every knob profile (31) on BASE, per-map choice selected on seeds 26-28 and confirmed on seeds 29-31 against
# the league (v65, v61, v58, proxy per team). New entries go on top of BASE's table (existing profile first on shared
# knobs). bots/v77 = BASE + that table, validated against BASE on fresh seeds 32/33.
# Usage: bash research/v75/round6.sh bots/v76   (output research/v75/round6.txt)
cd "/c/projects/cambridge battlecode/work/neural-full-stack"
P=../neural-gameplay/.venv/Scripts/python.exe
BASE=${1:-bots/v76}
TABLE=${2:-research/v75/knob_table_v76.json}
B=$(basename $BASE)
echo "round 6 on $B started $(date -u +%FT%TZ)"
NAMES=$($P -c "import sys; sys.path.insert(0,'tools/v67'); from c_profiles import PROFILES; print(' '.join(PROFILES))")
$P tools/v67/c_profiles.py --base $BASE --out-prefix artifacts/tmp/v67/r6 --only $NAMES > /dev/null
J="base=$BASE"; for n in $NAMES; do J="$J $n=artifacts/tmp/v67/r6-$n"; done
args() { for j in $J; do echo "$1-${j%%=*}=${j#*=}"; done; }
for stage in s:26,27,28 c:29,30,31; do
  tag=${stage%%:*}; seeds=$(echo ${stage#*:} | tr ',' ' ')
  for o in v65 v61 v58; do $P tools/v67/c_batch.py --seeds $seeds --workers 1 --opponent $o $(args R6$tag-$o); done
  $P tools/v67/c_batch.py --seeds $seeds --workers 1 --opponent proxy --per-team --plan research/v70/pool_plan_teams.json $(args R6$tag-proxy)
done
A=""; for o in v65 v61 v58 proxy; do A="$A --base $o=R6s-$o-base --confirm-base $o=R6c-$o-base"; done
for n in $NAMES; do for o in v65 v61 v58 proxy; do A="$A --option $n:$o=R6s-$o-$n --confirm-option $n:$o=R6c-$o-$n"; done; done
$P tools/v67/c_draft_league.py $A --keys artifacts/tmp/v67/map_keys_full.json --out research/v75/knob_table_r6.json --min-gain 100 --max-loss 250
$P - "$TABLE" <<'PY'
import json, sys
old = json.load(open(sys.argv[1]))['table']
new = json.load(open('research/v75/knob_table_r6.json'))['table']
merged = dict(old)
for m, t in new.items():
    prev = old.get(m)
    names = (prev['profile'].split('+') if prev else [])
    merged[m] = dict(t, profile='+'.join(names + [t['profile']]) if t['profile'] not in names else prev['profile'])
json.dump({'note': 'round-6 entries on top of the base table', 'table': merged}, open('research/v75/knob_table_v77.json', 'w'), indent=1)
print('v77 table', len(merged), 'maps;', len(new), 'round-6 entries')
PY
mkdir -p bots/v77; cp -r $BASE/src bots/v77/
$P tools/v67/c_v71_knobs.py bots/v77 research/v75/knob_table_v77.json --replace
for o in v65 v61 v58; do $P tools/v67/c_batch.py --seeds 32 33 --workers 8 --opponent $o "Y-$o-$B=$BASE" "Y-$o-v77=bots/v77"; done
$P tools/v67/c_batch.py --seeds 32 33 --workers 8 --opponent proxy --per-team --plan research/v70/pool_plan_teams.json "Y-proxy-$B=$BASE" "Y-proxy-v77=bots/v77"
for o in v65 v61 v58 proxy; do $P tools/v67/c_paired.py "Y-$o-v77" "Y-$o-$B"; done
echo "round 6 finished $(date -u +%FT%TZ)"
