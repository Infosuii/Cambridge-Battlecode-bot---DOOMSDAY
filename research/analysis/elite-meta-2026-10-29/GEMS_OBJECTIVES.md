# Gem conversion and the altar pipeline

Winning sides' median conversion is 96.5%, losing sides 78.4%, using lifetime submitted/collected. Lifetime collection includes stolen gems, so this ratio measures a body's/team's conversion of received assets, not the fraction of unique map gems created. Three winners collect fewer gems: contest, elkring and rows. Three win with less earned gold: broken_curve, islands and rows. These are mechanisms to explain, not statistical causal estimates.

The objective is first 1000 submitted gems, or at R2000 the submitted total, then lifetime earned gold, then champion kills; an exact tie goes to side B. Carried gems are not score. Recall preserves them; death transfers them to a champion killer or destroys them if a camp kills. The game does not reward a large inventory independently of its delivery or champion-specific passive.

## Strongest exact finding: pre-start the tribute before capture payout

On boss_battle (`3b30c86a-59c6-4ba9-985b-e771210c3f51`), newer team clears group 16 at R533. Vendetta actor 6 reaches(24,20) and starts tributing 109 gems at R534. Its end-of-round timer is 10. At R538 the gate capture gives it 200 more gems; its bag becomes 309 and the timer remains 6. Timer zero is observed at R544, and at its R545 turn start all 309 are submitted. HP remains 1320 through this entire channel. Prism shares the same group reward and keeps its own bag.

The team repeats the interaction. Varg actor 9 has 49 gems and starts a tribute at(24,20) on R748 after the next gate clear. Its Tribute emblem, completed at R624, makes this a four-tick channel. At R752 the camp capture gives 200 more gems before champion-turn channel completion; all 249 are immediately banked. Team score rises 721→970. Vendetta contributes the final 30 at R772. Exact surrounding rounds/actions are in `artifacts/local-only/elite-meta-2026-10-29/metrics/GATE_TRIBUTE_EXACT.json.gz`.

This is consistent with the authoritative rule: channel duration is fixed from the bag at start, but completion submits the current bag; camp capture precedes champion channel resolution. Starting 109 uses 11 ticks instead of the 31 needed for 309, a20-tick duration difference holding modifiers fixed. Varg's49 with Tribute uses 4 ticks instead of 17 for 249, a13-tick difference. These are arithmetic comparisons, not independently simulated alternative match outcomes. We observed two instances in one match, so general intent and cross-map prevalence remain low-confidence.

## Why large bags can be rational

Prism's989 retained gems at the boss_battle finish add 1483.5 Focus and can support access while other bodies bank. A generic “bank every large bag” policy would discard that role. Conversely, Ad Astra's808-collected Marcella banks zero and loses 608 at R672: her scoring-gold passive cannot repay without access. Distinguish intentionally retained damage capital from stranded inventory by comparing gate progress, delivery capacity and alternative carriers.

Contest is another countercondition: Mite's first bank is R1779 and it still wins 400–0. On tangle, NEETCoders delays its first bank until 550 and finishes with 159+159 on consecutive late rounds. On split and islands, earlier consistent conversion beats greater equipment. A universal banking round or bag threshold does not explain all these cases.

## State-dependent bank policy

Estimate reachable altar-front tiles, lock state, gate feasibility, travel plus channel completion, visible interruption threats and likely opponent finishing time. Bank urgently if a safe completion ends the game or prevents a round-limit loss; otherwise compare farming's marginal delivery value and the carrier's passive value. Consider a pre-started tribute when a positive current bag and an imminent capture can share the same legal altar-adjacent tile. Preserve capture occupancy while respecting the full phase order.

Escorts are justified when they change survival/interruption probability enough to outweigh their own lost production. The cheap denial tool is an altar lock:10 gold can stop an opposing channel, but the opponent can remove it with five basic attacks. Tribute damage by itself does not cancel; stun, death and locks do. Treat large bags, channel duration and route threats jointly, not as separate heuristic thresholds.
