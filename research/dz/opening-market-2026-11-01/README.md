# Priced openings and committed delivery — 2026-11-01

Unpromoted engineering checkpoint. Selected defaults, validation partitions and
the release holdout remain unchanged. The current trace candidate is
`8a1f24ea09b4c242e7437579a64410a522806a5efa0125ba5ba80a41bb4ea86a`.

## Implemented

- Complete opening bids can replace one whole group's solo cuts with an isolated
  crew quote. Every remaining cut, Home recovery, delivery and channel is still
  paid. Actual carried stock is credited once; missing later work earns nothing.
  The chosen roster uses the existing consent/role agreement and a fixed project
  deadline. Partial-clear completion releases helpers without restarting the gate.
- Closed delivery no longer grants terminal gem value or speculative equipment
  gains in ordinary auction bids. A bounded first-bag fallback preserves discovery.
- Isolated single-monster crews can pay for a sleep/re-entry cycle. Public designs
  certify the entire formation/staging envelope; live sleep must be observed.
  A crew wakes only before any member has spent its turn, so the last marcher
  cannot substitute one lone hit for the quoted joint phase. Multi-monster jobs
  retain their previous exposure model. This is not general V-M1 acceptance.
- A ready carrier now commits to delivery using the selected `bank_now` policy.
  The actual bag/channel must fit the known window; the deadline cannot slide.
  Banking precedes optional new farm/shop/crew offers, with neutral recovery and
  fresh pre-submit admission retained. This is a finite executable bank schedule.
- Live siege execution gets fuel before speculative searches. Departure from a
  due-respawn spawn checks the next position's exit first. A sealed exit can quote
  an adjacent harmless obstruction, including the complete counterfactual escape.
  Root ownership survives prerequisite children; nested access retains its altar.
- Recovery revalidates the retained ray BEFORE searching alternatives. The old
  ordering could spend the entire budget first and oscillate until death.
- One dated camp-occupancy scan serves all altars. Bank navigation caches the
  actual quoted submission root, with topology/respawn expiry. Fair bank forecasts
  run before cold physical routes; opening tables construct one workspace per turn.
- Forecast validity now follows topology, observed threat strength, gear/channel
  and expiry, rather than an arbitrary four-frame TTL. Submission still checks
  current conditions. Same-turn channel-duration calls share their inventory read.
- Trace builds drain bounded circular-buffer chunks and retain partial writes.
  A full buffer never bypasses the physical fuel guard. The non-trace layout is
  preserved, keeping the selected release byte-identical. Scenario `--source` now
  actually freezes the requested source; unsupported uses fail explicitly.

## Verification and limits

The existing 17-suite host runner passed before the final cache/delivery changes.
Five affected suites pass on the final source (see `FOCUSED_HOST.txt`), including
10,000 independent queue/write schedules, non-sliding delivery and forecast
invalidation. Selected and combined-table builds compile. The current trace
rebuild is byte-identical to the final native candidate; the selected Mac release
remains `437f91c3a6abb160ea151be081c4d410e9e3161d4ef8042c73df2db4063581f0`.

Final26 and independent27 use the SAME candidate. All ten native cells have zero
deaths, faults and fuel-outs. They bank:

| Fixture | A | B |
|---|---:|---:|
| opening-crew | 372 | 288 |
| siege-two-layer | 14 | 0 |
| crew-double-wolf | 0 | 40 |
| isolated-elk | 240 | 300 |
| crew-sequence | 60 | 72 |

The new opening fixture is a controlled capability check, not a tuning map or
strength benchmark. Layered conversion remains poor; wolf-A collects NO gems
despite earning gold. Native acceptance of a useful opening crew bid remains
open. Sleep entry has native traces, but the final synchronized wake and harmless
bridge recovery are not independently isolated/calibrated. Respawn-exit prevention
and ordinary recovery have native execution evidence.

The strict final26 audit stays FALSE: opening rows pass26/33 cycles and layered-A
passes22; layered-B has0. Ordinary crew rows have0 siege cycles. Independent27
also has no siege cycles, so its strict siege audit is FALSE. These gates are
preserved; ordinary banking does not establish general siege/model correctness.

## Rejected evidence

All completed capsules are retained and verified in `RESULTS.json`. Resource-wave
financing06–08 and singleton root leases18 were rejected and removed.09 had six
round5 fuel-outs;12 had one death from exit oscillation;20 had two wolf fuel-outs.
Trace buffering was repaired;26/27 have clean runtime, without claiming an isolated
causal reproduction of every earlier fault. Window variants23/24 banked ZERO in
all six cells each and were removed, including their runtime adapters. Their code
is frozen in their capsules.19 and21 failed compilation (missing declaration and
Wasm32 narrowing respectively), were fixed, and ran no native games.

`ring-control` and `runtime-debug` are INVALID requested controls: before the runner
fix, scenario ignored `--source`. Do not attribute their behaviour to c182eb5.
The separately named `ring-control-valid` really reproduces frozen candidate
`96438ba99effb901075d33f801792391c1d6d7ed4152ce97081cc316d09266b7` and has clean
runtime. `runtime-debug-valid` is also distinct. The cache-debug variant has
intrusive diagnostics; its banking is not final-candidate evidence.

Next: restore useful layered-B access and gem production on wolf-A, jointly model
ability-aware crew phases/arrival and demonstrate an accepted opening allocation.
Then address contested gold/equipment/combat and map access. Do not scale opponent
screens or promote this candidate. No new competitive, validation, holdout,
submission, ladder or online actions were performed.
