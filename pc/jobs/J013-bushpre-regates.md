id: J013
title: X1_BUSHPRE fuel fix, then re-gate the 14 fuel-blocked features on top of it
commit: 0d9f67b on build/z-plan (off build still 1746f2bb7fa3)
bot: x1
run: gate (tools/x1_gate.sh); opponents x2 x2-s2; maps ladder styled (maze when it exists)
priority: FIRST, before J011 / J012 (run those after, at 0d9f67b, with BP added to every line)
why: half of x1's fuel-outs came from first-use bush-cluster labelling (50-120k spikes inside the ward / ambush code).
X1_BUSHPRE labels clusters ahead of use from leftover fuel and makes on-demand labelling resumable. PC screen on the
6 worst maps (12 games vs x2): fuel-outs 73 -> 22, rounds 0-150: 52 -> 6-8. The features below lost their R1 gates
only on the fuel-out clause; with the spikes gone they get a fair retry (fuel attempt 1 of max 3 per feature).
BP = --set X1_BUSHPRE=15 --set X1_BUSHPRE_LAZY=60
lines (base for the verdicts of lines 3+ is line bp, not x1):
  bp:        BP
  bp2050:    --set X1_BUSHPRE=20 --set X1_BUSHPRE_LAZY=50
  af3w250:   BP --set X1_ANTIFEED=3 --set X1_ANTIFEED_WIN=250
  af4:       BP --set X1_ANTIFEED=4
  p4r100:    BP --set X1_PLAN=1 --set X1_PLAN_ROUND=100 --set X1_PLAN_ID=4
  p4r150:    BP --set X1_PLAN=1 --set X1_PLAN_ROUND=150 --set X1_PLAN_ID=4
  p6r150:    BP --set X1_PLAN=1 --set X1_PLAN_ROUND=150 --set X1_PLAN_ID=6
  burst2:    BP --set A2_BURST2=1
  stage05:   BP --set X1_ECON=1 --set X1_STAGE_MULT=0.5f
  wait15:    BP --set X1_ECON=1 --set X1_WAIT_MULT=1.5f
  need13:    BP --set X1_ECON=1 --set X1_NEED_MULT=1.3f
  prunefix:  BP --set X1_PRUNEFIX=1
  locks:     BP --set V58_LOCKS=1
  disengage: BP --set A2_DISENGAGE=1
  belief:    BP --set A2_BELIEF=1
  tsvis:     BP --set A2_TS_VIS=1
  P5bp:      BP --set X1_SECURE=1 --set X1_SOAK64=1 --set APEX_ESCORT=1 --set A2_HIDEREC=1 --set A2_BURST_HOLD=1
report: same columns as RQ6, plus fuel-outs split rounds <150 / >=150 (fuelExhausted entries in summary.json), so the
PC can see what the late-game fuel-outs are. Verdict for bp / bp2050 vs x1 base; every other line vs bp.
done when: g5060/results/J013.md
