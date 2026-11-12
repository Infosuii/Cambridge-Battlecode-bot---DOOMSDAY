# Owned crews, renewable production and task allocation — 2026-10-31

Default-off `DZ_ECONOMY_V2=0`; **not promoted; competitive/runtime gates fail**.

## Implemented

- Six-champion subset DP for immediate task allocation, with objective exclusivity.
  Actual disjoint alternatives price foregone work; removed the duplicated solo
  opportunity charge that counted several bodies farming the same camp at once.
  Compact local actor bits, active-table copying and physical budget checks keep
  a feasible prefix when interrupted. Optimality applies only to a complete
  search over the supplied bid estimates, not the whole game or an interrupted DP.
- Three-visit renewable circuits, explicit full-generation work/respawn timing,
  cumulative HP budget, release of spawn occupancy, bounded conversion/delivery
  deadlines and observed generation counters. Shifting a delayed ready tick is
  not another capture. Skipped visits resynchronise the next repeated generation.
- Caller-owned crew offers; self is included and is the publishable lowest slot.
  Healthy idle-at-home capacity differs from a committed shopping/recovery trip.
  Existing physical partial/capture/cooldown workers are fixed; new assignments
  cannot implicitly recruit a siege worker into an unaccepted role controller.
- Native targeting-aware melee role alternative, bounded partial-clear visits,
  checked individual escape routes with other poses occupied, paid heal/return
  time and current-HP admission. No future shield, ally protection or reset credit.
  Joined crews can retain visible task consent after releasing the global offer
  register, allowing another pending offer; concurrent independent crews still
  need native validation. Recovery handoff remains unverified.
- Role geometry cached across travel/HP changes, invalidated by roster/gear,
  camp geometry/strength, topology and nearby replenishment. Current HP and fire
  readiness are always re-evaluated. Per-turn exact equipment decoding is reused;
  auction allies use conservative visible stats, with exact inventory refinement
  in the executable crew controller. This avoids spending the first-quote budget
  decoding all five bodies before producing any bid.
- Own successful neutral attacks and capture progress count as contribution for
  starvation recovery; travel alone does not. Crew release clears role ownership,
  stale promises and pending navigation. The actual capturer retains its slot.
- Cached fixed-task reservations replace per-objective SDK/shared-memory scans.
  Model/search budget stops preserve valid work. Map-sized spell targeting gets
  an explicit operation budget (this does NOT fix the remaining Vesper R9 fault).

## Evidence and exact limits

Nine host suites pass. New checks include 200 independent exhaustive task-allocation
references, sparse global-slot remapping, productive-helper/no-solo opening cases,
2,000 independently enumerated distinct/renewable schedules, cumulative HP,
delayed-conversion identity, skipped-visit recovery, tank selection and bounded
partial visits. All 28 measurement and six parser/audit checks pass. All 24 capsules
verify frozen sources, binaries, maps, summaries and replays. RESULTS.json retains
all intermediate failures; do not count source variants as independent samples.

01–05 expose startup offer deadlocks and insufficient modelling budget. 06 enables
partial quotes; 07's geometry cache produces 170/60 actual formed elk attacks.
07 still has three fuel-outs elsewhere. Initial DP08/09 exceeds runtime gates
(43/60 fuel-outs); compact active tables/budget boundaries remove these in11/12.
These are failed snapshots, not accepted milestones.

Final strategy source is represented by untraced22 and diagnostic23. In23, banks
are 585/30 on isolated elk (initial01 was0/0),234/92 on the layered gate. All four
cells have zero faults/fuel-outs; the unchanged strict layered audit passes 43/24
complete escape/heal-return cycles with no recorded withdrawal deaths. The side
asymmetry and limited fixtures do not establish general ObjModel or Z11 validity.
The final source only adds diagnostic phase marks after23; default-off output
and compatible flag builds are checked separately. Full release acceptance is open.

Famine remains decisive rejection:22 banks 21/41 vs selected control 400/236, with
ONE Vesper fuel exhaustion on round9 on EACH side. The spell-board guard does not
repair it. Earlier14/16/17 stalled all five bodies at spawn with zero production;
19 exposes five participants but zero bids after setup. Conservative observed
bids20 restore production, but not strength or the cold-turn runtime gate. The
instrumented24 profile changes scheduling enough to stall again (zero income,
zero fuel-outs); it does not prove the uninstrumented fault is repaired. Stop
larger competitive campaigns. No validation/release pool or promotion was used.

## Next implementation

1. Isolate/fix the uninstrumented Vesper R9 cold path without relying on intrusive
   profiling that changes first-quote admission. Preserve execution fuel through
   roster/quote setup. Do not treat zero-fault but idle runs as success.
2. Complete ability-aware objective forecasts/execution using the existing reset,
   shield and champion primitives. Basic-only admission is still conservative;
   controlled partial-wave success is not general V-M1. Prioritise economic
   progression and productive contested tasks over more retreat thresholds.
3. Join ordinary crew roles to persistent siege ownership, support/focus/handoff,
   capture progression and productive bank schedules. Current code respects
   siege workers but does not make them participate in these spatial crews.
4. Finish joint combat/action enumeration, opening/map access and remaining
   conformance/model/release gates. A serious integrated candidate must pass
   independent opponent/validation checks before selection. Holdout 121–124 is
   untouched. No submission, online duel, ladder action or main merge occurred.

## Final build identity

The final selected-default Mac build remains
`437f91c3a6abb160ea151be081c4d410e9e3161d4ef8042c73df2db4063581f0`.
The final compatible `DZ_ECONOMY_V2 + DZ_SIEGE + DZ_PLAN_TABLE` build is
`fd284dd2e5a5252aa6e9633b6cebf4377d0bb8e1b6f09bf9a407451c612b1d51`.
This compatibility build is not native competitive validation. The recorded
Windows selected release `5cf28cb7…` is preserved, not rebuilt on this Mac.
