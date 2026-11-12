# Strategy archetypes of the teams that beat us (last 48 h, teams rated >= 2000)

898 distinct losses, 40 opponents, 86 maps. k-means on 26 strategy features chose k=9 (silhouette 0.090). For each archetype: the features that set it apart (z-score vs all winners), its values next to ours in the same games, where it beats us and who uses it.

## A1: 126 losses

| feature | z | them | us (same games) |
|---|---|---|---|
| clears_enemy_late | +1.60 | 0.32 | 0.10 |
| clears_enemy_mid | +1.23 | 0.26 | 0.12 |
| clears_enemy_early | +1.04 | 0.20 | 0.11 |
| pickups_enemy | +0.96 | 0.26 | 0.13 |
| deposits_total | +0.53 | 36.13 | 15.72 |
| shards_300 | -0.36 | 28.79 | 21.07 |
| deposits_300 | -0.31 | 3.99 | 3.37 |

Categories: C1 48, C5 34, C3 24, C4 10, C7 6, C2 3, C6 1
Opponents: 0xDEADBEEF 17, Beehive 11, an iq too high 10, bbas 7, shoutout MAPS 6, will think later 6, Shawarma 🐫 6, Nameless 6
Maps: 00oasis 13, 01gold_rush 11, 00anvil 9, 01hooks 9, 01fracture 9, 00fragment 6, 03ultrastarvation 6, 02arena 5, 00swirl 5, 01concentrated_wealth 4
Their champions: Marcella 111, Vesper Vale 100, Heart of Ruin 94, Vendetta 89, Ryth 40, Tavi 22, Cassi+Issac 21, Willow 16

## A2: 32 losses

| feature | z | them | us (same games) |
|---|---|---|---|
| gems_lost_300 | +3.20 | 83.44 | 70.03 |
| deposit_size_300 | +2.25 | 91.56 | 86.93 |
| kills_300 | +1.46 | 3.84 | 3.34 |
| deaths_300 | +1.35 | 4.28 | 4.81 |
| deposits_total | -1.01 | 14.22 | 7.91 |
| clears_300 | -0.69 | 9.56 | 8.78 |
| deposit_size | +0.60 | 108.48 | 95.10 |

Categories: C2 13, C3 7, C1 5, C4 3, C6 2, C7 2
Opponents: 0xDEADBEEF 3, Shawarma 🐫 3, we were fed fish 2, QS2isLaw 2, 剑桥夜爬者 2, Nameless 2, PtitLK 2, Beehive 2
Maps: 00vault 8, 03showdown 4, 01shortcut 3, 00the_line 3, 03the_front 2, adgato_gemcombat5 2, 02stalactites 2, 00crater 1, 02treasure_box 1, adgato_gemcombat2 1
Their champions: Marcella 31, Heart of Ruin 29, Vesper Vale 26, Vendetta 23, Ryth 10, Cassi+Issac 7, Prism 4, Willow 4

## A3: 64 losses

| feature | z | them | us (same games) |
|---|---|---|---|
| opens_bruiser | +2.94 | 1.00 | 0.00 |
| bruiser_300 | +1.03 | 14.95 | 0.00 |
| deposits_300 | +0.44 | 7.17 | 4.86 |
| locks | +0.41 | 6.45 | 5.12 |
| clears_enemy_late | -0.33 | 0.04 | 0.02 |
| first_kill | -0.32 | 252.77 | 484.50 |
| first_deposit | -0.32 | 90.91 | 243.41 |

Categories: C3 22, C4 15, C1 11, C5 10, C7 2, C2 2, C6 2
Opponents: shoutout MAPS 15, BBL 9, FürFortnite 8, SilverSamurai 5, Nameless 5, 剑桥夜爬者 4, we were fed fish 4, the ruliad 4
Maps: 01the_farm 4, 02fields 3, adgato_gemcombat3 3, 03the_front 3, 00galaxy 2, 00road_of_riches 2, 02the_pond 2, 00dunes 2, 03fan 2, 02treasure_box 2
Their champions: Vesper Vale 59, Marcella 45, Heart of Ruin 38, Vendetta 32, Cassi+Issac 28, Tavi 27, Ryth 20, Willow 17

## A4: 54 losses

