id: K014
title: SPEEDRUN (Rishik): feature sweep rows 14-26 on x3mf - right after K011, before K012 / K013
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
priority: 0 (after the K011 reproduction passes). Results: g5070/results/K014.md.
lines (row: line name: switches):
14: sec3 / sec15 / sec6: X1_SECURE=1 with X1_SECURE_MULT=3 / 1.5 / 6
15: bp1560 / bp2570 / bp1050: X1_BUSHPRE=15 X1_BUSHPRE_LAZY=60 ; 25 / 70 ; 10 / 50
16: sf45 / sf55: X1_SIEGEFUEL=45 / 55
17: af3w250 / af5w400 / af4w150: X1_ANTIFEED 3 / 250, 5 / 400, 4 / 150 (count / window parameters; find their names),
    each + X1_WALKTAIL=3
18: fd15 / fd25 / fd40: X1_FLEEDROP=15 / 25 / 40
19: fh4: X1_FLEEHOLD=4
20: teamwin / heartfix / bag40 / bag80: X1_TEAMWIN=1 ; X1_HEARTFIX=1 ; X1_BAGRISK=40 ; X1_BAGRISK=80
21: solo3 / solo5: X1_HUNT_SOLO=3 / 5
22: alone: X1_ALONE=1
23: vision / threat / stale: V58_VISION=1 ; A2_THREAT=1 ; APEX_STALE_BAG=1
24: reset / ffirst / mprof: A2_RESETFIX=1 ; A2_FIELDFIRST=1 ; A2_MAP_PROFILE=1
25: policywt / assesswt: A2_POLICY=1 X1_WALKTAIL=3 ; A2_ASSESS=1 X1_WALKTAIL=3
26: items0 / a3i1 / a3i2: V58_ITEM_PLAN=0 ; A3_ITEMS=1 ; A3_ITEMS=2
(33 lines; then work-steal from J026's bottom.)
