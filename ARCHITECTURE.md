# Neural full-stack architecture — implementation checkpoint

**Not accepted as training-ready yet.** Candidate modules and native twins exist; the gameplay hooks are staged,
not applied to the original translation units. Official compilation is blocked in this session. The engine fuel
budget, real-record checks, full integration and packaging remain acceptance requirements. See [STATUS.md](STATUS.md).

## Information flow and boundaries

The original bot computes its teacher choice, legality and narrowed alternatives first. A per-head compile-time
gate calls the neural admission check before expensive features. Candidate0 remains that teacher choice. The scorer
uses a shared observation encoder and a small task head, adds a bounded residual to teacher priors, and uses stable
masked argmax in development/deployment or logged softmax sampling in a training profile. Empty, incompatible,
non-finite, unverified or unaffordable calls fall back to candidate0. SDK execution rechecks legality.

Strategy option0 is the remaining original priority chain, because that chain decides by acting. Shop option0 is
the complete original purchase loop; its plan descriptors use explicit unknown zero sentinels, avoiding a duplicate
purchase-plan preview. Other strategy/shop
options are guarded attempts, including no-op/save on failure. These are explicit action options, not promises that
an SDK action will succeed. The inherited draft network remains a separate unchanged teacher model.

`nn_obs_glue.cpp` captures only the acting champion's permitted public, visible and remembered state. The pure
`nn_obs.cpp` / `nfs.obs` encoders have bit-exact native parity. [C's visibility audit](agents/C/VISIBILITY.md)
records freshness limits: observation/history updates are lazy; group memory has no explicit state-observation age;
alive transitions between captures can be missed. No privileged replay state or terminal outcome is an input.

## Snapshot and option semantics

The shared context is a **first-admitted-call snapshot** per turn serial, champion and round. Later actions can change
the live state; candidate features and execution guards use that live state while the shared embedding intentionally
retains its first snapshot. One queued RawTurn reconstructs that embedding in Python. `context_position` exposes the
snapshot's position so belief sectors stay anchored correctly after movement. Changing this to multiple snapshots
would require versioned record keys and parity tests; silently overwriting a turn's context would corrupt labels.

The role option lasts at most20 rounds and resets on death through its staged hook. Objective choices are logged
where the teacher reselects; forced continuations are not fresh samples. Python streams are separated by match,
side, champion and head, with interval rewards and gamma^tau. Draft has no shared-context requirement. A separate
critic handles PPO; the runtime value head supplies bounded planning features when combined with strategy/objective.

## Neural coverage matrix

All rows below describe implemented modules and **staged hook locations**, not completed engine integration.
`P` means provisional feature fuel reservation; inference/context/record costs are additional. Every new head is
untrained and inactive in the checked-in `teacher_exact` profile.

| Decision | Observed state / candidates | Output and module | Staged call site | Fallback | P feature fuel | Later labels |
|---|---|---|---|---|---:|---|
| Draft | Public map, composition, available champion IDs; teacher first | Ranking, `nns::draft_pick` | draft.cpp after cap_draft_pick; gated Bot reference | Inherited draft pick |3000| Teacher pick; observational outcomes are confounded |
| Strategic mode | Health/bag/time, nearby bodies, role/value;6 priority options | Ranking, `nns::act` | play_turn after emergency go_home | Remaining teacher chain |2500| Instrumented teacher options / on-policy returns |
| Objective / camp assignment | Teacher-narrowed8 groups, travel/score/risk/claims | Ranking, `nns::objective` | score_groups after cap_objective | Teacher group and its need/score |1800+600K| Teacher selection / SMDP returns |
| Team role | Carrier/farmer/fighter/escort/scout; slot, claims, health | Ranking, `nns::current_role` | nns::act; death reset | Teacher-implied role |2500| Teacher role and20-round option return |
| Bank timing and route | Carry/score/deadline and existing safe/static altar fields | Ranking, `nne::bank` | tribute_if_needed after cap_bank | Teacher verdict/field; force/win/late protected |1800| Teacher verdict / secured team objective |
| Economy | Gold, item progress; opaque whole teacher plan/save/guarded legal purchase | Ranking, `nne::shop` | shop in place of duplicate preview | Original buy loop |6500| Teacher plan / option return |
| Navigation and positioning | Narrowed legal endpoint/dash tiles, route distances, local threats | Ranking, `nne::move_rank/local_move` | follow_field, retreat_from, dash_away, kite_step | Teacher endpoint |1200+950K /12000| Instrumented movement intents |
| Combat | Visible target intents and ready legal spell alternatives/keep | Ranking, `nne::combat_target/combat_cast` | handle_enemies and cast_on_enemy | Teacher target/spell |8000 /5000| Instrumented target/ability options |
| Engage / retreat | Search verdict, local threats, health/TTD; fight/run/keep | Ranking, `nne::engage` | after cap_fight_final | Teacher verdict; emergency masks |4000| Teacher verdict / return |
| Ward | Teacher-narrowed placement tiles and no-ward | Ranking, `nne::ward_rank` | ward_ahead, ward_reveal, reveal_bush_camp | Teacher placement |1400+600K| Teacher placement / information value |
| Opponent/fog belief | Legal history, nine canonical sectors relative to snapshot | Sector logits used in move.raw23; guarded belief-only rerank | Staged movement hooks | Zero influence | **unmeasured** | Own next-visible observations; target/loss path incomplete |
| Long-term value | Shared context | Win logit, margin per1000 submitted gems, carry-loss logit | nns::act and same-round objective features | Zero influence | Central runtime gate | Outcome/margin regression implemented; carry-risk target/loss incomplete |
| Tactical-search leaf | Bounded simulated leaf deltas, plan and home distance | Bounded residual, `nne::leaf` | active tactical_decide after teacher evaluation; max4/round | Zero residual |2200| Leaf record/target/loss path incomplete |

Team assignments continue to communicate through the original claims/sighting protocol. Roles affect local priorities
and objective features; no additional shared bytes are written. The optional intent proposal in C's audit is a
proposal only. This checkpoint does not claim a separate learned team communication protocol.

## Model, memory and fuel contracts

The small default has a16-unit global projection,8-unit entity projections,16-unit context and8-unit head hidden
layers. The current synthetic exports have8367 parameters each. Entity rows use masks and mean/max pooling.
Candidate bounds are K<=16 and F<=24 (economy F20, search leaf F8). There is no per-decision heap allocation in the
new modules. The log queue is49152 bytes, with at most8 records per turn and explicit drop counters.

`models/budget.json` remains **provisional**, not engine-measured:55000 neural allowance,6000 tail reserve and
10000 default teacher reserve. These numbers are not acceptance evidence. `tools/probe_neural_fuel.py` prepares an
official-release probe for real capture/encode and labelled synthetic dense kernels/records. Full hook/capture
prologues and downstream search reserves also require engine measurement; a kernel probe alone is insufficient.

NFS1 logging and NFT1 telemetry now run after `play_turn`, from leftover fuel. Telemetry prints bounded per-head
summaries with names and invalid/NaN counters. This placement protects decisions from stdout cost, but queueing,
captures and inference still consume in-turn fuel. Credit accounting is experimental; the only exact-equivalence
claim permitted is a verified `teacher_exact` build.

## Schemas, lifecycle and installation

Observation and per-head schemas version feature meanings, normalisation, contexts and output units. All kinds,
including value/belief/leaf, carry semantic hashes. Dataset/checkpoint action hashes include every per-head schema.
Export validates finite f32 weights/checksums; runtime verifies segments and rejects mismatched descriptors.
`tools/install_models.py --profile ...` is the single installation switch. Development/training can install an
unregistered exported directory; release overrides are refused and only validated registry selections may activate.

Release has no new trained heads selected. Original drafting remains trained through the teacher. All new exports
are seeded synthetic initialization, not learned artifacts. Zero residual establishes scorer choice neutrality only;
it does not establish engine neutrality. The recorded protocol amendment requires a neutral_real overhead control.
