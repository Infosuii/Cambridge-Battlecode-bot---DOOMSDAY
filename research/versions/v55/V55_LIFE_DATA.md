# v55 ladder replay analysis: where, why, and what winners do

Platform v55; interval 2026-10-25 18:53:28-19:54 UTC. 210 finished games in listing; 210 with decoded replays (98 losses, 112 wins). Offline omniscient replay analysis with the pinned engine; descriptive, confounded by map, opponent and draft. Medians of per-game values unless stated; "opp" is the winner in our losses and the loser in our wins.

## Listing results and replay coverage

- ranked: 22/30 wins in listing; decoded 30 games (22 wins).
- unranked: 90/180 wins in listing; decoded 180 games (90 wins).
- loss families (a loss can have several): mid-game slide 35, early contact spiral 29, conversion (gear parity or lead at R500) 19, opening economy 17
- close losses (margin ≥ −150 gems): 12/98; median margin of losses -610

| Map | W/L | mean margin | median R250 gear ratio | our deaths / opp deaths (median) |
|---|---:|---:|---:|---:|
| 00swirl | 4/8 | -327 | 0.36 | 20.5 / 12.0 |
| 00eight | 7/5 | +49 | 0.56 | 6.5 / 15.5 |
| 01islands | 1/5 | -204 | 0.77 | 2.0 / 3.5 |
| 01hooks | 11/4 | +547 | 1.0 | 5 / 27 |
| 01big_world | 1/4 | -173 | 0.5 | 2 / 1 |
| 00rushbait_v2 | 2/4 | -159 | 0.55 | 6.5 / 5.5 |
| 00collision | 3/4 | +54 | 1.06 | 9 / 6 |
| 00fragment | 4/4 | +42 | 0.92 | 4.5 / 17.5 |
| 01concentrated_wealth | 5/4 | +96 | 0.41 | 4 / 10 |
| 00lost_world | 4/3 | -7 | 2.57 | 8 / 13 |
| 00elkring | 2/3 | -66 | 0.82 | 5 / 4 |
| 00ambush | 2/3 | -89 | 0.92 | 3 / 4 |
| 01broken_curve | 2/3 | +52 | 0.87 | 4 / 2 |
| 01fracture | 2/3 | -237 | 0.85 | 2 / 6 |
| 01shortcut | 0/3 | -408 | 0.7 | 5 / 5 |
| 00gem_fields | 4/2 | +316 | 1.65 | 2.5 / 8.5 |
| 00lanes | 5/2 | -2 | 0.97 | 1 / 3 |
| 00corners | 6/2 | +91 | 0.9 | 2.0 / 3.5 |
| 00interlock | 4/2 | +158 | 1.09 | 6.0 / 14.0 |
| 01starfish | 5/2 | +299 | 0.81 | 27 / 21 |
| 00rows | 0/2 | -252 | 1.46 | 1.0 / 1.5 |
| 01starvation | 1/2 | -249 | 0.81 | 22 / 6 |
| 00quadrants | 2/2 | +89 | 0.66 | 1.5 / 3.0 |
| 01gold_rush | 2/2 | +34 | 0.97 | 25.0 / 9.0 |
| 00split | 0/2 | -248 | 1.43 | 2.5 / 6.5 |
| 01boss_battle | 1/2 | -607 | 0.5 | 21 / 4 |
| 01corridors | 5/2 | +403 | 1.07 | 2 / 7 |
| 00monolith | 3/2 | -115 | 0.9 | 4 / 2 |
| 00packs | 1/2 | -35 | 0.81 | 13 / 6 |
| 00road_of_riches | 0/2 | -1000 | 0.51 | 3.5 / 0.5 |
| 00contest | 2/2 | -400 | 4.02 | 16.5 / 21.0 |
| 00gemfight | 0/2 | -1022 | 0.19 | 20.5 / 1.5 |
| 01the_farm | 5/1 | +234 | 0.74 | 1.0 / 1.5 |
| 00reverse_spiral | 1/1 | +13 | 2.12 | 11.5 / 23.0 |
| 00pilgrimage | 3/1 | +588 | 1.57 | 3.5 / 12.5 |
| 00stampede | 2/1 | +589 | 0.48 | 7 / 5 |
| 01yellow_brick_road | 6/0 | +558 | 1.54 | 6.0 / 13.5 |
| 01elk_arena | 3/0 | +928 | 1.6 | 10 / 47 |
| 00great_wall | 1/0 | +607 | 1.38 | 1 / 3 |

