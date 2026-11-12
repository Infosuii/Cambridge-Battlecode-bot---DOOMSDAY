id: L008
title: URGENT - gate x3mf2 (J023 weak-map fits added to x3mf's table); STOP L006 (the 5060 already finished J023)
priority: 0. L006 is cancelled: the 5060 completed all 13 J023 maps at 01:50 UTC (research/x3/es on build/z-plan).
commit: build/z-plan 15848079 (bots/x3mf2 = x3 with X1_MAPFIT 1 and the 25-map table)
run, in this order, posting each result line as soon as it lands:
  1. head-to-head (the user's rule: > 60% = better, > 53% = notify):
     SETS=pool OPPS="x3mf" WORKERS=14 bash tools/x1_gate.sh x3mf2 h2h-g3
  2. SETS=pool OPPS="x3inv v81hl v86h-s2" WORKERS=14 bash tools/x1_gate.sh x3mf2 mf2-g3
     (x3mf: x3inv 102, v81hl 137, v86h-s2 107)
done when: g3/results/L008.md with wins, candidate sha, gained / lost vs the x3mf numbers above.
