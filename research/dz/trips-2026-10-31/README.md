# Collection, delivery and gear trips — 2026-10-31

Default-off development (`DZ_ECONOMY_V2=0`); **not promoted**.

## Source changes

- Bounded complete collection circuits: up to three distinct jobs from six known
  nodes, travel/clear/capture, exposure discount, delivery and deposit duration in
  one finite-horizon schedule. Follow-ups require cached routes and harmless ready
  resources; combat jobs can lead a solo circuit but are not chained speculatively.
  Capture endpoints use worst static distance over supported member tiles.
- Retained job sequence, fixed per-job/overall deadlines, respawn-generation
  completion evidence, stolen/stalled-job skipping, fresh crew reassignment and
  actual terminal banking. Unrelated kill income cannot finish a job. Optional
  quoted bank->home equipment visits are retained through a Shop phase. Death or
  changed altar access invalidates the plan. This is a bounded local circuit,
  not a global optimum, arbitrary combat circuit or complete Z7/Z8 certificate.
- Affordable batch gear values: partial shards earn only actual stat growth;
  passive value appears once at real completion. Combination bonus growth comes
  from official result metadata. Cash spent, travel and equipment arrival time
  are explicit costs in visit/defer schedules. Macro and gear use the same
  attainable production stream, including delivery/return/replenishment costs.
- Conditional job unlock estimate compares full-home-health current gear against
  the exact quoted inventory on up to four known damaging jobs. It credits no
  unfunded passive. Access, future ownership and enemy pressure remain uncertain;
  this is not general V-M1 or calibrated gear utility. It only evaluates the
  selected affordable project, so the broader project frontier remains unfinished.
- Gear quote work is scheduled before objective/circuit search and cached across
  turns. A truncated ranking retains a legal evaluated batch and rotates candidate
  coverage. Previously every over-budget search discarded all its candidates and
  retried the same prefix, preventing gear visits despite thousands of unspent gold.
  Exact champion type is cached per search to avoid repeated SDK queries. The
  final buy still checks actual inventory, cash and can_buy through Actuator.
- Persistent neutral recovery: after a checked ordinary escape, hold Home until
  physically home and fully healed. Merely stepping out of camp reach cannot
  reactivate farming. Siege retains its existing precise shield/strike controller.

## Evidence and limits

All nine host suites pass, including1,000 independently enumerated complete-route
references, fixed-deadline/delivery/shop/abandonment states, recovery latch and
partial-shard/passive/combination timing checks. All28 measurement and six audit
checks pass. Selected and economy+siege+runtime-table builds compile. Selected
Mac binary remains SHA437f91c3 (full hash in prior checkpoint); Windows selected
SHA5cf28cb7 unchanged. All nine new immutable capsules verify. See RESULTS.json.

01/02 expose one-job deposit churn and absent gear visits. 03/04 add common
production accounting, unlock estimates and quote scheduling, but gear still
never executes. 05's new quote diagnostic proves every long search is discarded,
even with ample remaining fuel. These failed intermediate snapshots are preserved;
01 also contains a corrected extra-token include warning in its frozen source.

06's retained/rotating frontier executes actual planned purchases:130/170 logged
buys on recovery-shop A/B,59/61 on isolated-wolf and29/34 on collection-circuit.
Recorded multi-job circuits are134/99 on collection-circuit A/B. Banks224/196
(recovery shop),284/288 (wolf),1001/1004 (circuit); all six cells have zero deaths,
faults, fuel-outs or caught errors, p9988013. Idle correctness fixtures are not
strength evidence. Optional deferred Home phase has host coverage; zero sampled
TRIP_HOME markers means native phase-transition proof remains incomplete.

07 finds a reliability regression: layered A/B banks276/92, and B has three
recorded withdrawal deaths in two intervals. Native traces show ordinary workers
escape and re-enter camp reach before healing. The final latch09 banks354/170,
with zero faults/fuel-outs and strict unmodified audit PASS on both sides:62/43
complete escape/heal-return cycles and no recorded withdrawal deaths. Scenario
survival is still not general release acceptance; exact deaths/cells are retained.

08 is the only competitive screen here (pre-latch source): Famine v65 banks63/11
(mean37), worse than prior crew09's84/78 and selected control400/236. It fails the
preliminary gate; no larger opponent campaign, validation pool or promotion was
run. Final latch source09 has targeted layered checks only; do not relabel08 as
final-source evidence or claim a competitive gain.

## Continue

Priority is contested production and scheduling, not another threshold sweep.
Single-job deposit churn remains inefficient on sparse maps; model bounded
renewable circuits, capacity/survival and shared bank schedules. Integrate real
spatial crews into persistent siege, complete independent crew/focus handoff,
and couple combat opportunity costs with macro work. General ObjModel/EE,
full action enumeration and release gates remain open. No holdout121–124,
online duel, ladder action, submission or main merge used.
