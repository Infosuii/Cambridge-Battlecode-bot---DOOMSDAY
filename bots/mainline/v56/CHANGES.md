# v56: stop gold-only shop trips once the build plan is complete

Built 2026-10-25 by Claude Code from live platform v55 (`bots/v55`, hash `11a6f5e9…`). **Not submitted.** Source
SHA-256 (sorted name + NUL + bytes of `src/`): `35d8ea4a5883186e66d38158d351087a7fdc68122649c11efbc6dfc4fe5dd607`.

## Change

`V56_SHOP_DONE` (`src/common.h`, default 1). Implements the confirmed defect from the v55 architecture report: once
every `BuildStep.total` is reached, `shop()` buys nothing, but `go_home_if_needed()` kept sending a champion home
whenever `gold >= kShopGold` (and the respawn-wait branch did the same at 90 gold). The report logged boss-battle
carriers with 300-700 gems making 200-300 such trips.

* `shop()` records `shop_done` when a visit walks the whole plan with every step complete, or when the engine refuses
  a purchase on our spawn (inventory or stat limit; nothing more can be bought). An early return for lack of gold
  records nothing.
* With `shop_done`, gold alone no longer triggers a home trip, in `go_home_if_needed` and in the respawn-wait detour.
  Health retreats, threat retreats, banking, builds and every other branch are unchanged.
* The report's branch-and-bound bound correction was **not** ported: its full test was 84-84, −1.9 and rejected.

## Evidence (bench3 vs v55, 28 development maps × 2 sides; zero faults throughout)

| Test | Games | Record | Mean margin | Bootstrap 95% (maps) | Bayesian posterior (gems), P(better) |
|---|---:|---:|---:|---|---|
| seeds 1-12 | 672 | 352-320 | +45.1 | | +53.7 [−22.5, +135.7], 0.921 |
| seeds 13-24 (replication) | 672 | 357-315 | +43.9 | | +52.9 [−14.2, +125.0], 0.939 |
| **seeds 1-24** | **1344** | **709-635** | **+44.5** | **[+2.4, +103.4]** | **+55.2 [−12.9, +123.6], 0.944** |
| release holdout, 12 final maps, seeds 1-3 (once) | 72 | 38-34 | +51.2 | [−2.4, +120.1] | +63.5 [−86.7, +212.6], 0.802 |

Per map over 24 seeds (pooled posterior): boss-battle +489 [+326, +651], contest +505 [+355, +649], swirl +165
[−3, +335]; no map has P(gain) ≤ 0.1. Nine maps produced exactly mirrored games (the fix never triggers where plans
do not complete). Fuel-exhausted turns 1279 vs 1209 (seeds 1-12).

Gate (HANDOFF §4) against live v55: (a) declared target boss-battle won 6/6 on seeds 1-3, one of them a 0-margin
tiebreak (5/6 by a clear margin); (b) 0.528 and +44.5; (c) holdout aggregate 38-34, +51.2. The overall gain is real
but concentrated in boss-battle and contest; the hierarchical model is right not to call the overall effect
decisive at 95%.

## Limits

Evidence is against our own lineage; the ladder losses (`research/v55/V55_LADDER_ANALYSIS.md`) are driven
by income rate, draft and survival, which this change does not address. Hooks and the holdout maps have prior
exposure.
