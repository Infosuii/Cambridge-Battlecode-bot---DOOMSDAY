# Strategy, objective and role SDK integration

Implemented `bot/src/nn_policy_strategy.cpp` behind `NN_POLICY_V2`. Checked-in default stays off. Builders use the
declared F12 features and `nnpc::build`, ascending public action IDs and exact finite/mask validation. No original
teacher ranking, priority chain, route search, fight verdict, prior, inference or parameter update is called here.

## Execution semantics

- Strategy intents are the declared farm/bank/defend/contest/regroup/attack/retreat enums. Farm and contest expose
  reachable cached-field group availability, preserve a valid current assignment, and otherwise describe a nearest
  static-distance assignment (scout uses oldest observation). Runtime must obtain a direct objective decision
  before physical farming when a new strategy commits; this provisional descriptor is not a substitute policy.
- Bank requires carried gems and potential altar access; destination/deposit are the separate bank head's
  responsibility. When the aggregate altar field exists it can exclude a provably unreachable bank intent. Exact
  per-altar availability is still checked by bank execution; an absent aggregate field is unknown.
- Defend and retreat commit an own-spawn endpoint; regroup commits the nearest current visible live ally; attack
  commits the nearest current visible live enemy, or the newest legal own/team sighting no older than100rounds.
  Canonical coordinate or public-handle ties are deterministic. These are destination executors only: physical
  movement/attacks remain separate direct decisions in the runtime.
- Objective action IDs are public `GroupRec.handle` values. `OptionsState.objective` and `Bot.target_group` are local
  vector indices. Missing cached fields, unreachable groups and malformed/empty group geometry are excluded.
  Narrowing retains the nearest four per canonical quadrant, then fills unused quotas round-robin. Distance then
  unsigned public handle breaks ties. Fixed storage retains at most16per quadrant; no heap allocation per decision.
- Objective features include canonical anchor displacement, actual cached static distance, public rewards,
  remembered camp health/strength, SDK `bc::constants::capture_time`, remembered respawn wait, other ally claims,
  current visible enemies within8tiles of the anchor, and observation age. Unobserved age is current round+1.
- Farmer requires a reachable group; carrier requires gems/potential bank access; fighter requires a current
  visible live enemy; escort requires a current visible live ally; scout requires a reachable group. Role execution
  commits a meaningful initial assignment: farmer farm, carrier bank, fighter attack, escort regroup, scout farm
  toward the oldest observed reachable group (distance/ID tie). A subsequent strategy decision has authority and
  can replace that intent. Roles never invoke an inherited behavior chain.
- Executors recheck the same current availability, commit state/claim/goal, and report legal/executed/changed.
  Failed execution leaves state intact. Claim indices outside the shared encoding publish idle, never truncated or
  aliased group IDs. Runtime owns option start/end/expiry and execution acknowledgments.
- `resume_assignments` is a separate cheap legality/claim boundary for semantically suspended commitments after
  transient whole-teacher fallback. It checks current role availability without reexecuting that role, current
  strategy availability, and an on-map stored goal. Farm/contest require the SAME stored cached reachable group;
  no nearest replacement is selected. Nonfarming bootstrap permits no camp objective. On success it reapplies
  Bot target/claim only where needed, never changes OptionsState, and does not itself authorize physical farming.
  Runtime must require the objective policy commitment first, distinguish semantic validity from censored log
  option IDs, enforce deadlines, and count resumed continuations outside the direct-start numerator.
- All nearby entity features use current visible live records. Threat features sum visible basic-attack strength
  whose attack ranges contain the goal. Unknown non-group walk distances use sentinel10000 (normalizes/clips to4),
  never a Chebyshev distance mislabeled as walking distance. Cached bridge-enabled static distance retains the
  existing SDK primitive's interpretation.

## Verification performed

`run_fixture.py --cxx <root>/artifacts/tmp/native-toolchain/w64devkit/bin/g++.exe --sdk-syntax` passed with the
bundled Python. The first phase compiles the active production source against the actual read-only SDK and actual
Bot headers, so private friend access and real SDK types are checked. The second compiles unchanged production
strategy/candidate source against explicitly synthetic SDK fixtures and executes it.

Synthetic checks cover high unsigned public group IDs distinct from vector indices; exact capture-time feature;
four-quadrant quotas and spillover; canonical mirror bit parity; missing/unreachable cached fields; invalid and
stale execution rejection; visible fighter/escort roles and preconditions; explicit defend/retreat destination;
recent/expired own sightings; dead self refusal; and shared-claim overflow. This is synthetic/native evidence,
not engine gameplay, fuel calibration, model strength, ownership coverage or training readiness. Root owns all-off
official byte identity and integrated verification. No training, collection job, login or submission ran here.

The targeted runner stages ordinary temporary copies under ignored `artifacts/tmp`, leaves production config
untouched and removes its temporary fixture directory afterward.

Subsequent resume fixtures also pass: teacher-altered target/claim is reapplied exactly once; repeated unchanged
resume performs no shared write; an unreachable selected group is rejected even when a different group remains
reachable; carrier banking can bootstrap without a camp objective and is invalidated when the bag disappears.
