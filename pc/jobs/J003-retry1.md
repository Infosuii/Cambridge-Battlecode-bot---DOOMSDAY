id: J003
title: retry round 1 for X1_SECURE and X1_ALONE (research/x1/RETRY_QUEUE.md #1, #2)
commit: latest build/z-plan
bot: x1
run: gate (tools/x1_gate.sh), one gate per line below
opponents: x2 x2-s2
maps: ladder styled maze (maze once J004 lands; run ladder + styled first)
priority: 3
switches:
  base:      (no switches)            -> tag base   (the gate baseline every other line is compared with)
  secure15:  --set X1_SECURE=1 --set X1_SECURE_MULT=1.5f
  secure3:   --set X1_SECURE=1
  secure6:   --set X1_SECURE=1 --set X1_SECURE_MULT=6.0f
  alone:     --set X1_ALONE=1
done when: g5060/results/J003.md: per line and cell wins vs base, fuel-outs, verdict by the gate rule.
(X1_ALONE radius variants need code knobs; the PC posts them as J005 after adding X1_ALONE_ALLY / X1_ALONE_ENEMY.)
