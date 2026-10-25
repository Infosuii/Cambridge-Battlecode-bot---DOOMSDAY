# bot v52

v51 plus the sole-gem-camp rule (`A2_SOLE_GEM 1`, `A2_SOLE_FROM 500` at the top of `src/common.h`; the code is at the top of `Bot::score_groups`).

## Fix: the map's only gem camp was never attacked (stampede, 0/28 on the ladder)

On stampede one group (20 monsters, 16,080 HP, 160 gems per clear) holds every gem on the map. Winning teams farm the gold-only camps until mid-game, then the whole team clears it repeatedly and banks after each clear. Our team-job calls never filled:
- `open_call_by_lower` ignored the team-size cap;
- joiners counted as initiators.

So the camp's health never dropped below full in 2,000 rounds. Now, on a map where one group holds at least 90% of the gems, a champion targets that group from round 500 onwards if it is at 60% health or more and carries fewer than `kTributeCarry` gems. Existing `fight_camps` staging gathers the team.

The check runs once per `score_groups` call and never inside the group loop: this bot runs at its fuel limit, so hot-path instructions cost games.

## Measured (bench v2: NOVA_SEED 1-3 × both sides, against v51)

| Test | Result |
|---|---|
| stampede only, start round 300, 600, 900 | 6-0, 6-0, 6-0 (+762, +738, +583); about 870 gems banked against v51's 100 |
| 28 development maps (168 games) | 83-85, +6.7; stampede 5/6; most other maps mirror v51 exactly |
| 12 holdout maps (72 games) | 36-36, +29.6 |

The starvation and boss_battle differences are fuel perturbation: neither map has a sole gem camp.
