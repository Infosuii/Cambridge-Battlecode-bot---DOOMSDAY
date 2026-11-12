id: K005
title: R2 variant grids on BUSHPRE (anti-feed, whole-game plans, fuel floors)
commit: 6efc360 on build/z-plan
bot: x1
run: gate; opponents x2 x2-s2; maps ladder styled (+maze if present); tags end in -g5070
priority: after K004
why: these lines gained +13..+27 wins but failed R1 on fuel-outs only; with x1's own fuel spikes fixed (BUSHPRE),
the retry protocol needs >= 2 variants each before any verdict (RETRY_QUEUE R2).
BP = --set X1_BUSHPRE=15 --set X1_BUSHPRE_LAZY=60   (every line = BP + the switches shown; base = the bp line from K004)
grid 1 anti-feed:  X1_ANTIFEED K in {2,3,4,5} x X1_ANTIFEED_WIN in {150,250,400}       (12 lines)
grid 2 plans:      X1_PLAN=1, X1_PLAN_ID=4 at X1_PLAN_ROUND in {50,100,150,200,250};
                   X1_PLAN_ID=6 at {100,150,200}; X1_PLAN_ID=7 at {250,350}             (10 lines)
grid 3 joint:      best of grid 1 + best of grid 2 (by total wins, then fewer fuel-outs) (1 line)
grid 4 fuel:       X1_BUSHPRE in {10,15,25} x X1_BUSHPRE_LAZY in {50,60,70}, base = x1 (no switches) (9 lines)
                   plus X1_SIEGEFUEL in {45,55,65} on BP                                 (3 lines)
report: g5070/results/K005.md, one table per grid, same columns as K004; mark the best line per grid.
