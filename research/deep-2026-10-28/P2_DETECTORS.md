# Examined-game detector screen

**Association, not causal bug attribution.** Engine 2.0.0; thresholds registered
before examined trajectories in commit 148d845 / DETECTOR_SPEC.json.

All 385 examined games pass snapshot/event checks: 360 DOOMSDAY games
(191 losses, 169 wins) and 25 top-v-top reference games.
The 165 hands-off games have **not** had detectors run or decision trajectories reviewed.
Five calibration games remain excluded. DETECTOR_VALIDATION.json records their checks.

## Coverage

| Primary cohort | Games | Wins | Losses | Maps | Opponents |
| --- | ---: | ---: | ---: | ---: | ---: |
| All | 360 | 169 | 191 | 70 | 30 |
| Learn | 60 | 7 | 53 | 38 | 5 |
| Climb | 202 | 119 | 83 | 70 | 6 |
| Other | 98 | 43 | 55 | 62 | 19 |

## Losses compared with wins

Each occurrence means at least one of our physical champions triggered the flag
in that game. Cells give count/n, rate and Wilson 95% interval. Difference is
loss-minus-win; clustered intervals resample whole maps or whole opponents
(2,000 bootstrap draws). These are exploratory, unadjusted multiple comparisons.
DETECTOR_DATA.json also contains every subtype and map/opponent/cohort table.
Clustered intervals describe the marginal study contrast; they do not adjust away
map/opponent confounding. Cluster overlap counts are retained in the JSON. This
purposive corpus is not a random or rank-proportional sample of ladder opponents.

| Flag | Losses (Wilson 95%) | Wins (Wilson 95%) | Difference | Map-cluster 95% | Opponent-cluster 95% |
| --- | --- | --- | ---: | --- | --- |
| D1 | 170/191 (89.0%; 83.8%–92.7%) | 148/169 (87.6%; 81.8%–91.7%) | +1.4 pp | [-8.6, +10.4] pp | [-8.2, +8.4] pp |
| D2 | 150/191 (78.5%; 72.2%–83.8%) | 112/169 (66.3%; 58.9%–73.0%) | +12.3 pp | [+0.0, +24.3] pp | [-0.4, +18.8] pp |
| D3 | 129/191 (67.5%; 60.6%–73.8%) | 74/169 (43.8%; 36.5%–51.3%) | +23.8 pp | [+10.8, +36.8] pp | [+13.7, +34.2] pp |
| D4 | 187/191 (97.9%; 94.7%–99.2%) | 163/169 (96.4%; 92.5%–98.4%) | +1.5 pp | [-0.5, +3.8] pp | [-3.9, +3.6] pp |
| D5 | 184/191 (96.3%; 92.6%–98.2%) | 165/169 (97.6%; 94.1%–99.1%) | -1.3 pp | [-5.6, +2.1] pp | [-4.0, +2.6] pp |
| D6 | 138/191 (72.3%; 65.5%–78.1%) | 130/169 (76.9%; 70.0%–82.6%) | -4.7 pp | [-14.0, +4.8] pp | [-19.8, +2.7] pp |
| D7 | 32/191 (16.8%; 12.1%–22.7%) | 19/169 (11.2%; 7.3%–16.9%) | +5.5 pp | [-2.3, +13.0] pp | [-3.9, +14.6] pp |
| D8 | 52/191 (27.2%; 21.4%–33.9%) | 79/169 (46.7%; 39.4%–54.3%) | -19.5 pp | [-30.0, -8.7] pp | [-35.5, -11.5] pp |
| D9 | 181/191 (94.8%; 90.6%–97.1%) | 168/169 (99.4%; 96.7%–99.9%) | -4.6 pp | [-9.4, -1.0] pp | [-7.0, -1.7] pp |
| D10 | 6/191 (3.1%; 1.4%–6.7%) | 42/169 (24.9%; 18.9%–31.9%) | -21.7 pp | [-30.0, -13.8] pp | [-30.4, -12.7] pp |
| D11 | 66/191 (34.6%; 28.2%–41.5%) | 29/169 (17.2%; 12.2%–23.6%) | +17.4 pp | [+8.5, +27.1] pp | [+5.3, +25.1] pp |

## Registered time-based flag durations

All own-game rows; overlapping subtype ranges are counted once per champion.
These are pooled measured durations, not independent-turn confidence intervals.

