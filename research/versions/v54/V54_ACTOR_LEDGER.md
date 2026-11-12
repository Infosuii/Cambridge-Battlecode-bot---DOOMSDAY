# Actor-level opening ledger (v54 phase 1)

Offline omniscient replay analysis with the pinned engine (`tools/replay/actor_ledger.mjs`, this report: `tools/replay/ledger_report.py`). Never a bot input. Each alive champion-round is assigned one activity in priority order bank > PvP attack > camp attack > cast > on own spawn > travel/other. Capture income is the positive gold change between round states not explained by a kill or purchase (Marcella tribute gold is excluded when the bag drops). "Shared" captures are reward events received in the same round by allies within 3 tiles (a split reward). Values are cohort medians of per-game team values, us / opponent. Cohorts overlap and are not random samples.

## v53 losses — 39 games

| Window | Metric | Us | Opponent |
|---|---|---:|---:|
| R100 | dead share of champion-rounds | 0.04 | 0.00 |
| R100 | camp-attack share of alive rounds | 0.20 | 0.30 |
| R100 | cast-only share | 0.05 | 0.05 |
| R100 | PvP-attack share | 0.02 | 0.03 |
| R100 | moving, no attack share | 0.47 | 0.45 |
| R100 | stationary off-spawn, no attack share | 0.17 | 0.13 |
| R100 | on-spawn share | 0.04 | 0.04 |
| R100 | banking share | 0.00 | 0.00 |
| R100 | capture gold per actor | 61 | 93 |
| R100 | capture gold per 100 alive champion-rounds | 65 | 94 |
| R100 | capture gold per attack/cast round | 2.81 | 2.62 |
| R100 | capture events per actor | 1.00 | 1.00 |
| R100 | shared-capture fraction | 0.00 | 0.00 |
| R100 | actors with no capture yet | 2 | 1 |
| R100 | actors with Treasure emblem | 0 | 1 |
| R100 | emblems per actor | 0.00 | 0.25 |
| R100 | kill gold (team) | 0.00 | 0.00 |
| R250 | dead share of champion-rounds | 0.05 | 0.05 |
| R250 | camp-attack share of alive rounds | 0.20 | 0.25 |
| R250 | cast-only share | 0.05 | 0.06 |
| R250 | PvP-attack share | 0.02 | 0.04 |
| R250 | moving, no attack share | 0.49 | 0.43 |
| R250 | stationary off-spawn, no attack share | 0.19 | 0.15 |
| R250 | on-spawn share | 0.03 | 0.04 |
| R250 | banking share | 0.00 | 0.01 |
| R250 | capture gold per actor | 144 | 267 |
| R250 | capture gold per 100 alive champion-rounds | 66 | 114 |
| R250 | capture gold per attack/cast round | 2.93 | 3.46 |
| R250 | capture events per actor | 2.25 | 2.60 |
| R250 | shared-capture fraction | 0.00 | 0.00 |
| R250 | actors with no capture yet | 0 | 0 |
| R250 | actors with Treasure emblem | 0 | 2 |
| R250 | emblems per actor | 0.60 | 1.00 |
| R250 | kill gold (team) | 100 | 100 |
| R500 | dead share of champion-rounds | 0.09 | 0.05 |
| R500 | camp-attack share of alive rounds | 0.18 | 0.26 |
| R500 | cast-only share | 0.05 | 0.06 |
| R500 | PvP-attack share | 0.02 | 0.04 |
| R500 | moving, no attack share | 0.49 | 0.44 |
| R500 | stationary off-spawn, no attack share | 0.19 | 0.17 |
| R500 | on-spawn share | 0.03 | 0.03 |
| R500 | banking share | 0.01 | 0.01 |
| R500 | capture gold per actor | 320 | 552 |
| R500 | capture gold per 100 alive champion-rounds | 69 | 120 |
| R500 | capture gold per attack/cast round | 3.64 | 4.30 |
| R500 | capture events per actor | 4.00 | 5.40 |
| R500 | shared-capture fraction | 0.00 | 0.06 |
| R500 | actors with no capture yet | 0 | 0 |
| R500 | median first purchase round | 147 | 107 |
| R500 | actors with Treasure emblem | 0 | 4 |
| R500 | emblems per actor | 1.50 | 2.60 |
| R500 | kill gold (team) | 100 | 233 |

