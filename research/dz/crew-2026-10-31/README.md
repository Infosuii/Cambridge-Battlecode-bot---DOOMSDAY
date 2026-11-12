# Spatial crews and production recovery — 2026-10-31

Default-off development checkpoint (`DZ_ECONOMY_V2=0`); **not promoted**.

## Implemented

- SDK-free deterministic tank/rear positions, native nearest/handle target ties,
  distinct helper positions, reserved checked tank escape ray and range-aware
  whole-encounter incoming allocation. Coalition bids use this geometry; unsupported
  range, heterogeneous size, missing reach or exhausted budget rejects the quote.
- Actual pose navigation, shared static member focus, current visible consenting
  roster, first-wake readiness, helper release on capture and local recovery-owner
  handoff. Fresh crew ownership also excludes recovered former leaders/legacy solos.
  The handoff branch compiles but no native handoff event was observed.
- One bounded legal neutral frame shared by normal/legacy recovery, travel and siege.
  Observed awake hazards are distinct from hidden uncertain camp occupancy; current
  observed strength is retained and invalidates risk caches. Legacy first-wake paths
  obey admission. Ranged helpers move into their assigned pose before attacking.
- Batched visible-tile sampling and resumable member scans leave planning budget.
  Cold resource fields can be explicitly requested below the Full tier when physical
  fuel permits. Cached static role fields avoid full-map recomputation every step.
- Reachable production gets shortlist coverage; bounded coalition-size trials resume
  across replans instead of repeating only pairs/triples. Helpers pay foregone income.
- Execution preflight and diagnostic fuel floor preserve physical execution headroom
  after one native fuel-out was found. No release thresholds were relaxed.

## Checks and limits

All eight host suites pass, including 1,200 independent stationary camp-phase/order
references, geometry/range/tank/escape invariants, a four-body-only cohort regression
and navigation-budget checks. All 28 measurement checks and four siege parser tests
pass. Selected, standalone siege and economy+siege+runtime-map-table Wasm compile.
Selected Mac output remains `437f91c3a6abb160ea151be081c4d410e9e3161d4ef8042c73df2db4063581f0`.
All nine new immutable run capsules verify; exact results are in RESULTS.json.

- Initial hidden-as-awake scene failed (layered bank0/106); separated evidence from
  uncertainty. Formation-wolf03 banks300/304 with no deaths/faults/fuel-outs and actual
  formed attacks. Runtime-reserve05 demonstrates actual double-wolf focus0 then1.
- Handoff-integration04 has ONE fuel-out (double-wolf B, round150, executor8186 fuel).
  The physical preflight/logging fix removes it in05 and final10. Preserve04 as failed.
- Final10 banks336/448 (double wolf),300/304 (isolated wolf),276/318 (layered gate).
  All six cells have zero deaths, native faults, fuel-outs or caught errors; p9986394.
  The final double-wolf cells use production/solo progression and do not exercise the
  crew controller; do not represent these as final-source multi-member crew validation.
  Final isolated-wolf A has15 formed crew attacks; handoff remains unverified.
- Unmodified strict withdrawal audit passes the two final layered cells:51/43 complete
  escape/heal-return cycles, no recorded withdrawal deaths. The mixed full-run audit
  is false because non-siege fixture cells have zero cycles; scoped details retained
  in WITHDRAWAL_AUDIT.json. This is not all-map or general crew safety acceptance.
- Small four-cell v65 preliminary06 fails badly: mean41.75 vs selected control294.5.
  Observation-only07 does not fix zero Famine production. Cold navigation08 restores
  bank42/28; production/cohort09 improves to84/78, still below control400/236. All these
  screens are fault/fuel-out clean. No larger confirmation is justified or was run.

The formation forecast is a conditional fixed-position camp bound, not general V-M1.
Future traffic, travel, enemy intervention, role changes and hidden strengths are
runtime uncertainties. Siege gate workers still pre-empt the economy and cannot yet
recruit these spatial crews. No competitive parity or completed Z11 is asserted.

## Continue implementing

Replace repeated full-horizon gear payoff with a deferred-upgrade counterfactual;
execute concrete delivery/circuit commitments rather than receding promises to bank
later. Then join partial-clear siege roles to crew scheduling, calibrate combat and
complete the remaining joint action/model/reliability gates. See ../BACKLOG.md.
Release121–124 untouched; no submission, ladder activation or online duel.
