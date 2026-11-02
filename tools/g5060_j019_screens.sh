#!/bin/bash
# J019 screens (research/x1/FEATURE_SWEEP_X3.md): x3 + variant vs v92 on the 86-map pool, 172 games each, in row order.
# One line per variant to comms as it finishes (tag, wins/172, fuel-outs). Run from the gate checkout.
#   bash tools/g5060_j019_screens.sh            (resumes: finished screens are skipped by x1_gate.sh)
set -u
cd "$(dirname "$0")/.."
X1=${X1WORK:-/c/x1work}
export OPPS=v92 SETS=pool DZ_MAX_PARALLEL=${DZ_MAX_PARALLEL:-6} WORKERS=${WORKERS:-6}
WT="--set X1_WALKTAIL=3"; BP="--set X1_BUSHPRE=15 --set X1_BUSHPRE_LAZY=60"
LOG=$X1/artifacts/tmp/j019-screens.tsv
screen() {  # row tag switches...
  local row=$1 tag=$2; shift 2
  bash tools/x1_gate.sh x3 "s$tag" "$*" > /dev/null 2>&1
  local f=research/dz/runs/x1g-s$tag-pool-v92-01/results.json
  local line
  if [ -f "$f" ]; then
    line=$(python -c "import json;r=json.load(open('$f'));print(r['wins'],r['fuel_outs'],r['per_game'][0]['candidate_sha256'][:12])")
  else
    line="FAILED - -"
  fi
  printf '%s\t%s\t%s\t%s\n' "$row" "$tag" "$line" "$*" | tee -a "$LOG"
  (cd $X1 && mkdir -p /c/x1-comms/g5060/results/J019 && printf '%s\t%s\t%s\t%s\n' "$row" "$tag" "$line" "$*" >> /c/x1-comms/g5060/results/J019/screens.tsv \
    && SIDE=g5060 bash tools/x1_comms.sh push "J019 screen row $row $tag: $line" > /dev/null 2>&1)
}
screen 0 base                                            # x3 plain: the per-game base for the sign test (PC: 86/172)
screen 1 burst2 --set A2_BURST2=1;                       screen 1 burst2wt --set A2_BURST2=1 $WT
screen 2 tsvis --set A2_TS_VIS=1;                        screen 2 tsviswt --set A2_TS_VIS=1 $WT
screen 2 tsvisbpwt --set A2_TS_VIS=1 $BP $WT
screen 3 locks --set V58_LOCKS=1;                        screen 3 lockswt --set V58_LOCKS=1 $WT
screen 4 diseng --set A2_DISENGAGE=1;                    screen 4 disengwt --set A2_DISENGAGE=1 $WT
screen 5 prune --set X1_PRUNEFIX=1;                      screen 5 prunewt --set X1_PRUNEFIX=1 $WT
screen 6 stage05 --set X1_ECON=1 --set X1_STAGE_MULT=0.5f
screen 6 stage07 --set X1_ECON=1 --set X1_STAGE_MULT=0.7f
screen 6 stage035 --set X1_ECON=1 --set X1_STAGE_MULT=0.35f
screen 7 wait15 --set X1_ECON=1 --set X1_WAIT_MULT=1.5f
screen 7 wait20 --set X1_ECON=1 --set X1_WAIT_MULT=2.0f
screen 7 wait125 --set X1_ECON=1 --set X1_WAIT_MULT=1.25f
screen 8 need13 --set X1_ECON=1 --set X1_NEED_MULT=1.3f
screen 8 need115 --set X1_ECON=1 --set X1_NEED_MULT=1.15f
screen 8 need15 --set X1_ECON=1 --set X1_NEED_MULT=1.5f
screen 9 belief --set A2_BELIEF=1;                       screen 9 beliefwt --set A2_BELIEF=1 $WT
screen 10 hiderec --set A2_HIDEREC=1;                    screen 10 hiderecwt --set A2_HIDEREC=1 $WT
screen 11 soak --set X1_SOAK64=1
screen 12 escort --set APEX_ESCORT=1
screen 13 bhold --set A2_BURST_HOLD=1
screen 14 sec15 --set X1_SECURE=1 --set X1_SECURE_MULT=1.5f
screen 14 sec6 --set X1_SECURE=1 --set X1_SECURE_MULT=6.0f
screen 15 bp2570 --set X1_BUSHPRE=25 --set X1_BUSHPRE_LAZY=70
screen 15 bp1050 --set X1_BUSHPRE=10 --set X1_BUSHPRE_LAZY=50
screen 16 sf45 --set X1_SIEGEFUEL=45;                    screen 16 sf55 --set X1_SIEGEFUEL=55
screen 17 af3w250wt --set X1_ANTIFEED=3 --set X1_ANTIFEED_WIN=250 $WT
screen 17 af5w400wt --set X1_ANTIFEED=5 --set X1_ANTIFEED_WIN=400 $WT
screen 17 af4w150wt --set X1_ANTIFEED=4 --set X1_ANTIFEED_WIN=150 $WT
screen 18 fd15 --set X1_FLEEDROP=15; screen 18 fd25 --set X1_FLEEDROP=25; screen 18 fd40 --set X1_FLEEDROP=40
screen 19 fh4 --set X1_FLEEHOLD=4
screen 20 teamwin --set X1_TEAMWIN=1; screen 20 heartfix --set X1_HEARTFIX=1
screen 20 bag40 --set X1_BAGRISK=40;  screen 20 bag80 --set X1_BAGRISK=80
screen 21 hs3 --set X1_HUNT_SOLO=3;   screen 21 hs5 --set X1_HUNT_SOLO=5
screen 22 alone --set X1_ALONE=1
screen 23 vision --set V58_VISION=1; screen 23 threat --set A2_THREAT=1; screen 23 stalebag --set APEX_STALE_BAG=1
screen 24 resetfix --set A2_RESETFIX=1; screen 24 fieldfirst --set A2_FIELDFIRST=1; screen 24 mapprof --set A2_MAP_PROFILE=1
screen 25 policywt --set A2_POLICY=1 $WT; screen 25 assesswt --set A2_ASSESS=1 $WT
screen 26 itemplan0 --set V58_ITEM_PLAN=0; screen 26 a3items1 --set A3_ITEMS=1; screen 26 a3items2 --set A3_ITEMS=2
P="--set X1_PLAN=1"
screen 28 p4r100 $P --set X1_PLAN_ROUND=100 --set X1_PLAN_ID=4; screen 28 p4r100wt $P --set X1_PLAN_ROUND=100 --set X1_PLAN_ID=4 $WT
screen 28 p4r150 $P --set X1_PLAN_ROUND=150 --set X1_PLAN_ID=4; screen 28 p4r150wt $P --set X1_PLAN_ROUND=150 --set X1_PLAN_ID=4 $WT
screen 28 p7r0 $P --set X1_PLAN_ROUND=0 --set X1_PLAN_ID=7;     screen 28 p7r0wt $P --set X1_PLAN_ROUND=0 --set X1_PLAN_ID=7 $WT
screen 28 p7r250 $P --set X1_PLAN_ROUND=250 --set X1_PLAN_ID=7; screen 28 p7r250wt $P --set X1_PLAN_ROUND=250 --set X1_PLAN_ID=7 $WT
screen 30 br3 --set APEX_BANK_RATIO=3.0f; screen 30 br25 --set APEX_BANK_RATIO=2.5f; screen 30 br35 --set APEX_BANK_RATIO=3.5f
echo J019_SCREENS_DONE
