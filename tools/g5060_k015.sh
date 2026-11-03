#!/bin/bash
# K015 leftovers (comms/x1 pc/jobs/K015): banking B1-B3 screens + near-miss stacks on x3mf (x3 + X1_MAPFIT=1), pool.
# Part B lines run vs v92, v86h and x1bru (base 341/516); part A screens vs v92, promoted to all three at >= 102/172.
#   bash tools/g5060_k015.sh LINE...   (run from a 6f462c4 checkout; resumes: finished cells are skipped by x1_gate.sh)
# LINE is a tag below; lines g5070 already posted are left out by the caller.
set -u
cd "$(dirname "$0")/.."
X1=${X1WORK:-/c/x1work}; R=${R:-/c/x1-comms/g5060/results/K015A.md}; export BASE=${BASE:-mf} BASETOT=${BASETOT:-341}
export DZ_MAX_PARALLEL=${DZ_MAX_PARALLEL:-6} WORKERS=${WORKERS:-6} SETS=pool
MF="--set X1_MAPFIT=1"
# mf base vs v86h / x1bru = the x3mf2 runs (same build c3da892053a7, 115 / 130)
for o in v86h x1bru; do [ -d research/dz/runs/x1g-mf-g5060-pool-$o-01 ] || cp -r research/dz/runs/x1g-x3mf2-pool-$o-01 research/dz/runs/x1g-mf-g5060-pool-$o-01; done
declare -A SW=(
  [mf]=""
  [b1]="--set X1_SAFEROUTE=1"
  [b1h]="--set X1_SAFEROUTE=1 --set X1_SR_HOLD=1"
  [b12]="--set X1_SAFEROUTE=1 --set X1_BAGRISK2=1"
  [b12r07]="--set X1_SAFEROUTE=1 --set X1_BAGRISK2=1 --set X1_BR2_RATE=0.7f"
  [b3]="--set X1_RACEBANK=1"
  [b123h]="--set X1_SAFEROUTE=1 --set X1_BAGRISK2=1 --set X1_RACEBANK=1 --set X1_SR_HOLD=1"
  [bag80]="--set X1_BAGRISK=80"
  [hrwt]="--set A2_HIDEREC=1 --set X1_WALKTAIL=3"
  [bag80hrwt]="--set X1_BAGRISK=80 --set A2_HIDEREC=1 --set X1_WALKTAIL=3"
  [mfst]="--set X1_G3_STYLE=1 --set X1_G3_STYLE_NUMBERS=0 --set X1_G3_STYLE_PWIN=0.5 --set X1_WALKTAIL=3"
  [mfsec]="--set X1_G3_SECURE=1"
  [i02d]="--set X1_G3_STYLE=1 --set X1_G3_STYLE_NUMBERS=0 --set X1_WALKTAIL=3 --set X1_G3_STYLE_PWIN=0.5f"
  [i02dp04]="--set X1_G3_STYLE=1 --set X1_G3_STYLE_NUMBERS=0 --set X1_WALKTAIL=3 --set X1_G3_STYLE_PWIN=0.4f"
  [i02dp06]="--set X1_G3_STYLE=1 --set X1_G3_STYLE_NUMBERS=0 --set X1_WALKTAIL=3 --set X1_G3_STYLE_PWIN=0.6f"
  [i02deq30]="--set X1_G3_STYLE=1 --set X1_G3_STYLE_NUMBERS=0 --set X1_WALKTAIL=3 --set X1_G3_STYLE_PWIN=0.5f --set X1_G3_STYLE_EQ=0.30f"
  [i02deq35]="--set X1_G3_STYLE=1 --set X1_G3_STYLE_NUMBERS=0 --set X1_WALKTAIL=3 --set X1_G3_STYLE_PWIN=0.5f --set X1_G3_STYLE_EQ=0.35f"
  [i02dfo0]="--set X1_G3_STYLE=1 --set X1_G3_STYLE_NUMBERS=0 --set X1_WALKTAIL=3 --set X1_G3_STYLE_PWIN=0.5f --set X1_G3_STYLE_FOCUS=0.0f"
)
[ -f $R ] || printf '%s\n' "# K015 result part A (g5060, per pc msg 0040): banking B1-B3 + near misses on x3mf (pool)" "" \
  "Commit 6f462c4 (+ g5060 dz.py fix). Every line adds --set X1_MAPFIT=1. Base mf-g5060 = 96 / 115 / 130 = 341 / 516." "" \
  "| line | part | vs v92 /172 | Δ | gained / lost | z | v86h | x1bru | total /516 | Δ total | fuel-outs | deaths/game | banked / collected per game | sha | exact --set |" \
  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|" > $R
