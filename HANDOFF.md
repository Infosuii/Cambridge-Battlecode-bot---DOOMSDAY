# SAFE STOP — current implementation checkpoint, 2026-10-24

This section supersedes all implementation-status claims below. User explicitly requested: **stop safely and
update HANDOFF.md and NEXT_AGENT_PROMPT.md**. Work stopped; all known exec sessions finished; both active workers
reported no live jobs. A read-only Windows process inventory found zero matching repo Python/compiler/engine/Git
processes. No training, parameter update on match data, Battlecode login/upload/submission/activation occurred.
Five bounded official release/default-fuel diagnostic games ran, all on reused calibration maps; these are NOT
training or strength evidence. Training data and raw diagnostic replays/stdout remain local and ignored.

## Checkout and continuation

Fresh clone of Infosuii/neural-networkk-battlecode main started at `2b81782`. Current local checkout:
`C:/Users/ishan/.codex/.chatgpt-projects/g-p-6ad14bd9b02481918601a95d4cc0e007/work/neural-networkk-battlecode`.
Do not resume old cancelled 120GB backup work. Repository scope stays development-only. Synced project `sources/`
and all reference/SDK/map/old-experiment inputs remain read-only. New gameplay heads remain UNTRAINED/OFF in the
checked-in default; inherited trained drafting remains separate. No80% ownership or training-ready claim.

The workspace now has a separate CPU `.venv-dev` (Python3.12.14, torch2.11.0+cpu, numpy2.5.2). Native GCC was absent,
so a complete normal w64devkit2.10.1 distribution was downloaded/extracted under ignored
`artifacts/tmp/native-toolchain/w64devkit` (archive SHA256
`add1edf984ce4d473cfeb7c52e0ab38db73a855bba6c7f564d5e16648eb2896a`). Compiler is `bin/g++.exe` there.
Official bundled cambc3.0.5 and installed WASI clang22.1.0 work through reviewed escalation.
Clone-local paths were saved in ignored `config/paths.local.json`; tracked `config/paths.json` was restored exactly
to its original contents before saving. Most tools/tests still read tracked paths directly. On this clone rerun:
`.venv-dev/Scripts/python.exe tools/configure_dev.py --native-cxx artifacts/tmp/native-toolchain/w64devkit/bin/g++.exe`
then `. ./artifacts/tmp/dev-env.ps1`. Keep temporary/cache/environment files local; do not commit machine paths.

## Saved implementation — integration is now present but UNFINISHED

- Added flat SDK modules `nn_policy_strategy.cpp` (strategy/objective/role), `nn_policy_economy.cpp` (bank/shop),
  `nn_policy_tactics.cpp` (move/combat/engage), plus `nn_policy_options.h`.
- Added `nn_policy_runtime.cpp`, gated Bot/main hooks, model warmup, direct dispatcher, explicit execution acks,
  opportunity inventory/cadence and telemetry. Original teacher runs on explicit fallback. Root default V2 stays0.
- Canonical coordinate transform cached. Macro state changes intentionally share the first-admitted same-turn
  observation; candidate rows are live. Physical effects require refresh/invalidation. No teacher priors/ranking.
- Bank uses destination-specific real field distances, explicit altar destinations/deposit. Latest saved bank code
  caps field search at64; if cap leaves an unresolved altar it refuses the WHOLE decision (does not silently label
  that destination unreachable). `bank_candidate_fuel` estimates metadata/container costs without live SDK reads.
  It is NOT wired into root admission/probe and is NOT engine-calibrated. Stale bank execution never cold-searches.
- Shop selects explicit affordable single purchases/save, handles four raw consumable ABI slots (live IDs0/2),
  and fifth-shard combination gains. Item capacity is not exposed by SDK; feature0 is documented unknown sentinel.
- Tactics cover visible enemy/camp targets, supported targeted/AoE/reset/shield/heal actions, local movement/dash
  subset/hold and engage choices. Limitations: offset AoE, altar-lock attacks, handle namespace collisions and
  hole-crossing dash paths. See worker reports, not a claim of complete combat action coverage.
- Pure `nn_policy_schedule.h` now plans eligible starts before fallible work; skipped starts remain fallback.
  Continued options never enter direct numerator. Successful macros in a later-fallback turn count interrupted.
- Dataset rejects unclosed/interrupted macro starts from PPO/imitation. Ending validation tightened to matching
  continued-source execution/ID/outcome. Three focused synthetic termination tests passed before later edits.
