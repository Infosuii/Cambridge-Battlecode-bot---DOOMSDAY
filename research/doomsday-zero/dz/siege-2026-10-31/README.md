# Persistent siege and actual altar access — 2026-10-31

Development implementation, **not promoted**. `DZ_SIEGE=1` enables it independently
of the earlier losing integrated candidate; `DZ_ECONOMY_V2=1` includes it too.
Both default to 0. No submission, activation, online duel or holdout was used.

## Implemented

- `siege_model.h`, `siege.cpp`: persistent member target, finite progress contract,
  approach/strike/escape/heal-return phases, explicit checked escape path and
  partial-HP reuse. Infeasible targets receive bounded exclusions. No automatic
  fallback to walking into a blocked altar and attacking the same rejected pull.
- Reserve 15% maximum HP, 1.25 times the escape loss and a full surprise camp
  phase. Current protection by a visible ally counts only after that ally's turn
  has completed and it can survive its assigned nearest-target damage. Escape
  still prices the champion alone. Equal-distance ties use native handles.
- Shield credit is limited to the current incoming phase. Required shields must
  actually exist before the executor damages the camp; failed casts withdraw.
  Future cooldown resets, shielding or cooperative tanking are not invented.
- Bounded escape search retains only completely checked paths. Its search may
  stop with a valid conservative path; a partially evaluated path is never used.
- `access_route.h`: first live obstacle on a descending static route, including
  multiple camp layers. A dead ring member is no longer treated as proof of access.
- Cached SDK reachability with remembered live camps blocked distinguishes a
  usable detour from a real camp barrier. Mask construction resumes across turns;
  death/generation changes and respawn deadlines invalidate the cache. Expired
  dead-cell observations are uncertain obstacles and are explicitly scouted.
- Per-tile member indices and exported altar distances avoid repeated SDK tile
  scans. All new planner, field, cast and movement work retains turn/fuel guards.

The camp model remains bounded and conditional: up to 64 nearby damaging members,
current legal observations and a checked walking escape. Nearby enemy contact
still interrupts the camp-only plan. It is not a general ObjModel or EE calibration,
and committed-position support is not the planned multi-turn tank formation.

## Executed checks

Host checks cover persistent multi-visit completion, independent damage/escape
accounting, first-phase shielding, nearest-target ties, unsafe ally rejection,
interrupted path search and multi-layer route dependencies. Existing host suites
also run. Python measurement and negative audit checks are separate.

The official MapBuilder generated `siege-ring-golem` and `siege-two-layer` under
`tests/dz/maps`, with pinned engine hashes and exact camp/wall manifests. The
production bot runs on these with `tools/dz.py scenario`, clearly marked as
correctness fixtures rather than strength evidence.

Frozen `dz-siege-access-fixtures-09` passes the **corrected** audit in
`STRICT_FIXTURE_AUDIT.json`: 169 completed retained-target damage/healing/return
cycles across four cells; no recorded withdrawal deaths, native faults or
fuel-outs. Own camp damage and native healing counters must increase. Banked gems
are positive on all four cells. This does not claim zero deaths outside siege
withdrawals or competitive strength.

The initial auditor could miss a withdrawal ending in death without Return.
It now checks unreturned/censored withdrawals too, requires completion-capable
traces, and has negative tests for fatal interruption and misleading later events.
Superseded reports are labelled in `legacy/`; their passing fields are not current
acceptance. The raw failed/early run capsules remain immutable.

## Strategy result and next work

`dz-siege-route-access-03`, six development cells on boss-battle, guardians and
the-pack versus v65: banked **1.17**, versus **13.0** for the paired selected-source
control subset in `dz-mac-control-dev-01`. Native faults/fuel-outs 0; p99 fuel
72,560. This fails the banking gate. No larger campaign or second-opponent
confirmation is justified. Earlier variants and all failures are in RESULTS.json.

Next engineering priorities:

1. Make equipment/economy progression a prerequisite for expensive gates; do not
   spend the opening attempting an unaffordable boss or abandon basic income.
2. Allocate actual tank and rear attack positions, common crew focus and recovery
   handoff. The one-round committed-ally credit is the foundation, not completion.
3. Couple enemy arrival and combat opportunity costs to clear/withdraw plans;
   the current blanket contact interruption is too restrictive for contested work.
4. Finish the common action enumerator, general native model calibration, opening
   rollout and mobility conformance. V-M1/V-M2, remaining CTs and full release gates
   remain open. Keep the once-only release holdout untouched.

Reproduce using Python 3.12+ and `DZ_CAMBC=artifacts/tmp/dz-env/bin/cambc` on this
Mac. Native CLI access works. Untracked `.vscode/` settings were left untouched.
