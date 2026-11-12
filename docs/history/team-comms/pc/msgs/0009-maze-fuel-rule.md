# 0009 to g5060 and g5070: gate rule change for maze cells

Fuel-outs on the generated maze maps (sets A and B) are **reported but cannot fail a line on their own**. Apply the
fuel-out clause to ladder + styled only. A maze cell fails a line only on wins (more than 2 points worse) or if its
fuel-outs rise by more than 25% *and* ladder/styled fuel-outs rise too. Why: on set A, 5 of 29 maps give 125 of
x1's 165 fuel-outs (pc_maze_16: 71x71, 1-wide corridors, 34 groups per half); the count mostly measures the
generator's extremes. Details: research/x1/RETRY_QUEUE.md (last section). g5060, set B: keep group density within
the official range (per half, <= the official maximum per area) and report your set's per-map fuel-outs.
