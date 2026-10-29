# DZ engine conformance — partial, 2026-10-28

Pinned CLI/SDK 4.0.0, local engine 2.0.0. **G0 is not complete.** The 27-test
design is a work queue, not a claimed completed suite. Instrumented games are
diagnostics, not strength evidence. Truncated 12-round games have no native match
summary, so their bot-fault count is **not measured** (the runner marks this explicitly).

Evidence: `runs/dz-ct-03/evidence.zip` contains source, binaries, logs and all four
diagnostic replays (00collision and 01big-world, both sides). CT-2 intentionally
exhausts fuel. `dz-ct-02` is the earlier three-sample diagnostic; its large-map
camp-group measurement crossed a round and is invalid. The initial `dz-ct-01`
runner wrongly expected a native summary for a truncated game; that harness issue
was fixed and the experiment repeated as ct-02, preserving the same observations.

## Observations

CT-1 single-sample wrapper costs, guest fuel including wrapper/loop/query overhead:

| Primitive | 41×41 (00collision) | 100×100 (01big-world) |
|---|---:|---:|
| `distance_field.compute` (home roots) | 2,370 | 29,943 |
| all allied champion handles/views | 2,779 | 3,830 |
| visible camps | 1,374 | 905 |
| static camp groups | 23,499 | 30,913 |
| champion state | 45 | 45 |
| shared read | 77 | 77 |
| bitboard union | 330 | 463 |

Use exact stdout for small-map values. These are **not** universal per-import
constants or statistically repeated timings. Cost depends on geometry, roots and
list sizes. The bot caches groups and gates field construction with a provisional
size envelope; the full-pool release traces provide the actual runtime check.
Unseen-group root construction, rather than BFS alone, caused the 00vault failure:
expanding every camp tile to nine roots was unbounded. The fixed implementation
uses a bounded nearest-frontier scan and at most nine roots.

- Fuel trace budget words: `(10000000, 100000, 200000, 100000)` for each team.
  SDK startup already spends fuel before `main`, so `fuel_remaining()` is below
  those values on the first turn. Never infer the initial budget from that query alone.
- CT-2: slot 0 captured round 4, deliberately exhausted its budget, resumed in
  round 5, and reported `stale_refused=1`. Native host tests exercise DZ's guard
  with a mutation sentinel. Production traces also show stale aborts rather than
  faults in the deliberately retained failed runtime experiments.
- CT-5: later allied slots in round 1 saw masks `1`, `3`, `7` (and `15`, `31`
  with six bodies), written earlier in that same round. Shared writes are immediate.
- CT-20/21: three picks yielded four bodies, five picks yielded six when drafting
  C&I; `team_size()` counts picks. Both teams' prior picks were revealed on later
  draft turns. Always pick before optional work.
- Partial CT-27 fingerprint: `8b09d31d` across both maps/sides. It covers five
  settings, base HP/strength/focus/range for all 13 bodies, and six fields for all
  84 items. It excludes ability payloads, growth, other settings and camp designs:
  **do not treat this as the complete planned engine fingerprint.**

## All 27 tests, with limitations

| ID | Status | Remaining work / resulting policy |
|---|---|---|
| CT-1 | Partial | Repeat bounded samples; add compute_to/BFS/shadowcast/visibility/damage/move_towards/write costs and more roots/maps |
| CT-2 | Observed | Suspension/resumption established; guard host test passes; add automated transcript assertions |
| CT-3 | Observed | Budget trace words match; first-query startup overhead documented |
| CT-4 | Pending | Deliberate uncaught-exception fixture must be isolated from candidates |
| CT-5 | Observed | Immediate same-round allied writes; add assertions rather than manual transcript review |
| CT-6 | Partial | Allied handle order observed; enemy interleaving and priority-change timing not isolated |
| CT-7 | Partial | Ranged, melee, reset, exclusive cast and shield order checks pass; hidden collision/dash pending |
| CT-8 | Partial | Visible bags/items/cooldowns pass; hidden queries reject 97; channel-time pending |
| CT-9 | Pending | Do not query hidden enemy liveness or infer death from invisibility |
| CT-10 | Partial | Group visibility/state used through SDK; single-spawn-tile visibility fixture not isolated |
| CT-11 | Partial | Every-round elk damage established; nearest-target/tie checks pending |
| CT-12 | Pending | Tribute passive not purchased or valued |
| CT-13 | Pending | No model assumes Prospector benefits outside clusters |
| CT-14 | Pending | Hunter not purchased or valued |
| CT-15 | Pending | Skirmish/Collectors not purchased or valued |
| CT-16 | Partial | Damage interruption, 5 owner ticks, arrival-before-heal verified; Home/spawn-start pending |
| CT-17 | Pending | Basic tribute/lock handling exists; controlled lock/channel fixture required |
| CT-18 | Pending | Teleport and dash disabled in the starter |
| CT-19 | Partial | Two C&I instances/body slots established; linked death/order still needs a fixture |
| CT-20 | Partial | Pick/reveal behavior observed for 3 and 5; missed-pick and 4-pick diagnostic fixture pending |
| CT-21 | Observed | team_size=picks, not bodies |
| CT-22 | Pending | Spawn healing/health purchase/blocked respawn fixtures |
| CT-23 | Pending | Bush and ward visibility fixtures; no belief claims about hidden absence |
| CT-24 | Partial | Even/odd split, occupied respawn and vacating verified; enemy contest pending |
| CT-25 | Pending | Controlled kill-credit fixture |
| CT-26 | Observed | Camp kill resets both CDs; it does not restore a second cast |
| CT-27 | Observed | 1,311 named fields, exact typed numeric bits; automatic mismatch gate |