## v53 wins — 36 games

| Window | Metric | Us | Opponent |
|---|---|---:|---:|
| R100 | dead share of champion-rounds | 0.00 | 0.00 |
| R100 | camp-attack share of alive rounds | 0.19 | 0.24 |
| R100 | cast-only share | 0.05 | 0.05 |
| R100 | PvP-attack share | 0.01 | 0.02 |
| R100 | moving, no attack share | 0.49 | 0.50 |
| R100 | stationary off-spawn, no attack share | 0.13 | 0.11 |
| R100 | on-spawn share | 0.04 | 0.05 |
| R100 | banking share | 0.01 | 0.00 |
| R100 | capture gold per actor | 50 | 48 |
| R100 | capture gold per 100 alive champion-rounds | 50 | 49 |
| R100 | capture gold per attack/cast round | 2.56 | 1.63 |
| R100 | capture events per actor | 0.80 | 0.67 |
| R100 | shared-capture fraction | 0.00 | 0.00 |
| R100 | actors with no capture yet | 2.00 | 2.00 |
| R100 | actors with Treasure emblem | 0.00 | 0.00 |
| R100 | emblems per actor | 0.08 | 0.00 |
| R100 | kill gold (team) | 0.00 | 0.00 |
| R250 | dead share of champion-rounds | 0.02 | 0.09 |
| R250 | camp-attack share of alive rounds | 0.18 | 0.22 |
| R250 | cast-only share | 0.05 | 0.05 |
| R250 | PvP-attack share | 0.02 | 0.01 |
| R250 | moving, no attack share | 0.47 | 0.52 |
| R250 | stationary off-spawn, no attack share | 0.18 | 0.13 |
| R250 | on-spawn share | 0.03 | 0.03 |
| R250 | banking share | 0.01 | 0.01 |
| R250 | capture gold per actor | 167 | 160 |
| R250 | capture gold per 100 alive champion-rounds | 70 | 69 |
| R250 | capture gold per attack/cast round | 3.01 | 2.42 |
| R250 | capture events per actor | 2.45 | 2.10 |
| R250 | shared-capture fraction | 0.00 | 0.05 |
| R250 | actors with no capture yet | 0.00 | 0.50 |
| R250 | actors with Treasure emblem | 0.00 | 1.00 |
| R250 | emblems per actor | 0.67 | 0.60 |
| R250 | kill gold (team) | 100 | 0.00 |
| R500 | dead share of champion-rounds | 0.04 | 0.11 |
| R500 | camp-attack share of alive rounds | 0.18 | 0.20 |
| R500 | cast-only share | 0.05 | 0.05 |
| R500 | PvP-attack share | 0.02 | 0.03 |
| R500 | moving, no attack share | 0.49 | 0.54 |
| R500 | stationary off-spawn, no attack share | 0.19 | 0.14 |
| R500 | on-spawn share | 0.03 | 0.03 |
| R500 | banking share | 0.01 | 0.01 |
| R500 | capture gold per actor | 356 | 309 |
| R500 | capture gold per 100 alive champion-rounds | 71 | 70 |
| R500 | capture gold per attack/cast round | 3.38 | 2.66 |
| R500 | capture events per actor | 5.40 | 3.83 |
| R500 | shared-capture fraction | 0.00 | 0.06 |
| R500 | actors with no capture yet | 0.00 | 0.00 |
| R500 | median first purchase round | 148 | 157 |
| R500 | actors with Treasure emblem | 0.00 | 3.00 |
| R500 | emblems per actor | 2.00 | 1.37 |
| R500 | kill gold (team) | 300 | 100 |

