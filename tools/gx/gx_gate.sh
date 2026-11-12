#!/bin/bash
# Usage: OPPS="v92 v86h x1bru" SETS=pool bash tools/gx/gx_gate.sh TAG [DZ smoke arguments]
# CANDIDATE defaults to gx. Candidate and opponent wasm can be supplied for exact reruns.
set -euo pipefail
cd "$(dirname "$0")/../.."
tag=${1:?usage: gx_gate.sh TAG [DZ smoke arguments]}
shift
[[ "$tag" =~ ^[A-Za-z0-9_-]+$ ]]
py=${PY:-python3}
for set in ${SETS:-pool}; do
  case "$set" in
    pool) maps=maps/ladder-pool ;;
    styled) maps=maps/x1-unseen ;;
    maze) maps=maps/x1-maze ;;
    *) echo "Unknown set: $set" >&2; exit 2 ;;
  esac
  test -d "$maps" || { echo "Missing map set: $maps" >&2; exit 2; }
  for opp in ${OPPS:-v92 v86h x1bru}; do
    name=gx-$tag-$set-$opp
    args=(smoke --name "$name" --pool --map-dir "$maps"
      --opponent "$opp" --candidate-bot "${CANDIDATE:-gx}" --workers "${WORKERS:-6}")
    if [[ -n "${GX_OPPONENT_WASM_DIR:-}" ]]; then
      args+=(--opponent-wasm "$GX_OPPONENT_WASM_DIR/$opp.wasm")
    fi
    "$py" tools/gx/dz.py "${args[@]}" "$@"
  done
done