| feature | z | them | us (same games) |
|---|---|---|---|
| first_deposit | +3.21 | 947.04 | 1325.57 |
| deposit_size | +2.28 | 256.00 | 47.95 |
| deposits_total | -1.59 | 5.93 | 3.83 |
| deposits_300 | -1.25 | 0.00 | 0.72 |
| deposit_size_300 | -1.06 | 0.00 | 10.20 |
| clears_300 | +0.50 | 19.87 | 22.52 |
| shards_300 | +0.40 | 42.67 | 31.00 |

Categories: C3 33, C5 17, C1 2, C2 2
Opponents: we were fed fish 6, QS2isLaw 5, SilverSamurai 5, Shawarma 🐫 5, 0xDEADBEEF 4, Tokenmaxxing 3, 𓎼𓃭𓅱𓂋𓇌 𓏏𓅱 𓂋𓄿 2, smurphy 2
Maps: 00stampede 12, 01boss_battle 11, 03homonoliths 8, 00contest 6, 02guardians 4, 01shortcut 3, 01elk_arena 2, 02cuts 1, 01big_world 1, 02stalactites 1
Their champions: Vendetta 46, Heart of Ruin 46, Marcella 46, Vesper Vale 44, Ryth 19, Cassi+Issac 14, Willow 11, Prism 7

## A5: 13 losses

| feature | z | them | us (same games) |
|---|---|---|---|
| power_300 | +5.94 | 10.46 | 0.00 |
| pickups_enemy | +1.35 | 0.31 | 0.01 |
| shards_300 | +1.09 | 55.23 | 27.54 |
| kills_300 | +1.00 | 3.08 | 1.46 |
| clears_enemy_mid | +1.00 | 0.23 | 0.02 |
| clears_enemy_early | +0.93 | 0.18 | 0.08 |
| bruiser_300 | +0.88 | 13.62 | 0.46 |

Categories: C3 4, C1 4, C4 3, C5 2
Opponents: 剑桥夜爬者 6, Claudus Maximus 2, The Party of Heroes 1, Univardisty of Shingtonwash 1, estrogen :3 1, PtitLK 1, BBL 1
Maps: 00great_wall 2, 03one_gem 2, 00dunes 1, 03shrines 1, 00eight 1, 01yellow_brick_road 1, 01boss_battle 1, 00elkring 1, 02fields 1, 02treasure_box 1
Their champions: Vesper Vale 8, Marcella 8, Willow 8, Heart of Ruin 8, Vendetta 7, Ryth 6, Cassi+Issac 5, Tavi 4

## A6: 244 losses

| feature | z | them | us (same games) |
|---|---|---|---|
| opens_treasure | -0.63 | 0.01 | 0.02 |
| treasure_300 | -0.59 | 1.47 | 0.38 |
| kills_enemy_side | +0.50 | 0.63 | 0.29 |
| deposits_300 | +0.37 | 6.87 | 6.22 |
| opens_jungle | +0.36 | 0.55 | 0.80 |
| clears_contested_early | -0.35 | 0.13 | 0.16 |
| opens_bruiser | -0.34 | 0.00 | 0.00 |

Categories: C3 80, C5 53, C1 49, C4 39, C2 10, C7 8, C6 5
Opponents: 0xDEADBEEF 48, QS2isLaw 28, will think later 19, Shawarma 🐫 13, the ruliad 12, smurphy 12, an iq too high 11, HBH 10
Maps: 03ambush_field 11, adgato_gemcombat4 9, 03shrines 9, 00monolith 8, 03the_front 8, 00elkring 7, 02uncharted_lands 7, 02fields 6, 02geodes 6, 00quadrants 6
Their champions: Marcella 215, Heart of Ruin 212, Vesper Vale 208, Vendetta 203, Ryth 73, Tavi 66, Cassi+Issac 56, Willow 35

## A7: 163 losses

| feature | z | them | us (same games) |
|---|---|---|---|
| treasure_300 | +1.30 | 13.16 | 0.70 |
| opens_treasure | +1.24 | 0.87 | 0.03 |
| opens_bruiser | -0.34 | 0.00 | 0.00 |
| first_kill | -0.33 | 249.55 | 557.48 |
| locks | +0.31 | 5.96 | 6.40 |
| deposits_total | +0.31 | 32.99 | 19.69 |
| deposits_300 | +0.29 | 6.53 | 4.97 |

