# v68 (2026-10-28)

Base: `bots/v65` (platform 65, the best version measured against the top 12). One change.

| Switch | What it does | Evidence |
|---|---|---|
| `V68_SIEGE_FIX 1` | The siege line-of-sight scan in `fight_camps` (`NOVA_SIEGE_LOS`) resumes next turn where it stopped (stopping at 15k fuel left) and keeps its result until the group's live camps change, instead of rescanning every turn | On `00vault` the siege target is a 49-camp group: the full scan overran the 100k turn budget, so the champion suspended every turn and stood frozen (v65 mirror: Marcella 662 fuel-outs from round 532 to 2000; up to 1,025 per game). Same as the frozen champions in the platform audit's Vault loss. |

Full-pool check against v65 (`research/v68/LOCAL_TESTING.md`; 560 distinct games, seeds 1/2/5/6, our bot as shipped):
fuel-outs per game 2.9 → 0.6, 00vault +156 gems per game, overall −12 gems per game (95% CI −32 to +5: no
difference elsewhere, as expected of a bug fix). Patch: `tools/v67/c_siege_fix.py`.

The carry-economy candidates first built under this name are now `bots/v68c` and `bots/v68cb`; on the full-pool test
they lose 176 and 223 gems per game to v66a, with 600-870 less gold per game, and are not release candidates.