for tag in "$@"; do
  sets="$MF ${SW[$tag]:-${EXTRA:-}}"
  case $tag in b1|b1h|b12|b12r07|b3|b123h|i02d*) part=A; opps=v92 ;; *) part=B; opps="v92 v86h x1bru" ;; esac
  OPPS="$opps" bash tools/x1_gate.sh x3 $tag-g5060 "$sets" > /dev/null 2>&1
  f=research/dz/runs/x1g-$tag-g5060-pool-v92-01/results.json
  if [ $part = A ] && [ -f $f ] && [ "$(python -c "import json;print(json.load(open('$f'))['wins'])")" -ge 102 ]; then
    OPPS="v86h x1bru" bash tools/x1_gate.sh x3 $tag-g5060 "$sets" > /dev/null 2>&1
  fi
  python - "$tag" "$part" "$sets" >> $R <<'EOF'
import json, math, os, sys
tag, part, sets = sys.argv[1:4]
def load(t, o):
    p = f'research/dz/runs/x1g-{t}-g5060-pool-{o}-01/results.json'
    return json.load(open(p)) if os.path.exists(p) else None
win = lambda g: g['outcome'] == 'team' + g['side']
c = {o: load(tag, o) for o in ('v92', 'v86h', 'x1bru')}; b = {o: load(os.environ['BASE'], o) for o in c}
if c['v92'] is None:
    print(f'| {tag} | {part} | build fail / no result | | | | | | | | | | | | `{sets}` |'); sys.exit()
W = L = 0
for o in c:
    if c[o] and b[o]:
        bb = {(g['map'], g['side']): g for g in b[o]['per_game']}
        for g in c[o]['per_game']:
            k = (g['map'], g['side']); W += win(g) and not win(bb[k]); L += win(bb[k]) and not win(g)
z = (W - L) / math.sqrt(W + L) if W + L else 0.0
games = [g for o in c if c[o] for g in c[o]['per_game']]
d = sum(g['deaths'] for g in games) / len(games); bk = sum(g['banked'] for g in games) / len(games); co = sum(g['collected'] for g in games) / len(games)
fo = sum(c[o]['fuel_outs'] for o in c if c[o])
tot = sum(c[o]['wins'] for o in c) if all(c.values()) else None
cell = lambda o: str(c[o]['wins']) if c[o] else ''
print(f"| {tag} | {part} | {c['v92']['wins']} | {c['v92']['wins'] - b['v92']['wins']:+d} | {W} / {L} | {z:+.2f} | {cell('v86h')} | {cell('x1bru')} | "
      f"{tot if tot is not None else ''} | {'' if tot is None else f'{tot - int(os.environ['BASETOT']):+d}'} | {fo} | {d:.2f} | {bk:.1f} / {co:.1f} | "
      f"{c['v92']['per_game'][0]['candidate_sha256'][:12]} | `{sets}` |")
EOF
  (cd $X1 && SIDE=g5060 bash tools/x1_comms.sh push "${JOB:-K015} $tag: $(tail -1 $R | cut -d'|' -f2-11)" > /dev/null 2>&1)
  echo "K015 $tag done"
done
echo K015_DONE
