# Maze set B: the 10 candidates not in maps/x1-maze

Same generator run as set B (tools/maze/gen_maze_g5060.py --count 40 --seed 5060; candidate names as generated).
Kept for reference only; **not in any gate** (x1_gate.sh reads maps/x1-maze). Per-candidate parameters are in
maps/x1-maze/g5060_maze_meta.json under `rejected_by_screen` / `unused_passing` (by candidate id in artifacts).

| file | sha256 (16) | why not in set B | screen max round | screen fuel-outs (2 games) |
|---|---|---|---|---|
| g5060_maze_07_cand.map26a | 3aa40e29f1e1f8cf | rejected: a self-play game reached R2000 unfinished | 2000 | 0 |
| g5060_maze_11_cand.map26a | 9c7f1c08ebe98166 | rejected: a self-play game reached R2000 unfinished | 2000 | 0 |
| g5060_maze_14_cand.map26a | 87069b655e6085f4 | rejected: a self-play game reached R2000 unfinished | 2000 | 0 |
| g5060_maze_21_cand.map26a | 3955fbac362446ec | rejected: a self-play game reached R2000 unfinished | 2000 | 0 |
| g5060_maze_34_cand.map26a | c04d34c4722c42de | rejected: a self-play game reached R2000 unfinished | 2000 | 0 |
| g5060_maze_35_cand.map26a | 3f409737d626ca24 | passed the screen; not needed (first 30 kept) | 979 | 0 |
| g5060_maze_36_cand.map26a | edb9d6c5116db987 | passed the screen; not needed (first 30 kept) | 981 | 0 |
| g5060_maze_37_cand.map26a | b5d15b560d2baed0 | passed the screen; not needed (first 30 kept) | 1908 | 0 |
| g5060_maze_38_cand.map26a | 7f6e839de0fa68fc | passed the screen; not needed (first 30 kept) | 919 | 0 |
| g5060_maze_39_cand.map26a | 123dfdee6057a920 | passed the screen; not needed (first 30 kept) | 1268 | 0 |
