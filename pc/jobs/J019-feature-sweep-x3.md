id: J019
title: re-fit EVERY dropped feature onto x3 (= v92): screen, refine, promote or abort (Rishik: max search effort)
commit: build/z-plan head (research/x1/FEATURE_SWEEP_X3.md = the full list, protocol and status table)
priority: FIRST, right after J018 finishes (or stop J018 now if it has > 30 min left and post its partial table).
Protocol (FEATURE_SWEEP_X3.md):
  screen = bash tools/x1_gate.sh x3 TAG "SETS" with OPPS="v92" SETS="pool" (172 games); x3 plain = 86/172.
  >= 92 -> full: OPPS="v92 v86h x1bru" SETS="pool styled maze", sign test vs x3 plain (you have x3 plain from J018).
  81-91 -> refine: up to 3 more variants (parameter around the best, + --set X1_WALKTAIL=3 when fuel-outs rose,
           + the best partner), then decide. <= 80 after refinement -> abort with the reason.
Rows for you: 1-26, 28, 30 (your I-60-04 conversion fix on x3). Use the variants listed per row; add more where a
refinement looks promising — do not stop at the first failure. Run the cheapest screens first, in row order.
Report: one line per variant on comms as it finishes (tag, wins/172, fuel-outs), and keep
g5060/results/J019.md as the table; mark each row promote / refine / abort in your copy.
At the end: greedy stack of all promoted rows (best first; keep each only if the stack gains on the full gate).
The PC does rows 27, 29, 31-34 (new code) and will add rows as features appear.

addendum (PC): rows 35 X1_CORNERED (N=2/3/5) and 36 X1_FIRSTFIELD=1 added to FEATURE_SWEEP_X3.md; screen them on pool vs v92 with the rest. Do not drop row 35 on its one-map result.
