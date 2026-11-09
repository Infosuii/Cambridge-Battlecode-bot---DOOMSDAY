# v115: v113 fuel fix merged with v114 (2026-11-09)

## Sources

Downloaded from the platform (submission archives):

| bot | platform note | archive sha256 |
|---|---|---|
| v112 | agentic-1108:auto_bank_arrive_learned | 9397a56e… |
| v113 | v112+fuel fix | 93332ea2… |
| v114 | claude-1108: v112 + early shop + 16-map profile table | 44afb7e9… |

`bots/v113`, `bots/v114` are those sources (LF line endings). `bots/v115` = v113 + the v114 diff
(`CL_NEWMAP_TABLE`, `CL_EARLYSHOP 90` until R300, `cl_newmap_table.h`). `bots/v115e` = v115 + two extra fixes below.

## What the v113 fuel fix changes (vs v112)

- Every fuel gate used `fuel_remaining() + nn_spent`, which credited back what the network had already spent this turn,
  so v92's gates over-estimated the fuel left and turns ran out. v113 uses the real `fuel_remaining()` everywhere.
- `CLFS 9 -> 15`.
- Neural fast path split into six budgeted stages over one frozen observation (`nnrec.cpp`, `fast_stage`), at most two rounds old.
- `ChannelRetry`: a cancelled recall / gem submission is not restarted on the same tile the same turn, or later while unsafe.
- Altar lock: query the enemy lock explicitly (`altar_lock_at` prefers ours when both lock), try every open altar first.
- Tribute: the route timeout no longer blocks scoring once already in range of an altar.

## Extra issues found in v113 (in `bots/v115e`)

1. **Enemy block refresh dropped.** v112 refreshed the enemy block in the same observation when enemies were in view
   (its comment: 63.8% vs 58.1% at 20M). v113's staged rewrite only refreshes it through the round-robin slow blocks,
   which are skipped while a staged observation is pending. v115e refreshes it in stage 4 when fuel allows.
2. **Possible network lockout.** v113's stage cost estimates never decay while held, and the first measurement
   (which can include allocation) is taken as-is. One expensive measurement can keep a stage above any affordable budget
   for the rest of the game. v115e decays a held stage's estimate (1/16) and caps it at `A2_NN_NNUE_CEIL`.

Neither showed a measurable gain locally, so v115 (not v115e) was the submission.

## Local results (cambc 5.0.0, engine 3.0.0, release builds, all 128 maps, both sides)

| candidate | vs v112 | vs v114 | vs v113 (head-to-head) |
|---|---|---|---|
| v113 | 134/256 (52.3%) | 139/256 (54.3%) | - |
| v115 | 130/256 (50.8%) | 135/256 (52.7%) | 134/256 (52.3%) |
| v115e | 132/256 (51.6%) | 130/256 (50.8%) | 128/256 (50.0%) |

Per-bot averages over the same games:

| bot | fuel-outs/game | gold earned by R300 | by R600 | deaths |
|---|---|---|---|---|
| v112 | 10.96 | 1146 | 2447 | 11.7 |
| v114 | 11.64 | 1157 | 2487 | 11.9 |
| v113 | 3.06 | 1185 | 2557 | 11.5 |
| v115 | 3.04 | 1157 | 2521 | 11.7 |
| v115e | 3.09 | 1172 | 2542 | 11.6 |

The fuel fix cuts fuel-outs by about 73%. The win-rate differences between v113, v115 and v115e are within noise (±0.06).

## Remaining fuel-outs (v113)

About 2.3 of the 3 per game fall in rounds 0-200: a burst at round 1 (about 24 per map, so every game on some maps:
00road_of_riches, 01boss_battle, 01yellow_brick_road, 03contours), and rounds 20-140 (field building and network warm-up)
concentrated on 04gem_caverns, 01islands, 03riverbed, 03the_front, 04lines, 04sanctum. Next step: a fuel-logged
debug build on those maps.

## Live ranked context (400 games, 8 Nov)

DOOMSDAY rank 47 (2178). Ranked play only paired us with ranks 31-150: 42/100 vs ranks 31-46, 173/300 vs 48-150.
Worst maps: 04comb 0-6, 01fracture 0-5, 04bridges 0-4, 00rows 0-4, 02famine 1-4.

## Status

v115 was submitted (version 115). Soon after, the platform showed it **cancelled** and the team selection **pinned to v106**,
changed by someone else. Not re-submitted or re-activated pending the team's decision.