| Opponent | rank now | W/L vs them |
|---|---:|---:|
| Claudus Maximus | 4 | 1/49 |
| Turbo Gold Clusters | 176 | 12/8 |
| Electric Tributers | 134 | 13/7 |
| Rogue Elk | 221 | 13/7 |
| Velvet Tributers | 67 | 4/6 |
| The row boats are hier | 276 | 26/4 |
| Palestine 🇵🇸 | 112 | 6/4 |
| Crimson Pathfinders | 149 | 2/3 |
| Ding | 76 | 2/3 |
| We NEED internships 🙏 | 95 | 3/2 |
| Sydney's Realist | 94 | 4/1 |
| an iq too high | 96 | 4/1 |
| bbas | 111 | 4/1 |
| Hidden Altar Keepers | 85 | 4/1 |
| sudo rm -rf Imperial | 99 | 9/1 |
| E=mc^2+AI^3 | 55 | 5/0 |

## Losses vs wins: us and the other team

| Metric | losses us | losses opp | wins us | wins opp |
|---|---:|---:|---:|---:|
| equipment value R100 | 150 | 210 | 120 | 150 |
| equipment value R250 | 510 | 990 | 735 | 645 |
| equipment value R500 | 1260 | 2640 | 2220 | 1410 |
| capture gold per actor R250 | 136.75 | 224.5 | 176.7 | 152.82 |
| capture gold per actor R500 | 290.27 | 552.77 | 451.95 | 290.3 |
| capture gold per attack/cast round R500 | 2.89 | 4.5 | 3.5 | 3.32 |
| camp-attack share R500 | 0.170 | 0.220 | 0.220 | 0.180 |
| moving share R500 | 0.500 | 0.460 | 0.450 | 0.520 |
| stationary off-spawn share R500 | 0.170 | 0.160 | 0.190 | 0.150 |
| respawn-wait champion-rounds R500 | 92.5 | 60 | 103.5 | 35.5 |
| gems from 20+ captures R500 | 79 | 206 | 153 | 94.5 |
| median first purchase round | 137.5 | 126.25 | 118.5 | 147 |
| actors with Treasure R250 | 0.000 | 2 | 2 | 1 |
| actors with Treasure R500 | 0.500 | 3 | 4 | 2 |
| deaths by R250 | 2 | 1 | 1 | 1 |
| deaths (game) | 9.5 | 4 | 3 | 14 |
| champion-rounds dead | 529.5 | 241 | 157 | 794 |
| gems lost on death | 58.5 | 7.5 | 0.000 | 49 |
| gems carried by our dead (death log) | 58.5 | 7.5 | 0.000 | 49 |
| completed banks | 15 | 27.5 | 36 | 11 |
| first bank round | 99.5 | 105.5 | 106 | 119 |
| median bank size | 22 | 28 | 22 | 23 |
| contact champion-rounds | 939.5 | 1006 | 1058.5 | 1156 |
| P(die within 5 | contact) | 0.060 | 0.020 | 0.020 | 0.060 |
| contact share below 50% hp | 0.220 | 0.150 | 0.200 | 0.140 |
| P(die within 5 | contact, hp ≥ 75%) | 0.020 | 0.000 | 0.000 | 0.010 |
| alone share of contact | 0.540 | 0.490 | 0.510 | 0.430 |
| hurt-in-contact episodes | 30 | 15.5 | 24 | 26 |
| enemy hp lost per contact round | 33.56 | 57.47 | 53.21 | 43 |
| rounds with PvP attacks | 88.5 | 79.5 | 126 | 58.5 |
| teleport hops | 2.97 | 2.76 | 4.8 | 2.21 |
| teleport hops by R250 | 0.290 | 0.330 | 0.580 | 0.250 |
| altar-lock placements | 0.560 | 3.43 | 0.650 | 2.54 |
| ward placements | 59.59 | 179.89 | 100.04 | 197.88 |
| dash moves | 41.34 | 44.56 | 63.74 | 29.02 |
| spawn visits (alive) | 48 | 53.5 | 62 | 49 |
| share of spawn visits by recall | 0.700 | 0.890 | 0.840 | 0.770 |
| gold carried on arrival at spawn | 100.83 | 151.44 | 144.17 | 79.43 |
| rounds between spawn visits | 94.91 | 80.28 | 75.54 | 94.8 |
| fuel-exhausted turns | 0.980 | 23.51 | 1.24 | 31.22 |

## Loss family: mid-game slide (35 games)

