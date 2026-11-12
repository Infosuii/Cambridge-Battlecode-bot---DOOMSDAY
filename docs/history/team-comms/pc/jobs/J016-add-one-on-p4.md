id: J016
title: add-one gates on top of the best passing line (BP + plan 4 from R100)
commit: build/z-plan head (30af738 or later; off build still 1746f2bb7fa3)
bot: x1
run: gate (tools/x1_gate.sh); opponents x2 x2-s2; maps ladder styled maze (all 59 maze maps, A + B)
priority: FIRST (now). Then start your own ideation (pc/msgs/0010, pc/IDEATION_RULES.md).
why: the 5-feature bundle P5 loses on every base (K004: -13..-47), but each piece passed alone. Adding them one at a
time to the line we will ship shows which ones still add on top of plan 4. Base P4 = BP + plan 4 from R100 (pooled
+36 vs x1, passes, no fuel problem). Plan 4 from R150 is +39 but fails on fuel; the PC is cutting its fuel now.
P4 = --set X1_BUSHPRE=15 --set X1_BUSHPRE_LAZY=60 --set X1_PLAN=1 --set X1_PLAN_ROUND=100 --set X1_PLAN_ID=4
lines (verdict of every line vs p4):
  p4:          P4
  p4sf55:      P4 --set X1_SIEGEFUEL=55
  p4secure:    P4 --set X1_SECURE=1
  p4soak:      P4 --set X1_SOAK64=1
  p4escort:    P4 --set APEX_ESCORT=1
  p4hiderec:   P4 --set A2_HIDEREC=1
  p4bhold:     P4 --set A2_BURST_HOLD=1
  p4belief:    P4 --set A2_BELIEF=1
  p4af5:       P4 --set X1_ANTIFEED=5 --set X1_ANTIFEED_WIN=400
report: RQ6 columns + fuel-outs split ladder+styled / maze. Then one more line: p4 + every add-one that passed.
done when: g5060/results/J016.md
