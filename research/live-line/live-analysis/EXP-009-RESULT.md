# EXP-009 result: exact labels, failed release safety

MEASURED: unsubmitted `codex-bushlinear`, release SHA-256 `c0a5134e6955c4b623d8d7c6bd83447fa1ff5d6b5ab8416195270145743494b2`, reproduced twice. Switches-off matched platform v80 / repo v92's local release `5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47`.

[Native equivalence](BUSH_EQUIVALENCE.json): 90 development maps, 261,510 tiles, 837 components, zero label/packing mismatches; restored bitboards matched. The 16 conformance maps are a subset of the 90, not additional independent maps. This fixture exports packed occupancy and runs the same fill helper against a separately implemented original SDK-membership flood. It validates components for row-major query order, not complete match trajectory equivalence.

**Performance limitation:** its aggregate fill + one final mask import cost 12,564,195 fuel versus reference 17,162,568 (−26.793%). The game integration imports the whole labelled mask after *each component*. The fixture omits that repeated cost; do not claim a 27% improvement in the actual game's labeller. A follow-up must measure the exact publication schedule on development inputs, with the full implementation charged.

[Official-pool L0](BUSHLINEAR_POOL_SAFETY.json), 172 pairs: candidate 85 wins versus baseline 86 (b/c=25/26, local descriptive only), 165 versus 160 fuel-outs, 15 cells increased and nine formerly clean cells now suspended. Round-one totals remained 28/28 with no per-cell increase. Zero faults and no diagnostic codes in either arm.

Verdict: reject; no L1/L2, holdout, ladder or promotion. Preserve this source/hash/result. A new development-only microbenchmark will separate full-mask publication overhead from fill cost before another candidate is proposed. No threshold or partition is changed based on pool cells.