| Metric | mid-game us | mid-game opp |
|---|---:|---:|
| equipment value R100 | 150 | 240 |
| equipment value R250 | 510 | 870 |
| equipment value R500 | 1320 | 2520 |
| capture gold per actor R250 | 137.5 | 240.67 |
| capture gold per actor R500 | 340 | 614 |
| capture gold per attack/cast round R500 | 2.83 | 4.32 |
| camp-attack share R500 | 0.190 | 0.250 |
| moving share R500 | 0.480 | 0.460 |
| stationary off-spawn share R500 | 0.170 | 0.160 |
| respawn-wait champion-rounds R500 | 96 | 78 |
| gems from 20+ captures R500 | 109 | 231 |
| median first purchase round | 136 | 126.5 |
| actors with Treasure R250 | 0 | 2 |
| actors with Treasure R500 | 0 | 3 |
| deaths by R250 | 2 | 1 |
| deaths (game) | 8 | 4 |
| champion-rounds dead | 484 | 243 |
| gems lost on death | 60 | 11 |
| gems carried by our dead (death log) | 60 | 11 |
| completed banks | 15 | 28 |
| first bank round | 100 | 85 |
| median bank size | 22 | 33 |

## Loss family: early contact spiral (29 games)

| Metric | early us | early opp |
|---|---:|---:|
| equipment value R100 | 120 | 240 |
| equipment value R250 | 390 | 1110 |
| equipment value R500 | 885 | 3390 |
| capture gold per actor R250 | 100 | 193.4 |
| capture gold per actor R500 | 184 | 542.67 |
| capture gold per attack/cast round R500 | 2.79 | 5.31 |
| camp-attack share R500 | 0.120 | 0.190 |
| moving share R500 | 0.520 | 0.420 |
| stationary off-spawn share R500 | 0.160 | 0.170 |
| respawn-wait champion-rounds R500 | 38 | 51 |
| gems from 20+ captures R500 | 23 | 169 |
| median first purchase round | 154 | 97 |
| actors with Treasure R250 | 0 | 3 |
| actors with Treasure R500 | 0 | 3 |
| deaths by R250 | 6 | 1 |
| deaths (game) | 26 | 4 |
| champion-rounds dead | 1510 | 243 |
| gems lost on death | 44 | 12 |
| gems carried by our dead (death log) | 44 | 12 |
| completed banks | 5 | 32 |
| first bank round | 145 | 109 |
| median bank size | 19 | 23 |

## Loss family: conversion (gear parity or lead at R500) (19 games)

| Metric | conversion us | conversion opp |
|---|---:|---:|
| equipment value R100 | 180 | 150 |
| equipment value R250 | 810 | 870 |
| equipment value R500 | 2430 | 1920 |
| capture gold per actor R250 | 221.2 | 209.33 |
| capture gold per actor R500 | 497.5 | 442.67 |
| capture gold per attack/cast round R500 | 3.71 | 3.39 |
| camp-attack share R500 | 0.210 | 0.210 |
| moving share R500 | 0.480 | 0.480 |
| stationary off-spawn share R500 | 0.160 | 0.150 |
| respawn-wait champion-rounds R500 | 115 | 43 |
| gems from 20+ captures R500 | 110 | 177 |
| median first purchase round | 118 | 176 |
| actors with Treasure R250 | 2 | 2 |
| actors with Treasure R500 | 4 | 3 |
| deaths by R250 | 0 | 1 |
| deaths (game) | 9 | 4 |
| champion-rounds dead | 483 | 243 |
| gems lost on death | 69 | 0 |
| gems carried by our dead (death log) | 69 | 0 |
| completed banks | 29 | 26 |
| first bank round | 83 | 83 |
| median bank size | 21 | 28 |

## Loss family: opening economy (17 games)

| Metric | opening us | opening opp |
|---|---:|---:|
| equipment value R100 | 90 | 240 |
| equipment value R250 | 450 | 1020 |
| equipment value R500 | 1200 | 2700 |
| capture gold per actor R250 | 137.5 | 251.4 |
| capture gold per actor R500 | 293.33 | 599.8 |
| capture gold per attack/cast round R500 | 2.67 | 4.54 |
| camp-attack share R500 | 0.180 | 0.250 |
| moving share R500 | 0.460 | 0.440 |
| stationary off-spawn share R500 | 0.190 | 0.170 |
| respawn-wait champion-rounds R500 | 128 | 75 |
| gems from 20+ captures R500 | 87 | 258 |
| median first purchase round | 145 | 134 |
| actors with Treasure R250 | 1 | 2 |
| actors with Treasure R500 | 3 | 4 |
| deaths by R250 | 0 | 0 |
| deaths (game) | 3 | 2 |
| champion-rounds dead | 182 | 106 |
| gems lost on death | 40 | 0 |
| gems carried by our dead (death log) | 40 | 0 |
| completed banks | 15 | 21 |
| first bank round | 230 | 151 |
| median bank size | 35.5 | 50 |

