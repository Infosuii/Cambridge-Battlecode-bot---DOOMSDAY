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
| CT-7 | Pending | Hidden collision, ranged allowance, exclusive spell and dash fixtures |
| CT-8 | Pending | Do not rely on visible enemy bag/item/cooldown queries yet |
| CT-9 | Pending | Do not query hidden enemy liveness or infer death from invisibility |
| CT-10 | Partial | Group visibility/state used through SDK; single-spawn-tile visibility fixture not isolated |
| CT-11 | Pending | Critical next: camp cadence/targeting for ObjModel and camp survival |
| CT-12 | Pending | Tribute passive not purchased or valued |
| CT-13 | Pending | No model assumes Prospector benefits outside clusters |
| CT-14 | Pending | Hunter not purchased or valued |
| CT-15 | Pending | Skirmish/Collectors not purchased or valued |
| CT-16 | Pending | Basic recall executes, but Home/interruption/spawn-start fixtures not isolated |
| CT-17 | Pending | Basic tribute/lock handling exists; controlled lock/channel fixture required |
| CT-18 | Pending | Teleport and dash disabled in the starter |
| CT-19 | Partial | Two C&I instances/body slots established; linked death/order still needs a fixture |
| CT-20 | Partial | Pick/reveal behavior observed for 3 and 5; missed-pick and 4-pick diagnostic fixture pending |
| CT-21 | Observed | team_size=picks, not bodies |
| CT-22 | Pending | Spawn healing/health purchase/blocked respawn fixtures |
| CT-23 | Pending | Bush and ward visibility fixtures; no belief claims about hidden absence |
| CT-24 | Pending | Controlled reward split and contest fixture; single-capturer policy not implemented yet |
| CT-25 | Pending | Controlled kill-credit fixture |
| CT-26 | Pending | Controlled Vendetta camp-reset fixture; executor reads live cooldown readiness |
| CT-27 | Partial | Complete canonical runtime fingerprint and automatic mismatch gate still required |

Do not enable ObjModel, EE or gear utility until their required conformance and
offline calibration gates pass. The full-pool zero-fault result does not close
untested mechanics questions.
