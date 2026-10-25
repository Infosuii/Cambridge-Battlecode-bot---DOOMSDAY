#!/bin/sh
# Usage: bench28.sh <a.wasm|bot dir> <b.wasm or ''> <out prefix>  -- 28 maps x 2 sides in 4 parallel shards
A="$1"; OUT="$3"
cd "/c/projects/cambridge battlecode/work/neural-full-stack"
export PYTHONPATH="$PWD/python" PYTHONDONTWRITEBYTECODE=1 TMP="$PWD/artifacts/tmp" TEMP="$PWD/artifacts/tmp" PATH="/c/msys64/ucrt64/bin:$PATH"
PY="C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe"
MAPS=$("$PY" -c "import json;p=json.load(open('evaluation/schedules/map_partitions.json'))['partitions'];print(' '.join(p['training']+p['selection']))")
BW="$2"
i=0; for s in 0 1 2 3; do
  set -- $MAPS; M=""; j=0; for m in "$@"; do [ $((j % 4)) -eq $s ] && M="$M $m"; j=$((j+1)); done
  "$PY" tools/bot_match.py --a "$A" ${BW:+--b "$BW"} --out "$OUT-s$s" --maps $M > "$OUT-s$s.log" 2>&1 &
done; wait
"$PY" tools/bench_summary.py "$OUT"-s0 "$OUT"-s1 "$OUT"-s2 "$OUT"-s3
