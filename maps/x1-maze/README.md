# x1 maze maps (stand-in for Agent 2's unseen maze set)

Agent 2's maze-test / real200b maps never reached GitHub, and unseen maze-style maps are where v88 beat x1. Two
independently generated sets stand in for them:

- **Set A, `pc_maze_*` (PC):** `python tools/maze/gen_maze.py --out maps/x1-maze --count 30 --seed 7 --prefix pc_maze`
  (recursive-backtracker maze, corridors 1-3 wide, 10-30% loops, camps from the official groups in carved rooms,
  symmetric, reachability-repaired, engine-verified). 29 maps: pc_maze_13 dropped (games hit round 2000 unfinished).
  Parameters per map: `pc_maze_meta.json`.
- **Set B, `g5060_maze_*` (5060, job J015):** its own generator; see README_g5060.md when it lands.

First play (x1 vs x2, all 30, both sides): 25/60 wins, 0 faults, 165 fuel-outs (2.75 a game; ladder ~0.8), median
finish round 814. `tools/x1_gate.sh` adds the maze cell automatically when this folder exists.

| map | sha256 (16) | size | team | corridor |
|---|---|---|---|---|
| pc_maze_00.map26a | b686441483f0d754 | 62x59 | 5 | 3 |
| pc_maze_01.map26a | 955bdb08f4fd9cb6 | 59x59 | 5 | 2 |
| pc_maze_02.map26a | caaece1b2f51e175 | 41x41 | 4 | 1 |
| pc_maze_03.map26a | b62a042307642f86 | 54x54 | 5 | 1 |
| pc_maze_04.map26a | b33bc8a812dba0b7 | 71x71 | 5 | 2 |
| pc_maze_05.map26a | 8e273d0fbc9179a7 | 45x46 | 5 | 3 |
| pc_maze_06.map26a | e05f49c306102bbe | 57x58 | 5 | 3 |
| pc_maze_07.map26a | 9989d35a67135a6f | 57x57 | 5 | 1 |
| pc_maze_08.map26a | aa29e277fd64ff81 | 77x77 | 5 | 1 |
| pc_maze_09.map26a | bcb51c6af6107110 | 60x60 | 5 | 2 |
| pc_maze_10.map26a | 160d3b2d1ac08f6a | 55x68 | 5 | 1 |
| pc_maze_11.map26a | d233d8985d6001dd | 53x48 | 5 | 3 |
| pc_maze_12.map26a | eaff492df54b8c5e | 59x60 | 5 | 2 |
| pc_maze_14.map26a | 915d7364540942d8 | 56x56 | 5 | 2 |
| pc_maze_15.map26a | 1ea0f2409ed41215 | 48x48 | 3 | 3 |
| pc_maze_16.map26a | 5e432437e1312621 | 71x71 | 5 | 1 |
| pc_maze_17.map26a | cda67648084c4b5a | 54x54 | 5 | 1 |
| pc_maze_18.map26a | 06e4f01e38e2493d | 63x51 | 5 | 2 |
| pc_maze_19.map26a | a91d37f292468b04 | 57x50 | 5 | 1 |
| pc_maze_20.map26a | dc6d40554ebcace0 | 41x40 | 5 | 2 |
| pc_maze_21.map26a | 1c0e54c065483c14 | 50x50 | 5 | 2 |
| pc_maze_22.map26a | 3e84c233846e198a | 67x67 | 5 | 3 |
| pc_maze_23.map26a | 005620ea149b2375 | 60x60 | 5 | 1 |
| pc_maze_24.map26a | 4c0982dc7c106e80 | 51x51 | 5 | 2 |
| pc_maze_25.map26a | 8e05f36351da47c7 | 75x57 | 5 | 1 |
| pc_maze_26.map26a | f688008e5c91b560 | 49x49 | 5 | 1 |
| pc_maze_27.map26a | d8387e82a45d5ab0 | 56x56 | 5 | 3 |
| pc_maze_28.map26a | cfca88e79837a3c1 | 58x58 | 5 | 1 |
| pc_maze_29.map26a | ddef0099b0190df8 | 46x46 | 5 | 3 |