Do not enable ObjModel, EE or gear utility until their required conformance and
offline calibration gates pass. The full-pool zero-fault result does not close
untested mechanics questions.

## Follow-up fundamentals checks

- **CT-7:** `dz-ct7-actions-01` passes all eight required action checks on
  00collision and 01big-world, both sides, plus shield-then-move on the five-pick
  map. Ranged movement prevents a basic attack; a ranged attack prevents movement;
  a reset restores another attack; a second cast returns code 27; exclusive casts
  after movement return 126, and movement after an exclusive cast returns 127.
  Both melee orderings and shield-then-move succeed. Dash path/hidden obstruction
  cases are still pending.
- **CT-11 cadence: the half-rate hypothesis was wrong.**
  `dz-ct11-asserted-04` passes strict transcript checks on 00elkring and 01elk-arena,
  both sides. A single damaging elk produces 60 HP loss **every round** for sixteen
  successive rounds; the two-elk case produces 120 every round for eight rounds.
  Zero-strength cluster members are counted as awake but contribute no damage.
  Future damage/feasibility models must use the observed per-round rate, not the
  design's 0.5 rate. Nearest-target and tie-breaking are not yet isolated.
- CT-11 fixture history is retained: cadence-01 trapped the subject at spawn;
  cadence-02 established damage but had unrelated parking collisions;
  asserted-03 correctly failed its strict no-error gate; asserted-04 fixes parking
  occupancy and passes. A quiet diagnostic with no damage is now automatically rejected.
- Native team-timeline `owner` is a team string, unlike champion-timeline owner
  objects. A parser regression test now checks that distinction. The completed
  `dz-kernel-02-idle` engine games were reanalyzed after correcting that parser;
  no raw matches were rerun or relabeled as new independent samples.

- **CT-16 / CT-22 subset:** `dz-ct16-channels-03` passes on 00collision and
  00elkring, both sides. Camp damage interrupts recall; base recall completes
  after five owner ticks; arrival precedes spawn healing; the following spawn
  turn restores full health. Earlier fixtures had inaccessible or spawn-start
  setups and remain preserved. Home-emblem and occupied champion respawn remain open.
- **CT-8:** `dz-ct8-visibility-02` passes visible gems/items/both cooldown reads
  and rejects their hidden equivalents with code 97. Hidden `is_alive()` returns
  true for the living idle opponents; hidden death behavior is not established.
- **CT-24:** `dz-ct24-capture-06` passes all four assertions in six cells: 00ribs
  (2 members, 14 gems => 7/7), 00anvil (3 members, 21 => 11/10, lower handle gets
  remainder), 00the-line (23 members). Occupied group tiles prevent respawn even
  after timer reaches zero; vacating allows respawn within two rounds. This is
  engine fixture selection, not per-map strategy tuning. Enemy contest remains open.
- **CT-26:** `dz-ct26-reset-01` establishes Vendetta's credited camp kill resets
  both cooldowns from 6/8 to 0/0. The engine still rejects a second cast (27).
- **CT-27:** `ENGINE_FINGERPRINT.json` pins schema 1, 1,311 fields, SHA256
  `f8e0ad6bc0546a6ac6d66603ee000e44b7be3a895a08319e5f270ee2451c6b3f`.
  Coverage: every non-padding game-setting field, all 13 champion and six camp
  designs/stats/growth/tagged abilities, all 84 full item records, both consumables,
  seven SDK passive constants. Geometry and per-group rewards/timers vary by map
  and are excluded. Runtime fields are distinct from explicitly named SDK constants.
  Exact IEEE bits avoid rounding; inactive payloads and ABI padding are excluded.
  `fingerprint-02` collected equal complete manifests on two maps/both sides but
  intentionally failed before a reference existed. `fingerprint-03` checks the
  pinned reference. The initial play-turn dump exceeded its budget and remains a
  failed diagnostic; the successful version dumps after picking on the first
  10M-budget draft turn. No production bot pays this diagnostic cost.
