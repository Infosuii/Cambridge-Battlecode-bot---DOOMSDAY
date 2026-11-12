# Resumed fundamentals: release gates and hidden obstructions

The user's current order is release validation, fewer than ten stuck episodes
without increased stall/idle time, then the Z plan. Map/item tuning is now
authorized, with separate-opponent checks. Earlier deferral notes are historical.

## Paused release changes: measured before retention

Both pools run from a9723ba have 140 games and zero candidate faults/fuel-outs.

- `dz-resume-release-idle-01`: banked 921.91. Against dz-gear-idle-02, +3.8
  (paired SE 9.4), broadly unchanged.
- `dz-resume-release-v65-01`: banked 228.82, zero wins. Against
  dz-parity-release-v65-01, -41.5 (paired SE 13.7), four wins lost. Reject the
  bundled change as a strength upgrade.
- Restore previous danger scoring in movement while retaining the exclusion of
  enemy-spawn attack targets. `DZ_PATH_REACH_ONLY=0` is now the default; the
  paused reach-only score is retained as an explicit experiment flag.
- `dz-resume-path-control-v65-01`: banked 267.56, four wins, zero faults/outs.
  Against prior release baseline, -2.8 (SE 6.5); against paused candidate, +38.7
  (SE 13.7). `...path-control-idle-01`: banked 917.58, zero faults/outs.

All comparisons use tools/dz_compare.py. Deterministic map/side cells are not
independent seeded trials or evidence of elite strength.

## Trace correctness

The claim that trace compensation makes production decisions fuel-neutral was
too strong and unsafe. Outer diagnostic scopes called trace(), crediting the
same interval twice. Unsigned executor-cost logs then wrapped to ~2^64. The
new SDK-free TraceMeter credits nested spans once and discards spans crossing
rounds. Host tests cover nesting, interleaved real work, bounds and suspension.

Governors and action gates now use **physical fuel**. Compensation is restricted
to diagnostic profiles. Trace builds can still make different budget decisions;
release pools are required for strength claims. Cheap buffered integer output
remains. DZ_TIME is one formatting call, not many fragments. Temporary
PRE_EXEC/CALL_EXEC/POST_EXEC output is removed; expensive fuel profiles are opt-in.
DZ_TRACE_PROFILE was defined outside the runner's config override file; moved it
to config.h so the documented option works. Initial tangle-01 failed before
running for this reason and is retained locally.

A second trace-only bug queried target.position() after moving out of its vision.
Three such diagnostic errors quarantined the executor (00packs), creating false
stuck bodies. Trace output now uses cached/static coordinates and cannot make
that private-state query. The complete six-cell meter-window-02 check has zero
native faults/outs and zero logged caught errors.

Failed diagnostics remain failures: window-01 has one out; meter-idle-01/02/03
have 15/9/2 outs, respectively; the first obstruction trace pool has five.
Never relabel them as runtime passes. Profiler tangle-02 also has two outs.

## Actual stalled movement: hidden occupancy

On 02the-pond A, the stuck Vendetta at (25,15) chose (24,16) every turn;
SDK move returned false. An ally occupied that bush tile but was absent from
the actor's personal view. Offline native scenes establish the obstruction;
the bot never reads that hidden ally's state. Similar routes recur in corridors.

The actor now remembers a tile for six rounds only after an actual SDK move
returns false. Actuator rejects due to fuel, movement restrictions, channels or
exclusive casts do not create a tile belief. Eight entries bound memory/scan
cost. The next observation merges these short-lived hints into dynamic occupancy
before routing; reaching a remembered tile clears it. This changes routes toward
existing productive goals, not the detector or the goals' work classification.
No wandering/random movement was added.

`dz-resume-obstruction-idle-01`: 5 stuck episodes, R1000 stall 3.2%, idle 0.9%,
progress 57.6%. Prior paused metric: 27 episodes, stall 3.6%, idle 0.9%.
This trace had five outs, so the metric improvement alone is not a runtime pass.

An additional field gate checks fuel **after** root construction and immediately
before the SDK field computation, leaving execution/footer space. Low-budget
turns follow a cached goal field instead of authorizing another expensive BFS.
`dz-resume-obstruction-idle-02`: 140 games, zero faults/outs/caught errors,
6 stuck episodes, stall 3.4%, idle 0.8%, progress 57.8%, banked 927.1. This closes
the requested <10 metric on that frozen source without increasing stall/idle.

The first obstruction release pair precedes this last gate: idle 917.29 with
zero faults/outs; v65 244.41 with two candidate outs. Its paired v65 change
versus path-control is -23.1 (SE 12.8); it is not a clean accepted checkpoint.
Native summaries also contain opponent fuel-outs, which must not be attributed
to the candidate.

## Subsequent checks and current experiment

The misleadingly named `dz-resume-final-{idle,v65,productivity}-01` passes
runtime checks but has 18 stuck episodes. A cold group field could never be
built late in a busy turn; the safety fallback then had no cached route. This
version is not selected. It also drops v65 banking to 231.54.

