#!/bin/bash
# Gauntlet: one candidate against a pool of opponents with bench3, then a pooled report with ladder-loss mechanism
# metrics (deaths, kills, gems lost on death). Self-play against one sibling over-rewards brawling (v58 beat v57 by
# +153 locally and did no better on the ladder), so a candidate is judged on the whole pool, not on one opponent.
#   bash tools/gauntlet.sh <abs candidate dir> <name> [seeds...]
# Env: POOL (space-separated bot names under bots/; default v58 v57 v55 v54), JOBS (benches run at once, default 2),
# MAPS28=1 for the old 28-map development set. By default every map in maps/local-benchmarks is played (the ladder
# pool: 63% of v58's ladder losses were on maps the 28-map set never contains).
set -e
CAND="$1"; NAME="$2"; shift 2
SEEDS="${*:-1 2 3}"
cd "$(dirname "$0")/.."
R="$PWD"
POOL="${POOL:-v58 v57 v55 v54}"
JOBS="${JOBS:-2}"
OUT="$R/artifacts/evaluations/gauntlet-$NAME"
mkdir -p "$OUT"
n=0
for tag in $POOL; do
  ( if [ "$MAPS28" = "1" ]; then bash tools/bench3.sh "$CAND" "$R/bots/$tag" "$OUT/vs-$tag" $SEEDS; else HOLDOUT=1 MAP_DIR="$R/maps/local-benchmarks" bash tools/bench3.sh "$CAND" "$R/bots/$tag" "$OUT/vs-$tag" $SEEDS; fi > "$OUT/vs-$tag.out" 2>&1 || echo "FAILED vs $tag (see $OUT/vs-$tag.out)" ) &
  n=$((n+1)); [ $((n % JOBS)) -eq 0 ] && wait
done
wait
PY="${PY:-$(sed -n 's/.*"python": *"\([^"]*\)".*/\1/p' config/paths.json)}"
"$PY" tools/gauntlet_report.py "$OUT" $POOL
