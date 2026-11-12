#!/bin/bash
# bots/v76 = BASE (bots/v74 or bots/v75) with v74's knob table plus round-5 entries (research/v75/knob_table_r5x.json),
# validated against BASE on fresh seeds 24/25 against the league. Usage: bash research/v75/build_v76.sh bots/v74
cd "/c/projects/cambridge battlecode/work/neural-full-stack"
P=../neural-gameplay/.venv/Scripts/python.exe
BASE=${1:-bots/v74}
$P - <<'PY'
import json
old = json.load(open('research/v71/knob_table_v73.json'))['table']
new = json.load(open('research/v75/knob_table_r5x.json'))['table']
merged = dict(old)
for m, t in new.items():
    prev = old.get(m)
    merged[m] = dict(t, profile=f"{prev['profile']}+{t['profile']}" if prev else t['profile'])
json.dump({'note': 'v74 knob table plus round-5 entries (existing profile first where both apply)', 'table': merged},
          open('research/v75/knob_table_v76.json', 'w'), indent=1)
print('v76 table', len(merged), 'maps;', len(new), 'round-5 entries,', sum(m in old for m in new), 'combined')
PY
rm -rf bots/v76/src; mkdir -p bots/v76; cp -r $BASE/src bots/v76/src
$P tools/v67/c_v71_knobs.py bots/v76 research/v75/knob_table_v76.json --replace
B=$(basename $BASE)
for o in v65 v61 v58; do $P tools/v67/c_batch.py --seeds 24 25 --workers 8 --opponent $o "W-$o-$B=$BASE" "W-$o-v76=bots/v76"; done
$P tools/v67/c_batch.py --seeds 24 25 --workers 8 --opponent proxy --per-team --plan research/v70/pool_plan_teams.json "W-proxy-$B=$BASE" "W-proxy-v76=bots/v76"
for o in v65 v61 v58 proxy; do $P tools/v67/c_paired.py "W-$o-v76" "W-$o-$B"; done
