# Full replay review

Every recorded loss is decoded with its matching engine and a complete hash-pinned visualiser bundle. Current and historical engines remain separate.

Counts of contact, time and death position use round boundaries. Cooldowns use actual champion turns and that champion’s own visible enemies within six tiles. Contact-entry shares are weighted by number of entries; positioning ratios are means of per-game shares.

## current-engine: 492 losses

| Observation | DOOMSDAY | Opponent |
|---|---:|---:|
| outnumbered | 0.175 | 0.132 |
| alone | 0.421 | 0.352 |
| contactHpLost | 34.404 | 18.64 |
| deathSamples | 7505 | 2384 |
| isolatedDeathShare | 0.3326 | 0.271 |
| outnumberedDeathShare | 0.3879 | 0.3205 |
| respawnRepeatShare | 0.2349 | 0.1036 |
| nearHomeDeathShare | 0.5071 | 0.4123 |
| deadTimeFraction | 0.174 | 0.057 |
| contactEntries | 50856 | 52208 |
| noOffensiveReadyShare | 0.202 | 0.284 |
| campCooldownEntryShare | 0.0411 | 0.0732 |
| longStationaryIntervals | 85 | 49 |

## historical-engine: 10 losses

| Observation | DOOMSDAY | Opponent |
|---|---:|---:|
| outnumbered | 0.142 | 0.176 |
| alone | 0.384 | 0.382 |
| contactHpLost | 35.667 | 21.731 |
| deathSamples | 137 | 40 |
| isolatedDeathShare | 0.3066 | 0.3 |
| outnumberedDeathShare | 0.3796 | 0.375 |
| respawnRepeatShare | 0.2409 | 0.15 |
| nearHomeDeathShare | 0.7518 | 0.525 |
| deadTimeFraction | 0.192 | 0.055 |
| contactEntries | 1003 | 804 |
| noOffensiveReadyShare | 0.2403 | 0.3719 |
| campCooldownEntryShare | 0.0379 | 0.102 |
| longStationaryIntervals | 5 | 0 |

## v60: 105 losses

| Observation | DOOMSDAY | Opponent |
|---|---:|---:|
| outnumbered | 0.176 | 0.129 |
| alone | 0.404 | 0.343 |
| contactHpLost | 36.53 | 17.1 |
| deathSamples | 1621 | 484 |
| isolatedDeathShare | 0.3282 | 0.2624 |
| outnumberedDeathShare | 0.3843 | 0.2975 |
| respawnRepeatShare | 0.2394 | 0.0909 |
| nearHomeDeathShare | 0.5133 | 0.4566 |
| deadTimeFraction | 0.166 | 0.053 |
| contactEntries | 11442 | 12052 |
| noOffensiveReadyShare | 0.2241 | 0.2688 |
| campCooldownEntryShare | 0.0377 | 0.0714 |
| longStationaryIntervals | 6 | 18 |

## v61: 99 losses

| Observation | DOOMSDAY | Opponent |
|---|---:|---:|
| outnumbered | 0.166 | 0.129 |
| alone | 0.406 | 0.33 |
| contactHpLost | 35.123 | 17.92 |
| deathSamples | 1558 | 467 |
| isolatedDeathShare | 0.3235 | 0.2248 |
| outnumberedDeathShare | 0.3935 | 0.2912 |
| respawnRepeatShare | 0.2125 | 0.0942 |
| nearHomeDeathShare | 0.482 | 0.3448 |
| deadTimeFraction | 0.171 | 0.054 |
| contactEntries | 11312 | 11711 |
| noOffensiveReadyShare | 0.2188 | 0.2626 |
| campCooldownEntryShare | 0.0434 | 0.0701 |
| longStationaryIntervals | 13 | 20 |

## v62c: 105 losses

| Observation | DOOMSDAY | Opponent |
|---|---:|---:|
| outnumbered | 0.183 | 0.123 |
| alone | 0.422 | 0.327 |
| contactHpLost | 35.762 | 17.093 |
| deathSamples | 1414 | 387 |
| isolatedDeathShare | 0.3048 | 0.2481 |
| outnumberedDeathShare | 0.3819 | 0.3463 |
| respawnRepeatShare | 0.2214 | 0.0982 |
| nearHomeDeathShare | 0.4873 | 0.4444 |
| deadTimeFraction | 0.158 | 0.043 |
| contactEntries | 9409 | 9752 |
| noOffensiveReadyShare | 0.232 | 0.2813 |
| campCooldownEntryShare | 0.0432 | 0.0805 |
| longStationaryIntervals | 9 | 4 |

## Death sampling crosscheck

0 team/match counts differ from native summary deaths. The native summary remains the authority for exact death totals; replay context is limited to captured death transitions.

## Interpretation limits

- An enemy’s omniscient position at a death does not prove our bot could see that enemy before committing. It identifies a dangerous encounter, not a proven observation bug.
- An offensive ability on cooldown after a camp cast is a measured sequencing event. It is not proof that holding the ability would have won the fight.
- Ready abilities are not automatically legal or useful casts. Channeling, control effects, target rules, range and tactical objectives also matter.
- Hostile-cast classification uses own-perspective target positions and ability radius. It omits attack-reset, healing, shields and non-damaging dashes from hostile counts. Kills during the cast can remove a target from the post-action state and undercount it.
- Long stationary intervals can include deliberate camping, capture or resource denial. They are review flags, not automatic pathfinding defects.
- The 502-loss corpus is exhaustive for the fixed match window and top-25 definition; it does not prove all possible controller bugs have been discovered.
