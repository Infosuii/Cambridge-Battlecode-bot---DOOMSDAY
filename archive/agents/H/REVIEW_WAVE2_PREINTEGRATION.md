# Wave 2 pre-integration review

Reviewer: resumed-session Codex worker `economy`, reassigned to H2. This review is independent of D, E, the runtime
and G. **F is a self-review:** this worker authored the economy implementation and cannot provide independent F
acceptance. The worker inherited the configured Codex model; the exact model identifier is not exposed by the
agent tools, and no Opus 5.5 run is claimed.

Scope: working-tree source, typed candidate modules, proposed integration hooks, schemas, native/synthetic parity,
runtime accounting and future training executability. Original gameplay files and implementations were not edited
by this review. Findings describe the source observed during review; lead fixes are in progress and need a fresh
verification record before these statuses change.

**Overall: FAIL for acceptance, PENDING official integration verification.** Synthetic candidate parity passes.
Several runtime/training correctness issues below need fixes. Official Wasm compilation/execution is currently
blocked by the session's execution policy (`clang++.exe: permission denied`), so native checks cannot establish
Wasm identity, engine fuel bounds, real-record parity, smoke safety or release readiness. No games, training,
parameter selection, upload, submission, browser or desktop actions were performed by this review.

## Actionable findings

| ID | Status / priority | Finding and source evidence | Required resolution |
|---|---|---|---|
| H2-01 | FAIL / high | `nn_tactics.cpp::leaf_value` first calls `nnh::admit(...,2200)`, then builds leaf features. `nn_head.cpp::leaf` ignores `g_token`, creates a new Meter at entry and calls `prepare(...,false,true)`. Unlike `decide`, the pre-admitted feature work is neither included in that Meter nor consumed as a token; the inference is admitted twice. | Consume an existing matching leaf token and start its meter from token.start, just as candidate decisions do; cover feature+inference accounting and refusal with native runtime tests. |
| H2-02 | FAIL / high | At initial inspection `nn_tactics.cpp::cast` logged a sampled alternative through `decide` and then returned **the teacher action** if the alternative's final readiness check failed. The record continued to claim the alternative and its logp. | Preserve declared guarded-option semantics (failure means no-op), or record the actual override with an execution status excluded from PPO. Never silently substitute teacher execution after recording a sampled alternative. |
| H2-03 | FAIL / high | `cli.py::cmd_train_value` originally wrote only `value_report.json`; gameplay value parameters and the `DraftOutcomeModel` instantiated inside `train_draft_outcome` were discarded. | Save exportable gameplay weights/checkpoints; explicitly save the distinct draft-outcome model and provenance. Recheck CLI paths after the lead's announced fix. |
| H2-04 | FAIL / high | `schemas/heads/value.json` declares `margin` in submitted gems, and `nns::bounded_value_signal` divides it by 500. `records_dataset.py::convert_match` instead targets `(final_team_gems-final_opponent_gems)/reward.margin_scale`; `value.py::value_loss` regresses that normalized target directly. | Pick one unit and use it consistently in schema, targets, loss, runtime consumer and tests. Current default produces a signal smaller by about 1000 than the declared unit. |
| H2-05 | FAIL / high | `first_experiment.json::_stop_criteria` promises aborts for invalid actions and fallback rate >0.2. `cli.py::cmd_rl` checked only rollout faults before `ppo_update`; `ppo.py::ppo_update` computed invalid/fallback statistics but did not enforce a pre-update threshold. | Implement actual configured pre-update quality guards and tests proving optimizer state and parameters remain unchanged on rejection. Entropy-collapse behavior must match its documented report/stop semantics. |
| H2-06 | FAIL / high | `records_dataset.py::action_schema_hash` hashes only the inventory `schemas/heads.json`, omitting the per-head feature schemas. `cmd_rl` calls `resume` without expected observation/action hashes, bypassing its otherwise useful guard. Conversion validates observation hashes only when explicitly passed; the CLI did not pass them or compare logged per-head action hashes with the installed model. | Hash the combined versioned head specifications, always supply expected hashes at CLI resume/conversion, and reject same-dimension semantic schema changes before any update. |
| H2-07 | FAIL / coverage | `value.py::value_loss` trains win and margin only; runtime uses `carry_risk`. `nnh::leaf` does not emit leaf-feature/target records and neither PPO nor imitation supplies a leaf loss. Belief likewise lacked a real target/loss path in the inspected pipeline. Candidate-policy PPO cannot backpropagate through the engine's use of leaf outputs to train that head. | Add defensible labels and explicit losses/record paths for these scalar/auxiliary outputs, or list them as incomplete. Do not call every head training-ready solely because its forward pass exists. |
| H2-08 | PENDING / fuel | All new builders have numeric admission allowances, but they are provisional. `archive/agents/E/apply_hooks.py::tile_rank` also copies narrowed tiles before wrapper admission/Meter; the inherited shop capture builds a duplicate teacher-preview pre-pass before F's gate. These costs are not established by kernel-only measurements. | Measure complete call-site prologues, teacher captures, candidate features/legality, encoder, records, and downstream action reserves in the official engine. Move expensive work behind gates and include all new spend in accounting. |
| H2-09 | PENDING / context contract | The shared context cache is invalidated at turn start, not after a purchase or movement. Later candidate-specific features use current state while shared context may describe an earlier same-turn snapshot. This can be valid only as an explicit snapshot design. | Document exactly when the first snapshot is taken and that later heads intentionally receive it, or invalidate after action effects with a record key/schema that distinguishes multiple snapshots. Test Python reconstruction against that declared behavior. |

