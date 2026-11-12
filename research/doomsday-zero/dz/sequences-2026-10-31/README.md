# Sequential crew projects and recovery ownership — 2026-10-31

Default-off `DZ_ECONOMY_V2=0`. **Unpromoted; contested economy still fails.**

## Implemented

- One actual formation per surviving monster, with resumable eight-neighbour BFS
  between roles. Serial routes avoid other crew positions; a role-swap cycle uses
  a checked parking move. Missing/disconnected/oversized paths reject the quote.
  Work resumes from geometry, escape-ray, BFS or pricing cursors across turns.
- Safe staging and re-entry routes, with helpers entering before the front tank.
  Movement prices use native nearest/handle targeting at the planned positions;
  escape and immediate attack admission retain each body's full raw camp reserve.
  Each phase pays repositioning, attacks, escape/heal/return visits and one final
  capture. It cannot claim the whole objective reward after a partial search.
- Execution follows one agreed walker/waypoint at a time, regroups off the camp,
  and advances to the next live member. Awake targets now obey the formation/fire
  gate too. Direct checked steps avoid rebuilding a full map field per waypoint.
  Known cleared own spawn tiles open in staging navigation. Current observations,
  occupancy and neutral recovery remain authoritative at every action.
- Canonical slot order, own-group topology counters, surviving-prefix matching and
  generation identity preserve future geometry after a member dies. Changes in
  other geometry, roster, equipment or scene invalidate it. Completed unchanged
  geometry survives an arbitrary age; unfinished jobs expire without progress.
  Spare end-turn fuel advances geometry instead of waiting eight auction rounds.
- Bounded recovery projects retain partial work and renew exact-round ownership
  while healing. Home/Retreat publishes the project objective; a recovering crew
  cannot silently advertise its members as idle shopping capacity. Fresh different
  assignments supersede the old recovery project. Current real movement/work
  extends project progress; travel does not count as income for starvation.
- A completed crew alternative can re-enter the auction during the legacy latch;
  failed pricing still keeps the proven fallback. Winning/nearby/deadline banking
  takes priority over a recovery commitment. Existing bank and release defaults stay.

## Evidence

All ELEVEN host suites pass. New checks include 120 independent shortest-path BFS
references, tiny-budget resumptions, disconnected rejection, physical serial role
marches and swap parking, movement exposure against the independently implemented
native-targeting adapter, recovery-before-unaffordable-travel and invalid inputs.
Protocol checks cover finite recovery ownership and fresh reassignment.

A new official-MapBuilder fixture, `crew-sequence`, has three adjacent wolves and
no resource distraction. Final10 banks 48/300, zero native deaths/faults/fuel-outs;
164/370 recorded formed attacks and 16/37 recorded later-phase entries. There are
no recorded unformed crew attacks. These are individual trace events, not counts
of independent objectives. The persistent side asymmetry remains a liveness/
allocation concern; the fixture is not competitive evidence or general V-M1.

Final09 layered fixture banks 416/127, zero faults/fuel-outs. The unmodified strict
withdrawal audit passes 50/22 complete escape/heal-return cycles and has no recorded
withdrawal deaths. This is scoped siege/neutral recovery evidence, not certification
of every crew return route. Final08 Famine banks only 77/7 against selected control
400/236, despite zero native faults/fuel-outs. Stop larger opponent campaigns.

All TEN capsules (32 cells) verify source, binaries, maps, summaries and replays.
01/02 failed elk production; 03 exposes paid entry/ownership limits; 04–07 retain
successive lifecycle fixes. RESULTS.json keeps every failure. Source variants and
trace/untraced runs are not independent confirmation. 08/09/10 match the final bot
source except documented build flags. Selected-default Mac SHA is unchanged at
437f91c3…; full selected/combined build identities are in BUILD.json. Windows release
5cf28cb7… is preserved, not rebuilt here. No validation/release holdout or online
submission/duel/ladder action was used.

## Remaining engineering

These are conditional static-scene economic estimates: future teammate consent,
traffic, enemy intervention, cast restrictions and home routing can change them.
Live full-roster readiness and retreat checks prevent using a quote as proof of
future survival. There are at most 64 monsters, a 16,384-cell route grid and 128
steps per route; unsupported work retains the fallback. Ability-aware multi-actor
phases, independent crews and general ObjModel/EE calibration remain unfinished.

Next priorities: legal per-body resource/project freshness, disjoint crew/reward
allocation and equipment progression; verify native crew reward-credit mechanics
before changing recipient policies. Then integrate actual resets/shields/abilities
with phase power, joint combat/action selection and opening/map access. Final
conformance and independent release gates remain required. Keep the full goal active.
