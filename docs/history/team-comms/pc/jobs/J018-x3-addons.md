id: J018
title: x1's switches on top of x3 (= v92), vs x1 / v86h / x1bru
commit: build/z-plan 67dcf02 or later. bots/x3 = v92 (Agent 2 E79-E89, ladder v75: 751-539 on the real ladder
        2 Nov 02:53-14:38) applied onto x1; its default build is byte-identical to v92 (5704d7ba41ac), so x3 is the
        new base, with all x1 switches available.
priority: after I-60-04's current gate (or pause it); before ideation.
lines (candidate bot x3; verdicts vs x3 plain):
  x3:      (none)
  x3bp:    --set X1_BUSHPRE=15 --set X1_BUSHPRE_LAZY=60
  x3sec:   --set X1_SECURE=1
  x3wt:    --set X1_WALKTAIL=3
  x3all:   all three
opponents: x1, v86h, x1bru; sets: pool (maps/ladder-pool = the current 86-map competition pool, new gate set), styled,
maze. The PC runs the same lines vs v92 on pool.
Also: rebase I-60-04 (conversion fix) onto x3 if it is a switch in bot.cpp; the ship base is x3 now.
report: g5060/results/J018.md (per kind, sign test vs x3).
