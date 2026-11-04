# EXP-053 exact movement findings

The movement-only diagnostic matched 17 of the 19 exact events by champion, round and cell. Two matched approach cases ran `counter_ambush()` in the original round, leaving 34,545 fuel at Marcella's R162 move and 45,956 at Cassi's R408 move. Both resumed a later move in the next round. They still occur in the exact EXP-052 build. These show that reserving only observation and tail can leave inadequate room for the new decision after that movement.

Three independently generated maps also had matched siege movements through `greedy_step()` at 2,068, 2,148 or 2,316 fuel, including one early case repeated against all four opponents. The exact EXP-052 tail guard already removes those particular events. The expensive siege setup can be investigated separately. [Movement trace](LARGE_ROSTER_MOVES.json), [exact turn inputs](LARGE_ROSTER_TURNS.json).
