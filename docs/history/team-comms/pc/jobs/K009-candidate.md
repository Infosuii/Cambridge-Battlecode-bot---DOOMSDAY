id: K009
title: ship candidate: BP + plan 4 R150 + WALKTAIL 3 (+ SECURE), full gate and strong opponents
commit: 2732245 on build/z-plan (off build 1746f2bb7fa3)
bot: x1
priority: right after the K007 WALKTAIL lines (before the rest of K006).
why: PC ladder + styled, p150wt3 vs x2 / x2-s2: 286/480 (p150 285, bp 275), fuel-outs 172 (bp 206, p150 227).
Attempt 2 removes the plan-4 fuel-outs without the win loss of WALKRES. J016: SECURE is the only add-on that still
passes on plan 4 (+2).
C = --set X1_BUSHPRE=15 --set X1_BUSHPRE_LAZY=60 --set X1_PLAN=1 --set X1_PLAN_ROUND=150 --set X1_PLAN_ID=4 --set X1_WALKTAIL=3
lines (verdicts vs bp; also report vs plain x1):
  cand:        C
  candsec:     C --set X1_SECURE=1
  bpwt3:       BP --set X1_WALKTAIL=3       (does the fix help the base too)
run each line: (a) gate x2 x2-s2, ladder styled maze; (b) OPPS="v86h v86h-s2 v81hl", ladder styled, same as K006.
Reuse the PC's ladder+styled x2/x2-s2 runs of cand if they are on build/z-plan (x1g-p150wt3-*).
done when: g5070/results/K009.md (the PC builds the zip from the best passing line)
