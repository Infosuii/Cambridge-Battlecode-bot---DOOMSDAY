# v54 ladder replay analysis: where, why, and what winners do

Platform v54; interval 2026-10-25T16:24:00Z through 17:10:10Z. 110 finished games in listing; 48 with decoded replays (48 losses, 0 wins). Offline omniscient replay analysis with the pinned engine; descriptive, confounded by map, opponent and draft. Medians of per-game values unless stated; "opp" is the winner in our losses and the loser in our wins.

## Listing results and replay coverage

- ranked: 14/25 wins in listing; decoded 11 games (0 wins).
- unranked: 48/85 wins in listing; decoded 37 games (0 wins).
- loss families (a loss can have several): mid-game slide 20, conversion (gear parity or lead at R500) 11, opening economy 11, early contact spiral 8
- close losses (margin ≥ −150 gems): 14/48; median margin of losses -360

| Map | W/L | mean margin | median R250 gear ratio | our deaths / opp deaths (median) |
|---|---:|---:|---:|---:|
| 01shortcut | 0/8 | -486 | 0.88 | 5.0 / 4.0 |
| 01islands | 0/6 | -375 | 0.73 | 9.0 / 7.5 |
| 01big_world | 0/4 | -162 | 0.48 | 2.5 / 1.0 |
| 00rows | 0/3 | -141 | 0.8 | 2 / 0 |
| 01hooks | 0/3 | -836 | 0.83 | 26 / 12 |
| 00swirl | 0/2 | -351 | 0.75 | 34.0 / 21.0 |
| 00eight | 0/2 | -860 | 1.04 | 29.5 / 10.5 |
| 00stampede | 0/2 | -360 | 1.19 | 13.5 / 3.5 |
| 01gold_rush | 0/2 | -613 | 1.12 | 32.5 / 10.0 |
| 00elkring | 0/2 | -297 | 0.54 | 4.0 / 3.0 |
| 00rushbait_v2 | 0/2 | -282 | 0.98 | 5.0 / 3.5 |
| 00quadrants | 0/2 | -241 | 0.54 | 3.0 / 2.5 |
| 01broken_curve | 0/1 | -88 | 1.23 | 1 / 5 |
| 00expanse | 0/1 | -38 | 1.0 | 0 / 3 |
| 01boss_battle | 0/1 | -1027 | 0.44 | 18 / 1 |
| 00fragment | 0/1 | -70 | 0.65 | 17 / 25 |
| 00corners | 0/1 | -96 | 1.14 | 1 / 5 |
| 00collision | 0/1 | -38 | 0.61 | 5 / 0 |
| 01corridors | 0/1 | -418 | 0.56 | 6 / 12 |
| 01concentrated_wealth | 0/1 | -146 | 0.42 | 12 / 12 |
| 00reverse_spiral | 0/1 | -571 | 0.7 | 18 / 9 |
| 01starfish | 0/1 | -564 | 0.24 | 30 / 15 |

| Opponent | rank now | W/L vs them |
|---|---:|---:|
| Midnight Wardens | 123 | 0/13 |
| Turbo Gold Clusters | 136 | 0/8 |
| Electric Tributers | 105 | 0/7 |
| Velvet Tributers | 85 | 0/7 |
| bbas | 122 | 0/3 |
| Velvet Recallers | 113 | 0/3 |
| Sir Chud | 163 | 0/2 |
| Palestine 🇵🇸 | 117 | 0/2 |
| snoc | 109 | 0/2 |
| TTS | 110 | 0/1 |

## Losses vs wins: us and the other team

