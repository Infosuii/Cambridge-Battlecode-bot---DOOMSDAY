# Persistent opening projects, progression and retreat lanes — 2026-10-31

Development implementation under `DZ_ECONOMY_V2=0`. Not promoted; strict
withdrawal reliability is still unaccepted. No competitive screen, release
holdout, ladder, activation or submission was used in this checkpoint.

## Implemented

- `gate_plan.h`, `access_route.h`, `siege.cpp`: resumable full static route,
  successive camp cuts (up to12), per-cut geometry/checked escape, repeated basic
  visits, withdrawal/Home/healing cost, final delivery, and per-altar alternatives.
  Scans advance eight route steps or one cut quote per call. Partial scans cannot
  publish a ready plan. Member/path dependencies and respawn deadlines invalidate
  it; unrelated farming does not constantly restart it. Gear changes reprice the
  inspected geometry rather than discarding the route.
- `economy.cpp`: NEW gate projects compete with farming and executable equipment
  visits. Farm -> Home -> opening -> delivery is a concrete itinerary. Gold
  continuation remains valuable with delivery closed; gem/gold continuation rates
  come from the same solo job, not independently maximised incompatible jobs.
- A bounded commitment makes the selected 'one farm/shop, then open' plan happen.
  It does not keep pushing the gate after another job. The project persists across
  layers, with a stable execution deadline. Partial camp HP remains in memory.
- A live route blocker can suspend an inner target, clear the respawned outer
  barrier and resume the parent. Stacks are bounded and reject cycles. Death,
  infeasibility and timeout clear stale commitments. Timed-out work withdraws.
- Known respawning camps have DESIGN HP in the ledger, not live occupancy. Both
  threat and movement checks now respect that state and the step's arrival tick.
  A camp due to respawn on arrival is conservatively blocking. Visible current
  strength is read for all included damaging camps, not only the intended group.
- Waiting for an occupied attack tile still runs health/withdrawal admission.
  Approaches do not invent a future shield cast. A cheap nine-cell movement mask
  preserves a backtrack to the checked escape, with a raw surprise phase; retry
  and detour movement use it too. It is a conditional safeguard, not proof against
  every future traffic change.
- A blocked escape publishes Retreat. A healthier visible teammate ahead of the
  retreating body yields Homeward by a checked step. The claim is only a soft hint;
  current legal position/HP and local threats drive the reversible action. Healthy
  yielders do not create a chain of full-HP distress messages.
- Completed safe cuts can convert bags or resume a parent without starting an
  unnecessary recall. Actual altar access ends the project and converts carried
  gems. Live strike/escape admission remains separate from strategic estimates.

Limits: static route choice is not a global minimum-work path; at most12 cuts,
128 path dependencies and512 spawn cells are supported. Future camp maintenance,
traffic, enemies, ability/support changes and scaling can change completion cost.
Unknown/unsupported paths never certify reachability. The runtime replans and
uses finite exclusions/commitments plus the proven fallback. This is not general
V-M1 certification, a completed tank formation or completion of the full Z8 scorer.

## Executed checks and failures

The first attempt `dz-opening-integration-01` failed compilation (mixed SDK integer
types in std::min), was corrected, and ran no games. Its build folder remains local.
Frozen completed capsules02–10 preserve every subsequent scenario, including
failures. No larger opponent campaign was run while these defects were present.

The early layered fixture banked0/0: the receding planner did not execute its
promised second step, and restored design HP falsely blocked an empty retreat
corridor. The fixes restored camp damage and delivery. Replay inspection then
showed a healthy teammate occupying the only exit while the clearing body lost HP.
The new lane-yield behaviour is observed in native traces (e.g. sideB R89–91).

Final-source `dz-opening-checkpoint-10`: layered fixture banks340/247; recovery-shop
banks228/240. Four games, zero native faults/fuel-outs, p99 fuel73,083. This is
functional scenario evidence, NOT a strength result. The strict existing audit
still fails: WITHDRAWAL_AUDIT.json records completed cycles AND deaths in recorded
withdrawal/censored intervals. Missing trace closure may broaden some intervals;
no threshold was loosened and no general no-death claim is made. Do not promote
or use a large competitive campaign to disguise this remaining reliability gap.

Host checks cover independent repeated-visit tick accounting, partial HP, horizon,
route layers, resumable scan/capacity failure, path/gear/respawn dependency changes,
arrival-tick occupancy, backtrack reserve, lane yielding and stable commitments.
All host suites,28 measurement and six audit/parser checks pass. These host checks
are not engine acceptance of the general objective or team model.

Default-source Mac Wasm is restored to the prior SHA256
`437f91c3a6abb160ea151be081c4d410e9e3161d4ef8042c73df2db4063581f0`.
An initial unconditional movement-function parameter changed the default hash;
its API/call sites are now explicitly compiled only in the development candidate.
Selected Windows release SHA5cf28cb7 and default feature flags remain unchanged.
The combined ECONOMY_V2+PLAN_TABLE+SIEGE build compiles (SHA0acd71ce), as does
standalone SIEGE (SHAfc2c0e98). Those are compile checks, not extra engine games.

## Next engineering

1. Real tank/rear/escape positions and shared crew focus/roles. Replace crowds on
   payout/attack cells with formation and lane ownership. Diagnose actual fatal
   withdrawals and legacy fallback interaction; strict audit remains a failed gate.
2. Integrate resource upgrades with actual future job/formation feasibility,
   opening maintenance cost, capture roles and opportunity costs. The bounded
   opening project is present, but its forecasts are not a calibrated general model.
3. Finish combat/retreat/capture/ward action enumeration, native calibration and
   remaining conformance. Keep release defaults and reserved holdout untouched.
