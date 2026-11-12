# Additional mechanics that affect policy interpretation

The fresh engine query is in MECHANICS.json. The current official rules export was downloaded from the handbook on 29 October and retained locally with source hashes in the evidence audit. Engine 2.0.0 is distinct from CLI/SDK 4.0.0; matching the CLI number to the engine version would be an error. Historical 1.0.3 findings are not pooled into this sample.

**Channels are not synonymous with inactivity.** Several elite controllers issue a recall after productive actions and cancel it on the next turn. For example, Sponge's arena Vendetta starts recall at R1, cancels it at R2, moves/acts and starts again. The R2 personal state can show a recall timer while the position has already changed from the prior round. This could be a fallback policy or another controller convention; its intent is unidentified. Activity counters therefore measure displacement independently of channel presence. Do not prescribe removing every cancellation, or label these rounds as wasted travel.

**Fuel suspension is delayed execution.** C++ normally has 100000 fuel per turn, with special initial/draft allowances. Exhaustion suspends execution for continuation rather than necessarily killing the process. Mite records 77 native fuel suspensions in its yellow_brick_road loss, but Trzy Kwaterki wins swirl with 49 and NEETCoders wins tangle with 23. These are associations. The useful target is timely, valid decisions and preservation of safe actions under suspension, not a claim that zero suspensions guarantees strength.

**Capture state belongs to the team region.** A Capture holder can cap the remaining timer and leave while an ally keeps it alive; an enemy contest or empty region resets it. Reward remainder goes to the lowest body ID. These details make turn order, receiver identity and shared-memory coordination economically relevant. Extra bodies do not automatically speed capture.

**Priority changes apply next round.** Champions within a team act by priority then draft order, while starting sides alternate. A planner can use priority for a future coordinated sequence but cannot assume a changed priority reorders the current round. The raw ordered action ledger preserves all priority events for later tests.

**Death is both time and asset transfer.** Respawn uses 60 owner turn-end ticks and a free spawn tile, with effects resolved at turn start. The duo shares death fate, and camp deaths destroy bags. Every body still has shopping turns while dead. A physical-body death count differs from independent combat losses or kill rewards.

**Full healing has timing.** Spawn healing occurs at the owner's turn end. A recalled champion that immediately leaves before that point can forgo the recovery the macro planner expected. Buying Health on spawn has a separate immediate healing effect; Tavi's field Health does not. Recovery models need the actual action/phase order.

**Small memory encourages compact coordination.** Runtime shared memory is 8 bytes; draft memory is 1024 bytes and becomes read-only during play. A proposed global planner must specify a realistic compact representation or reconstruct information locally. It cannot assume a large shared blackboard or automatic team vision.

No mechanics for experience levels, lane minions, conventional item slots, permanent team gold pooling or terrain destruction were invented to fill gaps in the requested taxonomy. Where the engine supports a different mechanism, the report uses that definition instead.
