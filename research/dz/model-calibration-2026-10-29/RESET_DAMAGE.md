Latest continuation: ../varg-mechanics-2026-10-29/README.md adds the restricted
shield forecast. This reset-exposure study and its frozen data remain intact.

# Reset-aware exposure diagnostics

The production survival gate and objective pricing remain unchanged. New
`timed_damage.h` prices stationary exposure using each target's elimination
round from the existing reset clock. Every surviving camp is assumed to hit
this body in each subsequent camp phase; the current phase already happened
before the quote. Cooldown state carries across kills, including Vendetta's
refresh. This is a mechanism, not a fitted damage discount. Work is bounded
to64 members/2000 attacks and runs in linear member count.

10,000 heterogeneous cases match an independent explicit attack/reset/camp-phase
reference, alongside the existing14,544 clock cases and other core invariants.
WASI/Node executes the C++ tests; it does not test native host ABI.

## Correcting isolation accounting

No helper damage does not imply no helper tanking. The replay audit now records
damage by the target group to other champions, plus any living other champion
within a live damaging camp's metadata attack range during the episode. The
pinned SDK's88-byte unit definition precedes camp stats; metadata gives ranges
3/4/3/3/5/4, with zero base strength for clusters. Missing design information is
an error; old records without spatial context cannot validate unshared damage.
These native positions are outcome context, never inputs to bot predictions.

Reanalysis of the same24 role games finds17 of50 old solo-damage cases with
potential bystanders,6 with observed damage to another champion.33 remain
unshared: damage bias86.13%, versus95.43% under the older broad definition.
By kit: Vesper12 cases24.37%; Varg16 cases189.13%; Heart5 cases135.05%.
Thus tanking explains part of the discrepancy but cannot justify a global
survivability discount. The older analyses stay intact; fresh roles-unshared-01
and clock-unshared-v76-01 directories freeze the new reader and results.

## Prospective quotes

36 fresh diagnostic games versus v76 use separate development geometries, then
fixed Vesper/Vendetta lineups to improve coverage. Plans and model source are
frozen before execution. All36 are native-fault/fuel-out free, with zero caught
trace errors. They are diagnostic builds, never release-strength comparisons.

TIMED_DAMAGE_POOLED.json scores23 completed, unshared, fresh-memory damage
episodes: old bias11.49%, reset-aware bias1.18%, median absolute relative error0,
p90 absolute error20HP. Constant-kit timing has68 cases: median error0%, bias0.89%,
p90 one round. Vesper has5 eligible damage cases (bias8.16%); Vendetta has18.
The three initial Vendetta cases match exactly; the separate15-case Vendetta
batch has bias-0.37%. Successful-reset accounting is per accepted input, not
animation frame. Deaths, changed goals, HP increases and censored cases remain
explicit outcomes, never zero-error clears.

These are restricted-model results, not full V-M1. Splash, shielding,
health-dependent damage, internal movement, crews, other spells and the wider
death/abort population remain unresolved. The old elapsed-time pricing change
lost release banking, so accurate quotes alone still do not authorize enabling
timing-based objective pricing. CLEAR_TIME_CLOCK, CLEAR_TIME_WORK_ONLY, auction,
EE, advanced gear planner and Prospector remain disabled.

Next: verify Varg's public radius1 splash against native attacks, then build a
bounded mechanism model and validate prospective quotes on separate geometry.
The SDK also exposes Heart's missing-health coefficient0.5; shielding and action
scheduling need explicit modeling before any safety change. Do not fit a global
scale to the role audit or copy opponent source.
