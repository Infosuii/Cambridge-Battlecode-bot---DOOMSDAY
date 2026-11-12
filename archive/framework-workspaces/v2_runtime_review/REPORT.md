# Independent source review of direct v2 dispatch

Reviewed the in-progress `nn_policy_runtime.cpp`, `nn_policy_core.h`, SDK strategy/tactics/economy boundaries,
NFS2 writer and dataset eligibility. This is source review and focused synthetic/native evidence; no engine game,
collection job, training, or full test suite was run by this reviewer. Root changed integration concurrently;
findings below distinguish the first snapshot from the later reread on2026-10-24.

## Findings fixed in the later source snapshot

1. **Ended options were being continued.** `close()` originally retained `Commitment.round` while clearing ID and
   state. A fallback/death could therefore suppress fresh role/strategy starts until an obsolete deadline. Later
   source resets interrupted timestamps and requires a live macro ID in the pure scheduler.
2. **Early failure removed later opportunities from coverage.** Originally `starts` incremented only in `choose`,
   so a role admission failure hid eligible strategy/objective/bank/shop/engage/combat/move starts. Later source
   prepares the world, freezes a `TurnInventory`, then checks readiness/dispatches. Every untouched eligible start
   is fallback+skipped. Conditional objective eligibility changes only after an executed upstream strategy.
3. **Bank intent forced a fresh decision every turn.** The old `force=intent==bank` bypassed the declared4round
   cadence. Later source forces only a newly committed bank macro and otherwise follows the fixed cadence.
4. **Prior disengagement was lost.** Resetting engagement to-1 immediately before every engage execution prevented
   `previous==disengage` from restoring an attack goal when the policy switched to fight. Later source preserves
   engagement when enemies remain and clears it only when no enemies are present.
5. **Deadline urgency ignored gem-dependent channel time.** The old base-duration-only guard activated too late
   for larger bags. Later source uses max(minimum,base+ceil(gems*multiplier)), matching the bank duration feature.
6. **Interrupted macro starts stayed eligible for PPO.** The original dataset considered only the initial execution
   acknowledgment. Later source requires an explicit ending and excludes missing/interrupted endings. This is a
   necessary improvement; the additional strict ending-validation issue below still needs checking.

## Remaining concrete checks / fixes

- **Validate the complete macro termination acknowledgment.** In the reread, the new dataset ending filter only
  required an ending, matching action/round, and zero reason on the end decision/ack. An end with `guard_refused`,
  `failed`, wrong executed action, or fallback source but reason0 could still make the start eligible. Require
  continued-option decision source, defined-option/end flags, continued-option ack source, option-executed outcome,
  and ack executed ID equal to the initiating action. Matching option/schema/snapshot joins alone do not establish
  execution. Add malformed-ending fixtures. Root was notified; recheck final source before treating this as open.
- **Admission/unready/disabled refusal reasons are not NFS2 events.** `Core::admit` returns an unadmitted ticket with
  no decision ID, and runtime exits before `decide`; whole-bot unready returns even earlier. The inventory correctly
  preserves aggregate fallback counts, but an NFS2 stdout stream cannot reconstruct those source/reason events.
  Either add a bounded refusal/override record path with a unique call ID, or explicitly limit NFS2 provenance to
  selected/admitted calls and publish reason counters alongside coverage. Do not infer absent calls were direct.
- **Safety overrides have aggregate telemetry but no explicit NFS2 override record.** Winning/deadline fallback
  increments bank `overrides`; it never emits `kSafetyOverride` describing why the teacher took over. An explicit
  event is needed for exact source auditing, or this limitation must remain documented.
- **Print the new accounting fields.** The reread NPO2 format still prints starts/direct/continued/fallback/overrides
  without `skipped` or `interrupted`. Include both so an independent reader can distinguish admission failures,
  upstream early exits, and discarded commitments. The pure inventory also conservatively classifies a macro
  started then discarded by same-turn teacher fallback as interrupted+fallback, while already executed physical
  decisions remain direct.
- **Respect head-mask scope.** A disabled required macro causes whole-bot fallback immediately; a move-only mask
  cannot measure movement policy execution through this dispatcher. Current installers enable all eight heads, so
  this is a profile/ablation limitation rather than an all-head nominal-path bug. Declare this before such probes.
- **Preparation exceptions precede the inventory.** Exceptions from initialization/world refresh/can-shop while
  constructing the eligibility snapshot reach main's error handler before any opportunity can be counted. Record
  an explicit failed-preparation turn counter if coverage acceptance includes such failures; do not silently treat
  them as successful ordinary execution. Main intentionally catches runtime errors and ends the turn.