The lead received H2-01 through H2-07 as actionable messages during review and announced fixes for token accounting,
value checkpoint persistence, value units, pre-update guards and schema validation. An announced fix is not PASS.

## Positive source findings

- **PASS:** D and F put teacher choices at candidate0 and keep its prior maximal. D draft rejects an already-taken
  teacher, then lists available IDs; objective carries the selected need/score with its group ID. Strategy option0
  denotes the unchanged remaining chain, as specified in A's contract issue: its teacher cannot be precomputed
  without acting. Other strategy options explicitly attempt a priority then fall through if no action succeeds.
- **PASS:** E's pure builders preserve provided teacher-first ordering, IDs and masks; illegal alternatives keep
  negative-infinity runtime logits. Move, retreat/dash, spell, target intent, final engage, ward and search-leaf
  hooks are proposed at active source paths, not only the inherited compiled-out paths.
- **PASS:** E canonicalizes movement/ward vectors with the shared team frame. Native feature scaling, contexts,
  reserved-zero fields and clipping match its Python twin on the tested synthetic fixtures.
- **PASS:** The runtime samples only active heads when `kTraining` is enabled, otherwise uses stable masked argmax.
  It records the chosen sample's log probability under the exact bounded masked logits. Shadow records execute
  choice0 and are excluded from PPO's ratio mask. H2-02 concerns the later caller override, not this scorer.
- **PASS:** Stateless `decision_stream(seed,round,champion,head,call)` keys decisions by champion/head/round/call.
  Resetting the per-turn call counter does not repeat the same random stream on the next round. Deterministic
  same-map games are still not independent additional samples.
- **PASS:** D role cache emits one choice when a 20-round option begins, no new sampled choices during the cache,
  and has an explicit death reset. G uses variable-gap interval rewards and gamma^tau; equal-round consecutive
  boundaries are supported with tau=0. Exact hook/reset placement still requires integrated verification.
- **PASS:** F uses existing reachable safe/static nearest-altar fields for bank destinations, re-queries raw field
  distance only after admission, and keeps force/wins/late priorities deterministic. Shop alternatives use actual
  SDK `can_buy` and recheck before guarded execution; failed checks mean save. Candidate0 executes the complete
  original purchase loop, while its feature preview describes **only its first purchase**, not total plan cost.
- **PASS:** No new dynamic constructors or per-decision heap allocations were found in the modules. The candidate
  maxima and fixed arrays are bounded. Role state and F per-round stamps are POD. All-off modules use compile-time
  or preprocessing gates; official byte identity remains PENDING.
- **PASS:** The current `teacher_record` profile is shadow with records on; `training_objective` activates only
  objective. The unregistered export installation test verifies a local model directory can install without
  mutating the registry and that an untrained external model is refused for release.
