# Camp damage modifiers and basic-clear work — 2026-10-29

Ten campaigns complete 20 native games on a separate correctness map, both
sides, with zero native faults/fuel-outs. All assertions and the independent
numeric checker pass. Production is unchanged; the advanced objective/gear
models and experimental camp-safety policy remain disabled.

## Procedure and results

Vendetta clears a 24-member gold group (480 gold), returns to spawn, buys the
configured emblems and approaches one isolated wolf at full health. Companions
park. Combat is stationary, with basic attacks only, constant stats and no other
combatants. The exact `basic_clear.h` is frozen into every probe.

`dz-camp-mods-MJD-01` covers all eight boolean combinations of Monster strength,
Jungle health and Durability health emblems. Each requires five shards. Inputs
use live effective champion strength, not raw item stat-point counts.

| Monster / Jungle / Durability | Basic hit | Incoming per round | Attacks | Future HP loss |
|---|---:|---:|---:|---:|
| 000 | 70 | 20 | 20 | 380 |
| 001 | 70 | 18 | 20 | 342 |
| 010 | 70 | 14 | 20 | 266 |
| 011 | 70 | 12.6 | 20 | ≈239.4 |
| 100 | 115 | 20 | 12 | 220 |
| 101 | 115 | 18 | 12 | 198 |
| 110 | 115 | 14 | 12 | 154 |
| 111 | 115 | 12.6 | 12 | ≈138.6 |

Monster adds 15% to damage after the item's stat gain. In this fixture its five
strength points raise Vendetta's live strength from 70 to 100; adding five raw
damage instead would be wrong. Jungle and Durability multiply: 20 × 0.7 × 0.9
= 12.6, not the additive-reduction result 12.

`dz-camp-mods-focus-100-01` / `focus-111-01` substitute Monster focus so strength
stays 70 and each hit is **80.5**. The model predicts and the engine performs 17
attacks over 16 elapsed rounds. HP loss is 320 without defenses and ≈201.6 with
both. These add fractional attack damage to the earlier integer-hit checks.

Every case asserts item construction, full initial health, asleep isolated target,
fixed stats, each effective hit, every intervening damage phase, exact attack
count, elapsed rounds and total damage. The independent checker recomputes the
modifiers, integer attack work and damage from printed measurements; pass markers
alone cannot satisfy it. Floating SDK health snapshots differ by less than 0.001
HP from the ideal fractional totals here; the total tolerance is 0.1 HP and the
per-phase/hit tolerance is 0.01 HP.

## Limits

This validates the restricted constant-stat single-wolf primitive, not V-M1 or a
complete combat model. Other monsters, multiple targets/crews, shield and heal
effects, attack resets, changing Heart damage, Ryth health synergy, duplicate
family stacking and combat interruptions remain outside these cases. Camp safety
stays off because the earlier matched contested benchmark did not improve banking.
No competition-map tuning or strategy promotion occurred.
