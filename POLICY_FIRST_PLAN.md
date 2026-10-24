# Revised plan: neural policy for the important decisions

Accepted direction from the user, 2026-10-24: aim for roughly80% neural decision control and use neural networks for
the important choices. This is a change of implementation target. It is **a plan, not an implemented policy**.
The code at a85ba8c remains the earlier untrained residual framework with staged hooks.

## What the target means

Neural policies should own the bot's ordinary strategic and tactical choices. Deterministic code provides legal
options and executes the selected action. “80%” is an approximate control/coverage target, not a fraction of source
lines, number of neural classes, inference calls or a claim about current gameplay. Never inflate it with networks
around getters, arithmetic or repeated movement calls. No playing-strength claim follows from coverage.

| Area | Intended neural responsibility | Deterministic responsibility |
|---|---|---|
| Draft | Champion/composition selection; retain the inherited trained draft model initially | Available picks and legal team size; preserve its distinct provenance |
| Strategic mode | Farm/bank/defend/contest/regroup/attack priorities | Check whether a selected intent can be executed; narrowly defined emergencies |
| Objectives and team roles | Select goals, camp/target assignments and local role commitments | Reachability, shared-memory bounds, claim conflict checks |
| Navigation and positioning | Select reachable waypoint/route alternative and local endpoint; spacing/chase | Graph search, terrain/occupancy, legal movement and ability destinations |
| Combat | Select target and attack/ability/mobility action | Exact range, readiness, resource and champion-specific SDK rules |
| Engage and retreat | Decide whether/where to fight, disengage or retreat | Immediate lethal-danger safeguards with explicit reasons |
| Banking | Deposit timing and destination/risk tradeoff | Deposit API legality and provably urgent winning/deadline guards |
| Economy | Choose affordable purchase/upgrade/consumable or save | Actual shop/inventory rules, exact costs and execution recheck |

Use one small shared encoder with task heads; combat and movement include the positioning/retreat contexts. The
table is a coverage inventory, not an assertion that eight rows equal80% of a game. Draft may continue using its
inherited independent trained model while new gameplay heads use the shared encoder.

Initial scope deliberately leaves ward placement and current fog/history bookkeeping deterministic. A critic supports
later training. Dedicated learned fog belief, carry-risk and tactical-search leaf models are deferred; activate them
only with a working target/loss path and measured value for decisions. They do not block the first direct gameplay
policy milestone. This supersedes the previous requirement to finish every optional auxiliary head before that milestone.

## Main architecture change

The new online path is:

1. Read the champion's permitted public/visible/remembered state and check immediate deterministic safety guards.
2. Admit the bounded neural work, including candidate construction, observation, inference and fallback reserve.
3. Construct bounded legal candidates using geometry, SDK rules and documented coverage/diversity rules.
4. Select using direct policy logits, with an illegal-action mask. Deploy argmax; later training may sample the exact
   same logits and must record true behavior probability.
5. Recheck exact legality and execute once. Log the selected intent and actual execution/override result afterward.
6. Run the original whole-bot teacher only on explicit model/runtime/budget failure or in a teacher-data profile.

The ordinary path must **not** compute the original teacher's action, run its full route/combat scoring, add a teacher
logit prior, place its preferred action at index0, or execute the original behavior chain as a selectable policy option.
Direct logits must be able to choose any generated legal option. Neutral feature scales and optional numerical logit
bounds are allowed; a residual bound around a teacher score is not the new policy interpretation.

Deterministic path distances, health fractions and cooldowns remain valid features. Teacher preference scores and
is_teacher/index0 flags are excluded from the new runtime inputs. Candidate order is canonical by stable action IDs,
with a fixed tie rule independent of the teacher. Shop options describe explicit purchases/save rather than an opaque
original buy plan. Strategy dispatch invokes the selected executor, not an unchanged heuristic priority chain.

Candidate narrowing must not silently let the original ranking choose the game. For K<=16, document reachable-option
selection and spatial diversity; use hierarchical choices where necessary. Report whether a teacher label falls
outside the new set during collection, rather than silently replacing it with index0.

## Teacher role and migration compatibility

