# EXP-042 movement trace result

The movement diagnostic reproduced the exact visible champion and camp state and all recorded actions at both original rounds, ignoring the replay input ordinal. Native summaries identified the same suspending champion and round. The successful movement caller was `counter_ambush()` in both cases.

After the first move, Marcella had 9,156 fuel left and Vendetta had 18,559. The next `follow_field()` movement in each trace ran after the engine advanced a round. Between the two moves the source immediately calls `World::update()` to re-observe the map, then attempts the ordinary decision flow. This localizes both suspensions to the work after the first movement and before the second. It does not isolate the precise instruction where the engine ran out. [Native and movement trace](PG_DASH_MOVE.json).