- **PASS:** New source and schemas clearly label heads untrained. The inherited original draft model remains a
  separate model; no new worker claims training evidence or strength gains.

## Checklist disposition

This applies `archive/agents/H/REVIEW_CHECKLIST.md` without treating unavailable engine evidence as a pass.

| Checklist area | Status | Evidence / reason |
|---|---|---|
| A sampling/argmax and masked logp math | PASS synthetic/source; FAIL caller override | Runtime scorer source plus H2-02. Real-record check still pending. |
| A C++/Python logits on real NFS1 | PENDING | No post-hook official training-profile match available in this review. |
| A real RawTurn encode, padding, team B | PENDING | Existing observation tests are synthetic; no new real capture fixtures were supplied. |
| A commitments/options and RNG | PASS source; PENDING integrated placement | D role cache/reset, G variable-gap rewards, stateless keyed decision stream. |
| A logging overhead / decisions lost | PENDING | Requires official instrumented vs logging-stub schedule. |
| B release ZIP audit, strings, exported lab controls, independent rebuild | PENDING | No post-Wave2 package/build exists yet; retain the known lab-preservation tradeoff in release documentation. |
| C teacher_exact identity | PENDING | Every original source hook change needs a new official byte comparison. Native parity cannot replace it. |
| C neutral_credit exact equality | FAIL known historical requirement | Handoff records prior divergence (4/12), so no equality claim is justified. Treat credit as experimental. |
| C neutral_real divergence / per-head divergence | PENDING | Added control protocol is not a completed post-hook engine result. |
| C shared-context once/turn cache | PASS source; PENDING semantics | Runtime turn serial invalidation exists; H2-09 documents action-effect ambiguity. |
| C gate before features / low-fuel accounting | FAIL/PENDING | H2-01 and H2-08; no full call-site measured bound. |
| D fuel exhaustion, tails, route reserve | PENDING | Need default-fuel official scenarios, not increased fuel or native timings. |
| E frozen protocol, ledger, split/gate code | PASS existing tested design; PENDING final current receipt | Framework schedules use training partitions and reused-benchmark labels. A final protocol/ledger/reference verification receipt must accompany integrated results. |
| E post-hook result provenance / summary spot-checks | PENDING | No new engine result set to inspect. |
| E no forbidden training/submission or fuel override | PASS review actions | This review ran only native/synthetic tests and source reads. No gameplay or learning job was launched. |
| F lifecycle release selection/checksums | PASS tested installation path; PENDING final bundle | External untrained release rejection/checksum-corruption test passes; final exported model manifests/checksums and package still need review. |
| F ready-to-train claim | FAIL currently | H2-03 through H2-07 and all official pending items must be resolved first. |

## Commands actually run

All tests below are synthetic, with `PYTHONPATH=ROOT/python`, native g++ on PATH and TMP/TEMP under
`ROOT/artifacts/tmp`. They perform no matches and no parameter updates:

```
python -m unittest tests.python.test_strategy_parity tests.python.test_tactics_parity tests.python.test_economy_parity tests.python.test_pipeline_integration -v
```

Result: **18/18 tests pass**. Strategy: 5; tactics: 5; economy: 4; installation/cache integration: 4. The candidate
tests compile/run native C++ and compare varied synthetic feature/mask/ID/prior fixtures. They validate pure
builder twins and central installation behavior, not SDK action execution, real rollout probability attribution,
fuel costs or strength.

## Acceptance required after fixes

1. Add targeted regressions for the token accounting, post-sample execution semantics, value units/persistence,
   pre-update quality rejection and same-dimension schema drift findings; rerun the full required suites.
2. Have a different reviewer inspect F and review these fixes. This worker's F report is self-review only.
3. Rebuild teacher_exact after every gameplay C++ integration and compare full Wasm bytes with original.
4. Complete real NFS1/RawTurn parity, every profile/per-head checks, measured feature/record fuel probes and both-side
   framework smoke/fuel schedules with the recorded overhead-matched control amendment.
5. Audit/package release and independently rebuild it. Do not submit. Until then report the implementation as
   incomplete/unverified, not a trained or fully accepted training-ready bot.