Categories: C3 53, C1 39, C5 38, C4 23, C2 4, C6 4, C7 2
Opponents: an iq too high 19, Nameless 19, Borufeczki 16, ha²t 14, bbas 11, we were fed fish 11, EggsAfter11AM 10, Beehive 10
Maps: 03honeycomb 9, 00elkring 8, 00quarry 7, 00corners 6, 00monolith 6, 00lanes 5, 00interlock 5, 02the_pond 5, 03fan 5, 02uncharted_lands 4
Their champions: Marcella 149, Heart of Ruin 147, Vesper Vale 126, Vendetta 123, Ryth 98, Willow 27, Cassi+Issac 17, Tavi 12

## A8: 80 losses

| feature | z | them | us (same games) |
|---|---|---|---|
| first_kill | +2.60 | 1738.22 | 1337.97 |
| kills_enemy_side | -1.27 | 0.00 | 0.14 |
| kills_300 | -0.82 | 0.00 | 0.17 |
| pickups_enemy | -0.75 | 0.04 | 0.03 |
| deaths_300 | -0.64 | 0.35 | 0.40 |
| clears_contested_early | -0.58 | 0.07 | 0.06 |
| clears_enemy_mid | -0.56 | 0.06 | 0.03 |

Categories: C5 41, C3 26, C6 10, C1 2, C4 1
Opponents: QS2isLaw 10, smurphy 9, Shawarma 🐫 7, bbas 6, Tokenmaxxing 5, an iq too high 5, 0xDEADBEEF 4, will think later 4
Maps: 01islands 10, 00rows 10, 00great_wall 7, 02geodes 7, 03reef 7, 01big_world 5, 02tangle 4, 00expanse 3, 01fracture 3, 02cuts 3
Their champions: Marcella 69, Vesper Vale 68, Vendetta 66, Heart of Ruin 65, Ryth 42, Cassi+Issac 22, Willow 14, Varg 14

## A9: 122 losses

| feature | z | them | us (same games) |
|---|---|---|---|
| clears_contested_early | +1.41 | 0.58 | 0.51 |
| clears_enemy_mid | -0.84 | 0.02 | 0.02 |
| kills_enemy_side | -0.84 | 0.16 | 0.20 |
| pickups_enemy | -0.75 | 0.04 | 0.04 |
| shards_300 | -0.67 | 22.98 | 18.60 |
| clears_enemy_early | -0.62 | 0.01 | 0.03 |
| bruiser_300 | -0.50 | 1.26 | 0.02 |

Categories: C3 42, C4 30, C5 22, C1 16, C7 5, C2 5, C6 2
Opponents: 0xDEADBEEF 13, QS2isLaw 12, we were fed fish 11, Beehive 9, Borufeczki 7, bbas 6, Shawarma 🐫 6, an iq too high 6
Maps: 00rushbait_v2 12, 00ribs 10, 01corridors 10, 00reverse_spiral 9, 01starvation 7, 00road_of_riches 5, 00lost_world 5, adgato_gemcombat4 5, 01shortcut 5, adgato_gemcombat3 4
Their champions: Marcella 109, Heart of Ruin 104, Vesper Vale 96, Vendetta 96, Ryth 56, Willow 34, Cassi+Issac 30, Tavi 16

## Winners vs us by map category (means over losses)

### C1: 176 losses

| feature | them | us |
|---|---|---|
| clears_300 | 15.60 | 14.39 |
| clears_enemy_early | 0.08 | 0.06 |
| clears_enemy_mid | 0.16 | 0.06 |
| clears_enemy_late | 0.15 | 0.03 |
| clears_contested_early | 0.23 | 0.23 |
| pickups_enemy | 0.21 | 0.09 |
| kills_300 | 1.45 | 1.80 |
| kills_enemy_side | 0.62 | 0.36 |
| first_kill | 268.19 | 312.85 |
| deaths_300 | 2.45 | 2.52 |
| deposits_300 | 5.74 | 4.68 |
| deposit_size_300 | 25.88 | 17.06 |
| first_deposit | 106.57 | 177.99 |
| deposits_total | 36.32 | 17.79 |
| deposit_size | 34.88 | 27.03 |
| bruiser_300 | 7.60 | 0.04 |
| treasure_300 | 5.53 | 0.49 |
| power_300 | 0.47 | 0.00 |
| shards_300 | 40.56 | 31.00 |
| opens_treasure | 0.32 | 0.03 |
| opens_jungle | 0.33 | 0.95 |
| opens_bruiser | 0.08 | 0.00 |
| teleports | 2.74 | 5.18 |
| locks | 5.40 | 6.47 |
| wards | 196.28 | 86.42 |
| gems_lost_300 | 8.09 | 7.81 |