## Snapshot semantics and teacher independence

The final integration intentionally keeps the first-admitted same-turn observation through internal macro goal,
role and engage commits; candidate rows remain live. Under this declared contract, an old goal/role in context is
an intentional anchored input, not an NFS2 replay mismatch: context+candidate rows reproduce the actual logits.
Physical effects must invalidate before subsequent action decisions. The original concern that engage changed its
goal without `changed=true` is therefore no longer a snapshot correctness issue under this explicit interpretation.
The prior-engagement behavioral issue above remains independently important and was fixed.

Nominal builders/executors do not call inherited strategy/farm/fight/route preference functions. They commit
explicit selected goals or exact SDK actions. Inherited world observation, static distance preprocessing and claim
serialization are permitted deterministic primitives. Whole-bot teacher execution follows explicit dispatcher
failure. A later failure can happen after a physical action already executed; its direct acknowledgment should
remain factual, and fallback must not claim that every decision in that turn was neural-owned.

The strategy builder's nearest camp descriptor cannot become a physical fallback objective: runtime forces the
objective head after a new farm/contest strategy. Roles establish initial assignments and strategy has subsequent
authority. Non-field walk-distance features are explicitly unknown sentinels; no heuristic preference score is
smuggled into the neural inputs.

## Files and focused verification owned by this reviewer

- Added pure `bot/src/nn_policy_schedule.h` inventory API and `tests/cpp/policy_schedule_test.cpp`, with focused
  Python compilation/execution wrapper `tests/python/test_policy_schedule.py`. The focused test passes using the
  checksum-verified w64devkit compiler supplied by root. It covers early failure preserving denominators, live-ID
  continuation, forced strategy/objective cadence, conditional suppression, dead shopping/channels, double-count
  refusal, interrupted continuations/macros, and real physical actions before fallback.
- Optimized strategic descriptors to reuse farm/contest group scans, defend/retreat home goals, and identical goal
  threat sums. Role-mask construction now checks reachability existence once and stops at the first reachable
  group; it does not select nearest/oldest destinations until execution. Active actual-SDK native syntax and the
  strategy synthetic executable both pass after those edits. Engine cost changes were not measured by this agent.

No approximately80% ownership, playing strength, training readiness, or full runtime acceptance is asserted here.

## Subsequent proposal: suspend assignments across transient budget fallback

Root's engine probe subsequently found that abandoning every successful early macro on a late budget refusal
restarted role/strategy every turn and starved objective/combat/movement. Retaining an assignment across that
transient fallback is coherent if all of these distinctions hold:

1. Separate semantic commitment validity from the NFS2 option interval ID. Close the old log interval with an
   interruption and clear its ID; never resume logging under an already ended option ID. Preserve the selected
   action/state/cadence only as a suspended semantic assignment. Actor eligibility stays excluded for that interval.
2. Before using it again, recheck exact availability without candidate construction, teacher ranking or a new
   sampled decision. A role recheck is a predicate: calling its executor would reset a later strategy assignment.
   Farm/contest must keep the same selected group or invalidate it; finding a different nearest group is a new
   objective choice. Dead/channel/expiry/incompatible state genuinely abandon the commitment and clock.
3. Teacher fallback can change Bot target/claims. Reapply a suspended selected assignment's target/claim only
   after resume guards pass; the fallback turn itself remains teacher-owned.
4. A resumed commitment creates no new direct start and contributes nothing to the direct numerator. Report
   suspension/blocked continuation separately from successful new policy starts. The pure schedule `live` flag
   describes this semantic validity, not the existence of a log ID. Added a synthetic suspended-versus-abandoned
   fixture to make the distinction explicit.

This addresses scheduling starvation without claiming that the failed turn or a resumed continuation was a fresh
neural-owned opportunity. It does not establish that current total decision costs meet the default-fuel acceptance
criteria; root retains that calibration task.

Root then requested and this reviewer implemented `resume_assignments` in the owned SDK strategy translation
unit. It performs role predicates and selected-intent availability checks, requires the same stored objective for
farm/contest, preserves OptionsState, and reapplies only mismatched target/claim. It permits no objective for
nonfarming bootstrap. The runtime remains responsible for requiring an actual objective policy commitment before
physical farming. Added synthetic resume fixtures and reran both the actual SDK native syntax and synthetic
execution runner successfully after this addition. No additional game was run by this reviewer.
