# v69 (2026-10-28)

Base: `bots/v68` (v65 + `V68_SIEGE_FIX`). Two idle fixes found by the replay idle audit (`tools/v67/c_idle_batch.py`:
champions alive, off spawn, with no action for 40+ rounds). Patch: `tools/v67/c_v69_fixes.py`.

| Switch | What it does | Evidence |
|---|---|---|
| `V69_ISLAND 1` | When `walk_toward` finds no route and we stand where walking cannot reach our spawn (a hole island we dashed onto), dash to the reachable tile closest to spawn, or recall | 01big-world: Vesper stood on a one-tile island at (28,19) from round 70 to ~1,300 in every seed, two tiles from the shore, earning nothing |
| `V69_CAPTURE_STALL 15` | A capture that has not paid out after 15 rounds on the region: attack a visible enemy on or beside it when we have at least as many there, otherwise leave the group for 80 rounds (wait 2.5x longer when no enemy is visible) | 00vault: both teams stood on the 49-camp reward region for 1,400 rounds without fighting |

Full pool vs v65 (560 games, seeds 1/2/5/6): even with v68 overall (−7 gems per game, 95% CI −38 to +24); idle champion
rounds 146 → 110 per game; 01big-world idles gone. Remaining 00vault idles are mostly v65's deliberate lead lock
(`V54_HOLD`) while we lead.
