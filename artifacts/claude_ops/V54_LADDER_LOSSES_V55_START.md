# v54 ladder replay analysis: where, why, and what winners do

Platform v54; interval 2026-10-25T16:24:00Z onward. 35 finished games in listing; 18 with decoded replays (18 losses, 0 wins). Offline omniscient replay analysis with the pinned engine; descriptive, confounded by map, opponent and draft. Medians of per-game values unless stated; "opp" is the winner in our losses and the loser in our wins.

## Listing results and replay coverage

- ranked: 5/10 wins in listing; decoded 5 games (0 wins).
- unranked: 12/25 wins in listing; decoded 13 games (0 wins).
- loss families (a loss can have several): mid-game slide 10, conversion (gear parity or lead at R500) 5, opening economy 3
- close losses (margin ≥ −150 gems): 6/18; median margin of losses -279

| Map | W/L | mean margin | median R250 gear ratio | our deaths / opp deaths (median) |
|---|---:|---:|---:|---:|
| 01shortcut | 0/5 | -427 | 0.86 | 5 / 3 |
| 01islands | 0/4 | -312 | 0.73 | 9.0 / 10.5 |
| 00eight | 0/2 | -860 | 1.04 | 29.5 / 10.5 |
| 01big_world | 0/2 | -161 | 0.45 | 3.0 / 2.5 |
| 00swirl | 0/1 | -200 | 1.21 | 47 / 26 |
| 00rows | 0/1 | -12 | 0.8 | 2 / 2 |
| 01broken_curve | 0/1 | -88 | 1.23 | 1 / 5 |
| 00stampede | 0/1 | -640 | 1.33 | 12 / 4 |
| 00expanse | 0/1 | -38 | 1.0 | 0 / 3 |

| Opponent | rank now | W/L vs them |
|---|---:|---:|
| Midnight Wardens | 123 | 0/13 |
| bbas | 122 | 0/3 |
| Sir Chud | 163 | 0/2 |

## Losses vs wins: us and the other team

| Metric | losses us | losses opp | wins us | wins opp |
|---|---:|---:|---:|---:|
| equipment value R100 | 150 | 150 | - | - |
| equipment value R250 | 510 | 615 | - | - |
| equipment value R500 | 1290 | 1875 | - | - |
| capture gold per actor R250 | 139.67 | 227.05 | - | - |
| capture gold per actor R500 | 294.33 | 438.27 | - | - |
| capture gold per attack/cast round R500 | 3.22 | 3.69 | - | - |
| camp-attack share R500 | 0.150 | 0.230 | - | - |
| moving share R500 | 0.530 | 0.540 | - | - |
| stationary off-spawn share R500 | 0.170 | 0.120 | - | - |
| respawn-wait champion-rounds R500 | 80.5 | 32 | - | - |
| gems from 20+ captures R500 | 30 | 136.5 | - | - |
| median first purchase round | 127.75 | 107 | - | - |
| actors with Treasure R250 | 2 | 1 | - | - |
| actors with Treasure R500 | 4 | 3 | - | - |
| deaths by R250 | 1 | 1.5 | - | - |
| deaths (game) | 5 | 4 | - | - |
| champion-rounds dead | 301.5 | 241.5 | - | - |
| gems lost on death | 30 | 16.5 | - | - |
| gems carried by our dead (death log) | 30 | 16.5 | - | - |
| completed banks | 17 | 36.5 | - | - |
| first bank round | 169 | 78.5 | - | - |
| median bank size | 29 | 29 | - | - |
| contact champion-rounds | 611.5 | 660 | - | - |
| P(die within 5 | contact) | 0.040 | 0.030 | - | - |
| contact share below 50% hp | 0.170 | 0.120 | - | - |
| P(die within 5 | contact, hp ≥ 75%) | 0.010 | 0.010 | - | - |
| alone share of contact | 0.610 | 0.650 | - | - |
| hurt-in-contact episodes | 16.5 | 11 | - | - |
| enemy hp lost per contact round | 30.51 | 42.16 | - | - |
| rounds with PvP attacks | 66.5 | 52.5 | - | - |
| teleport hops | 5.67 | 0.720 | - | - |
| teleport hops by R250 | 0.890 | 0 | - | - |
| altar-lock placements | 0.060 | 3.11 | - | - |
| ward placements | 66.78 | 302.28 | - | - |
| dash moves | 54.56 | 43.39 | - | - |
| spawn visits (alive) | 51.5 | 44.5 | - | - |
| share of spawn visits by recall | 0.680 | 0.830 | - | - |
| gold carried on arrival at spawn | 117.49 | 154.66 | - | - |
| rounds between spawn visits | 105.37 | 108.09 | - | - |
| fuel-exhausted turns | 3.17 | 28.11 | - | - |

## Loss family: mid-game slide (10 games)