## v53 targeted (meow, HAK) — 10 games

| Window | Metric | Us | Opponent |
|---|---|---:|---:|
| R100 | dead share of champion-rounds | 0.14 | 0.00 |
| R100 | camp-attack share of alive rounds | 0.19 | 0.23 |
| R100 | cast-only share | 0.05 | 0.05 |
| R100 | PvP-attack share | 0.02 | 0.01 |
| R100 | moving, no attack share | 0.52 | 0.45 |
| R100 | stationary off-spawn, no attack share | 0.15 | 0.16 |
| R100 | on-spawn share | 0.03 | 0.04 |
| R100 | banking share | 0.00 | 0.00 |
| R100 | capture gold per actor | 57 | 92 |
| R100 | capture gold per 100 alive champion-rounds | 66 | 92 |
| R100 | capture gold per attack/cast round | 2.64 | 2.77 |
| R100 | capture events per actor | 0.63 | 0.90 |
| R100 | shared-capture fraction | 0.00 | 0.00 |
| R100 | actors with no capture yet | 2.00 | 1.00 |
| R100 | actors with Treasure emblem | 0.00 | 0.00 |
| R100 | emblems per actor | 0.00 | 0.00 |
| R100 | kill gold (team) | 0.00 | 50 |
| R250 | dead share of champion-rounds | 0.11 | 0.05 |
| R250 | camp-attack share of alive rounds | 0.20 | 0.29 |
| R250 | cast-only share | 0.05 | 0.05 |
| R250 | PvP-attack share | 0.03 | 0.02 |
| R250 | moving, no attack share | 0.49 | 0.43 |
| R250 | stationary off-spawn, no attack share | 0.18 | 0.16 |
| R250 | on-spawn share | 0.03 | 0.03 |
| R250 | banking share | 0.00 | 0.01 |
| R250 | capture gold per actor | 138 | 286 |
| R250 | capture gold per 100 alive champion-rounds | 67 | 124 |
| R250 | capture gold per attack/cast round | 2.71 | 3.87 |
| R250 | capture events per actor | 1.80 | 2.67 |
| R250 | shared-capture fraction | 0.00 | 0.15 |
| R250 | actors with no capture yet | 0.00 | 0.00 |
| R250 | actors with Treasure emblem | 0.00 | 3.00 |
| R250 | emblems per actor | 0.50 | 1.20 |
| R250 | kill gold (team) | 100 | 100 |
| R500 | dead share of champion-rounds | 0.11 | 0.07 |
| R500 | camp-attack share of alive rounds | 0.19 | 0.29 |
| R500 | cast-only share | 0.05 | 0.05 |
| R500 | PvP-attack share | 0.04 | 0.03 |
| R500 | moving, no attack share | 0.51 | 0.43 |
| R500 | stationary off-spawn, no attack share | 0.17 | 0.17 |
| R500 | on-spawn share | 0.03 | 0.03 |
| R500 | banking share | 0.00 | 0.01 |
| R500 | capture gold per actor | 317 | 728 |
| R500 | capture gold per 100 alive champion-rounds | 69 | 158 |
| R500 | capture gold per attack/cast round | 2.97 | 5.24 |
| R500 | capture events per actor | 3.55 | 5.80 |
| R500 | shared-capture fraction | 0.00 | 0.08 |
| R500 | actors with no capture yet | 0.00 | 0.00 |
| R500 | median first purchase round | 148 | 72 |
| R500 | actors with Treasure emblem | 0.00 | 4.00 |
| R500 | emblems per actor | 1.45 | 2.88 |
| R500 | kill gold (team) | 150 | 390 |

## v53 losses, no deaths either side by R250 (pure economy) — 7 games

