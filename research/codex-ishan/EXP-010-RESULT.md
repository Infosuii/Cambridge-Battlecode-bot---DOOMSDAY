# EXP-010 result

MEASURED: unsubmitted `codex-bushsparse`, release SHA-256 `16487a779846d9c12d9faba7d93f17a006769389cc847f23c3206dba37f547b2`, reproduced in two independent directories; disabling `CODEX_BUSH_LINEAR` reproduced platform v80 / repo v92's local `5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47`.

[Exact-publication fixture](BUSH_SPARSE_EQUIVALENCE.json): 90 development maps, 261,510 tiles, 837 components, zero component/packing mismatches; all resulting labelled masks equal the terrain mask after full traversal. The fixture now publishes each tile with the same SDK operation as the candidate. Aggregate optimized fuel 12,744,322 versus SDK reference 17,162,563. This is a component microbenchmark with sequential root queries, not a promise of lower match fuel or unchanged policy trajectories.

[Pool L0](BUSHSPARSE_POOL_SAFETY.json): 172 pairs, 86 wins each (local b/c 25/25), 166 versus 160 fuel-outs; 13 map/side increases, eight previously clean cells newly suspended. First-round totals 28/28, no first-round cell increase, zero faults and no diagnostic codes.

Verdict: reject. Faster equivalent component results did not yield a safer release on the unchanged gate. Neither this nor EXP-009 advances to L1/L2 or ladder. No more bush variants are justified by the pool outcomes. Return to new Discovery and measure whole-turn effects on development data before further runtime changes. No ladder quota used; holdout untouched.
