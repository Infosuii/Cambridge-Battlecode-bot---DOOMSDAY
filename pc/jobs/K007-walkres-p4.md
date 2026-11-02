id: K007
title: fuel attempt 1 for plan 4 R150: X1_WALKRES walk search reserve
commit: 6ed38b9 on build/z-plan (off build still 1746f2bb7fa3)
bot: x1
run: gate (tools/x1_gate.sh); opponents x2 x2-s2; maps ladder styled maze (59)
priority: FIRST: run before the rest of K005 / K006.
why: plan 4 R150 is the best line (pooled +39 vs x1) but adds 21 ladder+styled fuel-outs. Telemetry: 19 of 29
fuel-outs cross right after walk_toward, whose capped search leaves only 1-2k for the rest of fight_camps.
X1_WALKRES=k keeps k thousand fuel instead of 6k. Screen: gen4_0105 vs x2-s2 24 -> 0 fuel-outs.
BP = --set X1_BUSHPRE=15 --set X1_BUSHPRE_LAZY=60
P150 = BP --set X1_PLAN=1 --set X1_PLAN_ROUND=150 --set X1_PLAN_ID=4
P100 = BP --set X1_PLAN=1 --set X1_PLAN_ROUND=100 --set X1_PLAN_ID=4
lines:
  bp:          BP                                   (base for every verdict)
  p150:        P150
  p150wr10:    P150 --set X1_WALKRES=10
  p150wr12:    P150 --set X1_WALKRES=12
  p150wr15:    P150 --set X1_WALKRES=15
  bpwr12:      BP --set X1_WALKRES=12
  p100wr12:    P100 --set X1_WALKRES=12
report: K005 columns; fuel-outs split ladder+styled / maze, and before/after round 150.
done when: g5070/results/K007.md
