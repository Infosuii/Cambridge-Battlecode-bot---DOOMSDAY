# HANDOFF — stopped at explicit user request, 2026-10-24

STOPPED SAFELY. Full task is incomplete; do not claim training-ready, trained, officially verified or packaged.
ROOT: C:/projects/cambridge battlecode/work/neural-full-stack.
Implementation commits: 757a0c3 (modules/runtime/pipeline/docs/evidence), 15dff22 (all13 head schemas).
This handoff is in the following stop commit. Original handoff is preserved at de514f4:HANDOFF.md.
All three workers and all shell jobs have finished. No training, new engine games, submission, upload, activation,
browser or desktop action ran. References and previous experiments were not modified.

## Verified current state
- FINAL Python suite: 210 tests OK. FINAL C++ suite: 11 targets, 460/460 checks.
- Observation C++/Python parity bit-exact (synthetic); included in full suite.
- Combined staged active AND teacher_exact SDK native syntax checks: 9/9 each.
- One pre-existing disabled farm branch warns about slot % squads with squads=0. Not changed.
- Protocol verify passed; all4 reference Wasm/code hashes preserved.
- Receipts: evaluation/results/native_checkpoint.json, cpp_tests.json, staged_dev_native.json,
  staged_teacher_native.json, stop_native_python.log, stop_native_cpp.log.
- PowerShell decorates unittest stderr progress as NativeCommandError in its log; actual exit0, ending210tests OK.
- All new model tests are labelled synthetic. Synthetic CLI tests mock fitting/collection; no learning job ran.

## Official execution blocker
Installed WASI clang++.exe returns permission denied, even --version. User verified compiler/ACLs externally and
said full access was granted; retries still failed here. Elevated compiler request was automatically rejected:
tool runtime still reports sandbox_approval:false. This is not lack of user authorization or an ACL diagnosis.
Do not bypass with a copied/private compiler, proxy daemon or desktop control.
Final failed official receipt: evaluation/results/teacher_exact_checkpoint.json (passed=false).
Current root source SHA at attempt: b99089fada190a9790032fe8efff931b531d087bab8aecdd44781a8b0d06f0b8.
Expected original Wasm SHA: eb0ea88fc734661cf93935e5eab3c79e7a2658c7d05b7965593fbeb22d9d4442.
FRESH TEACHER BYTE IDENTITY IS NOT VERIFIED. Previous successful identity belongs to earlier committed sources.

## What exists; what is staged
D/E/F modules, all13 schemas, Python twins and native tests exist. Root original bot.cpp/main.cpp/draft.cpp/draft.h/
tsearch.cpp were NOT hook-integrated. Root checked-in profile is teacher_exact, all heads off.
Use tools/stage_wave2.py --native-check to reproduce a full combined integration in artifacts/tmp/wave2_integrated.
Use --dest artifacts/tmp/wave2_teacher_exact --profile teacher_exact --native-check for all-off staging.
Both scratch copies exist and syntax passed. Script does not promote hooks to root.
D instructions: agents/D/INTEGRATION.md. E script: agents/E/apply_hooks.py. F patch: agents/F/HOOKS.diff.
Do not smoke root dev_untrained and mistake absent decision call sites for integrated coverage.

Implemented lead fixes: leaf pre-admission token consumption and full builder metering; cached observation anchor API;
NFT1 named heads/invalid/NaN counters deferred after play_turn; external model-directory installation without registry
mutation; teacher_record/training_objective profiles; canonical records.decode_stdout and obs.encode_bytes adapters;
seeded hidden initialization with zero residual outputs; value checkpoint persistence; fixed margin unit /1000;
RL game cap and actual pre-update rollout quality guards; CLI resume/conversion schema checks; semantic hashes for
ALL head kinds including versions/feature meanings/option semantics/output units; combined dataset hashes include
all per-head schemas; content-identity match cache and concurrency cap4.
Shop0 is now an opaque guarded whole-teacher-plan option with unknown zero item descriptors. Updated F patch removes
the duplicate pre-admission preview entirely. Independent F reviewer confirmed source fix. A subsequent hash-version
gap was also fixed by lead and regression-tested. Runtime shared context is intentionally first-admitted snapshot;
later candidate features are live. context_position anchors belief sectors to the snapshot.

