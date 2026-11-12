id: J009
title: whole-game plan gates from the J005 partial (plan 4 turtle +20/+27 net, plan 6 +17 @R150)
commit: e15b68d or later on build/z-plan (any commit with X1_PLAN)
bot: x1
run: gate (tools/x1_gate.sh), one gate per line; opponents x2 x2-s2; maps ladder styled (maze when it exists)
priority: 1, right after J005 finishes (before J006)
switches (X1_PLAN=1 compiles the hook; ROUND 0 = the whole game):
  p4r0:    --set X1_PLAN=1 --set X1_PLAN_ROUND=0   --set X1_PLAN_ID=4
  p4r100:  --set X1_PLAN=1 --set X1_PLAN_ROUND=100 --set X1_PLAN_ID=4
  p4r150:  --set X1_PLAN=1 --set X1_PLAN_ROUND=150 --set X1_PLAN_ID=4
  p6r0:    --set X1_PLAN=1 --set X1_PLAN_ROUND=0   --set X1_PLAN_ID=6
  p6r150:  --set X1_PLAN=1 --set X1_PLAN_ROUND=150 --set X1_PLAN_ID=6
  p3r150:  --set X1_PLAN=1 --set X1_PLAN_ROUND=150 --set X1_PLAN_ID=3
also: report fuel-outs per line vs base carefully (plan 4 added 39-49 new fuel-outs per 480 branches in J005).
done when: g5060/results/J009.md, same columns as J006.