| Window | Metric | Us | Opponent |
|---|---|---:|---:|
| R100 | dead share of champion-rounds | 0.00 | 0.00 |
| R100 | camp-attack share of alive rounds | 0.25 | 0.34 |
| R100 | cast-only share | 0.05 | 0.05 |
| R100 | PvP-attack share | 0.01 | 0.03 |
| R100 | moving, no attack share | 0.47 | 0.43 |
| R100 | stationary off-spawn, no attack share | 0.16 | 0.12 |
| R100 | on-spawn share | 0.04 | 0.04 |
| R100 | banking share | 0.00 | 0.01 |
| R100 | capture gold per actor | 40 | 106 |
| R100 | capture gold per 100 alive champion-rounds | 40 | 106 |
| R100 | capture gold per attack/cast round | 1.64 | 2.47 |
| R100 | capture events per actor | 0.67 | 1.00 |
| R100 | shared-capture fraction | 0.00 | 0.00 |
| R100 | actors with no capture yet | 2 | 1 |
| R100 | actors with Treasure emblem | 0 | 1 |
| R100 | emblems per actor | 0.00 | 0.33 |
| R100 | kill gold (team) | 0.00 | 0.00 |
| R250 | dead share of champion-rounds | 0.00 | 0.00 |
| R250 | camp-attack share of alive rounds | 0.21 | 0.33 |
| R250 | cast-only share | 0.04 | 0.06 |
| R250 | PvP-attack share | 0.01 | 0.01 |
| R250 | moving, no attack share | 0.35 | 0.38 |
| R250 | stationary off-spawn, no attack share | 0.29 | 0.15 |
| R250 | on-spawn share | 0.02 | 0.04 |
| R250 | banking share | 0.00 | 0.01 |
| R250 | capture gold per actor | 120 | 285 |
| R250 | capture gold per 100 alive champion-rounds | 48 | 114 |
| R250 | capture gold per attack/cast round | 2.28 | 2.93 |
| R250 | capture events per actor | 2.00 | 2.33 |
| R250 | shared-capture fraction | 0.00 | 0.00 |
| R250 | actors with no capture yet | 0 | 0 |
| R250 | actors with Treasure emblem | 0 | 1 |
| R250 | emblems per actor | 0.00 | 1.00 |
| R250 | kill gold (team) | 0.00 | 0.00 |
| R500 | dead share of champion-rounds | 0.00 | 0.00 |
| R500 | camp-attack share of alive rounds | 0.21 | 0.26 |
| R500 | cast-only share | 0.05 | 0.06 |
| R500 | PvP-attack share | 0.01 | 0.02 |
| R500 | moving, no attack share | 0.43 | 0.41 |
| R500 | stationary off-spawn, no attack share | 0.25 | 0.17 |
| R500 | on-spawn share | 0.03 | 0.04 |
| R500 | banking share | 0.01 | 0.01 |
| R500 | capture gold per actor | 218 | 701 |
| R500 | capture gold per 100 alive champion-rounds | 48 | 140 |
| R500 | capture gold per attack/cast round | 2.19 | 4.30 |
| R500 | capture events per actor | 3.40 | 5.33 |
| R500 | shared-capture fraction | 0.00 | 0.00 |
| R500 | actors with no capture yet | 0 | 0 |
| R500 | median first purchase round | 164 | 123 |
| R500 | actors with Treasure emblem | 0 | 3 |
| R500 | emblems per actor | 1.00 | 1.67 |
| R500 | kill gold (team) | 0.00 | 0.00 |

## v52 losses — 40 games