| Metric | mid-game us | mid-game opp |
|---|---:|---:|
| equipment value R100 | 135 | 135 |
| equipment value R250 | 540 | 510 |
| equipment value R500 | 1065 | 1815 |
| capture gold per actor R250 | 139.67 | 220.1 |
| capture gold per actor R500 | 259.17 | 417 |
| capture gold per attack/cast round R500 | 3.22 | 3.61 |
| camp-attack share R500 | 0.150 | 0.230 |
| moving share R500 | 0.580 | 0.570 |
| stationary off-spawn share R500 | 0.160 | 0.110 |
| respawn-wait champion-rounds R500 | 63 | 30 |
| gems from 20+ captures R500 | 30 | 145 |
| median first purchase round | 125 | 99.25 |
| actors with Treasure R250 | 2 | 1 |
| actors with Treasure R500 | 4 | 3 |
| deaths by R250 | 1 | 1.5 |
| deaths (game) | 6 | 4 |
| champion-rounds dead | 363.5 | 241.5 |
| gems lost on death | 63 | 16.5 |
| gems carried by our dead (death log) | 63 | 16.5 |
| completed banks | 26 | 38 |
| first bank round | 130.5 | 80 |
| median bank size | 26.75 | 28.75 |

## Loss family: conversion (gear parity or lead at R500) (5 games)

| Metric | conversion us | conversion opp |
|---|---:|---:|
| equipment value R100 | 150 | 60 |
| equipment value R250 | 720 | 540 |
| equipment value R500 | 2010 | 1890 |
| capture gold per actor R250 | 187.2 | 213.2 |
| capture gold per actor R500 | 420.8 | 440.8 |
| capture gold per attack/cast round R500 | 3.61 | 3.2 |
| camp-attack share R500 | 0.180 | 0.160 |
| moving share R500 | 0.520 | 0.580 |
| stationary off-spawn share R500 | 0.190 | 0.120 |
| respawn-wait champion-rounds R500 | 210 | 68 |
| gems from 20+ captures R500 | 74 | 44 |
| median first purchase round | 128 | 157 |
| actors with Treasure R250 | 3 | 1 |
| actors with Treasure R500 | 5 | 3 |
| deaths by R250 | 0 | 0 |
| deaths (game) | 5 | 4 |
| champion-rounds dead | 277 | 240 |
| gems lost on death | 12 | 12 |
| gems carried by our dead (death log) | 12 | 12 |
| completed banks | 9 | 30 |
| first bank round | 299 | 77 |
| median bank size | 32 | 28.5 |

## Loss family: opening economy (3 games)

| Metric | opening us | opening opp |
|---|---:|---:|
| equipment value R100 | 60 | 210 |
| equipment value R250 | 510 | 750 |
| equipment value R500 | 1380 | 3090 |
| capture gold per actor R250 | 139.67 | 252.6 |
| capture gold per actor R500 | 288.33 | 653.6 |
| capture gold per attack/cast round R500 | 3.07 | 5.23 |
| camp-attack share R500 | 0.140 | 0.270 |
| moving share R500 | 0.260 | 0.460 |
| stationary off-spawn share R500 | 0.520 | 0.160 |
| respawn-wait champion-rounds R500 | 522 | 95 |
| gems from 20+ captures R500 | 0 | 178 |
| median first purchase round | 130 | 72 |
| actors with Treasure R250 | 2 | 2 |
| actors with Treasure R500 | 4 | 4 |
| deaths by R250 | 1 | 3 |
| deaths (game) | 5 | 7 |
| champion-rounds dead | 302 | 395 |
| gems lost on death | 0 | 38 |
| gems carried by our dead (death log) | 0 | 38 |
| completed banks | 10 | 36 |
| first bank round | 169 | 64 |
| median bank size | 29 | 30 |

## Item programmes (first three emblem families per actor)

- our losses: first emblem treasure 77, durability 5, jungle 3, bruiser 1; top sequences treasure>jungle>durability 54; treasure>durability>jungle 9; treasure 4; treasure>durability>bruiser 4; treasure>jungle>bruiser 3
- winners vs us: first emblem treasure 59, power 6, durability 5, bruiser 4, jungle 4; top sequences treasure>jungle>durability 13; treasure>durability>jungle 12; treasure>jungle>power 11; treasure>power>durability 10; treasure>jungle>monster 5
- our wins: first emblem ; top sequences 

## Drafts (draft-pick IDs; Cassi/Issac is one pick)

- our losses (18 games): Vendetta 1.00, Varg 1.00, Ryth 0.67, Ren 0.61, Marcella 0.50, Cassi/Issac 0.39, Heart 0.11, Vesper 0.11, Prism 0.11
- winners vs us (18 games): Marcella 1.00, Vendetta 0.94, Heart 0.89, Vesper 0.83, Ryth 0.61, Willow 0.17, Varg 0.06
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

