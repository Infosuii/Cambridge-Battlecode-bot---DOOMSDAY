#!/bin/bash
# Reuse the candidate bytes across opponents and map sets. A finished run
# may be resumed by adding untouched opponent or set names to the matrix.
set -euo pipefail
cd "$(dirname "$0")/../.."
tag=${1:?usage: gx_matrix.sh TAG [smoke options]}
shift
[[ "$tag" =~ ^[A-Za-z0-9_-]+$ ]]
py=${PY:-python3}
candidate=${CANDIDATE:-gx}
first_wasm=
for set in ${SETS:-pool}; do
  case "$set" in
    pool) maps=maps/ladder-pool ;;
    styled) maps=maps/x1-unseen ;;
    maze) maps=maps/x1-maze ;;
    *) echo "Unknown map set: $set" >&2; exit 2 ;;
  esac
  for opponent in ${OPPS:-v92 v86h x1bru}; do
    name=gx-$tag-$set-$opponent
    run=artifacts/tmp/gx/$name
    args=(smoke --name "$name" --pool --map-dir "$maps" --opponent "$opponent"
      --candidate-bot "$candidate" --workers "${WORKERS:-6}")
    if [[ -n "${GX_OPPONENT_WASM_DIR:-}" ]]; then
      args+=(--opponent-wasm "$GX_OPPONENT_WASM_DIR/$opponent.wasm")
    fi
    if [[ -n "$first_wasm" ]]; then args+=(--candidate-wasm "$first_wasm"); fi
    "$py" tools/gx/dz.py "${args[@]}" "$@"
    if [[ -z "$first_wasm" ]]; then first_wasm=$run/candidate.wasm; fi
  done
done
