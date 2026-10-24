# Status — untrained implementation checkpoint

**Incomplete; not yet ready to train.** No training, submission, upload, activation, browser or desktop action ran
in this session. No new engine games ran. The inherited original drafting network remains the only trained model
used by the teacher. All new heads are untrained and inactive in checked-in `teacher_exact`.

Implemented: D/E/F candidate modules, per-head schemas/Python twins, belief movement contribution, staged full-hook
integration, native parity, safer runtime leaf accounting/deferred telemetry, record/observation adapters, external
model-directory installation, teacher-record/objective-training profiles, schema/checkpoint guards and rollout stop
checks. `tools/stage_wave2.py` produces a reviewable combined source copy under `artifacts/tmp` without promoting
unverified hooks into the original source files.

Verified this session: baseline186 Python tests and451 C++ checks; observation parity bit-exact. The final full suite
passed210 tests and460/460 C++ checks, including the shop-opacity and schema-version regressions. All such new model
tests are synthetic. Combined active and all-off source native SDK syntax checks each passed9/9, with one pre-existing disabled farm-path
division-by-zero warning. Native syntax does not establish official Wasm compatibility.

Official builds repeatedly fail to start the installed WASI `clang++.exe` with "permission denied". The user said
full access was granted, but the execution runtime continued to report `sandbox_approval:false`, and an elevated
compiler check was automatically rejected. This is an execution-policy blocker, not a diagnosis of file ACLs.
See `evaluation/results/teacher_exact_checkpoint.json`. A fresh teacher_exact byte identity is **not verified** for
the current sources. The last successful byte identity belongs to the earlier committed build only.

Remaining acceptance work:

1. Restore official compiler execution; run current and staged teacher_exact byte checkpoints.
2. Run the official fuel probe, measure full builder/capture/log costs and teacher reserves, replace provisional
   `models/budget.json`, resize if needed, then integrate each original-source hook with immediate byte rechecks.
3. Complete defensible carry-risk, belief and leaf record/target/loss paths. A forward pass is insufficient.
4. Capture real RawTurns/NFS1, verify Python/C++ logits/encoding and option semantics in official games.
5. Build every profile and per-head ablation; run plumbing/fuel/smoke against original/v47/first-hour both sides with
   neutral_real control under the recorded protocol amendment. Report failures plainly, never as strength evidence.
6. Re-review after integration, audit release diagnostics/lab controls, package ZIP/Wasm/checksums, and independently
   rebuild through the official CLI. No new release is packaged or accepted at this checkpoint.

All local maps are reused benchmarks. The current8367-parameter exports are synthetic initialization. Budgets remain
unmeasured. Zero residual and experimental fuel credit do not prove engine neutrality. Architecture, diagnosis,
later commands and actual worker assignments are in the accompanying documents.
