id: K004
title: J011 + J012 (moved from the 5060): combinations of the R1 passes, and x1 vs v86h, all on BUSHPRE
commit: 6efc360 on build/z-plan
bot: x1
run: gate (tools/x1_gate.sh); run tags end in -g5070
priority: first
BP = --set X1_BUSHPRE=15 --set X1_BUSHPRE_LAZY=60
P5 = --set X1_SECURE=1 --set X1_SOAK64=1 --set APEX_ESCORT=1 --set A2_HIDEREC=1 --set A2_BURST_HOLD=1
part A (opponents x2 x2-s2; maps ladder styled, maze if maps/x1-maze exists at the commit):
  bp:        BP                                    (the base for every line below)
  P5:        BP + P5
  P3:        BP --set X1_SOAK64=1 --set APEX_ESCORT=1 --set A2_HIDEREC=1
  P5af:      BP + P5 --set X1_ANTIFEED=3 --set X1_ANTIFEED_WIN=250
  P5p4:      BP + P5 --set X1_PLAN=1 --set X1_PLAN_ROUND=250 --set X1_PLAN_ID=4
  P5af_p4:   BP + P5 + both of the above
  P5burst2:  BP + P5 --set A2_BURST2=1
part B (OPPS="v86h v86h-s2"; maps ladder styled): lines x1 (no switches), bp, P5, and the best part-A line.
report: g5070/results/K004.md, columns as g5060/results/RQ6-sweep-leaders.md (wins, delta, per map kind, fuel-outs,
deaths/game, gold@R500, games changed, sha, verdict by rule R1 vs bp) + win % per map kind for part B.
