# EXP-043 counter-ambush guard result

The exact release retained both original ward placements and defensive moves, reduced native suspensions from two to zero and kept all eight frozen controls clean. There were no faults or diagnostic codes. Two clean builds reproduced SHA-256 `58533151c13b3f7d3392bb8c1f6c0618d223b4e420a3fcc1831c25a3e8dd2e75`, and all switches off reproduced v92. [Development fixture](PG_AMBUSH_DEV.json), [hashes](PG_AMBUSH_BUILDS.json).

Across the 172 paired official-pool games it won 90 versus 86 for v92, b/c 37/33. Fuel suspensions were 47 versus 160, including 16 versus 28 in round one. Five previously clean cells suspended, with zero round-one increases, faults or diagnostic codes. The release failed L0. L1, L2 and ladder tests were not run. [Safety results](PG-AMBUSH_POOL_SAFETY.json).
