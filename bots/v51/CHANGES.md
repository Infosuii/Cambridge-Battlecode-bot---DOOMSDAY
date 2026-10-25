# bot v51

v50 plus one fix (26 changed lines in `src/bot.cpp` and `src/bot.h`). Built from this source, the bot is the same binary as the `v51a` build tested locally.

## Fix: champions froze at camps they cannot walk to

On big_world and islands, some camp groups sit on an island inside a moat of holes two tiles wide. Ranged allies kill those camps from the shore, but no walking route reaches the capture tiles or the melee attack positions. `walk_toward` returned "unreachable" every turn, and the champion stood still for the rest of the game. In a logged local game, five of six champions were frozen from roughly round 100–300 onwards.

The fix: when the walker finds no route over the static terrain, the champion drops that group for 300 rounds and farms elsewhere. This applies in the to-capture and approach modes.

## Measured locally (engine 1.0.3, default fuel, 28 training and selection maps × both sides)

| Matchup | Record | Mean gem margin |
|---|---|---|
| v50 vs heuristic-v1 | 26-30 | -2.6 |
| **v51 vs heuristic-v1** | **31-25** | **+70.6** |
| **v51 vs v50** | **31-25** | **+51.5** |

- big-world: v51 beat v50 1006-446 as side A and 1002-45 as side B (v50 collected about 50 gems all game).
- islands: 1054-808 and 1008-512.
- Every map without a moat produced the same game as v50, so nothing regressed.

Ladder context (doomsday's last 800 ranked games): big_world 0/26 and islands 3/25 were two of the worst maps.

## Not included

- A team-job fix for stampede's sole gem camp. It won stampede locally but lost 24-32 head-to-head with this version, so it was dropped.
- Finding: this bot runs at its fuel limit. A behaviour-identical change that added a few instructions to a hot loop lost 0-8, while a change in a cold path played identical games. Code added to hot paths must be cheap. Making existing hot paths cheaper is likely a real strength lever.
