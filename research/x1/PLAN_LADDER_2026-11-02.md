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
| 0 | **Conversion**: bank the bag (47% of losses end with collected-but-unbanked gems; 5060 J017, reproduces on the adgato gem-only maps vs x2) | I-60-04 | 5060 building |
| 0b | Few-camp-map feeding (28% of losses: 03one_gem 62 deaths a game, 01starvation, 03ultrastarvation, 00ribs) | X1_ANTIFEED family on those maps | PC |
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

## Results so far (2 Nov, 17:30 UTC)

| Attempt | Local result | Verdict |
|---|---|---|
| Plan 4 ends at R400 / R600 (X1_PLAN_END) | vs x1 68 / 73 of 140 (x1c1 63), vs v86h 74 / 69 (x1c1 75), ladder maps | noise; dropped |
| Bruiser builds (V58_ITEM_PLAN=0) | x1: 62 vs x1, 61 vs v86h; x1c1: 67 / 68 | not better with our fight logic; parked until the fight work |
| ANTIFEED 3/100, 3/250, 5/250 on 8 feeding maps vs v86h | wins 7 / 3 / 7 of 16 (x1 9), deaths 250 / 301 / 219 (x1 221) | feeding moves to the other side; dropped |
| X1_EARLYFLEE 7/1.0, 7/1.5, 5/1.0 (lone champion leaves before contact) | wins 10 / 8 / 8, deaths 254 / 249 / 279 | does not reduce deaths; dropped |

Death log (APEX_DEATHLOG, 03one-gem side A vs v86h, 70 deaths): 193 of the last-turn notes are mode=flee, nearly
all with no ally within 4 tiles, 30-60 steps from spawn. Side A feeds on this map whichever v81hl-family bot plays it
(x1, v86h, x1bru: 67-75 deaths as A, 5-13 as B). Next idea (rethink): **do not be alone far from home while enemies
roam**: a buddy rule (farm targets within reach of an ally once enemies have been seen in the last N rounds) and a
leash on spawn distance after a death, tested on the same 8 maps vs v86h and x1bru.
