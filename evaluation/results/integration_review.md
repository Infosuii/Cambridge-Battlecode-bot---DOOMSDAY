# Lead integration self-review — 2026-10-24

This is a separate lead review pass using agents/H/REVIEW_CHECKLIST.md, adapted to direct interpretation2. The user requested solo work. No independent review agent was run or claimed.

| Area | Result | Evidence / limit |
|---|---|---|
| Python/C++ direct logits and masks | PASS | Full Python suite; integration_smoke.json replays328 actual logits, max error8.94e-8. |
| Sampling probability and actual execution acknowledgment | PASS | Synthetic core/NFS2 joins; real sampled records parse and pass exact behavior probability checks. Missing/failed/overridden/censored rows excluded. |
| Observation padding/canonical transforms | PASS | Synthetic observation/candidate/native parity, both-side real record replay. No teacher-prior input. |
| Persistent champion RNG | PASS | Synthetic trajectory regression: same champion reproduces, different champions use distinct persistent streams. |
| Commitment semantics | PASS | Synthetic schedule/resumption/termination tests; closed log IDs cleared, semantic assignments separately guarded, unclosed/interrupted starts excluded. |
| Admission before builders / overflow / reset / ticket authentication | PASS | Synthetic reserve, stale-ticket, UINT64_MAX, clock-reset and execution-reserve regressions. Metadata estimates may traverse cached container counts; they are not universally O(1). |
| Full component costs | PASS WITH LIMITS | integration_components.json covers real positive-gem bank and all builders, synthetic dense kernels/logs. No invalid measurements. Finite reused-map calibration is not a universal upper-bound proof. |
| Complete gameplay fuel | LIMIT | Final18checks have two candidate exhaustions on islands, no bot faults. Larger-map refusals remain. Paired opponent counts are diagnostic, not causal equivalence. |
| All-off original identity | PASS | integration_teacher_exact_final.json: full Wasm SHA256 matches frozen original. |
| Clean heads-off release / independent rebuild | PASS | artifacts/release/2026-10-24/neural-framework-untrained.verification.json; all gates off, no neural record strings/lab exports, full rebuilt SHA identical. |
| Release distinct from teacher_exact | PASS | Release strips inherited lab exports and has its own recorded Wasm/source hash. No byte-neutrality or strength claim. |
| Legacy neutral_credit / residual shadows | N/A | Retained legacy tooling; not the new direct policy's neutral control. Uniform is an independent policy, never a teacher-neutral claim. |
| Protocol/reference hygiene | PASS | Frozen protocol/lock plus recorded amendments; immutable references verified by package tool. Reused training-partition maps only. No final selection or fuel override. |
| Later training tooling | PASS WITH LIMITS | Synthetic batch parity, group leakage, terminal-discount, authorization, generated-budget and install tests. Optimizer, CUDA fitting and epoch recovery are implemented but not run on match data. |
| Teacher imitation data | FOLLOW-UP | Loss/CLI support exists; current direct checks intentionally contain no teacher annotation. Separate annotation collection is needed; never fabricate labels. |
| Lifecycle honesty | PASS | New1056-parameter model is synthetic/untrained, release selection empty, inherited draft separate. No training, activation or submission. |

Review fixes include late whole-teacher fallback on depleted fuel, unsigned reset hiding, suspended log IDs, draft telemetry crash, non-draining closed recording queues, shared champion RNG seeds, overbroad execution reserves, distant winning-carrier freeze, release verifier ignoring the V2 gate, and an offline terminal-return discount off-by-one. Source/test receipts distinguish intermediate failed diagnostics from final checks.

Remaining limitations are recorded in ARCHITECTURE.md and TRAINING_LATER.md: sparse movement records, conservative large-map refusals, capped-distance whole-decision refusal, dash/combat action-space subsets, missing imitation annotations and unexecuted authorized learning/recovery trials. These do not establish playing strength or full competition readiness.
