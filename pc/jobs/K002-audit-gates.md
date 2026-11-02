id: K002
for: g5070
title: = J007, moved from the 5060: full gates of the six x1-audit fixes
commit: latest build/z-plan (bots/x1; off build 1746f2bb7fa3)
run: tools/x1_gate.sh, SETS="ladder styled", OPPS="x2 x2-s2", tag suffix -g5070, in this order:
  1. base-g5070        (no switches; the gate baseline for every line below)
  2. prunefix-g5070    --set X1_PRUNEFIX=1
  3. teamwin-g5070     --set X1_TEAMWIN=1
  4. soak64-g5070      --set X1_SOAK64=1
  5. heartfix-g5070    --set X1_HEARTFIX=1
  6. fleehold4-g5070   --set X1_FLEEHOLD=4
  7. fleehold15-g5070  --set X1_FLEEHOLD=15
  8. fleehold8-g5070   --set X1_FLEEHOLD=8
  9. siegestrict-g5070 --set X1_SIEGE_STRICT=1
  (base on x2 ladder must reproduce 68/140; K001 already ran that cell.)
report per line: wins per cell vs base, deaths/game, gold@R250/R500, finish round, fuel-outs, faults, verdict by
the gate rule (tools/x1_gate_report.py on build/z-plan-5060 computes these; fetch it into your local checkout).
Post after each line. PC quick screens (19 ladder maps vs x2): prunefix 21, teamwin 20, soak64 19, heartfix 18,
siegestrict 17, fleehold8 15 vs base 17.
