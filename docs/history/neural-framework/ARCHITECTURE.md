# Direct neural gameplay framework

The eight gameplay heads are integrated. They are untrained and disabled in the checked-in bot and packaged release. The inherited trained draft network remains separate. The goal is the strongest validated competition bot; neural ownership is a diagnostic, not a percentage quota.

The current path is `Bot::play_turn` -> `nnp::play_turn` -> admitted candidate builder -> direct masked logits -> exact guarded SDK execution. It does not compute a teacher choice, teacher score/prior, or preferred index first. The original whole bot remains the all-off reference and early model-failure fallback. Legacy residual-v1 modules, models and NFS1 tooling remain separate.

## Coverage

| Head | Neural choice | Deterministic work | Implementation |
|---|---|---|---|
| Strategy | Farm, bank, defend, contest, regroup, attack, retreat intent | Available intent descriptors; claims and dispatch | `nn_policy_strategy.cpp` |
| Objective | Camp/group assignment | Exact cached distance, canonical spatial quotas, claim bounds | `nn_policy_strategy.cpp` |
| Role | Farmer, carrier, fighter, escort, scout commitment | Availability, commitment expiry, exact resumption guard | `nn_policy_strategy.cpp` |
| Bank | Save, altar destination, explicit deposit | Per-altar walking distances, locks/channel rules, legal urgent deposit | `nn_policy_economy.cpp` |
| Shop | Explicit affordable purchase, supported consumable, save | Costs, combination gains, raw ABI slots, execution recheck | `nn_policy_economy.cpp` |
| Move | Legal walking/dash endpoint, positioning or hold | Reachability, occupancy, geometric diversity, exact endpoint recheck | `nn_policy_tactics.cpp` |
| Combat | Target plus basic attack/ability or hold | Visibility, readiness, range, supported target rules, actual SDK acknowledgment | `nn_policy_tactics.cpp` |
| Engage | Fight, disengage or hold | Permitted current threats and bounded exact walking retreat trace | `nn_policy_tactics.cpp` |

Drafting uses the inherited model in `draft.cpp`. Ward/fog/history bookkeeping stays deterministic. Dedicated belief, carry-risk and search-leaf networks are deferred; they are not current integrated learned capabilities. A separate critic is available in the later trainer, outside Wasm.

## Model and schemas

The compact observation has173 floats:40 self/global fields, five masked10-feature ally rows, and six masked12-feature enemy rows. Inputs are permitted public, visible or remembered state. Canonical coordinates mirror both sides consistently; terminal outcomes occur only in offline targets. Each decision has up to16 canonical ascending stable IDs and12 normalized features per candidate. There is no teacher position or teacher-prior input. Absent teacher labels stay absent.

`schemas/policy_v2.json` defines per-head meanings. Observation hash is `0x1346e3ba`, action hash `0x16df3b9e`. NFS2 and model interpretation2 are distinct from legacy NFS1/residual interpretation1; incompatible artifacts fail closed.

`configs/model/policy_v2.json` defines G4/E4/context4/head4. The exported untrained model has1056 float32 parameters, checksum `0x5a9d6349c9dc07b5`. Width-four register kernels retain sequential float32 lane operations. Python/C++ synthetic parity and actual record replay test the numeric path. Changing architecture requires a newly measured matching budget; installing a different width silently is refused.

## State, recording and fuel

Role/strategy/objective are explicit semantic commitments with32/8/8-round cadence. Banking/shopping use4/16-round cadence; movement/combat/engage are tactical. A forced combat hold can bypass inference. A mere safe held turn preserves the same live option interval and guarded semantic assignment; actual abandonment or recording cap closes/censors the interval. An ended log ID is never the live-state flag. Death, channel and replacement abandon incompatible assignments. No alternative objective is silently substituted during resumption.

The first admitted same-turn context can serve multiple intent changes; live candidate rows accompany it. Physical effects invalidate it. World refresh is guarded and repeated refresh after a no-op is avoided. Static anchors, objective narrowing and walking fields can be prepared after actions from spare fuel, with position/geometry/field-availability cache keys; live F12 rows are rebuilt at selection.

`models/policy_v2_budget.json` generates `nn_policy_budget.h`. Root admission includes builder bounds, observation, inference, per-candidate recording, execution and tail reserve. Tickets authenticate both candidate and execution reservations. Unsupported or overflowing bounds refuse before construction; fuel increase/round advance fails closed. Macro writes and the final movement recheck have separate execution reserves. A late refusal safely ends the turn rather than starting an expensive whole-teacher search on depleted fuel. An unverified model returns to the whole teacher before preparation.

NFS2 copies bounded immutable record bytes in-turn; checksum, base64 and output run afterward. Recording can target one head to avoid paying every head's data overhead. Pending records drain even after the recording cap closes. Sampling uses install seed mixed with champion ID, once per VM, and persists across turns. Actual SDK outcomes are acknowledged separately from selection. Missing context/ack/closure, overrides, interruption, non-sampling and clock failures are excluded from actor updates.

See `evaluation/results/integration_components.json` and `integration_smoke.json`. Component measurements are bounded observations on reused maps, not universal worst-case guarantees. Larger maps still produce refusals and some fuel exhaustion. Periodic coverage is explicitly partial, per champion and head; it is never summed as if every snapshot were a new match.

## Known action-space limits

Movement uses a conservative known-legal dash subset, excluding hole-crossing paths. Capped unknown distances refuse the whole decision. Combat omits ambiguous champion/camp numeric-handle collisions, offset AoE centers and altar-lock attacks. Shop inventory capacity is an unavailable SDK feature and uses a documented unknown sentinel. These are explicit limits, not claims of full SDK action coverage.

`tools/install_policy_v2.py` installs a saved compatible model/seed/record mask into a fresh development directory. Release verification independently checks that every direct-policy gate is off. Training, validation and promotion remain separate; a trained export alone is not a competition release.
