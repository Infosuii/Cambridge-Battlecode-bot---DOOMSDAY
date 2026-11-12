# v59: stat stacks instead of Greed, retreat when clearly outnumbered (from submitted v58 = platform 57)

Not submitted. Built 2026-10-26 from the review of v58's first 320 ladder games
(`research/v59/V59_LOSS_ANALYSIS.md`) and the process review (`research/v59/V59_PROCESS_FIXES.md`).

## Why

- v58 loses ranked games because it dies twice as often as the winner (14.0 vs 6.9 deaths per loss). It is
  outnumbered in contact twice as often (21% vs 11%) and takes 47% more damage per contact round. 40% of our
  deaths happen outnumbered and 34% with no ally within 8.
- The winners' carries out-gear ours. v58's plan ends in Greed, a 25-shard (750-gold) emblem that our champions
  rarely complete, so the last 200-500 gold of a champion went into 1.0x shards.
- On the ladder, opponent-adjusted, v58 is no better than v57, although it beat v57 by +153 locally. The local
  bench is a safety net only; the final check for v59 is the paired ladder A/B (`tools/replay/ladder_ab.py`).

## What changed

| Switch | Value | Effect |
|---|---|---|
| `V59_ITEMS` | 2 | v58's opening emblems unchanged (Prospector, Jungle, Durability, Monster, Capture, Collectors), then Bruiser stacks of the main stat with Bruiser health interleaved (2:1 melee, 3:1 ranged/casters, 1:1 Heart; Marcella adds strength). Replaces the three 25-shard Greed milestones. Each 150 gold completes an emblem (7 shards of stats). Levels 1 and 3 (winner-style opening, short opening) are kept for screens. |
| `APEX_OUTNUMBERED` | 2 | Existing rule, previously off: retreat when visible enemies within 8 are at least 2 more than this champion plus healthy allies within 5, unless the kill is sure this turn. Level 1 was too passive (-228 vs v58). |
| `V59_ALONE` | 0 | Optional: with the rule on, a champion with no healthy ally within 5 also leaves two enemies. Rejected: -41 vs v58, pooled +69. |

Draft, banking, the v58 economy and every other switch are unchanged.

## Local safety net (`research/v59/V59_RESULTS.md`)

Full ladder pool, 70 maps x both sides x seeds 1-3 (420 games per opponent):

| | vs v58 | vs v57 | vs v55 | vs v54 | Pooled |
|---|---:|---:|---:|---:|---:|
| v58 | 0 | +156.0 | +141.6 | +205.7 | +125.8 |
| v59 | +9.2 | +157.8 | +175.6 | +256.2 | +149.7 |

On the 28-map development set v59 is +61.0 vs v58 (pooled +196.7 vs +160.4). Deaths fall 1.3-1.6 per game against
every opponent, with zero faults and unchanged fuel. Gems lost on death did not fall; bag survival remains open.
This is a non-regression check, not ladder evidence.

## Ladder check

After the user submits v59, run `python tools/replay/ladder_ab.py queue --yes` (24 paired sets, about 45 groups),
then `ladder_ab.py collect --since <submission time>`. Keep v59 only if it is at least as good as v58's 149/225 on
the same sets. Otherwise reactivate platform 57 (`cambc submissions activate 57`).

## Reproducibility

`bots/v59/src` seed 1 builds to wasm SHA-256 ae8d616afbb598df7bea74c8ebc54fc71ffac7ed0493fa05e44c58600e2cfadf,
the same bytes as the benchmarked candidate (`artifacts/evaluations/gauntlet-i2o2`).
