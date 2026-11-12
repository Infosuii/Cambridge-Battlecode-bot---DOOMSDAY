# Maze set B (`g5060_maze_*`, 5060, comms/x1 J015)

Independent of set A (`pc_maze_*`, tools/maze/gen_maze.py, recursive backtracker). Generator:
`tools/maze/gen_maze_g5060.py` (engine 2.0.0 MapBuilder via tools/mapgen; integrity check + the game must load).

```
python tools/maze/gen_maze_g5060.py --out artifacts/tmp/mazeB-cand --count 40 --seed 5060
python tools/dz.py smoke --name g5060-mazeB-screen --pool --map-dir artifacts/tmp/mazeB-cand --opponent x1 --candidate-bot x1
```

Design (differs from set A on purpose):
- **Rooms first**, 2-5 open rectangles of 2-4 x 2-4 maze cells, each pre-joined as one node.
- **Randomized Kruskal** maze over the cell grid (pitch = corridor 1-3 + 1 wall) with the rooms as nodes: many short
  dead ends rather than a backtracker's long winding corridors; then 10-30% of the closed cell walls reopened (loops).
- **Cave variant** on about a third of the 2-3-wide maps: corridor tiles touching a wall become wall with p = 0.2
  (outside rooms), giving ragged corridors with 1-wide chokes.
- **Camps** in rooms (70%) or at maze junctions (cells with 3+ links); official groups with exact member types and
  offsets. Count per half = area / 2 x the official median group density x U(0.7, 1.5), capped at the official
  maximum (pc/msgs/0009): full-map density 0.0027-0.0062 vs official median 0.0046, max 0.0202.
- Symmetry rotational, or reflective on square maps; team size and spawn rectangle from an official template;
  bushes 1-4% of corridors, holes 0-5% of walls; repair knocks walls (with their mirror) until every open tile, camp
  and altar is reachable from both spawns.

Screen: x1 (1746f2bb7fa3) vs itself, both sides, on 40 candidates: 0 faults; 5 rejected because a game hit round
2000 unfinished (candidates 07, 11, 14, 21, 34); the first 30 passing kept and renumbered 00-29 (5 unused passers).
Screen fuel-outs on the 30: **32 in 60 games (0.53 a game)**, vs set A's 2.75 a game (x1 vs x2) and ~0.8 on ladder.
Per-map parameters, candidate id, sha256 and screen rounds / fuel-outs: `g5060_maze_meta.json`.

