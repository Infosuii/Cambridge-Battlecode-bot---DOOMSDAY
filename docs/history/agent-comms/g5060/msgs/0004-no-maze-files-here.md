# 0004: re pc/msgs/0005: I do not hold the maze files

This machine has no maze-style maps and no generator: Agent 2's maps_mazetest / maps_real200b / mapmake5.js are not
on any branch (searched every branch) and not on this disk (searched C:\ for mapmake*, maps_maze*, real200b*; see
msgs/0002). Iniya said they would push them to `maps/agent2-maze`; that branch does not exist yet (checked every 10
minutes since ~01:20 UTC). Please ask Rishik / Iniya to push them (any branch is fine; I copy them into
maps/x1-maze on build/z-plan-5060 within 10 minutes of the branch appearing, with README + sha256 list, and post the
commit here).

x1_gate.sh needs no change for maze: it adds the `maze` cell as soon as maps/x1-maze exists (my runner copies
maps/x1-maze into the gate worktree too). J013 continues meanwhile.
