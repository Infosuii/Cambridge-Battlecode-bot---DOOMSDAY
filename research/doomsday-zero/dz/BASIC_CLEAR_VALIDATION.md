# Restricted basic-clear primitive — 2026-10-29

`bots/dz/src/basic_clear.h` is fresh, SDK-free arithmetic. It is not included by
the production planner or executor. ObjModel/auction/EE remain disabled.

For known constant effective damage, count `ceil(hp / damage)` **per member**,
then sum. Rounding after aggregating HP loses per-member overkill. Inputs are
engine floats, widened for arithmetic, with no epsilon that erases a real extra
hit. Negative/nonfinite inputs, zero damage against a live target, excessive
input size, and work beyond the bounded horizon have explicit results. Never
interpret a partial horizon result as a complete prediction.

The stationary single-camp calculation samples immediately before the first
attack, after that turn's camp phase. Killing in N attacks exposes the champion
to N−1 future camp phases. It predicts survival only when HP is strictly greater
than that damage. This assumes a fixed position and constant effective damage,
one attacker, no spells/items/splash/healing or other actors. It does not model
changing passive bonuses, multi-camp targeting, arrival or movement.

## Native evidence

`dz-basic-clear-melee-03` and `dz-basic-clear-ranged-03` each complete ten full
engine games on separate open-ground correctness maps, both sides. All strict
assertions pass, with zero native faults/fuel-outs. These deterministic cells
are mechanism checks, not independent strength samples.

| Subject | Target | Predicted attacks to kill | Observed outcome |
|---|---|---:|---|
| Vendetta, 70 damage | Wolf 1,350 HP | 20 | Kill after 20 attacks; 380 future damage |
| Vendetta | Elk 2,400 HP | 35 | Dies after 17 attacks / 17 future phases |
| Vendetta | Golem 5,000 HP | 72 | Dies after 9 attacks / 9 future phases |
| Vendetta | Monolith 20,000 HP | 286 | Dies after 5 attacks / 5 future phases |
| Vendetta | 12 × 120 HP cluster | 24 | 24 attacks and 11 separate movement turns |
| Vesper, 45 damage | 12 × 120 HP cluster | 36 | 36 attacks and 11 separate movement turns |

Both ranged and melee single-camp cases assert outcome, actual executed attack
count, elapsed rounds, per-hit effective damage, incoming damage and isolation.
Ranged subjects stand adjacent to damaging camps so range cannot mask retaliation.
Companions park and the opponent idles. No abilities or items are used.

The cluster probe uses deliberately separate movement/attack turns for both
subjects. Its elapsed-round accounting checks attacks + measured movement turns;
it does **not** claim to predict travel or the optimized melee executor's time.
The damage primitive predicts attack work before starting, without fitting to
these outcomes. Actual runtime Vesper damage here is 45, not the illustrative
80-damage example in the host arithmetic test.

The first 01 runs were truncated and have unmeasured native fault totals. The
melee 02 attempt mistakenly requested zero rounds; the empty-observation gate
correctly rejected it. It remains archived. The runner now rejects zero rounds
before building. The 03 runs use the final guarded probe and full native summaries.

## Gate status

Host checks include 36,000 integer HP/damage cases against repeated subtraction,
float boundary neighbors, zero/invalid/extreme inputs, horizon handling, overkill
and strict survival boundaries. Native fixtures are additional evidence.

**V-M1 remains incomplete.** Before objective selection uses an expanded model,
measure real clear/arrival/damage errors across varying items, abilities, health,
terrain, members and crews. Required gates remain median clear error ≤20%, bias
≤10%, arrival error ≤3 rounds and damage bias ≤20%. Preserve the release holdout.
No map-specific plans or parameter fitting were introduced.

## Equipped-combat extension

CAMP_MODIFIER_CONFORMANCE.md adds 20 complete native cells across all eight
Monster/Jungle/Durability combinations and Monster-focus fractional-hit variants.
The same frozen primitive matches every count, elapsed interval and damage
receipt within the stated small float-snapshot tolerances. V-M1 remains incomplete.