| Window | Metric | Us | Opponent |
|---|---|---:|---:|
| R100 | dead share of champion-rounds | 0.00 | 0.00 |
| R100 | camp-attack share of alive rounds | 0.20 | 0.27 |
| R100 | cast-only share | 0.04 | 0.05 |
| R100 | PvP-attack share | 0.01 | 0.01 |
| R100 | moving, no attack share | 0.50 | 0.47 |
| R100 | stationary off-spawn, no attack share | 0.17 | 0.12 |
| R100 | on-spawn share | 0.04 | 0.05 |
| R100 | banking share | 0.00 | 0.00 |
| R100 | capture gold per actor | 56 | 79 |
| R100 | capture gold per 100 alive champion-rounds | 57 | 81 |
| R100 | capture gold per attack/cast round | 2.03 | 2.20 |
| R100 | capture events per actor | 0.80 | 0.78 |
| R100 | shared-capture fraction | 0.00 | 0.00 |
| R100 | actors with no capture yet | 2.00 | 2.00 |
| R100 | actors with Treasure emblem | 0.00 | 1.00 |
| R100 | emblems per actor | 0.00 | 0.20 |
| R100 | kill gold (team) | 0.00 | 0.00 |
| R250 | dead share of champion-rounds | 0.06 | 0.05 |
| R250 | camp-attack share of alive rounds | 0.19 | 0.22 |
| R250 | cast-only share | 0.05 | 0.05 |
| R250 | PvP-attack share | 0.02 | 0.02 |
| R250 | moving, no attack share | 0.48 | 0.50 |
| R250 | stationary off-spawn, no attack share | 0.18 | 0.15 |
| R250 | on-spawn share | 0.03 | 0.04 |
| R250 | banking share | 0.01 | 0.01 |
| R250 | capture gold per actor | 136 | 217 |
| R250 | capture gold per 100 alive champion-rounds | 61 | 89 |
| R250 | capture gold per attack/cast round | 2.57 | 2.97 |
| R250 | capture events per actor | 2.00 | 2.00 |
| R250 | shared-capture fraction | 0.00 | 0.00 |
| R250 | actors with no capture yet | 0.50 | 0.00 |
| R250 | actors with Treasure emblem | 0.00 | 2.00 |
| R250 | emblems per actor | 0.40 | 0.83 |
| R250 | kill gold (team) | 0.00 | 126 |
| R500 | dead share of champion-rounds | 0.07 | 0.05 |
| R500 | camp-attack share of alive rounds | 0.18 | 0.23 |
| R500 | cast-only share | 0.05 | 0.05 |
| R500 | PvP-attack share | 0.02 | 0.02 |
| R500 | moving, no attack share | 0.48 | 0.50 |
| R500 | stationary off-spawn, no attack share | 0.18 | 0.16 |
| R500 | on-spawn share | 0.03 | 0.04 |
| R500 | banking share | 0.01 | 0.01 |
| R500 | capture gold per actor | 326 | 533 |
| R500 | capture gold per 100 alive champion-rounds | 69 | 114 |
| R500 | capture gold per attack/cast round | 3.10 | 4.02 |
| R500 | capture events per actor | 4.00 | 4.55 |
| R500 | shared-capture fraction | 0.00 | 0.00 |
| R500 | actors with no capture yet | 0.00 | 0.00 |
| R500 | median first purchase round | 166 | 134 |
| R500 | actors with Treasure emblem | 0.00 | 3.00 |
| R500 | emblems per actor | 1.45 | 1.80 |
| R500 | kill gold (team) | 100 | 220 |

## top-team reference wins (us = winner) — 11 games