### C2: 39 losses

| feature | them | us |
|---|---|---|
| clears_300 | 8.46 | 6.21 |
| clears_enemy_early | 0.10 | 0.04 |
| clears_enemy_mid | 0.14 | 0.06 |
| clears_enemy_late | 0.03 | 0.00 |
| clears_contested_early | 0.21 | 0.35 |
| pickups_enemy | 0.17 | 0.10 |
| kills_300 | 3.18 | 2.54 |
| kills_enemy_side | 0.58 | 0.40 |
| first_kill | 157.69 | 162.92 |
| deaths_300 | 2.74 | 3.28 |
| deposits_300 | 3.46 | 3.23 |
| deposit_size_300 | 79.64 | 92.18 |
| first_deposit | 161.67 | 266.82 |
| deposits_total | 14.82 | 8.64 |
| deposit_size | 111.06 | 101.11 |
| bruiser_300 | 3.05 | 0.00 |
| treasure_300 | 3.77 | 0.56 |
| power_300 | 0.49 | 0.00 |
| shards_300 | 22.23 | 13.51 |
| opens_treasure | 0.36 | 0.08 |
| opens_jungle | 0.15 | 0.92 |
| opens_bruiser | 0.13 | 0.00 |
| teleports | 0.79 | 1.54 |
| locks | 3.62 | 2.13 |
| wards | 75.56 | 38.69 |
| gems_lost_300 | 31.15 | 48.41 |

### C3: 291 losses

| feature | them | us |
|---|---|---|
| clears_300 | 15.36 | 15.76 |
| clears_enemy_early | 0.07 | 0.06 |
| clears_enemy_mid | 0.10 | 0.05 |
| clears_enemy_late | 0.06 | 0.03 |
| clears_contested_early | 0.21 | 0.24 |
| pickups_enemy | 0.11 | 0.06 |
| kills_300 | 1.12 | 0.95 |
| kills_enemy_side | 0.45 | 0.26 |
| first_kill | 430.50 | 659.76 |
| deaths_300 | 1.62 | 2.31 |
| deposits_300 | 4.97 | 4.75 |
| deposit_size_300 | 25.95 | 17.72 |
| first_deposit | 226.96 | 330.68 |
| deposits_total | 25.04 | 17.59 |
| deposit_size | 69.56 | 36.85 |
| bruiser_300 | 7.05 | 0.05 |
| treasure_300 | 5.51 | 0.37 |
| power_300 | 0.38 | 0.01 |
| shards_300 | 39.78 | 28.69 |
| opens_treasure | 0.30 | 0.02 |
| opens_jungle | 0.38 | 0.78 |
| opens_bruiser | 0.11 | 0.00 |
| teleports | 3.49 | 7.26 |
| locks | 4.73 | 5.96 |
| wards | 154.94 | 78.43 |
| gems_lost_300 | 8.81 | 9.05 |

### C4: 124 losses

| feature | them | us |
|---|---|---|
| clears_300 | 21.22 | 19.90 |
| clears_enemy_early | 0.09 | 0.08 |
| clears_enemy_mid | 0.12 | 0.09 |
| clears_enemy_late | 0.05 | 0.05 |
| clears_contested_early | 0.32 | 0.30 |
| pickups_enemy | 0.12 | 0.09 |
| kills_300 | 2.03 | 1.20 |
| kills_enemy_side | 0.29 | 0.21 |
| first_kill | 207.56 | 456.50 |
| deaths_300 | 1.47 | 2.83 |
| deposits_300 | 7.52 | 5.62 |
| deposit_size_300 | 30.49 | 23.64 |
| first_deposit | 113.72 | 199.73 |
| deposits_total | 32.17 | 16.54 |
| deposit_size | 38.90 | 30.39 |
| bruiser_300 | 5.09 | 0.07 |
| treasure_300 | 4.15 | 0.65 |
| power_300 | 0.60 | 0.00 |
| shards_300 | 29.95 | 20.15 |
| opens_treasure | 0.29 | 0.04 |
| opens_jungle | 0.49 | 0.87 |
| opens_bruiser | 0.12 | 0.00 |
| teleports | 4.97 | 6.73 |
| locks | 3.89 | 3.79 |
| wards | 157.90 | 51.44 |
| gems_lost_300 | 11.31 | 21.85 |

