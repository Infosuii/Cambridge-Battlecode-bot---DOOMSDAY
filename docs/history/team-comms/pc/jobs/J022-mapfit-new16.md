id: J022
title: per-map fit for the 16 pool maps without a ladder table (top priority)
commit: build/z-plan head (X1_MAPFIT, tools/x3_mapfit.sh, tools/x3_mapfit_table.py, dz --candidate-wasm)
why: your J018 split - x3 (= v92) vs x1: 119/140 on the 70 maps with v92's tables, 14/32 on the 16 without one
(v86h 91/140 vs 17/32; x1bru 100/140 vs 17/32). v92's whole edge is its per-map fit; ~19% of ladder games are on
maps it never fitted. This job fits them the same way.
priority: FIRST. It supersedes J020 A (plan per map) and J021 run 2 (fight-new); keep J021 run 1 going beside it
if the machine has room.
run:   bash tools/x3_mapfit.sh            (16 maps x 6 iterations x 7 candidates x 3 opponents x 2 sides ~ 8,000 games;
                                           one build per candidate now; state in research/x3/es/mapfit-<map>.json)
then:  python tools/x3_mapfit_table.py    (writes bots/x3/src/x1_mapfit.h; maps with no gain keep v92)
gate:  x3 with --set X1_MAPFIT=1 vs x3 plain on pool (and the 16 maps alone) vs v92, v86h, x1bru; post both.
Push research/x3/es/ and the generated x1_mapfit.h to build/z-plan-5060; the PC merges.
Refinement if the gain is small: more iterations on the maps still below 0.5 fit/game, sigma 0.3, more opponents.
