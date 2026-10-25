# v57: contest the middle (stop discounting camps where enemies were seen)

Built 2026-10-25 by Claude Code from v56 (= live v55 + `V56_SHOP_DONE`). **Not submitted.** Source SHA-256 (sorted
name + NUL + bytes of `src/`): `dff699d59dfe682e761504859af24d28967b27f84626cc61b2f776e207470bbf`. Release Wasm is
byte-identical to the benchmarked build (`914b49a0…`).

## Why

The full Claudus Maximus series (80 games, all 40 maps both sides; 1-79) and v55's other ladder losses were decoded
with a new camp-clearing tool (`tools/replay/camp_clear.mjs`):

* Our own-half farming is roughly equal; the gap is the **contested, gem-rich middle**: Claudus clears 14.4 middle
  groups per game for 455 gems, we clear 7.9 for 117. Other winners: 13.6 / 321 gems vs our 10.2 / 201. In our wins
  we hold the middle (15.5 / 336 gems vs 11.9 / 124).
* While engaged with a camp our attack use equals theirs (0.62 vs 0.63); solo elk clears cost us the same 40% of
  max health; so the controller is not wasting turns at camps. The difference is where we farm and how much we
  survive.
* `UB_ENEMY_CAMP` 0.6 cut a camp's value by 40% whenever an enemy had been seen near it in the last 15 rounds, which
  in practice cedes the middle.

## Change

`UB_ENEMY_CAMP` 0.6 → **1.0** (`src/common.h`). One existing scoring weight; no new code, no hot-path change.
Screened against two alternatives first (4 seeds, paired against v56): a 1.5× middle-value weight was neutral (−5.2,
P 0.46) and the combination was +22.4 (P 0.66); this change was +64.0 (P 0.91) and was the one extended.

## Evidence (bench3, 28 development maps × 2 sides × 12 seeds; zero faults)

| Comparison | Games | Result | Bootstrap 95% (maps) | Bayesian, P(better) |
|---|---:|---|---|---|
| v57 vs live v55 | 672 | 379-293 (56.4%), +122.3 | [+66.7, +189.2] | +162.2 [+77.6, +253.0], 1.000 — ACCEPT |
| v57 vs v56, paired | 672 | 379 vs 352 wins, +77.1 | [+39.4, +115.4] | +60.7 [−9.0, +134.1], 0.957 — ACCEPT |
| **release holdout vs v55, once** | 72 | 38-34, **−31.3** | [−117.5, +54.4] | −23.3 [−179.9, +135.1], 0.383 |

Mechanism (local games vs v55, seeds 1-3): middle gems 295 vs 235 (v56: 283 vs 245); capture gold per champion
R500 347 vs 336; big-capture gems 151 vs 140; deaths 14.8 vs 15.6. Respawn waiting unchanged (122 vs 120).

**Holdout does not confirm the development gain.** Against v56's holdout (same games) it is −82.6 (interval
includes zero): pilgrimage −560, elk-arena −512 (a sole-gem map), monolith −197, fracture −154; gains on interlock
+185, ambush +135, expanse +99. Six games per map is inside the measured inert-change band, but the aggregate misses
the margin half of the holdout rule (≥ 50% wins and ≥ 0 margin). The holdout maps were not used for tuning.

## Rejected in this round

`V57_TP_BRIDGE` (non-dashers cross one-tile hole gaps with a teleport crystal on disconnected maps, three
iterations: plain, one-hop limit, group-only terrain). Big-world improved +45 to +51 every time; islands lost −345 to
−414 every time (chains of one-gap islands; single-use crystals; groups beyond need helpers). Diff and results:
`artifacts/claude_ops/rejected/`. Respawn waiting on disconnected maps remains the largest unsolved waste.

## Recommendation

v57 is the strongest development candidate so far, but it fails the holdout margin rule; v56 passes every gate.
Either keep v57 under test (more development seeds will not settle it; new maps or ladder games would) or release
v56. Survival against stronger-geared teams (3.5× our death rate per contact against Claudus) is still open: every
local opponent is our own lineage, so it cannot be validated locally.
