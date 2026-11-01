#!/bin/bash
# Fuel probes on v81hl's fuel-out hotspot maps, x1 vs v81hl (x1 default = v81hl binary).
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}; M="02the-pack 00vault 01islands 02gift-wrapping"
for p in 0 1 2; do
  name=x1-fuelprobe$p-v81hl-01
  [ -f research/dz/runs/$name/results.json ] && continue
  "$PY" tools/dz.py smoke --name $name --maps $M --opponent v81hl --candidate-bot x1 --workers ${WORKERS:-2} --set X1_FUEL_PROBE=$p > artifacts/tmp/$name.log 2>&1
  echo "$name: $(grep -o '"fuel_outs": [0-9]*' artifacts/tmp/$name.log | head -1) $(grep -o '"mean_banked": [0-9.]*' artifacts/tmp/$name.log | tail -1)"
done
echo PROBE_DONE