| map | sha256 (16) | size | symmetry | team | corridor | caves | rooms | groups/half | group density | walls | screen max round | screen fuel-outs (2 games) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| g5060_maze_00.map26a | efa33411d6776255 | 66x66 | horizontal | 5 | 1 | no | 3 | 7 | 0.0032 | 43% | 1089 | 0 |
| g5060_maze_01.map26a | f3bf536500071579 | 52x52 | rotational | 5 | 2 | yes | 2 | 6 | 0.0044 | 39% | 1017 | 2 |
| g5060_maze_02.map26a | ed18eee55be52a49 | 52x52 | rotational | 5 | 1 | no | 4 | 8 | 0.0059 | 33% | 1175 | 0 |
| g5060_maze_03.map26a | bbd5c251d70afdd7 | 46x49 | rotational | 5 | 1 | no | 2 | 5 | 0.0044 | 40% | 1152 | 0 |
| g5060_maze_04.map26a | dfadc9b0aaabd975 | 41x40 | rotational | 4 | 2 | no | 2 | 4 | 0.0049 | 30% | 1098 | 0 |
| g5060_maze_05.map26a | a5bbb9fa62be8220 | 65x65 | rotational | 5 | 2 | no | 3 | 6 | 0.0028 | 31% | 1086 | 3 |
| g5060_maze_06.map26a | b42d8d9aee9e90e7 | 65x72 | rotational | 5 | 2 | no | 2 | 12 | 0.0051 | 27% | 681 | 2 |
| g5060_maze_07.map26a | 389a10d72599623f | 66x74 | rotational | 5 | 3 | yes | 5 | 15 | 0.0061 | 29% | 814 | 3 |
| g5060_maze_08.map26a | 46ee31d8cfc690ff | 51x51 | vertical | 5 | 2 | no | 5 | 5 | 0.0038 | 29% | 992 | 0 |
| g5060_maze_09.map26a | 78b71cfef669949b | 66x66 | horizontal | 5 | 2 | yes | 5 | 13 | 0.0060 | 32% | 919 | 2 |
| g5060_maze_10.map26a | 82e0367e29b73245 | 65x72 | rotational | 5 | 1 | no | 5 | 8 | 0.0034 | 41% | 701 | 0 |
| g5060_maze_11.map26a | 0b72e83648611d21 | 62x51 | rotational | 5 | 2 | no | 5 | 7 | 0.0044 | 26% | 927 | 2 |
| g5060_maze_12.map26a | 776785f8387290e0 | 52x52 | rotational | 5 | 2 | no | 5 | 5 | 0.0037 | 28% | 1382 | 0 |
| g5060_maze_13.map26a | 40911245536a1795 | 49x49 | rotational | 5 | 3 | no | 2 | 6 | 0.0050 | 19% | 528 | 0 |
| g5060_maze_14.map26a | 0a023ea98323411f | 40x42 | rotational | 4 | 2 | yes | 2 | 5 | 0.0060 | 39% | 754 | 0 |
| g5060_maze_15.map26a | dfa5dd17d2738d12 | 44x44 | rotational | 5 | 2 | no | 4 | 3 | 0.0031 | 25% | 1283 | 0 |
| g5060_maze_16.map26a | 38c0a6aaf94b8bf6 | 56x58 | rotational | 5 | 2 | no | 4 | 10 | 0.0062 | 25% | 1086 | 1 |
| g5060_maze_17.map26a | 1079ca8b141fb97d | 48x48 | vertical | 5 | 2 | yes | 2 | 6 | 0.0052 | 38% | 769 | 3 |
| g5060_maze_18.map26a | 01ae1d24846b550d | 62x62 | rotational | 5 | 2 | no | 3 | 9 | 0.0047 | 31% | 618 | 1 |
| g5060_maze_19.map26a | 7b597a7b6c18f71c | 61x59 | rotational | 5 | 3 | yes | 2 | 11 | 0.0061 | 28% | 942 | 3 |
| g5060_maze_20.map26a | f48e125fc48c4154 | 65x65 | vertical | 5 | 2 | no | 4 | 12 | 0.0057 | 29% | 865 | 3 |
| g5060_maze_21.map26a | 44fc70bef2f3c78e | 41x41 | rotational | 5 | 3 | yes | 4 | 3 | 0.0036 | 23% | 742 | 1 |
| g5060_maze_22.map26a | a8550f84a0cb3c21 | 46x46 | rotational | 4 | 2 | no | 5 | 5 | 0.0047 | 24% | 1101 | 0 |
| g5060_maze_23.map26a | 94bb6adc555e309e | 44x43 | rotational | 5 | 1 | no | 2 | 4 | 0.0042 | 39% | 1284 | 0 |
| g5060_maze_24.map26a | 3431dc8efc4a874e | 51x51 | horizontal | 4 | 3 | no | 2 | 7 | 0.0054 | 25% | 1388 | 0 |
| g5060_maze_25.map26a | 3d770251d3d631f5 | 62x63 | rotational | 5 | 2 | yes | 3 | 11 | 0.0056 | 36% | 629 | 1 |
| g5060_maze_26.map26a | 3b6f288e6a2a41fd | 40x40 | vertical | 5 | 3 | yes | 3 | 4 | 0.0050 | 30% | 1426 | 0 |
| g5060_maze_27.map26a | 066781717437bb77 | 55x55 | horizontal | 5 | 2 | yes | 5 | 8 | 0.0053 | 33% | 1323 | 1 |
| g5060_maze_28.map26a | 860d3aaa4f77aff3 | 49x49 | horizontal | 5 | 2 | no | 3 | 7 | 0.0058 | 26% | 1117 | 0 |
| g5060_maze_29.map26a | 681720eac83f54a1 | 79x79 | rotational | 5 | 2 | yes | 5 | 17 | 0.0054 | 37% | 574 | 4 |
