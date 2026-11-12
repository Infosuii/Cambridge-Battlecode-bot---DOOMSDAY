# Fresh holdout: the 15 new platform pool maps

Claude Code, 2026-10-25. The platform pool now has 55 maps. 40 are byte-identical to `maps/local-benchmarks`; 15 are
new and no version was developed or tuned on them: 00anvil, 00breadcrumbs, 00crater, 00dunes, 00galaxy, 00oasis,
00quarry, 00ribs, 00the-line, 00vault, adgato-gemcombat1-5. Pulled with `cambc maps pull` and kept local-only
(`artifacts/local-only/pool-maps/new15`; the pull writes into the repo's `maps/`, so the files were moved out).

Run once per frozen candidate with `tools/bench3_fresh.sh` (bench3 with the new `tools/fresh_match.py`,
which takes a map directory instead of the registered partitions): 15 maps × 2 sides × seeds 1-4 = 120 games each,
against live v55. Zero faults; fuel-outs 4-5 per run.

| Comparison | Record | Margin | Bootstrap 95% (maps) | Bayesian mean [95%], P(>0) |
|---|---|---:|---|---|
| v57 vs v55 | 67-53 (55.8%) | **+84.8** | [−20.7, +191.0] | +100.4 [−41.7, +242.7], 0.916 |
| v56 vs v55 | 60-60 (50.0%) | +4.4 | [−15.5, +23.0] | +1.9 [−122.1, +125.2], 0.510 |
| v57 − v56, paired | | +80.4 | [−22.7, +180.8] | +91.2 [−42.1, +222.7], 0.909 |

* **v57 passes the holdout rule here** (≥ 50% wins and ≥ 0 margin), where it failed on the original 12-map holdout
  (38-34, −31.3). Pooled over both holdouts (192 games): about +41 gems per game. Neither set alone is decisive at
  95%.
* v56 has a mean margin of exactly 0 against v55 on 10 of the 15 maps (the same games: shop completion is rare there); it is safe but adds nothing
  here.
* v57 per map: largest gains on crater +447, quarry +419, adgato-gemcombat1 +315, ribs +210, the-line +191, dunes
  +185; losses on adgato-gemcombat5 −313, adgato-gemcombat3 −158, anvil −91, oasis −79, breadcrumbs −64. 00vault is
  won by side B in all 8 games for both candidates (a side-asymmetric map).

Reading: v57's development gain (+77 to +122) shows up on maps no version has seen. The earlier holdout miss looks
like map noise more than overfitting. These 15 maps are now used once for v55-v57; reuse them only for the next
frozen candidate's final check, never for tuning.
