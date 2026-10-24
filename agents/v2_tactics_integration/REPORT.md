# Direct SDK tactics integration

Implemented only the new flat `bot/src/nn_policy_tactics.cpp`, guarded by `NN_POLICY_V2`.
The lead owns the options header, runtime admission, observation invalidation, original hooks and official checks.
No original behavior ranker, tactical search, spell preference, teacher action or behavior chain is called here.

## Implemented behavior

- Move: live SDK movement allowance, terrain/unit/reservation occupancy, SDK bounded reachability, explicit
  walk/slot0 dash/slot1 dash/hold IDs. Static navigation distances target the committed goal, or a walkable
  adjacent approach ring when the goal is static blocked. The static goal field is reused while the goal is
  unchanged. Features use canonical displacements and exact walking distances, not teacher route scores.
- Move narrowing: retain all candidates when they fit alongside hold; otherwise retain the shortest remaining
  static path distance, then canonical ID, per action-kind/canonical compass-octant bucket. Fill with octant/kind
  round robin and then let `nnpc::build` sort by canonical action ID. Normal adjacent choices are present before
  narrowing. Local radius above 16 explicitly refuses the builder instead of silently truncating a design.
- Combat: explicit currently visible enemy/camp basic attack; damage/CC/target-centered AoE in either ability
  slot; SDK-mask-legal ally heal; self shield/reset; intentional hold. Real slot metadata decides the cast
  signature and whether casting excludes prior movement. Basic attack, cast and cooldown allowances are read live.
- Combat narrowing: up to 16 including hold, using kind/octant round robin; channeling entities sort before other
  handles within each bucket. Final rows use the canonical builder. No target worth, TTK or damage ranking occurs.
- Engage: all three verdicts are available. A disengage commits a statically reachable friendly spawn tile.
  Fight preserves an existing goal unless the previous verdict was disengage, in which case it restores a fight
  destination using nearest visible enemy and handle ties. Hold commits its verdict. Strategy intent stays intact.
  Goal/engagement changes set `Execution.changed` so cached observation inputs/context are invalidated.
- Executors resolve the selected ID, recheck live permission, range, masks, occupancy/readiness and execute only
  that action. SDK refusal leaves executed false; successful physical actions update Bot movement/cast flags.
  Combat resolution finishes before issuing the SDK action, so killing a selected unit cannot make a later target
  enumeration erase its successful acknowledgement. Holds are explicit successful decisions with no physical change.

## Bounded coverage and semantics

The fixed combat ID has no entity-kind or ground-coordinate field. Champion/camp handle collisions are omitted
instead of aliasing two actions; handles above the schema bound are rejected. Altar-lock attacks are not represented.
An AoE may aim at a chosen visible entity's center only. Offset AoE centers outside direct cast range are not generated.
Dash endpoints belong to movement, retaining exact coordinate IDs; combat cannot separately identify a striking-dash
target and endpoint. Reset is an explicit untargeted cast, with any later basic attack a separate decision opportunity.
The lead must account for whether its current cadence actually exposes that follow-up opportunity.

The SDK has `can_move`, `can_attack`, `can_cast` and `ability.is_ready`, but no exact per-endpoint `can_dash` or
per-target `can_cast` query. Known legality is checked and the host validates the submitted SDK action. Dash paths
conservatively use the walking-reachable subset, excluding hole crossing and paths through occupied cells.
This is documented incomplete dash coverage, not a claim that every SDK-legal dash/ground action is represented.

Combat F12 `direct_damage` uses the SDK target-dependent spell damage predictor for visible champions, and outgoing
spell damage with the known camp multiplier for camps. Basic attack uses live Strength with the known camp outgoing
multiplier; the SDK has no basic-attack damage predictor, so this is pre-mitigation base damage, not a target-specific
prediction including every champion passive. Cooldown features use configured maximum cooldown. Channel rounds are
queried only on visible channeling champions. Ally/enemy attack totals and incoming damage in engage are sums of live
visible Strength within attack range, not the inherited DPS scorer. Terrain cover is the public bush mask.

Engage escape distance is a dedicated cached static walking field, because inherited `World::spawn_field` can contain
heuristic bridge shortcuts. Full pathfield construction and SDK entity inspection still require official fuel costing;
the implementation makes no accepted budget, 80% ownership, playing strength, training-ready or release claim.

## Checks

Active SDK source syntax passes native C++20 with `-Wall -Wextra -Werror`.
`run_synthetic.py` builds a synthetic SDK harness that includes the actual production builders/executors and candidate
normalizer. It checks canonical rotation, F12 values, endpoint occupancy and hidden refusal, consumed allowances,
stale/dead targets, exact selected slot/target/center, movement exclusion, live cooldown, all ability categories,
namespace collision omission, bounded diversity/channeling, target-order permutation invariance, engage goal/context
mutation and cache invalidation. Results are in `synthetic_result.json`; synthetic SDK behavior is not engine evidence.

No engine game, training, collection, submission, upload, activation, login or browser action was started by this worker.
No SDK, maps, frozen references, synced sources or previous experiment was edited. No commits were made.
