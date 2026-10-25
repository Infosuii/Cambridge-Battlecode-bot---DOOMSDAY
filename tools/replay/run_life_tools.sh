#!/bin/bash
# Run every offline replay analysis tool over one replay folder (omniscient, local-only; never a bot input).
# Usage: bash tools/replay/run_life_tools.sh <replay dir> <out dir>
set -e
IN="$1"; OUT="$2"; mkdir -p "$OUT"
cd "$(dirname "$0")/../.."
F=("$IN"/*.repl26a)
node tools/replay/v53_audit.mjs "$IN" "$OUT/audit.json" 2>/dev/null &
node tools/replay/actor_ledger.mjs "$OUT/ledger.json" "${F[@]}" 2>/dev/null &
node tools/replay/still_runs.mjs auto 500 "$OUT/still.json" "${F[@]}" 2>/dev/null &
node tools/replay/contact_cohesion.mjs 2000 "$OUT/cohesion.json" "${F[@]}" 2>/dev/null &
wait
node tools/replay/hurt_contact.mjs "$OUT/hurt.json" "${F[@]}" 2>/dev/null &
node tools/replay/focus_fire.mjs "$OUT/focus.json" "${F[@]}" 2>/dev/null &
node tools/replay/death_context.mjs 2000 "$OUT/deaths.json" "${F[@]}" 2>/dev/null &
node tools/replay/team_kinds.mjs "$OUT/kinds.json" "${F[@]}" 2>/dev/null &
node tools/replay/home_trips.mjs "$OUT/home.json" "${F[@]}" 2>/dev/null &
wait
echo done