- Core gained explicit option termination, logging-cost acks/counters, and authenticated custom candidate reserve.
  Latest custom-reserve change is UNTESTED. Core estimate no longer reserves candidate construction twice after
  it has already happened. NFS2 array serialization now bulk-copies on little-endian; latest optimization UNTESTED.
- Log output was bounded to about40k per champion, avoiding the first run's1MiB truncation. Telemetry is separate
  from record logging. `check_policy_v2.py` stores diagnostics locally and records invalid-record counts explicitly.
- Added independent frozen direct-framework protocol/lock, preserving legacy protocol/schedules unchanged.
  `probe_policy_v2.py` measures post-teacher components; its first real run was incomplete/unsafe (see evidence).
- Fixed genuine fresh-clone portability failures: evaluation rebuild uses exact locked scenario evidence when old
  local diagnosis paths are absent; release verifier resolves immutable local reference names and validates hashes.

## CRITICAL unfinished edits at the exact stop point

**Do not assume active V2 compiles.** The tactics worker was stopped during a fuel-bounding refactor:
1. `nn_policy_tactics.cpp` removed `channel()` while old `targets()` still calls it. Restore helper or finish refactor.
2. Tactics synthetic tests still reference removed `Boards.home_ready`; adjust tests to final cache representation.
3. `tactics_candidate_bound` is declared in options.h but has NO definition. Finish and wire it before admission.
4. Partial tactics changes: capped150 goal fields, whole-decision refusal for capped unknown distances, no-bridge
   cached group/spawn fields, engage uses spawn field, bounded retreat trace. These latest changes are UNVERIFIED.
5. Runtime suspension is incomplete: it preserves semantic state/clock after transient teacher fallback and closes
   log intervals interrupted, but still keeps an ended log ID as its live flag. Separate `committed`/semantic validity
   from log option identity; clear closed log IDs. Call new `resume_assignments` before using a suspended assignment;
   do not rerank/select a replacement objective. Reapply claims only after exact guard success. Dead/channel/expiry
   truly abandon commitments. Runtime currently does NOT call the saved resume helper.
6. Head-specific builder estimates are NOT wired. Root still admits using generic candidate3500/observation12000/
   log6000 defaults, which real measurements disprove. Preserve enough whole-teacher fallback fuel. Do not rerun
   unsafe active experiments until real bounds/gates are repaired. Catch fuel counter reset/round advance in ordinary
   runtime cost calculations too; current unsigned subtractions can wrap and Core spent() can hide resets.
7. Telemetry lacks champion ID, so cumulative rows from different bodies cannot be aggregated by head alone. Add
   champion identity and honest partial-output handling. Admission failures/skipped starts and safety overrides need
   explicit NFS2 source events if records alone are intended to reconstruct ownership.

## Actual verification and limitations

- Official all-off byte check PASSED at INTERMEDIATE source SHA
  `080bd659523b42d2b44fc7d91e5381373458700adbce492fcbc99d10658cd479`, Wasm exactly
  `eb0ea88fc734661cf93935e5eab3c79e7a2658c7d05b7965593fbeb22d9d4442`.
  Receipt `evaluation/results/v2_integration_teacher_exact.json`. Later C++ changes have NOT had fresh identity check.
- Legacy native11targets460checks PASSED: `v2_integration_cpp.json`, `v2_resume_cpp.log`. This does not validate
  final active SDK source. Initial full Python run:259 tests,5 errors,1skip, all errors old absolute evaluation paths;
  `v2_resume_python_initial.log`. Portability fix targeted34tests passed. Full suite NOT rerun afterward.
- Strategy actual SDK syntax and synthetic fixtures passed including latest resume helper and scan optimizations.
  Pure schedule fixture passed. Latest bounded bank SDK syntax/synthetic fixtures passed. Tactics92 synthetic checks
  and active syntax passed BEFORE its final partial refactor; current tests/source are not verified.
- First direct_record game completed but output hit1MiB; strict final NFS2 parse failed. Preserved locally.
- Second direct_record game: zero bot faults/errors, zero invalid records,42,426 stdout bytes;282 fuel exhaustion
  entries. Third direct_untrained game: zero bot faults/errors;198 fuel exhaustion entries. Both fail fuel/control
  acceptance; none proves80% coverage or strength. Early dispatcher repeatedly restarted macros and starved later
  heads; partial suspension changes were made afterward but final runtime remains incomplete.
