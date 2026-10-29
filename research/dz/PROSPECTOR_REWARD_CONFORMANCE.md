# Prospector and Vesper reward checks — 2026-10-29

**Correction to the supplied planning formula:** Prospector boosts gold-cluster
gold as well as gem-cluster gems. The planning formula omitted the gold effect.
Vesper gold cannot be reproduced by flooring each individual reward independently.
Production remains unchanged; the advanced economy/gear models are disabled.

## Evidence

Five final campaigns complete ten native games, both sides of a separate
MapBuilder-validated correctness map. All strict checks pass with zero native
faults/fuel-outs:

- `dz-ct13-prospector-05` / `dz-ct13-power-control-05`: Vendetta, with a
  Prospector emblem or a plain Power stat emblem.
- `dz-ct13-vesper-prospector-05` / `dz-ct13-vesper-power-control-05`: same
  comparison with Vesper.
- `dz-ct13-vesper-power-reversed-05`: Vesper control with wolf/gold reward order
  reversed, testing the rounding mechanism rather than fitting one reward.

Each actor first clears a 240-gold group without an emblem, buys five shards at
spawn, then captures isolated 7/14-gem clusters, a 20-gold cluster and a wolf.
Companions park, the opponent idles, no abilities are used and the actor never
dies. The Power control checks the effect against a stat item with no reward
passive. CPP assertions and a separate integer arithmetic checker agree.

| Base reward | Vendetta control | Vendetta + Prospector | Vesper control | Vesper + Prospector |
|---|---:|---:|---:|---:|
| 240 gold, before buying | 240 | 240 | 319 | 319 |
| 7 gem cluster | 7 | 8 | 7 | 8 |
| 14 gem cluster | 14 | 17 | 14 | 17 |
| 20 gold cluster | 20 | 25 | 26 | 33 |
| Wolf: 4 gems, 40 gold | 4 / 40 | 4 / 40 | 4 / 54 | 4 / 53 |

The Vesper rows are an **ordered sequence**, not universal per-event constants.
Reversing the last two control awards changes wolf gold to **53** and the small
gold cluster to **27**, preserving the total. Both sides reproduce this.

The observed gold deltas match differences of cumulative percentage-scaled
awards: `floor(sum through this award) - floor(sum before it)`, including the
earlier 240-gold award and intervening integer purchases. A rational denominator
of 400 represents the tested 25% Prospector and 33% Vesper modifiers exactly.
This is a functional model of the tested sequence, **not** evidence about the
engine's internal storage representation. With unknown prior reward history,
an evaluator must allow the one-unit rounding uncertainty rather than invent
the hidden remainder.

Prospector gem awards floor individually: 7→8 then 14→17 gives 25 extra-stage
gems, not the 26 from flooring their combined unrounded value. Its gold effect
combines multiplicatively with Vesper here: 20 × 1.25 × 1.33 gives a 33-gold
increment in this sequence, versus 31 for an additive 58% rule.

## Scope and retained failures

Only pure gem/gold clusters and a single wolf are tested. Golem/monolith, native
elk receipts, mixed groups, splitting between capturers, Treasure combinations,
multiple Prospector emblems and rounding across death/respawn remain open.
The current results do not close all CT-13 or validate ObjModel/gear utility.

The first 01 fixture wrongly expected gold-cluster rewards to be unchanged and
correctly failed. 02/03 establish the corrected Vendetta rule and controls; 04
adds Vesper and exposes the per-event rounding assumption (its Vesper Power
control fails by one). The final 05 suite asserts cumulative rounding and reverses
the reward order. Earlier binaries/replays/results are preserved, not relabeled
as new independent samples. No competition-map tuning was performed.