### C5: 217 losses

| feature | them | us |
|---|---|---|
| clears_300 | 14.76 | 15.27 |
| clears_enemy_early | 0.08 | 0.07 |
| clears_enemy_mid | 0.11 | 0.06 |
| clears_enemy_late | 0.10 | 0.04 |
| clears_contested_early | 0.15 | 0.12 |
| pickups_enemy | 0.11 | 0.05 |
| kills_300 | 0.97 | 0.70 |
| kills_enemy_side | 0.40 | 0.21 |
| first_kill | 641.95 | 852.07 |
| deaths_300 | 0.94 | 1.32 |
| deposits_300 | 4.51 | 3.51 |
| deposit_size_300 | 25.40 | 16.43 |
| first_deposit | 185.29 | 243.45 |
| deposits_total | 27.68 | 18.59 |
| deposit_size | 56.15 | 37.60 |
| bruiser_300 | 3.42 | 0.01 |
| treasure_300 | 5.38 | 0.77 |
| power_300 | 0.32 | 0.00 |
| shards_300 | 32.88 | 24.31 |
| opens_treasure | 0.29 | 0.04 |
| opens_jungle | 0.37 | 0.79 |
| opens_bruiser | 0.10 | 0.00 |
| teleports | 4.47 | 10.51 |
| locks | 3.80 | 7.47 |
| wards | 196.62 | 88.83 |
| gems_lost_300 | 2.57 | 4.30 |

### C6: 26 losses

| feature | them | us |
|---|---|---|
| clears_300 | 12.04 | 19.73 |
| clears_enemy_early | 0.03 | 0.04 |
| clears_enemy_mid | 0.07 | 0.03 |
| clears_enemy_late | 0.05 | 0.00 |
| clears_contested_early | 0.20 | 0.11 |
| pickups_enemy | 0.09 | 0.05 |
| kills_300 | 0.54 | 0.77 |
| kills_enemy_side | 0.36 | 0.17 |
| first_kill | 900.27 | 812.65 |
| deaths_300 | 1.31 | 1.08 |
| deposits_300 | 4.92 | 4.96 |
| deposit_size_300 | 39.37 | 21.67 |
| first_deposit | 99.65 | 140.69 |
| deposits_total | 26.46 | 26.35 |
| deposit_size | 41.79 | 36.32 |
| bruiser_300 | 9.00 | 0.19 |
| treasure_300 | 6.23 | 1.12 |
| power_300 | 0.15 | 0.00 |
| shards_300 | 40.08 | 36.77 |
| opens_treasure | 0.27 | 0.08 |
| opens_jungle | 0.38 | 0.62 |
| opens_bruiser | 0.08 | 0.00 |
| teleports | 5.12 | 6.15 |
| locks | 5.85 | 6.15 |
| wards | 108.15 | 83.65 |
| gems_lost_300 | 5.73 | 4.19 |

### C7: 25 losses

| feature | them | us |
|---|---|---|
| clears_300 | 10.00 | 11.72 |
| clears_enemy_early | 0.08 | 0.01 |
| clears_enemy_mid | 0.13 | 0.04 |
| clears_enemy_late | 0.09 | 0.03 |
| clears_contested_early | 0.35 | 0.25 |
| pickups_enemy | 0.19 | 0.05 |
| kills_300 | 2.52 | 0.68 |
| kills_enemy_side | 0.51 | 0.26 |
| first_kill | 260.56 | 974.48 |
| deaths_300 | 0.72 | 2.96 |
| deposits_300 | 5.64 | 2.48 |
| deposit_size_300 | 30.35 | 29.13 |
| first_deposit | 95.88 | 377.20 |
| deposits_total | 30.12 | 10.20 |
| deposit_size | 41.78 | 39.59 |
| bruiser_300 | 0.32 | 0.00 |
| treasure_300 | 1.92 | 0.00 |
| power_300 | 0.40 | 0.00 |
| shards_300 | 9.64 | 4.28 |
| opens_treasure | 0.28 | 0.00 |
| opens_jungle | 0.28 | 0.68 |
| opens_bruiser | 0.12 | 0.00 |
| teleports | 0.84 | 2.00 |
| locks | 3.48 | 2.12 |
| wards | 84.04 | 31.24 |
| gems_lost_300 | 13.60 | 64.52 |
