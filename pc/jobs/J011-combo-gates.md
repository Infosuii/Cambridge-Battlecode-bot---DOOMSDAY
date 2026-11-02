id: J011
title: full gates for combinations of the R1 passes (first x1 candidate)
commit: 0b3703b on build/z-plan (off build 1746f2bb7fa3)
bot: x1
run: gate (tools/x1_gate.sh); opponents x2 x2-s2; maps ladder styled (maze when it exists)
priority: now, before your own idle work (finish the gate already running first)
why: SECURE, soak64, APEX_ESCORT, A2_HIDEREC and A2_BURST_HOLD each passed R1 alone. This checks they add up, and
whether the biggest fuel-blocked gains (anti-feed, plan 4) carry the combination past the fuel clause.
switches (P5 = the five passes):
  P5:        --set X1_SECURE=1 --set X1_SOAK64=1 --set APEX_ESCORT=1 --set A2_HIDEREC=1 --set A2_BURST_HOLD=1
  P3:        --set X1_SOAK64=1 --set APEX_ESCORT=1 --set A2_HIDEREC=1
  P5af:      P5 + --set X1_ANTIFEED=3 --set X1_ANTIFEED_WIN=250
  P5p4:      P5 + --set X1_PLAN=1 --set X1_PLAN_ROUND=250 --set X1_PLAN_ID=4
  P5af_p4:   P5 + both of the above
  P5burst2:  P5 + --set A2_BURST2=1
notes:
  - Report per-line fuel-outs and deaths/game as in RQ6; the PC is cutting the fuel cost of anti-feed, plan 4,
    BURST2 and LOCKS in parallel, so a "fail on fuel only" here is expected and still useful (it sizes the fix).
  - If any line builds the same binary as another, say so and skip it.
  - 5 of 6 J007 hashes "not from the pushed source": the PC is checking this; use 0b3703b as is.
done when: g5060/results/J011.md, same columns as RQ6.
