#!/bin/bash
# Phase 1, sweep 1d: sweep 1c's 65 switched-off v81hl features on x1, now vs the new benchmark x2 (= v88: v86h + x1's
# fuel fix + camp watch), on 19 ladder + 19 unseen maps. Only switches whose build differs from x1 are played, and a
# build shared by several switches is played once (hashes from tools/x1_flag_hashes.py; waits for each hash).
# Baseline cells: x1e-cw-ladder-x2-01 / x1e-cw-unseen-x2-01.
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; SPEC=research/x1/sweep1c.json; HASHES=research/x1/sweep1c_hashes.json
LM=$("$PY" -c "import json;print(' '.join(json.load(open('$SPEC'))['maps']))")
UM=$("$PY" -c "import json;print(' '.join(json.load(open('$SPEC'))['unseen_maps']))")
FLAGS=$("$PY" -c "import json;print(' '.join(json.load(open('$SPEC'))['flags']))")
SNAP=research/x1/snapshots/sweep1c
rm -rf bots/x1-sweepd && mkdir -p bots/x1-sweepd && cp -r $SNAP/src bots/x1-sweepd/src
played=" "
for f in $FLAGS; do
  until h=$("$PY" -c "import json,sys;d=json.load(open('$HASHES'));print(d['$f'])" 2>/dev/null); do sleep 60; done
  base=$("$PY" -c "import json;print(json.load(open('$HASHES'))['BASE'])")
  if [ "$h" = "$base" ]; then echo "$f: same binary as x1 (not played)"; continue; fi
  if [ "$h" = "BUILD_FAILED" ]; then echo "$f: does not compile (not played; artifacts/tmp/x1-flaghash-$f.err)"; continue; fi
  case "$played" in *" $h "*) echo "$f: same binary as an earlier switch (not played)"; continue;; esac
  played="$played$h "
  t=$(echo $f | tr 'A-Z_' 'a-z-')
  for set in ladder unseen; do
    name=x1-sd-$t-$set-x2-01
    [ -f research/dz/runs/$name/results.json ] && continue
    rm -rf artifacts/tmp/dz/$name
    if [ $set = ladder ]; then M="--maps $LM"; else M="--map-dir maps/x1-unseen --maps $UM"; fi
    "$PY" tools/dz.py smoke --name $name $M --opponent x2 --candidate-bot x1-sweepd --workers ${WORKERS:-5} --set $f=1 > artifacts/tmp/$name.log 2>&1
  done
  echo "$f: ladder $(grep -o '"wins": [0-9]*' artifacts/tmp/x1-sd-$t-ladder-x2-01.log | head -1) unseen $(grep -o '"wins": [0-9]*' artifacts/tmp/x1-sd-$t-unseen-x2-01.log | head -1)"
done
echo X1_SWEEP1D_DONE
