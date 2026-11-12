# v59 local results (safety net, not ladder evidence)

Official CLI/SDK 4.0.0, engine 2.0.0, default fuel. Every run had complete coverage and zero native faults on both
teams. The final `bots/v59` builds byte-identically to the benchmarked i2o2 candidate (seed 1 wasm SHA-256
`ae8d616a...2cfadf`).

## Full ladder pool: 70 maps x both sides x seeds 1-3, 420 games per opponent (`tools/gauntlet.sh`)

| Candidate | vs v58 | vs v57 | vs v55 | vs v54 | Pooled | Deaths vs v57 (us/them) |
|---|---:|---:|---:|---:|---:|---:|
| v58 (baseline) | 0 | +156.0 | +141.6 | +205.7 | +125.8 | 14.48 / 16.14 |
| items2 (`V59_ITEMS 2`) | +12.5 | +140.2 | +164.5 | +209.9 | +131.8 | 14.66 / 15.72 |
| **v59 = items2 + `APEX_OUTNUMBERED 2`** | **+9.2** | **+157.8** | **+175.6** | **+256.2** | **+149.7** | **13.17 / 14.90** |
| v58 items + `APEX_OUTNUMBERED 2` | +22.8 | +122.0 | +119.5 | +235.5 | +125.0 | 13.39 / 14.51 |
| v59 + `V59_ALONE 1` | -41.0 | +50.2 | +81.3 | +186.1 | +69.2 | 12.59 / 13.45 |

v59 is at least as good as v58 against every opponent, and deaths fall by 1.3-1.6 per game against each
(13.55 vs 14.91 against v58). Fuel-outs stay at about 0.9 per game. Replays of the seed 1 games against v58: deaths
16.1 -> 13.2 per game at the same contact time, and outnumbered contact 15.3% -> 14.0%. Gems lost on death rose
(368 vs 312 per game; 40+-gem bag deaths unchanged), so bag survival remains open.

## 28-map development screens (seeds 1-3, 168 games per opponent; pooled over v58, v57, v55, v54)

| Variant | Pooled | vs v58 | Note |
|---|---:|---:|---|
| v58 | +160.4 | 0 | baseline |
| v57 build in v58 (`V58_ITEM_PLAN 0`) | +133.5 | -28.4 | |
| `V59_ITEMS 1` (winner-style opening) | +83.1 | -70.4 | |
| `V59_ITEMS 2` | +156.9 | -1.8 | |
| `V59_ITEMS 3` (three openers) | +155.2 | -37.3 | |
| outnumbered 1 + burst + v58 survive (v58 items) | -181.6 | -276.4 | deaths -35%, gold -20%: too passive |
| the same with the v57 build | -221.1 | -316.7 | |
| items 1 + outnumbered 1 | -90.3 | -228.3 | |
| items 1 + outnumbered 2 | +92.1 | -57.9 | |
| items 1 + burst | +80.5 | -38.7 | |
| **items 2 + outnumbered 2 (v59)** | **+196.7** | **+61.0** | best on both map sets |
| items 2 + outnumbered 2 + burst | -66.5 | -209.3 | too passive |

Head to head against v58, two style proxies show that copying the winners' surface choices does not transfer to our
code: meta draft (Vesper, Heart, Vendetta, Ryth, Marcella) + `V59_ITEMS 1` lost 34-134 (-356.7), and the same plus
all three survival switches lost 24-144 (-440.5).

## What this does and does not show

The gauntlet shows v59 is not a regression against our lineage and that it cuts deaths. It cannot show a ladder gain:
v58 beat v57 by +153 locally and was no better on the ladder. The ladder test is the paired A/B in
`V59_LADDER_AB_PLAN.json`: 24 sets, on which v58 scored 149/225.