| Metric | losses us | losses opp | wins us | wins opp |
|---|---:|---:|---:|---:|
| equipment value R100 | 150 | 195 | - | - |
| equipment value R250 | 525 | 720 | - | - |
| equipment value R500 | 1365 | 2085 | - | - |
| capture gold per actor R250 | 139.67 | 210.17 | - | - |
| capture gold per actor R500 | 282.67 | 450.3 | - | - |
| capture gold per attack/cast round R500 | 3.12 | 4.16 | - | - |
| camp-attack share R500 | 0.170 | 0.230 | - | - |
| moving share R500 | 0.510 | 0.520 | - | - |
| stationary off-spawn share R500 | 0.180 | 0.140 | - | - |
| respawn-wait champion-rounds R500 | 83 | 40.5 | - | - |
| gems from 20+ captures R500 | 65.5 | 144.5 | - | - |
| median first purchase round | 133 | 135 | - | - |
| actors with Treasure R250 | 2 | 2 | - | - |
| actors with Treasure R500 | 4 | 3 | - | - |
| deaths by R250 | 1 | 1 | - | - |
| deaths (game) | 6.5 | 4.5 | - | - |
| champion-rounds dead | 363.5 | 256.5 | - | - |
| gems lost on death | 36 | 22 | - | - |
| gems carried by our dead (death log) | 36 | 22 | - | - |
| completed banks | 18 | 28 | - | - |
| first bank round | 130 | 97 | - | - |
| median bank size | 26 | 30 | - | - |
| contact champion-rounds | 802.5 | 852.5 | - | - |
| P(die within 5 | contact) | 0.040 | 0.030 | - | - |
| contact share below 50% hp | 0.210 | 0.120 | - | - |
| P(die within 5 | contact, hp ≥ 75%) | 0.010 | 0.000 | - | - |
| alone share of contact | 0.580 | 0.530 | - | - |
| hurt-in-contact episodes | 23.5 | 14 | - | - |
| enemy hp lost per contact round | 35.98 | 49.97 | - | - |
| rounds with PvP attacks | 80 | 62.5 | - | - |
| teleport hops | 6.58 | 5.19 | - | - |
| teleport hops by R250 | 0.880 | 0.580 | - | - |
| altar-lock placements | 1.04 | 1.31 | - | - |
| ward placements | 69.58 | 262.94 | - | - |
| dash moves | 53.23 | 35 | - | - |
| spawn visits (alive) | 54.5 | 56.5 | - | - |
| share of spawn visits by recall | 0.730 | 0.870 | - | - |
| gold carried on arrival at spawn | 108.83 | 143.97 | - | - |
| rounds between spawn visits | 91.42 | 96.55 | - | - |
| fuel-exhausted turns | 2 | 35.1 | - | - |

## Loss family: mid-game slide (20 games)

| Metric | mid-game us | mid-game opp |
|---|---:|---:|
| equipment value R100 | 150 | 150 |
| equipment value R250 | 585 | 660 |
| equipment value R500 | 1230 | 1860 |
| capture gold per actor R250 | 146.33 | 176.78 |
| capture gold per actor R500 | 263.67 | 403.38 |
| capture gold per attack/cast round R500 | 3.26 | 3.66 |
| camp-attack share R500 | 0.140 | 0.210 |
| moving share R500 | 0.540 | 0.560 |
| stationary off-spawn share R500 | 0.160 | 0.120 |
| respawn-wait champion-rounds R500 | 60.5 | 32 |
| gems from 20+ captures R500 | 110 | 158.5 |
| median first purchase round | 136 | 161.25 |
| actors with Treasure R250 | 2 | 1.5 |
| actors with Treasure R500 | 3 | 3 |
| deaths by R250 | 2 | 1.5 |
| deaths (game) | 8 | 4.5 |
| champion-rounds dead | 484 | 256.5 |
| gems lost on death | 59.5 | 21.5 |
| gems carried by our dead (death log) | 59.5 | 21.5 |
| completed banks | 15 | 33.5 |
| first bank round | 137 | 88.5 |
| median bank size | 29 | 29.5 |

## Loss family: conversion (gear parity or lead at R500) (11 games)

| Metric | conversion us | conversion opp |
|---|---:|---:|
| equipment value R100 | 150 | 150 |
| equipment value R250 | 720 | 690 |
| equipment value R500 | 1800 | 1650 |
| capture gold per actor R250 | 187.2 | 213.2 |
| capture gold per actor R500 | 420.8 | 440.8 |
| capture gold per attack/cast round R500 | 3.12 | 3.2 |
| camp-attack share R500 | 0.210 | 0.230 |
| moving share R500 | 0.510 | 0.520 |
| stationary off-spawn share R500 | 0.170 | 0.120 |
| respawn-wait champion-rounds R500 | 176 | 39 |
| gems from 20+ captures R500 | 78 | 130 |
| median first purchase round | 126 | 154 |
| actors with Treasure R250 | 2 | 1 |
| actors with Treasure R500 | 4 | 3 |
| deaths by R250 | 0 | 1 |
| deaths (game) | 5 | 5 |
| champion-rounds dead | 277 | 300 |
| gems lost on death | 59 | 36 |
| gems carried by our dead (death log) | 59 | 36 |
| completed banks | 29 | 28 |
| first bank round | 96 | 126 |
| median bank size | 26 | 30 |

