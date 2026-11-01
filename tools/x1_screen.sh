#!/bin/bash
# x1 experiment screen: x1 with flags vs v81hl, v85, v76, v65 on the 70 maps, from a frozen snapshot of bots/x1.
# Pairs: x1-base-v81hl-<opp>-01 (x1 default = v81hl binary 809c6a80c4ac). Usage: bash tools/x1_screen.sh TAG "--set X1_A=1 ..."
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; TAG=$1; EXTRA=$2
SNAP=research/x1/snapshots/$TAG
if [ ! -d $SNAP/src ]; then mkdir -p $SNAP && cp -r bots/x1/src $SNAP/src; fi
rm -rf bots/x1-$TAG && mkdir -p bots/x1-$TAG && cp -r $SNAP/src bots/x1-$TAG/src   # --candidate-bot reads bots/<name>
for opp in v81hl v85 v76 v65; do
  name=x1-$TAG-$opp-01
  [ -f research/dz/runs/$name/results.json ] && continue
  [ -e artifacts/tmp/dz/$name ] && continue
  "$PY" tools/dz.py smoke --name $name --pool --opponent $opp --candidate-bot x1-$TAG --workers ${WORKERS:-2} $EXTRA > artifacts/tmp/$name.log 2>&1
  echo "$name: $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/$name.log | tail -1) $(grep -o '"wins": [0-9]*' artifacts/tmp/$name.log | head -1) $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/$name.log | head -1)"
done
echo X1_${TAG}_DONE
