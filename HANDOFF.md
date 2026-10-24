# HANDOFF — recovery checkpoint, 2026-10-24

## CURRENT STATE — supersedes historical checkpoint below

Latest user priority: create GitHub repository "neural networkk battlecode" and push EVERYTHING needed to clone
on a fresh laptop and continue with no missing source/features/tests/data. GitHub upload is explicitly authorized;
Battlecode submission/login/activation is still prohibited. Private repository CREATED:
https://github.com/Infosuii/neural-networkk-battlecode . Git Credential Manager's existing Infosuii credential
works through reviewed escalation. Never print/save its token. No browser or login used. GitHub connector lacks
creation/bulk Git transport, so tools/recovery_github.py uses official API and Git uses existing credentials.

Recovery: read RECOVERY.md and config/recovery_sources.json. tools/recovery_archive.py snapshots ALL of the
Cambridge Battlecode directory (~112GB raw), external official CLI workspace (~4GB), official cache (~2.3GB),
native compiler (~1.1GB), exact Python base runtime, previous environments/caches/data/analytics/history. ZIP
packs deduplicate SHA256 blocks and use Git LFS. File/block/pack SHA256 and source errors/exclusions are explicit.
Check recovery/progress.json, snapshot.json, source_errors.json and remote refs/LFS packs. Repository creation or
source-only push does NOT prove data is backed up. Current backup/publication may still be running: inspect actual
receipts/processes. The old configured `21 october matches` path was absent before this backup; all available
dated archives including23102026 are included. Credentials are excluded with paths/reasons only, never contents.

### V2 implementation since b17ace1

Foundation IS implemented; original gameplay dispatch/executors are NOT integrated. Root main.cpp/bot.cpp/draft.cpp
remain original. Default nn_policy_config.h has NN_POLICY_V2=0. nn_policy_runtime.h declares future glue;
nn_policy_runtime.cpp does NOT exist. nn_policy_state.h accessors need real option-state definitions. No80% neural
ownership, readiness to train, strength improvement or completed release packaging is claimed.

- Eight pure candidate heads: strategy/objective/role/bank/shop/move/combat/engage;K<=16,F12,contexts0..3,
  canonical IDs, no teacher-first choice/prior. Candidate0 may be illegal. Semantic action hash0x16DF3B9E.
- Compact observation173floats: self40,5x10allies+5mask,6x12enemies+6mask. Hash0x1346E3BA. C++/Python bit-exact
  on1013 synthetic cases. Strict shapes/masks/padding/nonfinite/import-schema validation, deterministic generator.
- Direct model2296params,G8/E4/context8/head8, interpretation2 wrapper over kernel1. Raw logits without teacher
  prior or residual bound. Strict exporter/loaders; synthetic untrained and zero-logit artifacts only.
- NFS2 bounded context/decision/execution records, stableIDs/optional teacher, true sampled logp. Dataset/PPO reject
  argmax, mismatched/missing execution acks, overrides/fallbacks/continuations. Imitation needs represented teacher
  actually executed. Synthetic direct imitation/PPO/SMDP GAE/autograd tests; NO optimizer updates/training jobs.
- nn_policy_core.h: resumable whole+segment checksums, admission BEFORE features, fuel metering, snapshot cache,
  single-use authenticated tickets, original selected-action verification on execution ack, sampled true logp or
  deterministic argmax probability1, leftover-only TEXT-byte-gated log flush. Budgets remain PROVISIONAL.
- nn_policy_capture.cpp reads own/public/current visible state and own aged sightings/claims only; bounded nearest
  visible/ID rows, compact encoder. Active SDK syntax passed; real engine capture not yet exercised.
- tools/install_policy_v2.py makes explicit UNTRAINED scratch trees only. direct_untrained install tested. No
  dispatch hook exists, so scratch installation is NOT proof of functioning direct neural gameplay.
- Macro SDK generators were only planned before priority switched. No nn_policy_options.cpp exists. Bank needs
  REAL per-altar distances: World's aggregate nearest-altar field cannot label every destination.

### Verified checkpoint

-255 Python tests OK: evaluation/results/v2_recovery_python.log,28.492s. Includes candidates5/model10/records15/
  observation6/core9 new synthetic tests. Core review caught/fixed forged tickets/acks and stale pending tickets.
