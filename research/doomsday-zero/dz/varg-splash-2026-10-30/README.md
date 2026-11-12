# Restricted Varg splash reduction: accuracy remains insufficient

Selected release5cf28cb7 and ordinary productivity traceb4bc106c reproduce
exactly from the final source-only export. All production settings are unchanged.
TRACE_SPLASH is0 by default, alongside TRACE_MODEL/TRACE_SHIELD0. This study
does not change survival, pricing, drafting, Prospector or the advanced planners.

## Mechanism and bounds

The new diagnostic reduces a mixed clear to the existing shield/reset model
only when one live damaging member is the stationary primary. Every other live
member must be harmless, within Chebyshev radius1 of that primary and have no
more HP. All therefore die no later than the primary's killing splash hit.
The executor's actual additive float target score must favor the primary even
at its initial HP against a resource's minimum score. A lexicographic sort
would not prove this when HP differences exceed1000.

Inputs are personal remembered per-member HP, public spawn geometry/stats,
own stats/cooldowns/shield and personally visible members. No native hidden
state supplies a bot prediction. Bounds are64 members and96 owner turns;
the model excludes multiple live monsters, higher-HP/out-of-radius resources,
movement, other actors, healing and Heart's passive. Clear means all members
dead; this does not forecast capture or banking.

10,000 explicit-hit cases independently follow the executor's score, apply
each splash and check whole-group death. These pass through WASI/Node along
with10,000 shield invariants,10,000 reset-damage and14,544 clock cases. This
does not exercise native host ABI.51 Python and13 Node tests pass.

## Instrumentation and admission findings

The first26 games were runtime clean but issued no mixed forecasts. Their
accuracy remains n0/null. A two-game refusal audit identified a budget gate:
cost65000 plus the existing12000 reserve requires more than77000 fuel after
planning. PLAN.json incorrectly called65000 a physical threshold; this is
corrected here and in GATE_PLAN_02.json. Likewise the older single-target
cost45000 gate requires more than57000 physical fuel, not45000.

Singleton helper costs in the first idle batch were1438..4105 fuel. A separate
pilot then used cost55000 plus12000 reserve (physical67000), retaining10000
extra over the singleton gate for the bounded reduction/visibility work. One
late refusal per goal records budget/domain reasons without inventing a quote.
The new pilot and both fresh12-game validations are runtime clean. A mixed
helper example costs8599 fuel. This is measured coverage, not a proof of the
worst64-member native cost. Maximum model line across this study is recorded
in RESULTS.json and remains below the existing512-byte reservation.

The replay reader independently checks member-order HP fingerprints, damaging
target identity, public spawn positions and movement. Matching aggregate HP
alone cannot establish the member distribution. A fingerprint is a sanity
check, not a security hash. Native values are outcome/context checks only.

## Prospective result and limit

With the adjusted gate, idle12 produces one mixed forecast; v76 on the same six
development geometries produces seven. All eight match the native member-HP
fingerprint, damaging target and static initial positions. Idle has one clear;
v76 has three clears and four changed-goal windows, including one predicted-dead
window. None survives the frozen stationary/unshared/no-healing criteria.
Strict accuracy is therefore n0/null for both opponents. No completed,
contaminated case is converted into a successful model-validation case.

For example, quadrants-A R138 correctly matches four live members and predicts
23 rounds,240HP loss and two shields. The actual clear is R160 (23 rounds),
but the body moves twice, takes180HP from another source, loses180HP to the
target camp and casts three shields. Matching time does not validate its
damage prediction; the episode is excluded by the predeclared context rules.

All54 new games have zero native candidate faults/fuel-outs and zero caught
trace errors. These comprise26 initial games, two refusal-audit games, two
adjusted-gate pilot games and24 final validation games. Repeated map-side cells
are not independent samples. All63 local evidence capsules verify. Frozen
analysis-source snapshots and all unsuccessful/insufficient attempts remain.

tools/dz_compare.py comparisons find identical banking in every matched cell
between the new idle/v76 diagnostic variants and their controls. These are
runtime controls, not release-strength tests. Clean final source export03
reproduces both selected binaries. Export01 mistakenly copied a stale cache
and failed before compilation; export02 and source-only03 are the valid checks.
config/paths.json and all prior experiments are preserved. Opponent binary
hashes in provenance identify the loaded opponent; a legacy runner label can
still say idle81 when --opponent-wasm supplies v76.

Full V-M1 and new-job admission remain open. The reduction stays diagnostic
and unpromoted. Do not broaden cohorts after seeing these outcomes. Further
native validation needs controlled stationary geometry or an explicit movement/
multi-monster model. Continue Z6 with Heart's public missing-health damage and
shield mechanism; preserve the selected policy and all open gates.
