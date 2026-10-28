#!/bin/bash
# Submit candidates one at a time and play each on the same duel plan, then report each against a baseline arm.
# A submission only compiles while it is the selected version and goes live when it finishes, so candidates cannot
# be precompiled side by side; each one is submitted only after the previous arm has finished.
#   bash tools/replay/duel_pipeline.sh <plan.json> <baseline arm> <bot dir>...
# Each bot's arm is named after its directory. Queueing and submitting were approved by the user (2026-10-26).
set -e
cd "$(dirname "$0")/../.."
PLAN="$1"; BASE="$2"; shift 2
PY="${PY:-$(sed -n 's/.*"python": *"\([^"]*\)".*/\1/p' config/paths.json)}"
export PYTHONIOENCODING=utf8
for BOT in "$@"; do
  name=$(basename "$BOT")
  out=$(./tools/vendor/cambc.exe submit "$BOT" --note "$name ladder duel candidate" 2>&1)
  ver=$(echo "$out" | sed -n 's/.*Submitted bot version \([0-9]*\).*/\1/p')
  [ -n "$ver" ] || { echo "submit failed for $name: $out"; exit 1; }
  echo "$name submitted as platform $ver"
  "$PY" tools/replay/await_active.py "$ver" --timeout-min 90
  "$PY" tools/replay/ladder_duel.py run --plan "$PLAN" --version "$ver" --arm "$name"
  "$PY" tools/replay/ladder_duel.py report --plan "$PLAN" --arms "$BASE" "$name" --margins
done
