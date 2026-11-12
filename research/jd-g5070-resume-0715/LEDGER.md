# Experiment ledger

All policy code was frozen before final confirmation. Final results never feed tuning. Frozen v92 and x1 were preserved.

| Mechanism | Outcome | Evidence and next condition |
|---|---|---|
| Baseline reproduction | Accepted | Canonical WASM hash;96 paired cells exactly identical, no faults. |
| CONTACT3 + GOV5 | Conditionally useful (experimental) | Selection +5.88pp;2232-cell confirmation +4.435pp (95% map-cluster CI +2.240,+6.586),99 net wins. C2 loses6/48 cells on4 maps (CI -33.33,+4.17); universal promotion gate remains unmet. No tuning on that slice. |
| CONTACT3 + PROGRESS1 + GOV5 | Accepted (local evidence), not release-qualified | Selection +4.75pp; confirmation +84 net wins/2232 cells. Trails the simpler candidate (+99) in aggregate; selected for delivery because no category/opponent point estimate breaches the declared-10pp gate. Incremental routing benefit is inconclusive. No assumption that component gains add. |
| PROGRESS1 + GOV5 | Conditionally useful | Selection +3.50pp (-0.88,+7.75). Not selected as an additional finalist. |
| Complete pending-pick roster | Accepted infrastructure / Parked strategy | 108384 legal prefixes;88 body instances in20 engine games across slots0-5 agree with actual roster. All800 selection cells exactly neutral. Default off. |
| Early fields alone | Retry required | First conf58 vs56 wins, fuel169 vs147. Verify activation before interpreting score. |
| Early fields + GOV5 | Retry required | Focused dependency test64 vs56 conf wins, fuel55 vs147. Heavy-map fixture builds0 fields; small-map fixture36 field builds on round1. Remaining first-turn budget on large maps cannot fit minimum full-field depth. The heavy-map gain cannot be attributed to route precompute. Kept off; no holdout tuning. |
| Neural exact exporter | Accepted infrastructure | Every56609 float32 literals round-trips exactly; old exporter changed1813. Checkpoint lineage retained, no overwrites. |
| Neural golden | Accepted infrastructure |121/121 feature vectors and WASM target/behavior argmaxes match checkpoint;185/185 native observations match including64 extremes. Relative error <=3.71e-5. Diagnostic game scores/fuel excluded. |
| Missing fast-kernel configuration | Accepted repair | Initial diagnostic used slow/unbounded path. Auto-enable fast kernels for event runtime; explicit FAST=0 rejected. Positive/negative preprocessing fixtures pass. Failed configuration not used to reject model quality. |
| Seed / last completed distillation checkpoint | Retry required for release | Corrected release conformance96 cells: seed57 wins/fuel197 vs baseline56/fuel147;iter31 54/fuel199. No faults. Does not pass fuel/quality gates, stays off. Existing training stopped, never restarted. Prior cadence failures remain documented upstream. |
| Broad turn-and-fight CONTACT bit4 | Retry required / Parked | Inherited720-cell dev result -17.92pp; replay metrics show fewer no-hit-back deaths but kill deaths6.41->8.98 and dead rounds421->571. A one-turn unavoidable hit was mistaken for no eventual escape. Needs a tighter repeated-failed-escape/kill condition; not implemented or tuned on final data. |

Public opponents have ceiling effects (near100% baseline wins). Reports retain them and show every opponent separately;
related bot lineages and map cells are correlated, so uncertainty is clustered by map. C6/C7 samples are small and no
category-specific policy was fitted. Generated-map categories are explicitly unknown; size/opponent strata are reported.

The phase-fuel and memory contracts are inherited verified evidence from the same engine/toolchain. Fresh baseline
identity and actual engine/map/randomness matching were checked. Official diagnostics are audited; silent SDK false
returns are not separately counted. Total fuel reductions do not prove zero new suspension failure modes in every cell.

Remote push is blocked by automatic approval review. No alternate publication route or official platform action was used.

Runtime-only final control: +25 net wins/2232 cells (+1.12pp, CI-0.762,+3.047); fuel790 vs1532. Accepted as fuel infrastructure; not a demonstrated standalone strength upgrade.
