# Plan after the first real-ladder test (2 Nov 2026, 16:00 UTC)

Goal (Rishik): dominate the ladder; never lose to sub-2000 teams. Evidence: 180 x1c1 (v76) ladder games
(data/ladder/x1c1, pc/analysis/K010_pc.md on comms) and local head-to-heads.

## What the ladder says (and local tests missed)

1. **Fights decide the games.** Deaths to enemy champions per game, losses vs wins: Borufeczki 10.7 vs 0.5,
   Claudus 20.4 (no wins), 0xDEADBEEF 6.4 (no wins), others 11.1 vs 2.6. Our economy stall after R500 is mostly the
   cost of those deaths (gems dropped, respawn time), not only plan 4's territory limit.
2. **We lose small fights.** 45% of our deaths in losses come from a lone enemy or one plus a helper.
3. **Items: the top teams build for fights, we build for farming.** Per champion they buy Bruiser shards (strength
   10.8, health 7.6, focus 6.6, plus emblems); we buy Greed / Prospector / Jungle / Collectors (V58_ITEM_PLAN).
   Our local opponents all use our own economy builds, so local tests never punished this.
4. Plan 4 from R150 to the end keeps us on our half when it is farmed out (0xDEADBEEF: 27% for x1 -> 0/25).
5. Fuel is not a ladder problem (0.33 fuel-outs a game; opponents 2.6).
6. Results repeat per map (deterministic): a record is a few map outcomes repeated.

## Order of work (each behind a switch, gated, then sent for ladder games)

| # | Work | Switch | Status |
|---|---|---|---|
| 1 | Bruiser stat builds (the existing V54_ITEMS 3 + V58_KIT builds, reached by V58_ITEM_PLAN=0) | V58_ITEM_PLAN=0 | PC testing vs x1, v86h |
| 2 | Plan 4 stops at R400 / R600 | X1_PLAN_END | PC testing |
| 3 | **Fight-style stand-in opponent**: x1 with the Bruiser build and higher aggression, so local gates punish what the ladder punishes | bots/x1bru | next |
| 4 | Fight forecast against stat-stacked enemies: estimate enemy stats from their level and gold seen, not our own build; refuse 1v1s we lose | X1_FORECAST | after 3 |
| 5 | Anti-hunter: after k deaths to champions in w rounds with no kills, move in pairs and bank small and often | X1_ANTIHUNT | after 3 |
| 6 | Kill-securing focus fire (all champions pick the same killable target) | X1_FOCUS | after 4 |
| 7 | Team camp planner (TOPTW) | - | after the fight work; economy is second to fights on the ladder |

Gates now: x1, v86h, v81hl, v88 (+ the fight stand-in from step 3) on ladder + styled + maze. A line is sent for
ladder games only when it beats x1 head-to-head and on the pooled gate. The ladder is the final judge: records per
top team vs x1's v73 record.
