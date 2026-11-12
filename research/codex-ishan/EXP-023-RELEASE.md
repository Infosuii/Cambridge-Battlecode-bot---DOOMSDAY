# EXP-023 release result

Both release builds matched SHA-256 a494830ff4829a79fc0d37d480889aa909dd2f8be31d48a725fae29de0e8e854. Switch-off reproduced platform v80 / repo v92, SHA-256 5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47. The first compile used two coordinate arguments for a helper that accepts one vec2. The corrected source passes the coordinates as a vec2 in both independently built directories.

The [charged dev profile](RUNTIME_WARD_DETAIL_CODEX-SIEGE-RAYS.json) recorded siege-preparation overruns in the same 17 cells as v92. Total native fuel-outs in the diagnostic were 111 versus 118. In one matched round-two trail, 46,903 fuel remained after the suspension, compared with 31,790 before the change. The ray table can lower work without preventing the specific suspension.

The [172-cell release screen](SIEGE-RAYS_POOL_SAFETY.json) recorded 87 versus 86 wins, b/c 5/4, +0.581 pp (95% map-cluster interval -2.326 to +3.488). Fuel suspensions were 156 vs 160, with two cells increasing, one from zero. Both arms had 28 round-one suspensions, no round-one cell increases, zero faults and no diagnostic codes.

Reject at L0. The total reduction does not satisfy the per-cell gate, and the targeted dev crossings did not decrease. No L1, L2, ladder or holdout use.
