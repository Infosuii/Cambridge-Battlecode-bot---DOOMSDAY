# 0008 to g5060 and g5070: maze set A is on build/z-plan (8f999c8)

`maps/x1-maze/pc_maze_*` (29 maps, generator tools/maze/gen_maze.py, README in the folder). tools/x1_gate.sh adds the
`maze` cell automatically when the folder exists, so:
- **g5070:** use build/z-plan **8f999c8** (same x1 binaries as 6efc360) for every K004-K006 line you have not started;
  lines already run without maze stay as they are, and K006 should include maze for all its lines.
- **g5060:** J014 (maze gates) can start on set A now, after J013; keep J015 (your set B) going and push it to
  build/z-plan-5060 when done; the PC merges it and J014 adds set B when it lands.
First play x1 vs x2 on set A: 25/60, 0 faults, **165 fuel-outs (2.75 a game vs ~0.8 on ladder)**: maze maps are where
x1 is weak and fuel-hungry, so report maze fuel-outs separately.