## Item programmes (first three emblem families per actor)

- our losses: first emblem treasure 210, jungle 163, monster 27, durability 14; top sequences treasure>jungle>durability 141; jungle>durability>power 101; jungle 30; jungle>durability 26; treasure>durability>jungle 24
- winners vs us: first emblem treasure 345, jungle 51, durability 12, power 7, bruiser 3; top sequences treasure>jungle>bruiser 80; treasure>jungle>durability 66; treasure>jungle>power 56; jungle>durability>bruiser 41; treasure>jungle>monster 39
- our wins: first emblem treasure 489, durability 22, jungle 4, monster 2; top sequences treasure>jungle>durability 335; treasure>durability>jungle 67; treasure>jungle>bruiser 48; treasure>durability>bruiser 17; treasure 12

## Drafts (draft-pick IDs; Cassi/Issac is one pick)

- our losses (98 games): Vendetta 1.00, Marcella 0.81, Varg 0.78, Ren 0.64, Ryth 0.27, Heart 0.24, Vesper 0.22, Cassi/Issac 0.22, Prism 0.17, Tavi 0.04, Willow 0.01
- winners vs us (98 games): Vesper 0.96, Heart 0.89, Vendetta 0.81, Marcella 0.71, Ryth 0.51, Tavi 0.29, Varg 0.07, Cassi/Issac 0.06, Prism 0.04, Willow 0.04, Ren 0.03
- our wins (112 games): Vendetta 1.00, Marcella 0.79, Varg 0.72, Ren 0.59, Heart 0.50, Vesper 0.39, Ryth 0.17, Cassi/Issac 0.15, Prism 0.09, Tavi 0.04, Stellar 0.04, Willow 0.02

## Playbooks of the teams that beat us most (their side of our losses)

### Claudus Maximus (rank 4, 49 wins over us)
- drafts: Vesper Vendetta Marcella Tavi Heart ×16; Ryth Vesper Vendetta Marcella Heart ×14
- item sequences: treasure>jungle>power ×47; treasure>jungle>durability ×47; treasure>jungle>monster ×33
- R250 equipment: them 1050, us 510
- R500 equipment: them 3000, us 1230
- capture gold/actor R250: them 240.67, us 112.0
- first bank: them 98, us 99
- banks: them 30, us 10
- bank size: them 28.0, us 18
- deaths: them 4, us 13
- teleports: them 0, us 0
- locks: them 4, us 0
- wards: them 111, us 43
- camp-attack share: them 0.22, us 0.15
- respawn waits: them 86, us 89
- damage per contact round: them 59.14, us 31.4

### Turbo Gold Clusters (rank 176, 8 wins over us)
- drafts: Ryth Vesper Marcella Heart ×5; Vesper Marcella Heart ×1
- item sequences: treasure>jungle>bruiser ×22; treasure>bruiser>durability ×6; treasure>bruiser ×1
- R250 equipment: them 780.0, us 480.0
- R500 equipment: them 1950.0, us 1140.0
- capture gold/actor R250: them 240.75, us 140.0
- first bank: them 60.0, us 112.5
- banks: them 27.0, us 21.0
- bank size: them 31.5, us 22.5
- deaths: them 4.0, us 8.0
- teleports: them 1.0, us 0.0
- locks: them 0.0, us 1.5
- wards: them 243.0, us 74.5
- camp-attack share: them 0.22, us 0.2
- respawn waits: them 40.5, us 88.5
- damage per contact round: them 73.17, us 38.4

### Electric Tributers (rank 134, 7 wins over us)
- drafts: Ryth Vesper Vendetta Marcella Heart ×3; Ryth Vesper Marcella Heart ×2
- item sequences: treasure>jungle>bruiser ×21; treasure>bruiser>durability ×5; treasure>durability>bruiser ×1
- R250 equipment: them 1170, us 810
- R500 equipment: them 2550, us 2220
- capture gold/actor R250: them 235.6, us 221.2
- first bank: them 109, us 76
- banks: them 29, us 33
- bank size: them 30, us 18.0
- deaths: them 3, us 5
- teleports: them 7, us 0
- locks: them 0, us 2
- wards: them 272, us 62
- camp-attack share: them 0.2, us 0.17
- respawn waits: them 29, us 94
- damage per contact round: them 57.08, us 33.46