## Loss family: opening economy (11 games)

| Metric | opening us | opening opp |
|---|---:|---:|
| equipment value R100 | 120 | 210 |
| equipment value R250 | 510 | 780 |
| equipment value R500 | 1470 | 2310 |
| capture gold per actor R250 | 136 | 246.4 |
| capture gold per actor R500 | 288.33 | 585.33 |
| capture gold per attack/cast round R500 | 2.81 | 4.25 |
| camp-attack share R500 | 0.190 | 0.250 |
| moving share R500 | 0.450 | 0.470 |
| stationary off-spawn share R500 | 0.200 | 0.150 |
| respawn-wait champion-rounds R500 | 303 | 73 |
| gems from 20+ captures R500 | 71 | 178 |
| median first purchase round | 146 | 128 |
| actors with Treasure R250 | 1 | 2 |
| actors with Treasure R500 | 4 | 4 |
| deaths by R250 | 0 | 2 |
| deaths (game) | 5 | 3 |
| champion-rounds dead | 301 | 181 |
| gems lost on death | 0 | 36 |
| gems carried by our dead (death log) | 0 | 36 |
| completed banks | 27 | 27 |
| first bank round | 169 | 98 |
| median bank size | 29 | 30 |

## Loss family: early contact spiral (8 games)

| Metric | early us | early opp |
|---|---:|---:|
| equipment value R100 | 150 | 270 |
| equipment value R250 | 435 | 1185 |
| equipment value R500 | 810 | 2820 |
| capture gold per actor R250 | 109.25 | 274 |
| capture gold per actor R500 | 203.8 | 633 |
| capture gold per attack/cast round R500 | 2.71 | 5.19 |
| camp-attack share R500 | 0.190 | 0.220 |
| moving share R500 | 0.480 | 0.440 |
| stationary off-spawn share R500 | 0.190 | 0.190 |
| respawn-wait champion-rounds R500 | 36.5 | 45 |
| gems from 20+ captures R500 | 33 | 115.5 |
| median first purchase round | 165.75 | 124 |
| actors with Treasure R250 | 1 | 3 |
| actors with Treasure R500 | 2 | 3.5 |
| deaths by R250 | 6 | 1 |
| deaths (game) | 20 | 8.5 |
| champion-rounds dead | 1174.5 | 512.5 |
| gems lost on death | 26 | 13.5 |
| gems carried by our dead (death log) | 26 | 13.5 |
| completed banks | 17.5 | 27 |
| first bank round | 130 | 156.5 |
| median bank size | 18 | 29.5 |

## Item programmes (first three emblem families per actor)

- our losses: first emblem treasure 199, durability 13, jungle 6, monster 2, bruiser 1; top sequences treasure>jungle>durability 135; treasure>durability>jungle 19; treasure 15; treasure>durability>bruiser 15; treasure>jungle 8
- winners vs us: first emblem treasure 160, jungle 16, power 11, durability 9, bruiser 5; top sequences treasure>jungle>bruiser 47; treasure>jungle>durability 23; treasure>jungle>power 22; treasure>durability>jungle 18; treasure>power>durability 12
- our wins: first emblem ; top sequences 

## Drafts (draft-pick IDs; Cassi/Issac is one pick)

- our losses (48 games): Vendetta 1.00, Varg 0.94, Marcella 0.65, Ren 0.54, Ryth 0.40, Cassi/Issac 0.38, Prism 0.23, Vesper 0.10, Tavi 0.10, Heart 0.06
- winners vs us (48 games): Marcella 0.90, Vesper 0.90, Heart 0.88, Vendetta 0.73, Ryth 0.62, Varg 0.15, Prism 0.08, Willow 0.06, Ren 0.04, Cassi/Issac 0.04
- our wins (0 games): 

## Playbooks of the teams that beat us most (their side of our losses)

### Midnight Wardens (rank 123, 13 wins over us)
- drafts: Ryth Vesper Vendetta Marcella Heart ×7; Vesper Vendetta Marcella Heart ×5
- item sequences: treasure>durability>jungle ×12; treasure>jungle>power ×11; treasure>power>durability ×10
- R250 equipment: them 660, us 510
- R500 equipment: them 1860, us 1200
- capture gold/actor R250: them 230.5, us 139.67
- first bank: them 76, us 169
- banks: them 36, us 10
- bank size: them 29, us 30
- deaths: them 5, us 5
- teleports: them 0, us 8
- locks: them 3, us 0
- wards: them 313, us 64
- camp-attack share: them 0.23, us 0.15
- respawn waits: them 30, us 78
- damage per contact round: them 33.65, us 20.22

