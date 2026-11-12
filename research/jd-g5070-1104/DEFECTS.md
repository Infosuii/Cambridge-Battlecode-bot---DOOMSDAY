# DEFECTS: traced contact and movement defects of v92 (FEAT-004)

Dev partition only. The pool holdout (`base-v92-pool-01`) was not traced, per GATES.md.

## Sources

| run | what | games |
|---|---|---:|
| `base-v92-dev-01` | v92 vs v92 / x3inv / p65pack / public-khiri, 90 dev maps, both sides (FEAT-001) | 720 (209 losses) |
| `diag-deathlog-01` | the same cells with the `APEX_DEATHLOG=1` build `jd-deathlog-b42f60d0b53c` (bot-side mode of the last 4 noted turns before each death; 0 faults, 71.7% wins, same as v92's 71.0% +- path noise) | 720, 5,237 deaths |

Tools:
- `py tools/jd_g5070-1104/defects.py extract --run R [--arm A]` runs `defects.mjs` on each replay with the official replay engine 2.0.0 (pinned visualiser assets, offline and omniscient, never a bot input).
- `report --run R` aggregates our side and the opponent side of the same games.
- `deathlog --run R` parses the death-log build's stdout.
- `compare --base R:arm --cand R:arm` gives metric deltas on matched cells.

The definitions are in the `defects.py` docstring. Basic-attack reach per type is the largest pvp attack distance seen in the replays: 1 for melee, 3 for Vesper, Cassi, Stellar, Prism, Willow and Tavi.

## Ranking (per lost game, our side vs the opponent in the same 209 games)

| rank | defect | us | opp | gap | cost per lost game |
|---:|---|---:|---:|---:|---|
| 1 | deaths to champions | 11.9 | 8.4 | +3.5 | 118 vs 74 gems lost; 746 vs 539 rounds dead |
| 2 | no ally within 5 at death | 4.3 | 3.4 | +0.9 | part of 1 |
| 3 | no hit back in the last 5 alive rounds | 2.5 | 1.7 | +0.8 | 21 gems, 139 rounds dead |
| 4 | carrier deaths (>= 25 gems) | 1.5 | 0.9 | +0.7 | most of the gem gap |
| 5 | late flee (flee began with the enemy within 2) | 2.3 | 2.0 | +0.3 | part of 1 |
| 6 | A-B-A oscillation rounds out of contact | 51 | 37 | +14 | 14 of ~2,150 quiet champion-rounds |
| 7 | no-progress rounds (8-round windows, >= 4 moves, net <= 2 tiles) | 105 | 96 | +9 | 9 champion-rounds |
| - | retreat moves in reach without a basic attack | 33 | 34 | 0 | none relative to the opponent |
| - | idle runs (>= 10 rounds, away from spawn and camps) | 70 | 71 | 0 | v92 idles more in its wins (110) |

By opponent (losses), deaths: x3inv 15.5 vs 11.4, p65pack 11.1 vs 8.4, v92 9.8 vs 6.2. By map size: small 21.1 vs 14.6, medium 7.9 vs 5.7, large 2.9 vs 2.3. The contact defect is mainly a small-map defect. The 16 `conf` maps are the largest dev maps, so conformance there checks mechanics, not the size of the gain.

## Bot-side context at death (`diag-deathlog-01`)

| | losses (2,705 deaths) | wins (2,532) |
|---|---:|---:|
| mode `flee` on the last turn | 1,998 (74%) | 1,772 (70%) |
| `fight-champ` | 225 | 209 |
| `flee-dash` / `home-escape` / `home` | 80 / 77 / 51 | 51 / 134 / 47 |
| 4-turn sequence `flee>flee>flee>flee` | 1,047 | - |
| above 60% health 4 turns earlier | 713 (26%) | 561 (22%) |
| no ally within 4 | 1,284 (47%) | 1,364 (54%) |
| carrier (>= 25 gems) | 349, of which 257 in `flee` | 353 |
| within 10 steps of our spawn | 1,128 (42%) | 686 (27%) |

The visible enemies at death are 1 in 700 cases and 2 in 865. The nearest enemy is adjacent in 1,294 cases.

Hits back by type (replay, losses): melee hit back in 85% of their kill deaths (Marcella 493 of 546, Vendetta 431 of 521, Varg 315 of 343). Ranged champions often do not:
- Cassi: 80 hit, 170 no hit. Many of these are deaths with Issac, 4+ tiles from the enemy.
- Vesper: 160 hit, 69 no hit.

In the flee code (`handle_enemies`), a fleeing ranged champion within 4 tiles of an enemy steps every turn (`APEX_RANGED_FLEE`) and shoots only if no step is possible. A fleeing melee champion hits back with the basic attack only: no attack reset and no spell.

## Choice of the two mechanisms

- **A (contact), `JD_CONTACT`**: defects 1-5. Most deaths are a lost chase (`flee` x4). Bit 1 (flee strike): melee uses the attack reset and a non-exclusive damage or stun spell before the step, keeping a ready dash for the escape. Ranged stands and shoots when no visible enemy can reach it next turn. Bit 2 (early disengage): leave unsupported contact when hurt or carrying, before the fight starts. Earlier attempts in this tree target the same defect and were dropped: `X1_EARLYFLEE` did not reduce deaths on 8 maps vs v86h; `APEX_STAND` bits 2/4, `APEX_STAND2` and `X1_CORNERED` are off. Bit 1 is new. Bit 2 differs from them by counting arrival within 3 turns and requiring hurt or carrying.
- **B (movement), `JD_PROGRESS`**: defects 6-7, the largest movement gaps. Both are small, about 1% of out-of-contact time, so a small effect is expected. Idle and staging runs show no gap to the opponent, so the staging-idle rule (M = 10) was not built: the existing stage timeouts stay.
- **Next defect, not built:** purchases and wasted recalls (`home-escape` / `home` deaths: 128 in losses, 181 in wins).