| Window | Metric | Us | Opponent |
|---|---|---:|---:|
| R100 | dead share of champion-rounds | 0.00 | 0.00 |
| R100 | camp-attack share of alive rounds | 0.41 | 0.28 |
| R100 | cast-only share | 0.07 | 0.05 |
| R100 | PvP-attack share | 0.00 | 0.00 |
| R100 | moving, no attack share | 0.36 | 0.44 |
| R100 | stationary off-spawn, no attack share | 0.11 | 0.11 |
| R100 | on-spawn share | 0.04 | 0.04 |
| R100 | banking share | 0.00 | 0.00 |
| R100 | capture gold per actor | 107 | 90 |
| R100 | capture gold per 100 alive champion-rounds | 107 | 90 |
| R100 | capture gold per attack/cast round | 2.29 | 2.37 |
| R100 | capture events per actor | 0.83 | 0.50 |
| R100 | shared-capture fraction | 0.29 | 0.00 |
| R100 | actors with no capture yet | 3 | 3 |
| R100 | actors with Treasure emblem | 1 | 1 |
| R100 | emblems per actor | 0.50 | 0.40 |
| R100 | kill gold (team) | 0.00 | 0.00 |
| R250 | dead share of champion-rounds | 0.00 | 0.05 |
| R250 | camp-attack share of alive rounds | 0.33 | 0.32 |
| R250 | cast-only share | 0.06 | 0.05 |
| R250 | PvP-attack share | 0.01 | 0.03 |
| R250 | moving, no attack share | 0.41 | 0.44 |
| R250 | stationary off-spawn, no attack share | 0.12 | 0.13 |
| R250 | on-spawn share | 0.03 | 0.04 |
| R250 | banking share | 0.01 | 0.00 |
| R250 | capture gold per actor | 307 | 270 |
| R250 | capture gold per 100 alive champion-rounds | 123 | 110 |
| R250 | capture gold per attack/cast round | 2.96 | 3.50 |
| R250 | capture events per actor | 2.00 | 2.00 |
| R250 | shared-capture fraction | 0.25 | 0.00 |
| R250 | actors with no capture yet | 1 | 1 |
| R250 | actors with Treasure emblem | 3 | 2 |
| R250 | emblems per actor | 1.40 | 1.20 |
| R250 | kill gold (team) | 100 | 0.00 |
| R500 | dead share of champion-rounds | 0.06 | 0.08 |
| R500 | camp-attack share of alive rounds | 0.31 | 0.27 |
| R500 | cast-only share | 0.06 | 0.05 |
| R500 | PvP-attack share | 0.02 | 0.02 |
| R500 | moving, no attack share | 0.44 | 0.46 |
| R500 | stationary off-spawn, no attack share | 0.13 | 0.14 |
| R500 | on-spawn share | 0.03 | 0.04 |
| R500 | banking share | 0.01 | 0.00 |
| R500 | capture gold per actor | 636 | 588 |
| R500 | capture gold per 100 alive champion-rounds | 127 | 124 |
| R500 | capture gold per attack/cast round | 3.79 | 4.11 |
| R500 | capture events per actor | 4.80 | 4.20 |
| R500 | shared-capture fraction | 0.29 | 0.23 |
| R500 | actors with no capture yet | 0 | 0 |
| R500 | median first purchase round | 130 | 137 |
| R500 | actors with Treasure emblem | 3 | 3 |
| R500 | emblems per actor | 2.17 | 2.40 |
| R500 | kill gold (team) | 366 | 253 |

## Capture gold by R250 per champion type (v53 games)

| Type | Our actors | Our median gold | Our zero-capture share | Opp actors | Opp median gold |
|---|---:|---:|---:|---:|---:|
| Vendetta | 74 | 210.0 | 0.01 | 49 | 120 |
| Varg | 60 | 160.0 | 0.00 | 14 | 210.0 |
| Marcella | 58 | 125.0 | 0.09 | 54 | 80.0 |
| Ren | 48 | 130.0 | 0.10 | 6 | 445.0 |
| Ryth | 22 | 120.0 | 0.32 | 47 | 100 |
| Prism | 21 | 110 | 0.38 | 7 | 0 |
| Vesper | 19 | 186 | 0.16 | 72 | 355.0 |
| Cassi | 18 | 145.0 | 0.33 | 3 | 40 |
| Issac | 18 | 175.0 | 0.11 | 3 | 0 |
| Tavi | 13 | 90 | 0.38 | 11 | 160 |
| Heart | 4 | 90.0 | 0.00 | 65 | 150 |
| Willow | 1 | 80 | 0.00 | 7 | 40 |
| Stellar | 0 | - | 0.00 | 3 | 120 |