### Turbo Gold Clusters (rank 136, 8 wins over us)
- drafts: Ryth Vesper Marcella Heart ×4; Ryth Vesper Vendetta Marcella Heart ×2
- item sequences: treasure>jungle>bruiser ×24; treasure>durability>bruiser ×3; treasure>bruiser>durability ×3
- R250 equipment: them 765.0, us 660.0
- R500 equipment: them 1995.0, us 1545.0
- capture gold/actor R250: them 168.75, us 159.33
- first bank: them 127.0, us 251.0
- banks: them 24.0, us 12.0
- bank size: them 35.0, us 24.0
- deaths: them 5.5, us 6.0
- teleports: them 0.0, us 0.0
- locks: them 0.0, us 3.5
- wards: them 250.5, us 57.0
- camp-attack share: them 0.21, us 0.17
- respawn waits: them 37.0, us 98.0
- damage per contact round: them 52.63, us 42.55

### Electric Tributers (rank 105, 7 wins over us)
- drafts: Ryth Vesper Vendetta Marcella Heart ×3; Ryth Vesper Marcella Heart ×2
- item sequences: treasure>jungle>bruiser ×16; treasure>bruiser ×3; treasure>jungle ×3
- R250 equipment: them 810, us 510
- R500 equipment: them 2310, us 1680
- capture gold/actor R250: them 209.33, us 153.5
- first bank: them 129, us 91
- banks: them 27, us 24
- bank size: them 30.0, us 26
- deaths: them 8, us 12
- teleports: them 1, us 0
- locks: them 0, us 1
- wards: them 270, us 69
- camp-attack share: them 0.2, us 0.14
- respawn waits: them 23, us 177
- damage per contact round: them 69.12, us 46.22

### Velvet Tributers (rank 85, 7 wins over us)
- drafts: Vesper Vendetta Marcella Varg Heart ×4; Vesper Vendetta Varg Heart ×2
- item sequences: treasure>jungle>power ×10; treasure>jungle>bruiser ×6; treasure>jungle>durability ×5
- R250 equipment: them 1110, us 480
- R500 equipment: them 2580, us 1800
- capture gold/actor R250: them 211.0, us 130.33
- first bank: them 85, us 105
- banks: them 25, us 18
- bank size: them 37, us 22.0
- deaths: them 3, us 4
- teleports: them 0, us 3
- locks: them 0, us 0
- wards: them 305, us 45
- camp-attack share: them 0.25, us 0.22
- respawn waits: them 65, us 58
- damage per contact round: them 35.77, us 27.82

### bbas (rank 122, 3 wins over us)
- drafts: Vendetta Marcella Willow Heart ×1; Ryth Vendetta Marcella Willow Varg ×1
- item sequences: bruiser ×3; durability>power ×2; jungle>durability>bruiser ×2
- R250 equipment: them 570, us 690
- R500 equipment: them 1560, us 1020
- capture gold/actor R250: them 122.5, us 87.5
- first bank: them 80, us 58
- banks: them 41, us 33
- bank size: them 26, us 15
- deaths: them 4, us 34
- teleports: them 3, us 1
- locks: them 4, us 0
- wards: them 58, us 146
- camp-attack share: them 0.17, us 0.11
- respawn waits: them 27, us 35
- damage per contact round: them 57.59, us 49.27

### Velvet Recallers (rank 113, 3 wins over us)
- drafts: Ryth Vesper Vendetta Marcella ×2; Ryth Vesper Vendetta Marcella Heart ×1
- item sequences: jungle>treasure>durability ×3; jungle ×2; jungle>durability>treasure ×2
- R250 equipment: them 420, us 540
- R500 equipment: them 1140, us 990
- capture gold/actor R250: them 109.2, us 111.2
- first bank: them 126, us 103
- banks: them 24, us 13
- bank size: them 35.5, us 43
- deaths: them 6, us 4
- teleports: them 24, us 13
- locks: them 0, us 0
- wards: them 31, us 40
- camp-attack share: them 0.17, us 0.14
- respawn waits: them 67, us 28
- damage per contact round: them 39.04, us 25.15

