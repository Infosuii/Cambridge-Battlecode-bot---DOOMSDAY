id: J026
title: SPEEDRUN (Rishik): feature sweep rows 1-13 on x3mf - pause J023 now
commit: 9c1bbde on build/z-plan (bots/x3). Every line adds `--set X1_MAPFIT=1` (base x3mf, c3da892053a7).
bot: x3
run: screen = gate on pool vs v92 only: `SETS=pool OPPS=v92 WORKERS=<all> bash tools/x1_gate.sh x3 <line>-<you> "--set X1_MAPFIT=1 <switches>"`
  Base x3mf vs v92 = 96/172 (g5060 J022 run; rerun it once yourself as `mf-<you>` so your pairs are exact).
switch names: the names below are from the tracker. Before each row, grep bots/x3/src/*.h for the exact `#define`
  (and its parameter defines). If a name differs, use the real one and write the exact --set you used. If a switch
  does not exist at all, or does not build, write "missing" / "build fail" for that row and go on. Never edit code.
promote: a line with >= 102/172 is played at once vs v86h and x1bru too (pool; base 115 / 130, total 341 / 516).
  Pass = total >= 347, paired z >= 1.3, no opponent more than 2 worse, fuel-outs not up > 10%.
report: one table row per line in your results file right after it finishes (wins, delta vs 96, gained / lost, z,
  fuel-outs, deaths/game, build sha, exact --set), pushed after every 3 lines. No waiting to the end.
order: top to bottom. Work stealing: when your list is done, take the other machine's unfinished rows from the
  bottom of its list upwards, after checking its results file so no line runs twice (skip any line it reported).
priority: 0. **Pause J023 now** (resume from cache after the sweep). Results: g5060/results/J026.md.
lines (row: line name: switches):
 1: burst2 / burst2wt: A2_BURST2=1 ; A2_BURST2=1 X1_WALKTAIL=3
 2: tsvis / tsviswt / tsvisbpwt: A2_TS_VIS=1 ; + X1_WALKTAIL=3 ; + X1_BUSHPRE=15 X1_BUSHPRE_LAZY=60 X1_WALKTAIL=3
 3: locks / lockswt: V58_LOCKS=1 ; + X1_WALKTAIL=3
 4: diseng / disengwt: A2_DISENGAGE=1 ; + X1_WALKTAIL=3
 5: prune / prunewt: X1_PRUNEFIX=1 ; + X1_WALKTAIL=3
 6: stage05 / stage07 / stage035: X1_STAGE_MULT=0.5 / 0.7 / 0.35 (+ X1_ECON=1 if that switch exists)
 7: wait15 / wait20 / wait125: X1_WAIT_MULT=1.5 / 2.0 / 1.25 (+ X1_ECON=1 if it exists)
 8: need13 / need115 / need15: X1_NEED_MULT=1.3 / 1.15 / 1.5 (+ X1_ECON=1 if it exists)
 9: belief / beliefwt: A2_BELIEF=1 ; + X1_WALKTAIL=3
10: hiderec / hiderecwt: A2_HIDEREC=1 ; + X1_WALKTAIL=3
11: soak64: X1_SOAK64=1
12: escort: APEX_ESCORT=1
13: bhold: A2_BURST_HOLD=1
(27 lines; then work-steal from K014's bottom.)
