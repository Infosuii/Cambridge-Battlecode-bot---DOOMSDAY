# DZ starter results — 2026-10-28

**Runtime foundation works; strength is far below existing bots.** No promotion,
idle parity, contested parity, model-validation or release-holdout claim is made.

## Current release candidate

All three campaigns below used the same frozen DZ source and Wasm. They ran to
normal game completion, in release mode, at official fuel/round limits.

| Run / opponent | Games | Wins | DZ faults | DZ fuel-outs | Mean fuel | Fuel p99 | Mean banked |
|---|---:|---:|---:|---:|---:|---:|---:|
| dz-pool-idle-02 / idle81 | 140 | 140 | 0 | 0 | 27,789 | 57,005 | 917.1 |
| dz-pool-v65-01 / v65 | 140 | 0 | 0 | 0 | 25,162 | 56,428 | 182.0 |
| dz-v76-screen-01 / v76 | 12 | 0 | 0 | 0 | 25,584 | 64,076 | 192.9 |

Zero opponent faults in all three. The idle and v65 schedules cover all 70 maps,
both sides. v76 is a six-map diagnostic strength screen, not a complete league.
Fuel quantiles exclude the first 20 post-header entries per game (draft/boosted
startup); exact fuel-outs and faults come from native events/diagnostics and include
startup. All source, binaries, native summaries, replay bundles and hashes are in
`runs/<run>/evidence.zip`; `python tools/dz.py verify` authenticates them.

Mean collected gems: idle 976.6, v65 268.8, v76 screen 242.3. Against idle, some
wins are gold tiebreaks, including low-output maps. **Idle wins do not establish
economy parity.** No v76-on-idle matched R250/R500 comparison has run yet.

The engine and this starter are deterministic; schedule cells are not independent
random-seed samples. No fabricated seed replication or confidence interval is used.
The development ledger records every campaign. No reserved seed or release holdout ran.

## Known weaknesses in the current release

- Severe camp deaths even without enemies: 00contest, 01starvation, 02guardians,
  02the-pack, 01shortcut. The nearest-group policy is not a feasibility/crew model.
- 02guardians now attacks the camps that block every altar approach, but clears
  them slowly and loses bags; current idle results are 207/200 banked, 72/75 deaths.
- 00contest A collected/banked zero with 48 deaths; 02the-pack B banked zero.
- Against v65/v76, the local strength fallback and basic farming are inadequate.
  Calibrated economy, camp tanking/survival, crew allocation and EE remain necessary.
- Dash, heal, locks as purchased consumables, team messages, the optimal-stopping
  bank rule, and complete draft optimization are not implemented.

## Failed and diagnostic experiments (preserved)

| Run | Finding |
|---|---|
| dz-v0-smoke-01 | First full 00collision game, 1,011 banked at R1259; 0 faults/fuel-outs. Superseded by complete frozen campaigns; initial binaries/raw evidence in `runs/initial-manual` |
| dz-ct-01 | Runner expected a native summary for a 12-round truncated diagnostic; harness error, repeated as ct-02 |
| dz-ct-02 | Three-sample group queries crossed a round on 100×100; invalid cost sample. Other timing/resumption observations preserved |
| dz-ct-03 | Bounded single-sample diagnostics; deliberate CT-2 fuel exhaustion, not a candidate |
| dz-trace-01 | 10 games, 0 faults, 10 fuel-outs; allied ward collisions and large-map startup |
| dz-trace-02 | Ward error removed; 10 large-map startup fuel-outs remained |
| dz-trace-03 | Cached camp design HP removed large-map first-use spike; gated altar still stalled |
| dz-trace-04 | Goal trace showed every altar adjacency occupied; empty roots had skipped gate clearing |
| dz-pool-idle-01 | 140 games, 0 faults, 9 fuel-outs, all on 00vault; runtime check failed |
| dz-trace-05 | Extra startup phase separation did not fix unseen-group root expansion; 11 fuel-outs |
| dz-trace-06 | Instrumentation located suspension inside the nine-roots-per-spawn loop; 45 fuel-outs. Fixed by one nearest frontier and bounded loops |
| dz-trace-current-v65 | Current source, six contested diagnostic games, 0 faults/fuel-outs and no printed caught SDK/module errors; p99 67,398 (tracing overhead); not strength evidence |

Tracing changes fuel and can change behavior. Trace runs never support strength
claims; they exist to diagnose faults and budgets. Most trace runs ended with zero
caught SDK/module errors after the ward fix; final release faults are engine-measured.
All completed diagnostic/failed runs have portable capsules. The first manual
smoke preserves exact binaries/summary/replay but did not freeze its source;
`runs/initial-manual/manual-manifest.json` records this limitation and also preserves
the complete failed ct-01 diagnostic source/replays. Later campaigns have complete
source provenance and support all current claims. Evidence is retained, not overwritten.

## Gate state

- Host core tests: 1,536 slot-codec combinations plus guard, contract, ledger and banking checks pass.
- Z1–Z3 starter: playable, clean source, zero faults/fuel-outs on 140 idle + 140 v65 games.
- G2 sampled runtime thresholds: pass across idle, v65 and the v76 screen; repeat as runtime changes.
- Z4: legal research-prior drafting on all 70 maps; exhaustive utility/opening not implemented.
- G0 conformance: incomplete. G1, G-P1, G-P2, G5–G8: not passed, mostly not attempted.
- Finals-ready: **no**. Existing live bot unchanged.
