# Stationary duel primitive: native conformance, no EE promotion

Selected release5cf28cb7 and ordinary traceb4bc106c reproduce from a clean
source-only export. duel.h is unused by production. Existing policy flags,
survival/prices, Prospector and advanced auction/EE/gear settings are unchanged.

## Mechanism and schedule

The primitive simulates two stationary actors using basic attacks, reset cast
priority, one cast per owner turn, shields and Heart's missing-health curve.
Shield depletion is immediate; duration0 protects a defender until that
defender's owner-start. Each actor's cooldown/duration advances at owner-end.
Inputs are current visible SDK stats/buffs/cooldowns. In the fixed no-CC test
controller, first-can-cast describes availability at the next action boundary.

The order is a REQUIRED input. Strict actor alternation is one supported
primitive; the engine's default equal-rank pair alternates the first team each
round. Fixed first-slot subjects consequently take zero or two enemy turns
between their own turns. TeamA starts odd rounds, teamB even rounds in these
no-priority fixtures. A different-rank pair also validates the fixed one-reply
branch. This does not infer arbitrary live priorities or future changes.

The first legal-tile pilot assumed one reply every turn. It matched the winner
but failed time/HP/basic assertions. Native phase reads identify the actual
order;22 owner-start states also verify owner-end cooldown/shield updates.
The initial ad-hoc phase read is repeated identically with explicit pinned
asset verification in NATIVE_PHASES_02.json. The frozen reader is included.
No damage coefficient or shield parameter was fitted to repair the failure.

## Controlled checks

10,000 bare cases match an independent closed-form strict-alternation reference;
another10,000 match the alternating-round-lead formula. Explicit tests cover a
duration0 defender shield and owner-start expiry. All earlier core cases pass
via WASI/Node; this does not exercise native host ABI.54 Python/13 Node tests pass.

All four fixed Varg/Heart kit combinations pass both candidate-side assignments.
A pre-quote shield setup tests existing shields, including native duration0
protection. A different subject-slot pair validates the other schedule branch.
Across14 accepted truncated games,28 overlapping windows match winner,
owner-observed inclusive time, HP, own basic count, own reset/shield casts and
stationary isolation. Four windows contain duration0 defender shields, including
a repeated final-API check. These are not independent samples.

On death, own HP is0 and the opposing HP is checked from the last personal view
under the explicit no-healing/no-retaliation controller. Both scripted teams'
source and binaries are frozen. This does not use hidden replay values as live
prediction inputs or copy any historical opponent code.

The current one-v-one raw fight heuristic, including its25% enemy-HP margin,
disagrees on nine windows: all nine are conservative false negatives, zero
false positives. Its intentional risk margin serves another purpose. These
scripted counterexamples do not establish that replacing it improves strategy.

## Preserved failures and practical limits

18 truncated games were run in total. Two initial games produced no quotes
because the proposed stand was the central altar, a forbidden landing tile.
Two later games correctly failed the wrong-order model. All four rejected games
remain intact. Final probes use legal adjacent tiles above the altar. The two
candidate-side assignments can begin with different HP/cooldowns because of
arrival timing; quotes capture that actual state, not a presumed symmetric start.

Observed fuel-outs are0. Native fault totals are UNMEASURED for these truncated
games, despite the legacy summary's printed0. Do not merge this placeholder
into measured full-game runtime totals. Capsule verification checks identities,
not whether a failed scientific assertion should be accepted.

Only prescribed Varg/Heart basic/reset/shield policies and base kits are covered.
Movement, CC/dashes, healing, projectiles, item damage modifiers, other actors,
arbitrary priorities and adversarial spell choices remain outside the model.
The default horizon is96 owner turns, hard-bounded2000. A lethal reply is
reported at our next owner observation; winning results are visible in the
current own action. This is not a general live engagement evaluator.

Next: audit enemy reset/shield choices from frozen native replays, keeping old
bots as opponents only; freeze any policy hypotheses before confirmation. Then
diagnostic field quotes must represent legal input and schedule uncertainty.
Full V-M1/EE and release/productivity gates remain open. Keep production intact.
