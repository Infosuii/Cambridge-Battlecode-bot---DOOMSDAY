# Fundamentals audit — continuing 2026-10-29

User direction: defer map-specific plans/tuning until fundamentals are solid.
Map selections below are correctness/stress fixtures. No map-name rules or per-map
parameters were added. The bot remains weak; G0 and finals promotion are incomplete.

## Corrections

- Actuator checks live action flags, restrictions and channels. History records
  successful actions only. Exclusive casts and movement are mutually exclusive;
  a kill reset does not authorize a second cast. Recall/tribute reject stunned,
  dead and already-channeling states.
- Retreat preserves movement from exclusive spells and ranged basic attacks.
  Ready offensive spells select targets beyond basic range. Pure stun skips
  Marcella. Shields are not spent merely because a harmless cluster is targeted.
  Area spells cannot pull an additional damaging group before feasibility is
  modeled. Varg splash is absent from the current draft.
- Remove duplicate full observations; refresh self only after purchases. Cache
  tile-to-group lookup and camp spawns; publish on-site with one position read.
- Observe dead members using visible spawn tiles. Preserve unseen partial damage
  within a generation; reset on observed state/HP proving a new generation.
  Publish group updates atomically after a round guard. Unseen-live travel skips
  known dead members; reward-capture roots still include defeated members.
- Yield group spawn tiles when waiting would block respawn. Cheap immediate
  capture/tribute/spawn recovery precedes expensive fields. Low-budget movement
  uses existing fields. Query enemy altar locks explicitly; the convenience
  lookup can prefer an allied lock when both are present.
- Recall checks awake damaging camps even with experimental safety off. An early
  recall optimization had caused repeated interrupted recalls.
- Retain the contract's best progress. Renewing on any descending dynamic-field
  step allowed back-and-forth oscillation to renew a failed objective forever.
  Removed after native traces exposed it.
- Bound enemy/group loops and escape scoring; reject incomplete candidates.
  Initial safety attempts had 112 and then one fuel-out; both remain failures.

## Engine and evidence checks

See `CONFORMANCE.md` for exact limits. Passing fixtures establish every-round elk
damage; ranged/melee/cast allowances; recall interruption and healing order;
visible/hidden queries; even/odd capture splits; occupied respawn; Vendetta reset
without another cast. A 23-member group now clears and captures in the fixture.

`ENGINE_FINGERPRINT.json` pins 1,311 named exact-bit fields. Its checker rejects
missing, duplicate or changed values. Runtime metadata and SDK constants are
labeled separately. Truncated diagnostics have no native fault total and mark it
unmeasured. Fuel quantiles omit exactly draft/boosted turns in full games; native
events determine exhaustions. R100/R250/R500 use native RLE without extrapolation.
Eight Python tests check measurement/gates; native C++ tests cover 1,536 codec cases,
stale guards, action history, contracts, generations and bounded escape paths.

`dz-kernel-02-idle` completed its games before a parser error. `recover` validated
frozen binaries/maps and reanalyzed the same raw games. Finished runs are immutable.

## Latest paired release results

Same source/schedule, only `DZ_CAMP_SAFETY` differs. Each campaign is 70 maps ×
both sides. Deterministic cells are not independent randomized samples.

| Campaign | Mean collected | Mean banked | Mean deaths | Fuel p99 | Faults / fuel-outs |
|---|---:|---:|---:|---:|---:|
| 07 idle control | 958.01 | 902.94 | 14.88 | 51,959 | 0 / 0 |
| 07 idle safety | 972.56 | 917.39 | 7.07 | 68,710 | 0 / 0 |
| 07 v65 control | 282.06 | 191.14 | 18.35 | 51,291 | 0 / 0 |
| 07 v65 safety | 284.28 | 187.04 | 14.76 | 60,590 | 0 / 0 |

Safety reduces deaths and improves idle income but slightly reduces contested
final banking. **It stays off by default.** At R500 idle banked 278.43→300.76,
deaths 5.68→2.36; v65 banked 102.01→103.14, deaths 9.50→7.28. Both v65 campaigns
lose all 140 games; this is not a strong baseline yet.

Retained regressions: `fundamentals-05-idle` banked 839.74 with zero engine faults/
fuel-outs; `05-trace` catches stunned recall (44); `06-trace` passes after guards.
`capture-regression-01` isolates permanent oscillation; `capture-regression-02`
confirms the correction and long-group clearing. All frozen evidence is retained.

## Still open before specialization

- Tribute/lock timing and elk nearest-target/lower-handle ties now pass. Enemy
  contest, hidden death, Home/item modifiers, bush/ward behavior and deliberate
  uncaught-fault behavior still need their remaining controlled fixtures.
- `08-v65-trace` passes all 140 cells: zero native faults/fuel-outs and zero
  printed caught action/module errors. Trace changes fuel and can change choices;
  use the uninstrumented 07 campaigns for strength comparisons.
- Per-module disable-after-three is implemented; controlled memory-failure
  injection checks three errors per body, no retries afterwards and continued
  round-100 safe turns. Host tests also prove unaffected modules keep running and
  stale-turn suspension is not counted as failure. `module-isolation-02` and
  `module-stale-01` complete native games with zero faults, and only the latter's
  exact intended one fuel-out per body. Complete 5k fallback remains open.
- Calibrated clear/arrival/damage/reward model, crews and one capturer.
- Banking interruption and enemy burst models; validated EE.
- Repeat stronger v76 comparison after fundamentals improve, then evaluate
  map-type and individual-map plans against that stronger baseline.

## Current foundation checkpoint

`dz-foundation-checkpoint-idle` and `dz-foundation-checkpoint-v65-trace` each pass
140 cells with zero native faults/fuel-outs; the trace also has zero caught
action/module errors. Idle mean banked 902.91, fuel p99 52,998. Contested trace
fuel p99 53,041 and zero wins; it is diagnostic, not strength evidence. Current
source hashes match the frozen idle source. Safety remains off.

The uninstrumented `dz-foundation-checkpoint-v65-release` supplies the matching
contested baseline: 140 games, zero faults/fuel-outs, mean banked 190.76, collected
282.29, fuel p99 52,114, zero wins. The 420 checkpoint games (idle, release v65,
trace v65) are runtime evidence, not proof of competitive strength or completed G0.
The same default binary rebuilds byte-for-byte from a clean source-only export of
5df59b6; `PORTABILITY_CURRENT_VERIFIED.json` records the same-host limitation.

New tests extend observed per-round damage to wolves, golems and monoliths.
Strict monolith attempts exposed a safety bug: camps can damage a champion while
absent from its visible awake masks. Channel checks now refuse hidden potentially
damaging camps in range; experimental observation marks that information incomplete.
It does not infer safety from an empty visible mask. This model remains conservative.

A separate open-ground monolith map, created and integrity-checked with the
official engine MapBuilder, removes visibility and collateral confounds and passes
five consecutive 200-damage samples on both sides. Its generation is byte-identical
on repeat. It is outside the competition pool and is never used for strength claims.
All failed attempts remain preserved. See `CONFORMANCE.md` and
`FOUNDATION_CHECKPOINT.json` for exact scope. The fundamentals audit is not complete.