The corrected `dz-resume-coldfield-{idle,v65,productivity}-01` triplet completes
420 games with zero candidate native faults/fuel-outs. Productivity trace caught
errors are zero. Requested cold fields are built before the following planner
work. Low-budget fallback also preserves post-move attack opportunities.
Productivity: **7 stuck episodes**, progress 58.1%, stall 2.8%, idle 0.8%.
Release idle banked 911.85 (-5.7, SE 8.4, versus path-control); v65 233.99
(-36.4, SE 14.6, versus the prior 270.36 baseline). **Do not accept that bundle
as a strength improvement.** The zero-runtime-failure/productivity result does
not erase its contested regression.

Two v65 ablations completed on the same source, with one boolean each:
`dz-resume-ablate-nav-v65-01` disables DZ_FAILED_MOVE_MEMORY;
`dz-resume-ablate-gate-v65-01` disables DZ_LATE_FIELD_GATE. Defaults currently
enable both while the experiment is in progress. Check results before deciding
what to retain. Results: nav disabled 240.06, gate disabled 236.81, both zero
faults/outs. Neither alone restores the prior baseline, so attribution remains
unresolved. A new same-source both-disabled control is
`dz-resume-ablate-both-v65-01`. `dz-resume-short-block-{v65,productivity}-01`
tests a shorter hint covering only the next turn (two-round expiry). All three
completed: both disabled restores 271.29 with zero faults/outs; the short hint
gives v65 236.67, seven trace episodes, stall 2.8%, idle .9%, zero faults/outs.
Shortening the lease alone does not restore contested performance.

The next candidate limits the hint to strategic travel with no visible enemies.
During visible contact, live occupancy takes precedence over stale hints that
could seal an escape route. The late gate defaults off in release and always
applies in instrumented builds, where the extra work required it. New triplet:
`dz-resume-strategic-nav-{idle,v65,productivity}-01`, currently pending. Default
short-hint flag remains off (six rounds). All source remains experimental until
both strength and productivity pass. Full evidence verification passed for all
capsules present at its start; later campaigns need their usual verification.
The host and 25 measurement tests pass. A final selected-source manifest remains
pending.

Strategic-only candidate: idle 918.46 (0/0), v65 246.59 (0 faults, two outs),
trace 927.11 (0/0). Not accepted. The next refinement requires three consecutive
same-tile rejected moves before issuing a remembered hint. The release field
gate checks physical fuel against the conservative field estimate plus 4k;
instrumented builds keep the larger reserve gate. Cold-field requests are
serviced before planner work. New pending triplet:
`dz-resume-persistent-nav-{idle,v65,productivity}-01`. This remains experimental;
inspect native runtime gates and paired comparisons before retaining it.

The five-to-six remaining trace episodes are mostly unreachable islands and
long corridor routes. They remain real work to improve; fewer than ten does not
mean all progress pathologies or full V-M1 are solved. Continue Z9/Z10/Z11 only
after the final release gates; keep deterministic training versus separate
opponent validation explicit.

## Later movement and purchase hypotheses (active checkpoint)

Persistent hints, own-income starvation and visible-only helper variants did not
pass all gates; their immutable capsules preserve the failures. Current active
state is at the top of CLAUDE_HANDOFF.md. Hidden allied occupancy is confirmed by
offline native scenes and failed-move diagnostics; rejected moves retain the
movement allowance. Immediate same-turn retries reduce the stuck count but lose
v65 banking. Narrowing them to persistent failed travel is the next controlled
experiment, before accepting any purchase tuning. No candidate is promoted.

Strategic retry triplet: idle916.14, v65245.36, trace9 stuck / stall2.8 / idle.9,
zero native faults/outs. Matched idle delta is +.01pp (display rounds unchanged),
not strict nonincrease proof. Retry-off source control v65262.71: delta-17.4,
SE8.1. Same-source v76 retry224.61 vs off225.14: delta-.5, SE8.9; clean.

Z9 first-purchase trial01 stays disabled: idle921.71 vs916.14, with one fuel-out
(00rushbait-v2 B, Marcella R83); v65238.66 vs245.23, delta-6.6 SE7.8; trace9 stuck,
stall2.8 idle.8 clean. Subsequent untested revision caches home distances during
setup and caps cold shop analysis15k. It is not a calibrated marginal-value model.

## Final paused selected development foundation

User requested wrap-up. Selected cold-retry source has3 stuck versus clean
source control30, matched stall-.1815pp and idle-.0302pp. Release banking:
idle919.46 vs918.24; v65260.80 vs262.71; v76222.64 vs225.14. Both candidate and
controls are clean across8 full pools (1120games). This selects a runtime and
productivity repair, not a strength improvement. The strong frozen controls
remain available. No map/item tuning was promoted in this resumption.

Normal movement no longer builds a retry array. Retry bookkeeping starts only
after persistent engine rejection; a bounded same-turn field recomputation
routes toward the same goal around this turn's observed rejected tiles. This
avoids cross-turn stale hard walls and arbitrary wandering. The earlier eager
bookkeeping caused fuel/trajectory changes before retries could logically fire;
offline trajectory observations are in RETRY_ROUTE_AUDIT_2026-10-29.json.

Current source/binary and all results: FOUNDATION_RESUMED_2026-10-29.json.
A clean source export (no local config/cache) builds byte-identically on this
Windows host; PORTABILITY_RESUMED_2026-10-29.json. A physical second device was
not tested. Runtime archive23parts and supporting2931files verified; full capsule
verification passed.29 Python tests and C++host checks pass. Exact continuation,
three remaining bugs and disabled hypotheses are at the top of CLAUDE_HANDOFF.md.
