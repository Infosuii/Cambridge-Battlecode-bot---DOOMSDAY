id: J004
title: maze-style map set
run: other
priority: 1 (blocking for every gate's maze cell)
steps:
  Agent 2 (Iniya's machine) tested on maze-test 0-59 and real200b 50-109 maps. If you have them (or can ask), put
  them in maps/x1-maze (*.map26a) on build/z-plan-5060 and post the list and their sha256 in g5060/results/J004.md.
  If they cannot be had by 2 Nov 12:00, post g5060/msgs saying so; the PC will build a maze-style set with the
  repo's map generator instead.
done when: maps/x1-maze exists on build/z-plan-5060 and the PC has cherry-picked it into build/z-plan.
