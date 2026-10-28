#!/bin/bash
# Job runner for the 5070 Ti box (docs/HANDOVER_5070TI.md). Portable: paths come from this checkout.
# Every 5 minutes: pull branch lab/box, run ops/box/pending/*.sh in name order (cwd = repo root), move each to
# ops/box/done/, write ops/box/logs/<job>.log (last 200 lines), push. Jobs put small results under ops/box/results/.
# A pushed ops/box/STOP ends the runner. Large outputs stay in artifacts/ (git-ignored) on this machine.
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO" || exit 1
export REPO PY="$(sed -n 's/.*"python": *"\([^"]*\)".*/\1/p' config/paths.json | head -1)"
export PYTHONPATH="$REPO/python" PYTHONDONTWRITEBYTECODE=1 TMP="$REPO/artifacts/tmp" TEMP="$REPO/artifacts/tmp"
export PYTHONIOENCODING=utf8 PATH="/c/Program Files/nodejs:$PATH"
mkdir -p artifacts/tmp ops/box/pending ops/box/done ops/box/logs ops/box/results

push() {
  git add ops/box >/dev/null 2>&1
  git diff --cached --quiet && return 0
  git commit -q -m "box: $1"
  for _ in 1 2 3 4; do git pull -q --rebase origin lab/box && git push -q origin HEAD:lab/box && return 0; sleep 20; done
}

while true; do
  git pull -q --rebase origin lab/box
  [ -f ops/box/STOP ] && { echo "STOP found"; break; }
  for job in ops/box/pending/*.sh; do
    [ -f "$job" ] || continue
    name=$(basename "$job" .sh)
    echo "started $(date -u '+%F %T UTC')" > "ops/box/logs/$name.log"
    push "start $name"
    out="$REPO/artifacts/tmp/box-$name.log"
    ( timeout 20h bash "$job" ) > "$out" 2>&1
    code=$?
    { echo "finished $(date -u '+%F %T UTC'), exit $code"; tail -n 200 "$out"; } > "ops/box/logs/$name.log"
    git mv -f "$job" "ops/box/done/$name.sh" 2>/dev/null || mv -f "$job" "ops/box/done/$name.sh"
    push "done $name (exit $code)"
  done
  { echo "alive $(date -u '+%F %T UTC')"; nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader 2>/dev/null; } > ops/box/HEARTBEAT
  [ $(( $(date +%M) % 30 )) -lt 5 ] && push "heartbeat"
  sleep 300
done
