# EXP-024 release result

Both clean builds match SHA-256 `e3b0f44990a8e35371061ba4f4b9eb3c0e0dba674ed5bf012e00e2aea9cb8ec7`. Switch-off reproduces platform v80 / repo v92, SHA-256 `5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47`.

The [charged 64-game diagnostic](RUNTIME_WARD_DETAIL_CODEX-SIEGE-LAZY.json) observed zero of the 17 v92 siege-preparation crossings, zero faults and 95 vs 118 native suspensions. The [release pool screen](SIEGE-LAZY_POOL_SAFETY.json) recorded 90/172 vs 86/172, b/c 11/7, zero faults or diagnostic codes, and 127 vs 160 suspensions. Both arms had 28 in round one with no round-one per-cell increases. One cell increased and no clean cell newly suspended.

Reject under the original per-cell gate. The mechanism improved and the total fell, but a single increase is enough to fail. No L1, L2, ladder use or holdout use.
