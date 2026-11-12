Latest continuation: RESET_DAMAGE.md and TIMED_DAMAGE_POOLED.json describe the
current diagnostic model. The original486-game study below is historical; its
frozen source, results and original4ee9731c control remain intact.

# Z6 model calibration, 2026-10-29

Default release remains byte-identical to the selected foundation. Both timing
experiments remain disabled. 486 fresh full local games have zero candidate
native faults/fuel-outs, with immutable source/binary/replay capsules.

## Prediction and outcome separation

`DZ_TRACE_MODEL=1` samples one configured body through R500. A quote precedes
execution, uses only SDK observations/remembered HP, and retries dropped output
at its NEW timestamp. It records goal changes and first visible legal-range
contact. Logging/estimation costs real fuel; these are diagnostic builds, never
release strength evidence. `DZ_TRACE_TO=0` avoids detailed trace windows.

The offline reader matches quote position/HP on its own turn and checks physical
group membership. The SDK's physical group API includes mirrored groups; the
map-editor template API does not. Using template indices initially failed the
membership assertion; that failure prevented scoring wrong groups. Personal
visibility code97 means false, as in the SDK, rather than a reader failure.
Incomplete roles-01/clock-v76-01 analyses are retained with failure notes;
roles-02/clock-v76-02 reanalyze the SAME games, not additional matches.

Outcomes retain deaths, goal changes, HP increases/respawns, unmatched inputs,
already-cleared objectives and right censoring. Failed episodes never become
zero-error successful clears. Actual group damage by helpers/unknown actors is
marked, and animation substeps cannot multiply one accepted basic attack.
Arrival is first personal visible range contact or a successful basic against
the group, including post-move attacks this turn. D movement actions can first
arrive at quote_round+D-1. Earlier pilot-01/v76-01 reports used next-turn arrival
sampling and have superseding pilot-02/v76-02 reports; their original outputs
remain intact. Damage error units are HP, not rounds.

## Findings

Pilot: six idle games on collision/lanes/fracture, slot0. On36 isolated basic
clears, the old attacks+.25*members estimate has23.44% median absolute relative
error and24.20% aggregate positive bias. Those thresholds fail the intended
20%/10% timing criteria. v76-02 on separate six-map development geometry finds
21.88% /24.13% on27 isolated clears. Quote/result comparisons are retrospective
diagnostics, not a strength or complete V-M1 claim.

Other-role audit:24 games, slots1–4 on lanes/fracture/expanse.111 isolated basic
clears have25% median error and23.09% positive bias.50 solo target-damage cases
have95.43% positive bias. Roles include Vesper, Varg (splash), Marcella and Heart;
the constant-damage stationary model omits splash, shielding and health-dependent
damage. Do not globally scale the safety margin down to fit these outcomes.

Two candidate changes were tested:

1. Work-only pricing removes the uncalibrated .25/member padding, retaining the
   old damage/survival gate. Full140-cell release deltas: idle-2.47 (SE1.97),
   v65-4.35 (SE5.31), v76-3.94 (SE5.32), zero faults/fuel-outs. It remains OFF.
   See RESULTS.json for exact calculations and development-only subsets.
2. `attack_clock.h` predicts stationary basic/reset elapsed time with current
   cooldown, configured period, one cast per turn, no reset after a first-hit
   kill, and optional monster-kill refresh. It uses bounded closed-form cycles,
   not a fuel-heavy per-turn search.14,544 cases match explicit reference ticks.
   `group_attack_clock` adds initial executor-like ordering and uses remembered
   per-member HP/quantized damage. It ignores internal movement, splash, other
   spells, help and future damage changes, and NEVER relaxes survivability.

Prospective clock diagnostics:12 v76 games on corners/crater/galaxy/gem-fields/
lost-world/oasis.30 isolated basic clears: old timing median62.5%, bias35.64%;
clock median0%, bias4.26%, p90 absolute error1 round. Restricted constant kits
have26 cases and4.58% bias. This is useful restricted-model progress; the full
V-M1 gate stays OPEN (damage bias21.43% on only6 damaging cases, other roles,
spells, crew timing, deaths/abort coverage still unresolved).

Improved timing did NOT establish improved policy: twelve-cell v65 release
screen delta-43.5 banked (SE24.9), versus the selected foundation. Clock pricing
stays OFF. Do not promote it from prediction accuracy alone. Extra pricing cost
and the current incomplete objective utility are possible causes, not proven
attributions. No larger clock campaign was launched after this failed screen.

## Checks and continuation

38 Python tests and8 Node event-accounting tests pass. The full SDK-free C++
invariant suite runs as WASI with Node24 (including the14,544 new clock checks).
This resolves arithmetic execution on the fresh device without pretending a
native host ABI was tested. Reproduce with tools/dz_core_wasi.py and a fresh name.
Default release SHA256 remains4ee9731c53c76e65bb43b4285a092664803e7011fd86359636f1258de11bcaa4.

Keep JOB_GEAR, CLEAR_TIME_WORK_ONLY, CLEAR_TIME_CLOCK and CREW_REACH disabled.
Auction/EE/gear-planner gates stay false. No competitive parity, full V-M1, new
seed independence, release holdout, submission or ladder action is claimed.

Next: evaluate the already-frozen Z14 mixed-table hypothesis separately against
v76, then require idle/productivity and broader release checks before promotion.
For Z6, model splash/shield/health-dependent damage by mechanism, not a fitted
global discount. Preserve these failed policy experiments as counterexamples.
