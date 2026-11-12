# Testing protocol against overfitting (3 Nov 2026)

Sources: the CAMBC Discord (organisers and top teams, 23 Oct - 1 Nov) and our own measurements.

## What we measured

- A do-nothing code change (X1_NOOP: one volatile store, so only fuel and layout move) flips 4-7 of 172 games
  against each opponent (338 vs 341 of 516). Fuel noise is small.
- Any behaviour change flips far more: each counter variant wins a different ~40 of x3mf's 90 lost cells; 5 variants
  "fix" 80 of 90. Games are chaotic: one changed decision sends the game down another path. A single deterministic
  win against one opponent is mostly that chaos ("you're basically choosing the seed that makes you win").
- x3ctr (table fitted on v92) went 171/172 vs v92 but lost ground to plain x3 vs v86h (100 vs 104) and x1bru
  (107 vs 115). x3mf (per-map knob fit on three opponents) held up on unseen ones (+14).

## Rules

1. **Optimise wins only.** Farming, gold and banking numbers explain what a change did; they are never the target.
2. **Several opponents per decision.** A per-map or per-cell choice switches away from the base only when it wins
   against several different opponents there (`x3_counter.py robust --min-opps`), never on one opponent's games.
3. **Varied sparring, not strong look-alikes.** Fitting opponents: x3mf, x3inv (invader), v86h, x1bru. Variety
   matters more than strength; our own lineage alone made the gate blind to invasions (ECONOMY_GAP.md).
4. **Judge on held-out opponents.** A change is adopted only if it also gains against opponents it never saw:
   v92, v81hl, v86h-s2, x1, plus the varied league (x3inv-t / -a / -i, dzs-rusher, dzs-turtle, dzs-farmer, proxy,
   public-decrest / -khiri / -wardens, mimic). The leave-one-opponent-out estimate printed by `robust` is the first
   warning; the held-out gate decides.
5. **Map features over map tables.** The maps are built rock-paper-scissors on purpose (organisers: read the map
   and choose the playstyle, in the draft). Next to every per-map table, fit "map features -> plan" and score it
   leave-one-map-out; a table that beats the feature model only in-sample is memorising.
6. **Tuners on averaged win rate.** SPSA / ES / GA (what top teams use) on wins averaged over many maps and the
   varied opponents, paired games (same maps, both sides), validated held out.
7. **The ladder decides.** Anything we would make live goes to the user as a zip for a ladder test first.

## Result: the four-opponent counter table does not transfer (3 Nov, 120 runs)

30 variants x 4 opponents (x3mf, x3inv, v86h, x1bru), all 86 pool maps, both sides; tools/x3_counter.py robust.
Left-out-opponent estimate (table chosen on the other three, scored on the fourth), per opponent in that order:

| setting | estimate vs variant 0 | cells switched |
|---|---|---|
| per cell, any win | -3 / -9 / -16 / -20 | 132 |
| per cell, 2-win margin | -4 / -4 / -10 / -8 | 71 |
| per cell, 3-win margin | -1 / -3 / -2 / -3 | 21 |
| per map (both sides), 1 | +9 / +1 / -16 / -15 | 158 |
| per map, 2 | +3 / +2 / -11 / -10 | 112 |
| per map, 3 | +2 / +3 / -3 / +2 | 44 |

In sample every setting looks large (+37 to +89); out of sample the best is about +1 per opponent, i.e. nothing,
and loose settings cost up to 20 because the average variant is worse than the tuned base. Per-map / per-side
variant tables are memorised chaos. On the ladder x3ctr's table cells did +8% +- 6% (z 1.4) vs the v92 era: not
significant, consistent with zero. The per-map knob ES (x3mf, +14 held out) is the method that transfers: it moves
smoothly on averaged wins instead of picking single games. Not adopted; no counter bot will ship.
