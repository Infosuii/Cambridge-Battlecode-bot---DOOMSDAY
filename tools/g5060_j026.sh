#!/bin/bash
# J026 speedrun (comms/x1 pc/jobs/J026): sweep rows 1-13 on x3mf (x3 + X1_MAPFIT=1), screen vs v92 on the pool;
# lines with >= 102/172 are promoted to v86h + x1bru at once. One results row per line, pushed every 3 lines.
#   bash tools/g5060_j026.sh        (run from the gate checkout; resumes: finished cells are skipped)
set -u
cd "$(dirname "$0")/.."
X1=${X1WORK:-/c/x1work}; R=/c/x1-comms/g5060/results/J026.md
export DZ_MAX_PARALLEL=${DZ_MAX_PARALLEL:-6} WORKERS=${WORKERS:-6} SETS=pool
MF="--set X1_MAPFIT=1"; WT="--set X1_WALKTAIL=3"; BP="--set X1_BUSHPRE=15 --set X1_BUSHPRE_LAZY=60"; EC="--set X1_ECON=1"
[ -f $R ] || printf '%s\n' "# J026 result: feature sweep rows 1-13 on x3mf (pool; screen vs v92, base mf-g5060)" "" \
  "Commit 9c1bbde. Every line adds --set X1_MAPFIT=1. Promote at >= 102/172 (then v86h + x1bru)." "" \
  "| row | line | vs v92 /172 | Δ vs base | gained / lost | z | fuel-outs | deaths/game | sha | v86h | x1bru | total /516 | exact --set |" \
  "|---|---|---|---|---|---|---|---|---|---|---|---|---|" > $R
n=0
line() {  # row tag switches...
  local row=$1 tag=$2; shift 2
  OPPS=v92 bash tools/x1_gate.sh x3 $tag-g5060 "$MF $*" > /dev/null 2>&1
  local extra=""
  if [ -f research/dz/runs/x1g-$tag-g5060-pool-v92-01/results.json ]; then
    w=$(python -c "import json;print(json.load(open('research/dz/runs/x1g-$tag-g5060-pool-v92-01/results.json'))['wins'])")
    if [ "$tag" != mf ] && [ "$w" -ge 102 ]; then OPPS="v86h x1bru" bash tools/x1_gate.sh x3 $tag-g5060 "$MF $*" > /dev/null 2>&1; fi
  fi
  python - "$row" "$tag" "$*" >> $R <<'EOF'
import json, math, os, sys
row, tag, sets = sys.argv[1:4]
def load(t, o):
    p = f'research/dz/runs/x1g-{t}-g5060-pool-{o}-01/results.json'
    return json.load(open(p)) if os.path.exists(p) else None
c, b = load(tag, 'v92'), load('mf', 'v92')
if c is None:
    print(f'| {row} | {tag} | build fail / no result | | | | | | | | | | `{sets}` |'); sys.exit()
win = lambda g: g['outcome'] == 'team' + g['side']
cb = {(g['map'], g['side']): g for g in c['per_game']}; bb = {(g['map'], g['side']): g for g in b['per_game']} if b else {}
W = sum(win(cb[k]) and not win(bb[k]) for k in bb); L = sum(win(bb[k]) and not win(cb[k]) for k in bb)
z = (W - L) / math.sqrt(W + L) if W + L else 0.0
d = sum(g['deaths'] for g in c['per_game']) / len(c['per_game'])
x = [load(tag, o) for o in ('v86h', 'x1bru')]
tot = f"{c['wins'] + x[0]['wins'] + x[1]['wins']}" if all(x) else ''
print(f"| {row} | {tag} | {c['wins']} | {c['wins'] - (b['wins'] if b else 96):+d} | {W} / {L} | {z:+.2f} | {c['fuel_outs']} | {d:.2f} | "
      f"{c['per_game'][0]['candidate_sha256'][:12]} | {x[0]['wins'] if x[0] else ''} | {x[1]['wins'] if x[1] else ''} | {tot} | `{sets}` |")
EOF
  n=$((n+1))
  if [ $((n % 3)) -eq 0 ]; then (cd $X1 && SIDE=g5060 bash tools/x1_comms.sh push "J026: $n lines done (last $tag)" > /dev/null 2>&1); fi
  echo "J026 $row $tag done"
}
line 0 mf
line 1 burst2 --set A2_BURST2=1;   line 1 burst2wt --set A2_BURST2=1 $WT
line 2 tsvis --set A2_TS_VIS=1;    line 2 tsviswt --set A2_TS_VIS=1 $WT;    line 2 tsvisbpwt --set A2_TS_VIS=1 $BP $WT
line 3 locks --set V58_LOCKS=1;    line 3 lockswt --set V58_LOCKS=1 $WT
line 4 diseng --set A2_DISENGAGE=1; line 4 disengwt --set A2_DISENGAGE=1 $WT
line 5 prune --set X1_PRUNEFIX=1;  line 5 prunewt --set X1_PRUNEFIX=1 $WT
line 6 stage05 $EC --set X1_STAGE_MULT=0.5f;  line 6 stage07 $EC --set X1_STAGE_MULT=0.7f;  line 6 stage035 $EC --set X1_STAGE_MULT=0.35f
line 7 wait15 $EC --set X1_WAIT_MULT=1.5f;    line 7 wait20 $EC --set X1_WAIT_MULT=2.0f;    line 7 wait125 $EC --set X1_WAIT_MULT=1.25f
line 8 need13 $EC --set X1_NEED_MULT=1.3f;    line 8 need115 $EC --set X1_NEED_MULT=1.15f;  line 8 need15 $EC --set X1_NEED_MULT=1.5f
line 9 belief --set A2_BELIEF=1;   line 9 beliefwt --set A2_BELIEF=1 $WT
line 10 hiderec --set A2_HIDEREC=1; line 10 hiderecwt --set A2_HIDEREC=1 $WT
line 11 soak64 --set X1_SOAK64=1
line 12 escort --set APEX_ESCORT=1
line 13 bhold --set A2_BURST_HOLD=1
(cd $X1 && SIDE=g5060 bash tools/x1_comms.sh push "J026: rows 1-13 done" > /dev/null 2>&1)
echo J026_DONE
