# J024 - URGENT, first: counter table vs v92 (Rishik wants a bot that steamrolls v92 within the hour)

commit: 1ff45a1 on build/z-plan (bots/x3; X1_COUNTER off = v92 5704d7ba41ac)

**Pause J022 and J021 now** (both resume from cache later) and give J024 every worker.

Idea: games are deterministic per (map, side, both bots). Each search build forces one variant of our play on every
map (team plan 1-8, late plans, 16 knob vectors; list in bots/x3/src/x1_counter.h). For each (map, side) that plain
v92 play loses, the table picks a variant that won it. Same builds -> same games, so every covered loss becomes a win.

1. `bash tools/x3_counter_run.sh "0 4 7 3 8 1 2 5 6 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29" v92 6`
   (172 games per variant, pool, both sides; k0 must be 86/172). Run two variants side by side if builds dominate.
   Post a one-line status with the per-variant wins after every ~8 variants (results file `g5060/results/J024.md`).
2. Table: `python tools/x3_counter.py table --runs ctr-v92-k{K} --vars 1-29` -> prints "expected N/172".
3. Verify: `python tools/dz.py smoke --name ctr-v92-table --map-dir maps/ladder-pool --maps <all 86> --opponent v92
   --candidate-bot x3 --workers 6 --set X1_COUNTER=1` (builds with the generated table). If the result is far below
   the expected count, rerun the table with the side swapped (team 0 = side A is assumed) and report.
4. Same table build vs v86h and x1bru on pool (does the counter cost us against others?).
5. Commit bots/x3/src/x1_counter.h **as a result file** `g5060/results/J024-x1_counter.h` (do not push bots/* to
   build/z-plan), plus J024.md with every number. The PC merges it, builds the zip.