| Flag | Loss flagged/eligible champion-turns | Win flagged/eligible champion-turns |
| --- | ---: | ---: |
| D1 | 27600/736375 | 37529/671532 |
| D2 | 78775/833704 | 49818/783987 |
| D6 | 13533/833593 | 23751/783974 |
| D9 | 16480/833704 | 16234/783987 |
| D10 | 334/968946 | 2069/844832 |

## Rates per eligible event

These registered denominators address differing opportunities to trigger a flag.
D3 is repeated deaths / all native deaths; D8 is interruptions / observed bank
attempts excluding censored attempts; D11 is sampled visibility gaps / eligible
enemy-champion deaths. Intervals below still describe marginal associations.

| Flag | Loss events/exposure | Win events/exposure | Rate difference | Map-cluster 95% | Opponent-cluster 95% |
| --- | ---: | ---: | ---: | --- | --- |
| D3 | 722/2337 (30.9%) | 188/1028 (18.3%) | +12.6 pp | [+7.2, +18.3] pp | [+3.8, +16.9] pp |
| D8 | 92/3304 (2.8%) | 278/5471 (5.1%) | -2.3 pp | [-6.4, +0.5] pp | [-8.0, -0.7] pp |
| D11 | 151/2047 (7.4%) | 51/831 (6.1%) | +1.2 pp | [-0.9, +3.7] pp | [-4.2, +3.6] pp |

## Subtypes to examine next

Ranked descriptively by loss-minus-win occurrence in Climb, the rating-relevant cohort.
A positive interval under both clustering choices is still association and requires
matched cards, visible-state review and eventual hands-off confirmation.

| Subtype | Climb loss flags/n | Climb win flags/n | Difference | Map-cluster 95% | Opponent-cluster 95% |
| --- | ---: | ---: | ---: | --- | --- |
| D5:reward_to_enemy_after_native_clear | 52/83 | 52/119 | +19.0 pp | [+4.7, +33.8] pp | [-34.2, +28.0] pp |
| D3:repeat_death | 50/83 | 50/119 | +18.2 pp | [+1.3, +36.2] pp | [+12.8, +43.8] pp |
| D2:high_bag_death | 38/83 | 38/119 | +13.9 pp | [-3.0, +28.9] pp | [-1.9, +55.1] pp |
| D2:high_bag | 60/83 | 71/119 | +12.6 pp | [-5.4, +28.8] pp | [-13.3, +47.3] pp |
| D11:turn_sampled_unseen_killer | 18/83 | 16/119 | +8.2 pp | [-3.8, +22.2] pp | [+3.7, +25.0] pp |
| D7:fuel_exhausted | 12/83 | 13/119 | +3.5 pp | [-7.7, +14.1] pp | [-14.5, +15.0] pp |
| D9:ground_island_proxy | 2/83 | 0/119 | +2.4 pp | [+0.0, +8.2] pp | [+0.0, +3.9] pp |
| D4:tile_oscillation_proxy | 81/83 | 114/119 | +1.8 pp | [-2.9, +6.2] pp | [-8.3, +4.4] pp |

## Example loss rounds

Selection is descriptive: longest registered episodes, distinct game IDs. Full
contexts and additional examples are in DETECTOR_DATA.json; no hands-off game appears.

D5:reward_to_enemy_after_native_clear:

- [03e19de0](https://2026a.battlecode.co.uk/game/visualiser/03e19de0-c834-4c2f-b29e-a66c765fb5fd), 01shortcut vs SquidProxyLovers, Vesper Vale #0: rounds 1024–1024, first flag 1024.
- [042a7132](https://2026a.battlecode.co.uk/game/visualiser/042a7132-8d25-47ae-8459-a317bcb444ab), 00lost_world vs error404, Vendetta #6: rounds 470–470, first flag 470.
- [04839e77](https://2026a.battlecode.co.uk/game/visualiser/04839e77-146b-43f5-8d9d-6a094db86605), 00quarry vs SkibidiSloppers, Ren #6: rounds 230–230, first flag 230.

D3:repeat_death:

- [02f08491](https://2026a.battlecode.co.uk/game/visualiser/02f08491-d2fb-4596-9bef-782570bb00e7), 00dunes vs Mite, Marcella #6: rounds 250–250, first flag 250.
- [03e19de0](https://2026a.battlecode.co.uk/game/visualiser/03e19de0-c834-4c2f-b29e-a66c765fb5fd), 01shortcut vs SquidProxyLovers, Varg #1: rounds 472–472, first flag 472.
- [042a7132](https://2026a.battlecode.co.uk/game/visualiser/042a7132-8d25-47ae-8459-a317bcb444ab), 00lost_world vs error404, Vendetta #6: rounds 396–396, first flag 396.

D2:high_bag_death:

- [02f08491](https://2026a.battlecode.co.uk/game/visualiser/02f08491-d2fb-4596-9bef-782570bb00e7), 00dunes vs Mite, Willow #7: rounds 758–758, first flag 758.
- [03e19de0](https://2026a.battlecode.co.uk/game/visualiser/03e19de0-c834-4c2f-b29e-a66c765fb5fd), 01shortcut vs SquidProxyLovers, Vendetta #2: rounds 1157–1157, first flag 1157.
- [043884db](https://2026a.battlecode.co.uk/game/visualiser/043884db-842e-4765-94ee-9d54e67badb9), adgato_gemcombat4 vs Intercontinental Fish, Vendetta #6: rounds 470–470, first flag 470.

D2:high_bag:

- [1473a066](https://2026a.battlecode.co.uk/game/visualiser/1473a066-b6df-4410-a447-2b374428adc2), 02guardians vs error404, Vendetta #0: rounds 1201–1595, first flag 1250.
- [b537154f](https://2026a.battlecode.co.uk/game/visualiser/b537154f-e309-4df2-b464-36012d82c82c), 00elkring vs Intercontinental Fish, Heart of Ruin #0: rounds 267–657, first flag 316.
- [f9977eba](https://2026a.battlecode.co.uk/game/visualiser/f9977eba-6769-4e5b-9dc0-a3b380917323), 00reverse_spiral vs Sheeesh---, Marcella #5: rounds 712–1090, first flag 761.

D11:turn_sampled_unseen_killer:

- [03e19de0](https://2026a.battlecode.co.uk/game/visualiser/03e19de0-c834-4c2f-b29e-a66c765fb5fd), 01shortcut vs SquidProxyLovers, Vendetta #2: rounds 1157–1157, first flag 1157.
- [042a7132](https://2026a.battlecode.co.uk/game/visualiser/042a7132-8d25-47ae-8459-a317bcb444ab), 00lost_world vs error404, Willow #8: rounds 380–380, first flag 380.
- [0f0d7b62](https://2026a.battlecode.co.uk/game/visualiser/0f0d7b62-aa80-4f22-83cb-6ecebd7f1509), 00corners vs newer team, Cassi #2: rounds 945–945, first flag 945.

## Validation, limits and next action

The extractor uses the engine's actual channel/stun state, official camp-group
identities and capture timers. Every examined game reconciles native fuel, wards,
purchases, banks and faults against replay steps, and each sampled turn-start own state agrees
with its omniscient counterpart. All masks and decoders use the pinned official assets.
Semantic tests cover channel/attack/capture/stun exclusions, passive displacement,
death/incomplete-turn censoring, gaps, overlapping ranges and Greed equipment cost.

Coverage limits are part of the registered definitions: D4 measures tile oscillation,
not hidden mode changes; D5 progress is sampled at round boundaries and reward ownership
means native last-clear ownership; D8 cannot observe rejected SDK calls or prove dynamic
gate inaccessibility; D9's ground component omits ability/teleport escape; D11 samples
the five preceding own-turn observations, not continuous vision or the death round.
Positive faults were absent from calibration, so their positive-event semantics have
less validation than fuel events. No flag alone is an actionable bot-code change.

Next: Session 2 round timelines, income/conversion/denial/time decomposition, openings,
game-separated calibrated win probability, then diverse loss/win cards and ceilings.
Do not queue wave 2 until FAST_FINDINGS.md and hypothesis/prediction/decision rules exist.


## Movement-blocked implementation correction

This table uses corrected source5052f245, examined-v3. Step23 is a blocked
destination, not an arrival.15 semantic cases now pass. D1/D4/D6 measurements
are regenerated without changing the registered thresholds; D9 and all native
event detector sets are unchanged. See DECODER_CORRECTION.md and
CORRECTION_VALIDATION.json. Session2 results and next work are in STATE.md.
