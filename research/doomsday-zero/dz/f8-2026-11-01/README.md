# F8 champion mastery and the mastery draft (2026-11-01)

Per-champion DZ results across the league (6 release-equivalent full-pool runs): Ryth 115 gems per 1k rounds,
Marcella 80 (best gold 574, fewest deaths 3.8, most kills 0.41), Vendetta 80 (most deaths 5.1), Varg 73, Vesper
70, Heart of Ruin 48 (lowest gold 308). `DZ_DRAFT_MASTERY` picks Ryth, Marcella, Vesper, Varg, Vendetta, Heart;
screened with survive/prospect gear, the fuel set and fast boot; paired with `dz-fastboot-<opp>-01`.

| Opponent | Δ banked (SE) | Δ margin (SE) | holdout Δ margin (SE) | deaths | wins |
|---|---|---|---|---|---|
| v76 | +33.6 (14.1) | **+44.2 (21.1)** | +77.4 (81.9) | 18.5 vs 19.0 | 4 vs 1 |
| v65 | +36.2 (12.3) | **+42.1 (16.6)** | +86.7 (27.6) | 18.2 vs 18.5 | 4 vs 3 |
| v74 | +36.4 (15.7) | +54.5 (25.4) | (same games as v76, see below) | 18.1 vs 18.9 | 5 vs 1 |
| v81hl (team's best) | +30.4 (10.2) | **+35.9 (13.6)** | +19.1 (22.3) | 18.1 vs 18.6 | 1 vs 1 |

0 fuel-outs. One global build (no per-map table): positive on every opponent and on the holdout, so G6 applies.

**Correction (v74 ≈ v76):** in this repository `bots/v74` and `bots/v76` differ only in bot.cpp, and 118 of 140
cells give identical results against either. v74 was therefore never an independent confirmation opponent: the
Z14b/Z14c table "confirmations vs v74" (+78 / +102) largely replay the v76 selection games and are inflated. The
independent unseen opponents are v81hl and v85. Against v81hl: mastery +35.9, dvg7 everywhere +31.5, Z14b table
+25.1 (dev), Z14c table +6.8 (dev).

## Second unseen opponent and idle (paired with dz-fastboot-v85-01 / -idle81-01)

| Opponent | Δ banked (SE) | Δ margin (SE) | holdout Δ margin (SE) | wins |
|---|---|---|---|---|
| v85 (unseen) | +52.9 (16.3) | **+65.2 (25.6)** | +77.2 (36.9) | 17 vs 13 |
| idle | +28.0 (12.0) | +28.0 (12.0) | +6.7 (11.2) | 138 vs 137 |

League (v76, v65, v74, v81hl, v85): +44.2, +42.1, +54.5, +35.9, +65.2 margin; mean ≈ +48; every lower bound above
-30; deaths not up; holdout positive; 0 fuel-outs. G5 at the +50 bar (just under on the mean), G6 and G2 pass.
This is the candidate core: DZ_DRAFT_MASTERY + DZ_GEAR_SURVIVE + DZ_GEAR_PROSPECT + DZ_FAST_FIGHT +
DZ_LATE_FIELD_GATE + DZ_FIELD_METER + DZ_FAST_BOOT (snapshot f8-2026-11-01/source).
