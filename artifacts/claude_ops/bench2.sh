#!/bin/bash
# Bench v2: candidate vs opponent on the 28 development maps x both sides x NOVA_SEED seeds (default 1 2 3).
# Both bots are rebuilt once per seed (their common.h ships "#define NOVA_SEED 1"; seed 1 is the shipped bot), so
# every seed is a distinct, equally costly game set.
# Usage: bench2.sh <candidate bot dir> <opponent bot dir> <out prefix> [seed ...]
set -e
CAND="$1"; OPP="$2"; OUT="$3"; shift 3
SEEDS="${*:-1 2 3}"
cd "/c/projects/cambridge battlecode/work/neural-full-stack"
export PYTHONPATH="$PWD/python" PYTHONDONTWRITEBYTECODE=1 TMP="$PWD/artifacts/tmp" TEMP="$PWD/artifacts/tmp" PATH="/c/msys64/ucrt64/bin:$PATH"
PY="C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe"
B="$OUT-build"; mkdir -p "$B"
build() { # <bot dir> <seed> <out wasm>
  local d="$B/src-$(basename "$3" .wasm)"; rm -rf "$d"; mkdir -p "$d"; cp -r "$1/src" "$d/"
  grep -q '^#define NOVA_SEED 1$' "$d/src/common.h" || { echo "no NOVA_SEED 1 line in $1"; exit 1; }
  sed -i "s/^#define NOVA_SEED 1\$/#define NOVA_SEED $2/" "$d/src/common.h"
  "$PY" -c "import sys; from pathlib import Path; from nfs import engine; engine.official_build(Path(sys.argv[1]), Path(sys.argv[2]))" "$d" "$3"
}
for s in $SEEDS; do build "$CAND" $s "$B/cand-s$s.wasm" & build "$OPP" $s "$B/opp-s$s.wasm" & done; wait
dirs=()
for s in $SEEDS; do
  bash artifacts/claude_ops/bench28.sh "$B/cand-s$s.wasm" "$B/opp-s$s.wasm" "$OUT-seed$s" > "$OUT-seed$s.txt" 2>&1 &
  for k in 0 1 2 3; do dirs+=("$OUT-seed$s-s$k"); done
done; wait
"$PY" tools/bench_summary.py "${dirs[@]}"
