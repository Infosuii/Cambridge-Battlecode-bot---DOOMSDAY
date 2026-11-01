#!/bin/bash
# Two-machine comms for the x1 plan. Messages live on the orphan branch comms/x1 (no shared history with any code
# branch), checked out in its own folder next to this repo (default ../x1-comms), never in the code checkout.
# Each machine writes only its own folder: pc/ (Rishik's PC) or g5060/ (the 5060 PC). push refuses anything else.
#
#   SIDE=g5060 bash tools/x1_comms.sh init           one-time: create the comms folder from origin/comms/x1
#   SIDE=g5060 bash tools/x1_comms.sh pull           fetch the other machine's news
#   SIDE=g5060 bash tools/x1_comms.sh push "msg"     commit and push your folder only
#   bash tools/x1_comms.sh dir                       print the comms folder
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
C=${X1_COMMS_DIR:-$(cd "$ROOT/.." && pwd)/x1-comms}
SIDE=${SIDE:-}
need_side() { case "$SIDE" in pc|g5060) ;; *) echo "set SIDE=pc or SIDE=g5060" >&2; exit 2;; esac; }
case ${1:-} in
  init)
    need_side
    git -C "$ROOT" fetch -q origin comms/x1
    [ -d "$C/.git" ] || [ -f "$C/.git" ] || git -C "$ROOT" worktree add -q --no-checkout "$C" origin/comms/x1
    git -C "$C" checkout -q -B comms/x1 origin/comms/x1
    git -C "$C" branch -q --set-upstream-to=origin/comms/x1 comms/x1
    echo "comms ready in $C" ;;
  pull)
    git -C "$C" pull -q --rebase origin comms/x1
    git -C "$C" log --oneline -5 ;;
  push)
    need_side; shift; msg=${1:-update}
    other=$(git -C "$C" status --porcelain | awk '{print $NF}' | grep -v "^$SIDE/" || true)
    if [ -n "$other" ]; then echo "refusing: changes outside $SIDE/:" >&2; echo "$other" >&2; exit 3; fi
    git -C "$C" add -A "$SIDE"
    git -C "$C" diff --cached --quiet && { echo "nothing to push"; exit 0; }
    git -C "$C" commit -q -m "comms($SIDE): $msg"
    git -C "$C" pull -q --rebase origin comms/x1
    git -C "$C" push -q origin comms/x1
    git -C "$C" log --oneline -1 ;;
  dir) echo "$C" ;;
  *) sed -n 2,11p "$0"; exit 2 ;;
esac