- Two post-teacher component-probe games ran on00rows/01islands. Missing bank/move/engage calibration, and at least
  one combat sample has unsigned underflow after fuel reset. Objective builder reached62,589 fuel; old43500 gate
  was insufficient. Original probe's `status=ok` is NOT accepted timing. Probe code now detects overrun and bound
  violations and rejects old underflow samples; Python syntax passed, but it has NOT been rerun.
- Compact dense encoder measured14,376; denseK16 heads13,237; context enqueue9,492; decision enqueue35,793 before
  the untested bulk-copy optimization. These are component observations, not a complete accepted runtime budget.
- Concise diagnostic/stop receipt: `evaluation/results/v2_safe_stop.json`. Raw replays/stdout/models/build trees
  remain only under ignored artifacts/tmp. Frozen references/protocol results were not rewritten. No final package,
  full smoke/profile/ablation suite, actual integrated record/logit parity or training-CLI adaptation accepted.

## Resume order

Read this section and NEXT_AGENT_PROMPT first, then current worker/review reports. Repair active tactics and finish
semantic suspension/admission wiring; run focused synthetic checks. Recheck full official teacher_exact identity
with fresh scratch after C++ milestones. Then recalibrate safely at official release/default fuel (never fuel
override); do not turn bad timing samples into budgets. Complete champion-identified ownership/record parity,
all profiles/both sides/per-head and smoke checks only after bounded costs permit them. Independent review,
training CLI adaptation and verified packaging remain later. NO TRAINING OR SUBMISSION.

---

# CURRENT HANDOFF - development-only repository,2026-10-24

## Latest user decision OVERRIDES the full-backup sections below

User selected "Smaller development repo (recommended)" and clarified that training will ALWAYS happen on this
original laptop, never on a different laptop. The original120GB full-workspace GitHub backup is CANCELLED.
Do not continue full archive repair/upload/restore. Keep original training data/environments/history local.
All bulk snapshot/publisher/verifier processes were STOPPED and checked absent. Their progress/error counts are
historical, not acceptance failures for the new smaller scope. Partial generated backup output was MOVED, not
removed, to artifacts/local-only/cancelled-large-recovery. No original source/data/previous experiment was deleted.

GitHub: https://github.com/Infosuii/neural-networkk-battlecode (private, Infosuii). Lean main is PUBLISHED and independently clone-verified (tested commit6f4e4f8). All development source, models, schemas, tests and required frozen replay/reference evidence,
results,40reused benchmark maps, exact official Windows CLI and setup/handoff are included. A source-history Git
bundle preserves the pre-cleanup commit graph without huge LFS payloads. Large datasets/runs/tool caches and old
experiment copies stay local, per config/repository_scope.json. Read DEVELOPMENT_SETUP.md and RECOVERY.md.

Verified before scope switch: root259 Python tests OK; a FRESH remote source-checkpoint checkout also259 OK,
without manual hydration or byte fixes; legacy native11targets460checks; active compact capture syntax passed;
official all-off build from root AND cloned source byte-identical to frozen original SHA
 eb0ea88fc734661cf93935e5eab3c79e7a2658c7d05b7965593fbeb22d9d4442.
FINAL DEVELOPMENT VERIFICATION: ordinary remote main clone (no LFS skip/no manual hydration) passes259 Python
 tests with newly installed CPU PyTorch2.11.0+cpu, plus11native targets460checks. The bundled official CLI rebuild
 matches original Wasm exactly. Receipts: evaluation/results/development_clone_verified.json,
 development_cpu_python.log, development_cpu_cpp.log, development_teacher_exact.json. Clone Git pack84370965B
 (~80.46MiB), tracked files190119960B(~181.31MiB),900files at tested commit6f4e4f8. Later changes only add these
 receipts/documentation. Current checked-out local branch main tracks origin/main; source-checkpoint was renamed
 to main. Cancelled archive refs master/cancelled-archive-remote/source-checkpoint remain LOCAL only for history.
 No backup/upload/verifier/worker or engine jobs remain running. Git LFS archive objects are absent from main.
 The official CLI83MB dominates repository size; its checksum is in tools/vendor/manifest.json.
 CPU test environment: artifacts/tmp/cpu_dev_venv; original CUDA environment remains in the sibling previous
 experiment. Do not replace it or start training. Active config/paths.json still preserves this laptop's original
 paths; fresh clones run tools/configure_dev.py to configure their own tools.
Separate copied-runtime probe failed due native GCC relocation/header paths; this is why the small setup uses a
normally installed MSYS2 UCRT64 compiler. No claim of a verified relocated full offline archive is made.