Models regenerated against final schemas:8367params each, status untrained, synthetic only:
fs_v1_untrained checksum0x6f8163630c208aa3; fs_v1_dev checksum0x165655b4ee67b5d1.
Inherited draft_net_original remains distinct/trained provenance-only, checksum0x3c09ba1cdb6e22fe.
release_selection remains empty. No new trained head is active.

## Reviews, documents, protocol
Read CONTRACTS.md lead amendments, agents/USER_REQUEST.md (definition of done), all D/E/F reports,
agents/H/REVIEW_WAVE2_PREINTEGRATION.md and REVIEW_ECONOMY_INDEPENDENT.md.
Initial review FAIL findings remain as historical observations. Lead fixes above are native/source passes only.
C audit completed: agents/C/VISIBILITY.md and REVIEW_FOLLOWUP.md. Memory/history are lazy; group state lacks explicit
observation age; alive transitions can be missed. Existing8-byte shared protocol unchanged, intent encoding proposal only.
Docs exist: ARCHITECTURE.md (coverage matrix), DIAGNOSIS_AND_DESIGN.md, TRAINING_LATER.md (NOT RUN commands and limits),
STATUS.md, AGENT_RECORD.md. Current workers actually launched: strategy, tactics, economy, plus their audit/review
follow-ups. They inherited configured Codex model; exact resolved identifier unavailable, no Opus5.5 tool option.
Earlier Opus/Kiro claims belong to historical reports only.
Current amended protocol SHA:70b872f3cd4ddabb95a152d0af93579c0d9f80f25ba4408014f5c80b2c17adc1.
Original/intermediate hashes retained in lock history. Adds neutral_real control and replaces impossible credit-neutral
claims with measured divergence. Strict teacher_exact, partitions, cells and promotion thresholds unchanged.
Historical results retain old protocol hashes; do not relabel them as new runs.

## Resume priorities
1. Restore official compiler execution. Run tools/check_teacher_exact.py for root, then with
   --src artifacts/tmp/wave2_teacher_exact/bot/src --out evaluation/results/teacher_exact_staged_checkpoint.json.
   Require full original SHA. Native syntax and historical binaries are not substitutes.
2. Run tools/probe_neural_fuel.py (official release/default fuel,2training maps; no learning). Preparation and native
   probe syntax passed; ENGINE MEASUREMENTS NOT RUN. Measure complete call-site/capture/features/logging/teacher reserves,
   not just kernels. models/budget.json remains PROVISIONAL:55000allowance/6000tail/10000teacher reserve. Resize if needed.
3. Integrate staged hooks incrementally into root, official teacher_exact byte recheck after every C++ milestone.
4. Complete auxiliary target/loss/record paths: carry-risk is consumed but unsupervised; belief needs censored own-future-
   visible targets/loss; leaf lacks feature/target record/loss. Value-only records do not supply decision rows by themselves.
   Future collected local matches also need a new grouped split manifest; archive IDs do not assign local episode IDs.
5. Real NFS1/RawTurn parity, all profiles and per-head ablations, official plumbing/fuel/logging-cost/smoke checks vs
   original/v47/first-hour both sides, paired neutral_real. Label untrained framework checks and reused benchmarks.
6. Independent post-integration review; close acceptance failures; package release ZIP/Wasm/checksums and independently
   rebuild officially with package_release.py/verify_release.py. NO NEW PACKAGE EXISTS. Do not submit.

## Environment/test setup
$py = C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe
Set PYTHONPATH=ROOT/python; TMP and TEMP=ROOT/artifacts/tmp; put C:/msys64/ucrt64/bin on PATH.
Commands: python -m unittest discover -s tests/python -p test_*.py ; python tools/run_cpp_tests.py.
All sources stay flat; no training; never modify references; official --release/default fuel only.
Central finding remains: a few dozen pre-decision fuel units can change teacher choices. See
 evaluation/evidence/neutral_equivalence_bisect.json. Logging/telemetry belongs after play_turn; zero weights or
experimental fuel credit cannot prove engine neutrality.
