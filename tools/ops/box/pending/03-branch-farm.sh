#!/bin/bash
# Plan-branch farm (tools/lab/branch_farm.py) on 400 box-only generated maps, disjoint from the 5060's (gen seeds 21/22).
# Results: ops/box/results/03-rows.jsonl.gz, 03-builds.json, 03-errors.jsonl (if any).
set -e
F=artifacts/farm-box; mkdir -p $F/tools $F/farm $F/workspace/bots $F/results
cp tools/vendor/cambc.exe $F/tools/; cp cambc.toml $F/workspace/; cp -r sdk cmake $F/workspace/
for b in v76p v74h v71; do rm -rf $F/workspace/bots/$b; mkdir -p $F/workspace/bots/$b; cp -r bots/$b/src $F/workspace/bots/$b/; done
cp tools/lab/branch_farm.py $F/farm/
echo '{"name": "box", "bot": "v76p", "opponents": ["v74h", "v71"], "seeds": [5, 6, 7, 8], "rounds": [300, 600, 900, 150, 450, 750, 1050, 1200], "plans": [1, 2, 3, 4, 5], "log_limit": 1048576}' > $F/farm/farm.json
if [ ! -d $F/workspace/maps ]; then
  EX="adgato-gemcombat1 adgato-gemcombat2 adgato-gemcombat3 adgato-gemcombat4 adgato-gemcombat5"
  ALL=$("$PY" -c "import json;print(' '.join(sorted(m for m in json.load(open('research/maps/official_maps.json')) if not m.startswith('adgato'))))")
  "$PY" tools/mapgen/gen_maps.py --out $F/gen-a --count 200 --seed 21 --anchor --templates $ALL --exclude $EX | tail -1
  "$PY" tools/mapgen/gen_maps.py --out $F/gen-b --count 200 --seed 22 --exclude $EX | tail -1
  mkdir -p $F/maps-tmp; cp $F/gen-a/*.map26a $F/gen-b/*.map26a $F/maps-tmp/; mv $F/maps-tmp $F/workspace/maps
fi
"$PY" $F/farm/branch_farm.py --pack $F | tail -5
"$PY" -c "import gzip,shutil; shutil.copyfileobj(open('$F/results/rows.jsonl','rb'), gzip.open('ops/box/results/03-rows.jsonl.gz','wb'))"
cp $F/results/builds.json ops/box/results/03-builds.json
[ -f $F/results/errors.jsonl ] && tail -c 200000 $F/results/errors.jsonl > ops/box/results/03-errors.jsonl || true
ls -la ops/box/results/03-*