- Legacy native11targets460checks: evaluation/results/v2_recovery_cpp.log and cpp_tests.json.
- Active compact capture SDK native syntax passed: evaluation/results/v2_capture_syntax.log empty(success).
- Fresh OFFICIAL teacher_exact byte check PASSED:
  evaluation/results/v2_recovery_teacher_exact.json; source SHA554ecea6272094e5069d80eb517de8ce5e6f0226b676581efb33d238a1083ccc;
  full Wasm SHA eb0ea88fc734661cf93935e5eab3c79e7a2658c7d05b7965593fbeb22d9d4442 (frozen original).
- Compiler access now works with reviewed escalation. Prior failed configuration cached EMPTY Release optimization
  flags, causing a misleading7d548... mismatch. Fresh reference/current rebuilds are exact. check_teacher_exact.py
  now always creates a fresh scratch directory. Never reuse poisoned old CMake caches.
- Official default-fuel LEGACY component probe DID RUN on2reused maps, no learning:
  evaluation/evidence/neural_fuel_probe.json. Max capture18172,encode11610,dense encoder28724,F24H8K16head20707,
  F20K16head18595,enqueue3862,flush31957. This motivated compact v2. Complete compact SDK/context/heads/flush
  fuel is NOT measured; neither budget JSON nor initial defaults are accepted. All local maps reused benchmarks.

Known core accounting gaps: per-record log fuel stays0 though total used includes enqueue; post-admission failures
have record reasons but invalid/refused counters need consistency. Keep explicit in next review. New hooks stay off.

### Next order

1. Finish COMPLETE GitHub archive + LFS upload, inspect source_errors/exclusions, verify ALL remote packs and a
   relocated clone restore. tools/configure_recovery.py rewrites paths for a fresh Windows x64 clone and uses
   exact offline Python packages. Run Python/native/official identity there. Recovery docs added after snapshot
   are current in Git HEAD; historical snapshot is a timestamped evidence tree, not a replacement for Git HEAD.
2. Implement eight SDK builders/executors and actual direct runtime dispatch, bypassing original heuristic ranks
   in nominal mode. Keep deterministic legality/channel/death guards, explicit fallback, inherited trained draft,
   flat src and fresh full original hash after every C++ milestone.
3. Engine-calibrate complete compact costs/cadence/budget, actual capture/records/parity, every profile, untrained
   smoke both sides vs original/v47/first-hour. Amend protocol before v2 comparative runs. Measure decision starts
   per area, excluding continued options from neural-ownership numerator. Do not manufacture an80% claim.
4. Independent review, docs/training CLI adaptations, release packaging/independent rebuild. NO TRAINING/SUBMISSION.
5. Before usage ends, update this handoff and NEXT_AGENT_PROMPT.md; give the user a continuation prompt and commit.

Three real workers strategy/economy/tactics produced agents/v2_* reports/interfaces. Exact configured model ID
unavailable; do not invent Opus runs. Workers hit usage limits during final followups and were stopped; no further
worker edits should be assumed. Preserve their native files, evidence and limitations. Current source is incomplete.

---

## HISTORICAL CHECKPOINT — superseded status/blockers retained below

## Latest direction: plan revision after the safe stop

The user subsequently asked to switch to roughly80% neural control of important decisions. This turn updated the
plan only: read POLICY_FIRST_PLAN.md and configs/design/policy_first_v2.json FIRST, then CONTRACTS.md. Direct masked
policies replace the future residual-first target; no mandatory online teacher scoring, teacher-first candidates or
teacher-logit priors. Keep teacher for explicit labels, evaluation and fallback; retain inherited trained drafting.
Legality, SDK calls, pathfinding primitives and narrow emergencies stay deterministic. Optional learned belief,
carry-risk and search leaf are deferred. All no-training/no-submission/workspace/default-fuel constraints persist.
No C++, weights, profiles or frozen evaluation results changed in this plan-only turn; v2 is not implemented.
The historical checkpoint and pending v1 results below are preserved as evidence, not the new implementation order.
The execution policy has since changed to reviewed escalation; compiler access has NOT been retested. On a future
implementation turn, retry the official checkpoint through the permitted approval flow instead of assuming the old
sandbox_approval:false restriction still applies. No background work is running.

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