### Rogue Elk (rank 221, 7 wins over us)
- drafts: Ryth Vesper Marcella Heart ×3; Ryth Vesper Vendetta Marcella Heart ×3
- item sequences: treasure>jungle>bruiser ×18; treasure>bruiser>durability ×3; treasure ×3
- R250 equipment: them 720, us 420
- R500 equipment: them 2130, us 1320
- capture gold/actor R250: them 200.75, us 142.5
- first bank: them 223, us 118
- banks: them 20, us 17
- bank size: them 50, us 43
- deaths: them 6, us 8
- teleports: them 2, us 2
- locks: them 0, us 0
- wards: them 267, us 64
- camp-attack share: them 0.2, us 0.19
- respawn waits: them 24, us 66
- damage per contact round: them 58.41, us 31.4

### Velvet Tributers (rank 67, 6 wins over us)
- drafts: Vesper Vendetta Marcella Varg Heart ×4; Vesper Vendetta Varg Heart ×2
- item sequences: treasure>jungle>durability ×7; treasure>jungle>power ×7; treasure>jungle>bruiser ×4
- R250 equipment: them 1020.0, us 795.0
- R500 equipment: them 2685.0, us 1890.0
- capture gold/actor R250: them 202.3, us 170.9
- first bank: them 160.5, us 111.5
- banks: them 23.5, us 20.5
- bank size: them 37.0, us 33.0
- deaths: them 2.0, us 3.5
- teleports: them 0.0, us 5.5
- locks: them 0.0, us 0.0
- wards: them 299.0, us 62.0
- camp-attack share: them 0.25, us 0.29
- respawn waits: them 76.5, us 154.5
- damage per contact round: them 43.62, us 26.22

### The row boats are hier (rank 276, 4 wins over us)
- drafts: Ryth Vesper Vendetta Marcella Tavi ×2; Vesper Vendetta Marcella Tavi ×2
- item sequences: jungle>durability>bruiser ×12; jungle>durability ×2; treasure>durability>bruiser ×2
- R250 equipment: them 1170.0, us 510.0
- R500 equipment: them 3105.0, us 1200.0
- capture gold/actor R250: them 216.68, us 130.33
- first bank: them 175.0, us 156.0
- banks: them 21.0, us 21.0
- bank size: them 39.25, us 23.5
- deaths: them 3.0, us 9.5
- teleports: them 3.5, us 10.5
- locks: them 3.0, us 0.5
- wards: them 38.5, us 72.5
- camp-attack share: them 0.22, us 0.16
- respawn waits: them 15.0, us 147.5
- damage per contact round: them 42.51, us 35.2

### Palestine 🇵🇸 (rank 112, 4 wins over us)
- drafts: Ryth Vesper Vendetta Marcella Heart ×3; Vesper Vendetta Heart ×1
- item sequences: treasure>durability>jungle ×9; treasure>jungle>durability ×3; jungle>durability>bruiser ×2
- R250 equipment: them 1560.0, us 930.0
- R500 equipment: them 4485.0, us 2970.0
- capture gold/actor R250: them 382.6, us 193.0
- first bank: them 414.5, us 93
- banks: them 14.0, us 11.5
- bank size: them 89.25, us 35.5
- deaths: them 2.0, us 10.0
- teleports: them 0.0, us 2.0
- locks: them 3.5, us 0.0
- wards: them 8.5, us 27.5
- camp-attack share: them 0.35, us 0.34
- respawn waits: them 47.0, us 164.5
- damage per contact round: them 59.18, us 49.66

### Crimson Pathfinders (rank 149, 3 wins over us)
- drafts: Ryth Vesper Vendetta Willow Tavi ×2; Vesper Vendetta Willow ×1
- item sequences: treasure>jungle>durability ×3; treasure>jungle>monster ×3; treasure>durability>jungle ×3
- R250 equipment: them 720, us 270
- R500 equipment: them 2130, us 810
- capture gold/actor R250: them 125.6, us 72.0
- first bank: them 79, us 148
- banks: them 34, us 9
- bank size: them 22, us 11
- deaths: them 11, us 11
- teleports: them 0, us 0
- locks: them 3, us 0
- wards: them 393, us 50
- camp-attack share: them 0.12, us 0.18
- respawn waits: them 35, us 58
- damage per contact round: them 52.13, us 27.4

