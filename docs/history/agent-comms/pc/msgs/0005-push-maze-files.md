# Push the maze files now (from Rishik, via PC)

Rishik asks: push the maze files to git now, don't wait for Iniya's `maps/agent2-maze` branch.

What to push, to **build/z-plan-5060** (your branch; not main, not build/z-plan):
1. `maps/x1-maze/`: the maze-style maps you have (maze-test 0-59 and real200b 50-109, or whatever you hold), as
   `.map26a` files.
2. The generator / runner files that made or run them (e.g. `mapmake5.js` and any script that builds or plays the
   set), under `tools/maze/`, with a short `maps/x1-maze/README.md`: source, generator command and seed, map count,
   sha256 list.
3. If `tools/x1_gate.sh` needs a change to run the maze set on your machine, push that too and say what changed.

Order: do this between two J013 lines (it takes a minute; don't stop the gate). Then post the commit hash in
g5060/STATUS.md. The PC will copy `maps/x1-maze` into build/z-plan so every gate (both machines) adds the maze set,
and will re-run the key lines (bp, best J013 lines) on maze.

If you don't hold the files locally (only Iniya does), say so in STATUS and the PC will ask Rishik to get them pushed.
