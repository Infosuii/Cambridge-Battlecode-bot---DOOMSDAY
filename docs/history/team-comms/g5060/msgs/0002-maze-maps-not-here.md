# 0002: J004 maze maps are not on this machine or any branch

Agent 2's maze maps (`v4/maps_maze` seed 55500000, `v4/maps_mazetest` seed 55800000, `v4/maps_real200b` seed 99500000)
and their generator (`tools/viz/mapmake5.js MAZE=1`, EXPERIMENTS.md E61) live only in Agent 2's local workspace
(`...\Videos\Default Project 2\v4`). None of them is on any branch (searched every branch for mapmake*, maze, real200b),
and they are not on this disk.

Options: (a) whoever has Agent 2's workspace pushes maps_mazetest 0-59 + maps_real200b 50-109 (or mapmake5.js),
then I commit them to maps/x1-maze on build/z-plan-5060; (b) the PC builds a maze-style set with tools/mapgen as J004
says. Until then every gate runs ladder + styled only (x1_gate.sh skips maze when maps/x1-maze is missing), and I mark
the maze cell as owed in each result.

Moving on to J005 (branch farm) now.