Keep the original bot as a frozen imitation teacher, evaluation opponent and whole-bot fallback. Teacher collection
is an explicit instrumented profile: it may compute teacher labels and log their stable action IDs/indices. Runtime
model inputs must not depend on those annotations. An absent/unrepresentable label is missing, never fabricated.
No training or collection job is authorized by this planning change.

Retain the current v1 residual code and NFS1 records as a separate legacy experiment. Introduce a versioned direct
policy descriptor, action schemas and records rather than silently changing the meaning of v1 weights/checkpoints.
Plan an architecture/interpretation v2 with explicit direct-policy kind and a versioned record containing:

- observation/snapshot and action-schema identities;
- canonical candidate IDs/features/mask, selected intent, logits and behavior logp;
- optional teacher annotation, marked absent when it was not computed;
- decision source: direct policy, continued policy option, teacher fallback, or deterministic safety override;
- executed action/guard failure and fallback/override reason;
- option start/end and inference/candidate/observation/log fuel accounting.

The exact wire layout is an implementation milestone; no NFS2 parser or model is claimed to exist now. Model registry
checks must reject a v1 residual model for a v2 direct slot even when tensor shapes match. Reuse pure kernels, masks,
encoders and checkpoint machinery where their semantics remain valid; rebuild teacher-dependent candidate builders.

Maintain teacher_exact as a separate all-heads-off reference path and recheck full Wasm byte identity after each C++
milestone. Default release remains the verified teacher until a trained direct policy passes the promotion gate.
Seeded/random direct logits may run only in explicit development checks; they are not a playable replacement.

## How to report progress toward80%

First freeze an opportunity inventory, head cadence, commitment boundaries and emergency reasons before results.
For each decision area above, report direct-policy starts, continued policy options, teacher fallbacks and safety
overrides. A neural decision choosing the same action as the teacher still counts as policy control if its direct
logits independently selected it; merely running a shadow network does not count.

The operational target is at least80% direct-policy ownership of ordinary eligible decision starts on the frozen
framework schedule, with coverage in every listed gameplay area. Publish per-area counts/rates alongside the overall
rate, and report deterministic overrides separately. Continued options retain their initiating source and do not
create extra decision starts. No-op/save choices and refusals stay visible. Predeclared cadence prevents avoiding
hard choices by ceasing to count them. A low-rate strategic head cannot be concealed by many movement calls.

This is a future deployment/control metric. Current new-head ownership in the checked-in default remains0%; only
the inherited draft network is trained. The target can fail; do not rename budget skips as policy decisions.

## Implementation order and acceptance

1. Freeze v2 semantics and coverage inventory. Implement pure Python/C++ direct masked scoring, model/version
   validation and optional teacher labels. Test masks, empty sets, NaN/Inf, stable ties, permutations and round trips.
2. Add a policy dispatcher and legal action builders independent of teacher preference. Integrate objective/mode,
   bank/shop, local movement and combat/retreat progressively, preserving exact off-path identity at every milestone.
   Keep role commitments explicit; retain inherited draft while the gameplay policy is being built.
3. Implement versioned collection and direct-logit imitation/PPO parity. Add grouped local-data splits and execution-
   override handling. Only well-defined, executed behavior/options enter the policy ratio. Synthetic tests only now.
4. Measure complete inference/feature/observation/record cost in the official engine under release/default fuel.
   Reserve enough fuel for deterministic execution and failure recovery. The existing55000 allowance is provisional;
   neither model size nor cadence is accepted until measured. Do not precompute the teacher to hide this issue.
5. Run official direct-policy development plumbing, per-head and combined checks, real record parity and both-side
   smoke/fuel schedules against original/v47/first-hour. Update the frozen protocol with an explicit amendment for
   direct-policy control arms before new results; keep existing results immutable.
6. Package a verified untrained framework with direct heads off and write the later-training instructions. Train
   only in a separately authorized later session: imitation first, then bounded on-policy experiments, per-opponent
   anti-regression gates, and independently rebuilt exports. Activation/submission remains unauthorized.

The last official-build attempts were blocked by compiler-launch policy. Current tools may now permit reviewed
escalation, but this plan-only turn does not retry or claim the issue resolved. Do the official checkpoint first
when implementation resumes. Native tests from a85ba8c belong to v1, not to this planned v2 policy.