Current BOT: v2 foundation implemented, not integrated into gameplay. Eight direct F12/K16 heads,173float compact
observation(hash0x1346E3BA),2296parameter direct model, NFS2 records/dataset/losses and pure runtime core exist.
No nn_policy_runtime.cpp or SDK world option generators/executors/dispatch yet. Default NN_POLICY_V2=0; inherited
trained draft stays separate. No80% neural ownership or training-ready claim. New model artifact is copied to
models/policy_v2_untrained with status untrained; no release registry selection or activation.

Next: lean GitHub/setup verification is COMPLETE. Implement the eight SDK option builders/executors
and runtime dispatch per POLICY_FIRST_PLAN.md. Bank needs real per-altar distances; aggregate nearest-altar field
cannot label all destinations. Measure full compact fuel and actual records, define decision-opportunity coverage,
profiles/smoke/protocol amendment, independent review, docs/training CLI adaptation and release packaging later.
No training or submission is authorized. All existing hard constraints persist: official CLI --release/default
fuel only, never --fuel; flat bot/src; immutable references and read-only old experiments/SDK/maps; full all-off
byte identity after C++ changes. Reviewed escalation for installed tools works; always fresh CMake scratch.

Keep this handoff and NEXT_AGENT_PROMPT current before usage ends. Do not invent model/agent runs or strength.

---

# Historical full-backup attempt and implementation evidence - SUPERSEDED scope

# HANDOFF - recovery checkpoint, 2026-10-24

## CURRENT STATE - supersedes historical checkpoint below

### Live publication update (2026-10-24,13:06UTC)

Current SOURCE is safely on GitHub branch source-checkpoint (first commitdf75fb837202489566e0fef43ea709799a4817ea),
created without the huge archive packs so source verification need not wait for hours of data transfer. A FRESH
REMOTE checkout of that branch passed ALL259 tests in24.708s with existing installed tooling, NO manual file
hydration or line-ending fixes. root259test log also passes. tools/publish_source_checkpoint.py can update this
branch from committed HEAD without force-pushing or disturbing the real index. main is the full archive branch.

Recovery scan is still RUNNING: exec session58054. Incremental Git LFS publisher still RUNNING: session2353.
At this update:159612files /70.97GB logical captured,198packs created,1excluded item and1source error flagged.
The current archiver writes error details only at completion; inspect recovery/source_errors.json then resolve
the issue before claiming a complete backup. Original archiver is the pre-resume code loaded at launch: it has
NO pid in progress.json. Do NOT start a second snapshot while it runs. If interrupted, current on-disk tool supports
snapshot --resume, retaining closed packs and preserving a truncated tail in recovery/incomplete/.

First263597932-byte LFS pack was downloaded from the remote and SHA256 verified exactly. First additional16packs
successfully pushed; the next batch is transferring. Source, frozen reference Wasm/manifest/build logs AND82small
frozen evaluation replay files(5.76MB) are committed directly to Git. Entire archived data/dependencies are NOT
yet all uploaded. evaluation/results/recovery_publish.json remains partial; its old running-process version may
record a newer LOCAL head if the lead committed during push. Use git ls-remote origin refs/heads/main as authority.
On-disk publisher code fixes that race for subsequent process launches; don't restart a live publisher casually.

Fresh-clone issues found/fixed: Git's Windows auto-CRLF broke frozen schedule hashes and generated schema tests;
.gitattributes now starts with `* -text` so EXACT original blob bytes survive any checkout. An unanchored builds/
ignore hid references/builds; it is now /builds/, and unchanged frozen binaries/manifests are tracked. configure
recovery now hydrates missing ignored project files from restored snapshot without overwriting existing Git HEAD.
The earlier clone failed, then passed255tests after exact-byte/frozen-data hydration, and rebuilt ORIGINAL Wasm
officially: evaluation/results/recovery_clone_teacher_exact.json. The newer source-checkpoint clone passes259
directly. This proves portable SOURCE/data checkout with existing tools; full relocated offline runtime/all-archive
restore has NOT yet been verified. No new game/training/submission occurred during backup.

Do not call repo/source creation a finished backup. Finish scan, repair source error/examine exclusion, finish
all LFS uploads, check every remote OID, checksum/restore archive, configure relocated dependencies and recheck
Python/native/official teacher identity. The user explicitly requested a handoff prompt before usage ends.

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

## HISTORICAL CHECKPOINT - superseded status/blockers retained below

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
