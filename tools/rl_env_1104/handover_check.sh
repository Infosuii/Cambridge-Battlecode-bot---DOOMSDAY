#!/usr/bin/env bash
# Read-only access check for an agent taking over Claude's DOOMSDAY workstream on this laptop.
# Run from Git Bash:  bash tools/rl_env_1104/handover_check.sh
# Prints OK / MISSING / WARN per item, then a summary. It changes nothing and prints no secrets.
# See research/rl_env_1104/HANDOVER_2026-11-09.md, section 2, for what to ask the user when an item is missing.

REPO=/c/Users/info/neural-networkk-battlecode
PY=/c/Users/info/.venvs/rlenv/Scripts/python
CAMBC=/c/Users/info/.venvs/cambc5/Scripts/cambc.exe
fail=0
warn=0
ok()   { printf 'OK      %s\n' "$*"; }
bad()  { printf 'MISSING %s\n' "$*"; fail=$((fail + 1)); }
note() { printf 'WARN    %s\n' "$*"; warn=$((warn + 1)); }
have() { if [ -e "$1" ]; then ok "$1"; else bad "$1 ${2:-}"; fi; }

echo "== repo"
if ! cd "$REPO" 2>/dev/null; then bad "repo folder $REPO (ask the user for access to it)"; exit 1; fi
ok "repo $REPO (branch $(git branch --show-current), HEAD $(git rev-parse --short HEAD))"
if [ -z "$(git status --porcelain --untracked-files=no)" ]; then ok "no uncommitted changes to tracked files"; else note "uncommitted changes to tracked files (git status)"; fi

echo "== programs"
for p in git gh node patch diff; do
  if command -v "$p" >/dev/null 2>&1; then ok "$p"; else bad "$p on PATH"; fi
done
if "$PY" --version >/dev/null 2>&1; then ok "python venv: $("$PY" --version 2>&1) at $PY"; else bad "python venv $PY"; fi
if "$CAMBC" --version >/dev/null 2>&1; then ok "cambc: $("$CAMBC" --version 2>&1) at $CAMBC"; else bad "cambc CLI $CAMBC"; fi

echo "== logins (nothing secret is printed)"
if gh auth status >/dev/null 2>&1; then ok "gh logged in as $(gh api user --jq .login 2>/dev/null)"; else bad "gh login (the user must run: gh auth login)"; fi
if git ls-remote --heads origin claude/rl-env-1104 >/dev/null 2>&1; then ok "git can reach origin (github.com/Infosuii/neural-networkk-battlecode)"; else bad "git access to origin"; fi
live=$("$CAMBC" submissions list 2>&1 | head -2 | tr '\n' ' ')
case "$live" in
  *Live:*) ok "cambc logged in. $live" ;;
  *) bad "cambc login (the user must run: cambc login). CLI said: $live" ;;
esac
sessdir=$(cygpath -u "$APPDATA" 2>/dev/null)/cambc
sess=$(ls -t "$sessdir"/session-*.json 2>/dev/null | head -1)
if [ -n "$sess" ]; then
  exp=$(( $(stat -c %Y "$sess") + 7 * 86400 ))
  left=$(( (exp - $(date +%s)) / 3600 ))
  msg="cambc session expires about $(date -u -d "@$exp" '+%a %d %b %H:%M UTC') (${left} h left; sessions last 7 days from login)"
  lock=$(date -u -d '2026-11-10 23:59' +%s)
  if [ "$exp" -lt "$lock" ]; then note "$msg: BEFORE the UK qualifier lock (Tue 10 Nov 23:59 UTC). Ask the user to run 'cambc login' early"
  elif [ "$left" -gt 12 ]; then ok "$msg"; else note "$msg. Ask the user to run 'cambc login' before then"; fi
else
  note "no cambc session file found under $sessdir"
fi

echo "== bot sources and eval data (git-ignored: they exist only on this laptop)"
for p in \
  artifacts/tmp/rl_env_1104/v112/x/src \
  artifacts/tmp/rl_env_1104/v113src/src \
  artifacts/tmp/rl_env_1104/v114/src \
  artifacts/tmp/upload_v115/src \
  artifacts/tmp/rl_env_1104/cand_v115ga/src \
  artifacts/tmp/rl_env_1104/cand_v114h/src \
  artifacts/tmp/rl_env_1104/cand_v114f/src \
  artifacts/tmp/rl_env_1104/eval-bots/v112opp \
  artifacts/tmp/rl_env_1104/v111base/nnfinal/nnfinal.wasm \
  artifacts/tmp/final_maps \
  artifacts/tmp/ladderpool_maps \
  artifacts/tmp/ladder_recent \
  artifacts/tmp/claude_scratch_20261109 \
  runs/rl_env_1104/eval/fixes-01/report.json \
  runs/rl_env_1104/eval/v113-01/report.json \
  runs/rl_env_1104/eval/split-01/report.json; do
  have "$p"
done

echo "== tracked tools, opponents and manifests"
for p in \
  bots/v86h bots/x3inv bots/x3mf2 bots/x3ctr3 \
  tools/rl_env_1104/cl_patches.py \
  tools/rl_env_1104/patches/v113_fixes_bot.cpp.diff \
  tools/rl_env_1104/ladder_monitor.py \
  tools/rl_env_1104/ladder_fuel.py \
  tools/rl_env_1104/eval_fuel.py \
  tools/rl_env_1104/eval/run_eval.py \
  tools/rl_env_1104/eval/pair_runs.py \
  tools/replay3/engine.mjs \
  tools/replay3/review.mjs \
  tools/replay3/still.mjs \
  tools/replay3/still_pick.py \
  research/rl_env_1104/candidates/manifests/final53_1108.json \
  research/rl_env_1104/candidates/manifests/new83_1108.json; do
  have "$p"
done

echo "== outside the repo"
have /c/Users/info/AppData/Local/cambc/assets "(engine and visualiser WASM that tools/replay3 decodes replays with)"
have /c/Users/info/bcws/sdk/cpp/cambc.h "(C++ SDK reference)"

echo "== machine"
free=$(df -BG /c | awk 'NR==2 { gsub("G", "", $4); print $4 }')
if [ "${free:-0}" -ge 10 ]; then ok "C: has ${free} GB free"; else note "C: has only ${free} GB free (each local game writes ~250 KB; delete old runs/rl_env_1104/eval/*/work folders whose report.json exists)"; fi
busy=$(tasklist 2>/dev/null | grep -c -i -E '^(cambc|engine)')
if [ "${busy:-0}" -eq 0 ]; then ok "no cambc or engine processes running (no evaluation in progress)"; else note "$busy cambc/engine processes running: an evaluation may be in progress"; fi

echo
echo "summary: $fail missing, $warn warnings"
[ "$fail" -eq 0 ]
