# Sparring calibration 01: camp invader and carrier/altar pressure (JOHNDOE #151/#152)

**Variants.** Each is one change applied to exact v109 (ZIP c013c216) by `tools/rl_env_1104/spar/spar_patch.py <src> <style>`.
- **Raiders:** claim slots 0 and 1, from round 100, while hp >= 50% and carrying < 40 gems. Every other body and every other turn plays v109.
- **Style 1, camp invader:** after all v92 and actor overrides, the raiders' farm target is forced to the best enemy-side camp group (d_enemy < 0.8 d_ours). Reward-state groups come first, then groups where an enemy was seen in the last 30 rounds.
- **Style 2, carrier/altar pressure:** before hunt(), a raider walks at and hits any visible off-spawn enemy holding 20+ gems within 12 tiles. Otherwise its farm target is forced to a group within 16 of the altar nearest the enemy spawn. With none open, it posts 3 tiles from that altar.

**Run.** e3-spar-calib-01: 15 development maps x A/B, release, cambc 5.0.0 / engine 3, 270 games, 0 faults. Opponents are v109, v92 and native Agent 2. The parent is unchanged v109.

## Strength

| opponent | v109 parent | invade | carrier |
|---|---|---|---|
| v109 | 15/30 | 11/30 | 11/30 |
| v92 | 15/30 | 12/30 | 14/30 |
| native | 14/30 | 6/30 | 8/30 |
| paired vs parent | - | -0.167 [-0.296, -0.026] | -0.122 [-0.219, -0.013] |

Both still take more than a third of their games off exact v109.

## Behavior, from official events (per-game means)

| cell | enemy deaths | enemy gems lost at death | enemy 30+ carriers lost (rate) | enemy camp gems | contested camp gems (ours) | our camp gems |
|---|---|---|---|---|---|---|
| v109 vs v109 | 16.6 | 78 | 15/281 (0.053) | 839 | 225 | 839 |
| invade vs v109 | 15.7 | 150 | 25/307 (0.081) | 963 | 149 | 631 |
| carrier vs v109 | 18.1 | 104 | 25/286 (0.087) | 914 | 211 | 747 |
| v109 vs v92 | 15.2 | 74 | 15/272 (0.055) | 787 | 184 | 812 |
| invade vs v92 | 17.4 | 104 | 19/267 (0.071) | 817 | 161 | 680 |
| carrier vs v92 | 18.5 | 93 | 14/275 (0.051) | 756 | 177 | 798 |
| v109 vs native | 13.6 | 96 | 16/298 (0.054) | 960 | 180 | 742 |
| invade vs native | 17.8 | 133 | 23/319 (0.072) | 981 | 159 | 682 |
| carrier vs native | 16.0 | 111 | 16/304 (0.053) | 959 | 145 | 712 |

The carrier columns come from JOHNDOE's carrier_events.py audit (1a6d171b), via `tools/rl_env_1104/strategy/spar_carrier_audit.py`. The other columns come from `tools/rl_env_1104/strategy/spar_behavior.py`.

**Trigger trace.** e3-spar-trace-01 replays the 60 games vs v109 with stdout logs on; the outcomes are identical, 11/30 each (`spar_trace.py`).
- **Invade:** 38 raid-target changes per game, so the raiders churn. They collected only 67 camp gems per game, 26 of them from the group they were sent to. Team camp gems were 631 vs the parent's 839.
- **Carrier:** 9.3 carrier chases started per game. Raiders collected 192 camp gems per game, 121 of them from the targeted altar-area group.

## Verdict

- **carrier/altar pressure: admit as a sparring style.** The intended change is visible against v109: the rate of enemy 30+ carriers lost rises from 0.053 to 0.087, and enemy gems lost at death rise from 78 to 104 per game. It keeps its own economy (raiders still farm near the altar) and wins 11/30 vs v109 and 14/30 vs v92. The pressure effect does not appear against v92 or native, whose carriers bank by other routes.
- **camp invader: not admitted in this form.** Its raiders reach enemy-side camps and start fights: enemy gems lost at death roughly double vs v109 (78 to 150). But they churn between targets and seldom finish captures, so enemy camp income rises instead of falling (839 to 963). That is not the intended denial behavior. The next step is a v2 with a sticky raid target (commit until the group is taken, lost or respawning) and reward-first selection.
