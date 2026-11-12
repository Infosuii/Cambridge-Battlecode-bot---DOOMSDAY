# v60: hold the spawn against pushes, funnel camp gold to Vesper (from v59 = platform 58)

## Why (ladder replays, research/v59)

- In ladder losses, 6.5 of our 13.8 deaths per game were within 15 tiles of our own spawn, and 23% of our deaths
  came within 60 rounds of respawning (winners 13%; our wins 6%). The worst losses are death spirals: 54/11, 63/21
  deaths on gold_rush, 18/1 on hooks. Champions leave the spawn one at a time into a waiting team.
- A champion standing on its spawn is at full health the next round (100 of 100 sampled rounds in ladder replays,
  48% -> 100%) and enemies cannot enter spawn tiles.
- Winners' Vesper captures 18.3 camps per game against our Vesper's 8.5 and earns 2,738 gold against 870; our camp
  rewards went to the poorest ally (`APEX_SHARE_GOLD`), spreading gold instead of concentrating it.

## What changed

| Switch | Value | Effect |
|---|---|---|
| `V60_HOME_GUARD` | 1 | On our spawn with visible enemies within 8 (not on their own spawn), stay and hit whatever is in reach unless we have more healthy champions within 6 than they have there and are at 90%+ health. A hold ends after 40 rounds, then normal play resumes for 20 (level 2, which also counts recent sightings, was worse locally). |
| `UB_GOLD_FUNNEL` | 1 | Existing switch: Vesper keeps the rewards she stands on, and allies hand theirs to her instead of the poorest teammate. |
| `V60_VESPER_FIRST` | 0 | New, off: draft Vesper first. Rejected locally (-90 pooled, -138 vs v59; our code plays Vesper poorly). |

## Local safety net (full 70-map pool, seeds 1-3, 420 games per opponent)

| | vs v59 | vs v58 | vs v57 | vs v55 | Pooled |
|---|---:|---:|---:|---:|---:|
| v59 | 0 | +9.2 | +157.8 | +175.6 | +85.6 |
| v60 | -11.3 | -0.6 | +107.7 | +155.0 | +62.7 |

Within the release rule (pooled no worse than the parent -30, no opponent below -100). Our lineage almost never
pushes an enemy spawn, so locally the guard rarely fires. Its test is the ladder.

## Ladder

v59's paired A/B: 79/120, against an expected 78.7 from v58's rates on the same sets. v60 runs the same 24 sets.
