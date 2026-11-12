#!/bin/bash
# Job runner for the training box (see docs/handoff.md). Runs against its own clone on branch `ops`:
# every 10 minutes it pulls, runs ops/jobs/pending/*.sh in name order (cwd = the training checkout), files each job
# under ops/jobs/done/ with its log in ops/jobs/logs/, refreshes ops/STATUS.md and pushes. A pushed ops/STOP ends it.
# `runner.sh --status-only` never runs jobs: it only publishes ops/STATUS.md (no remote execution).
OPS="/c/projects/cambridge battlecode/work/ops-runner"
export REPO="/c/projects/cambridge battlecode/work/neural-full-stack"
export PY="C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe"
export PYTHONPATH="$REPO/python" PYTHONDONTWRITEBYTECODE=1 TMP="$REPO/artifacts/tmp" TEMP="$REPO/artifacts/tmp"
export PATH="/c/msys64/ucrt64/bin:$PATH"
export CLI="$("$PY" -c "import json;print(json.load(open(r'$REPO/config/paths.json'))['cli'])")"
STATUS_ONLY=0; [ "$1" = "--status-only" ] && STATUS_ONLY=1
cd "$OPS" || exit 1

push() { # <message>
  git add -A ops >/dev/null 2>&1
  git diff --cached --quiet && return 0
  git commit -q -m "$1"
  for _ in 1 2 3; do git pull -q --rebase origin ops && git push -q origin ops && return 0; sleep 20; done
}

status() {
  {
    echo "# Training box status"
    echo
    echo "Updated $(date -u '+%Y-%m-%d %H:%M UTC') by ops/runner.sh (10-minute cycle)."
    echo
    echo "## Processes"
    echo '```'
    tasklist 2>/dev/null | grep -i -E "^(python|cambc|node)" | awk '{print $1}' | sort | uniq -c
    nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader 2>/dev/null | sed 's/^/gpu: /'
    echo '```'
    echo
    echo "## v51 ladder tracker (latest)"
    echo '```'
    tail -c 1500 "$REPO/research/early/logs/v51_ladder.log" 2>/dev/null || echo "no tracker log yet"
    echo
    echo '```'
    echo
    echo "## Recent benchmark summaries (artifacts/evaluations/*.txt, newest first)"
    echo '```'
    ls -t "$REPO"/artifacts/evaluations/*.txt 2>/dev/null | head -12 | while read -r f; do echo "$(basename "$f"): $(grep -m1 '^games' "$f")"; done
    echo '```'
  } > ops/STATUS.md
}

cycle=0
while true; do
  git pull -q --rebase origin ops
  [ -f ops/STOP ] && { echo "STOP found"; break; }
  mkdir -p ops/jobs/pending ops/jobs/done ops/jobs/logs
  for job in ops/jobs/pending/*.sh; do
    [ "$STATUS_ONLY" = 1 ] && break
    [ -f "$job" ] || continue
    name=$(basename "$job" .sh)
    echo "started $(date -u '+%F %T UTC')" > "ops/jobs/logs/$name.log"
    push "ops: start $name"
    out="$REPO/artifacts/tmp/ops-$name.log"
    ( cd "$REPO" && timeout 8h bash "$OPS/$job" ) > "$out" 2>&1
    code=$?
    { echo "started/finished: see commit times; exit code $code"; tail -n 400 "$out"; } > "ops/jobs/logs/$name.log"
    git mv -f "$job" "ops/jobs/done/$name.sh" 2>/dev/null || mv -f "$job" "ops/jobs/done/$name.sh"
    push "ops: done $name (exit $code)"
  done
  status
  cycle=$((cycle + 1))
  if [ $((cycle % 3)) -eq 1 ]; then push "ops: status"; fi
  sleep 600
done
