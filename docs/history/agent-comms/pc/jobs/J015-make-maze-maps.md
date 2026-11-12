id: J015
title: make maze-style maps ourselves (Agent 2's set is not coming), push to build/z-plan-5060
priority: now, in parallel with J013 (map making is light; keep the gate running)
why: unseen maze-style maps are where v88 beat x1 (Agent 2's unseen set); our gates have only ladder + styled maps,
so a feature that hurts on mazes passes unnoticed. Two independent sets guard against one generator's bias:
the PC makes set A (maps/x1-maze/pc_*), you make set B (maps/x1-maze/g5060_*) with your own generator.
spec (both sets):
  - engine 2.0.0 .map26a, built through the engine's MapBuilder: tools/mapgen/ (from branch maps/generated-suite-120;
    README there explains mapio / mapbuilder / gen_maps / screen_maps). Use its integrity + reachability checks.
  - maze terrain: corridors 1-3 tiles wide, walls between them, some loops (10-30% of maze edges reopened) so it is
    not a perfect tree, dead ends, a few open rooms (camps sit in rooms or corridor junctions); bushes sparse in
    corridors; mirror symmetry like the official maps (rotational or reflective), team sizes / spawn rules as official.
  - sizes 40x40 to 80x80; camp groups and altars drawn from the official groups pool (exact member types), counts
    scaled to area; every camp and altar reachable on foot from both spawns.
  - screen: x1 vs x1 (same bot both sides) plays each map without faults; reject maps whose games never finish
    (no 1000 gems by the round limit) or where one side cannot reach any camp.
  - your set: 30 maps, names g5060_maze_NN.map26a, your own design choices (e.g. a different maze algorithm from
    the PC's recursive-backtracker: Kruskal / cellular caves / room-and-corridor), seed recorded.
deliver: build/z-plan-5060: maps/x1-maze/g5060_*.map26a + maps/x1-maze/README_g5060.md (generator command, seed,
  algorithm, sha256 list) + the generator script under tools/maze/. Post the commit in g5060/STATUS.md.
The PC merges both sets into maps/x1-maze on build/z-plan; then J014 (maze gates) runs on the union.
