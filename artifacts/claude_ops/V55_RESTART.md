# V55 opponent-driven restart

User direction: explain losses against lower-ranked opponents and build a definite improvement over v54, with rank25 as the long-term target. Submission is authorized once definite improvement is demonstrated. Only bench3/bench_compare now; retain only a positive map-clustered95% interval, complete fault-free games, original release gate and mechanism evidence. No submitted version can be treated as an unsubmitted candidate in unranked groups.

All earlier E1-E6 variants are unretained after clustered re-check; patches/data preserved. In particular E2 +7.3 has95% interval[-20.6,+37.2]; E6 +17.5[-25.7,+59.4] and severe mobility regressions. Starting again from frozen v54 source, preserving the earlier prototype snapshots. v53/v54 and machine-specific config unchanged.

## R1: legal draft availability

Hypothesis: the learned draft unnecessarily excludes every champion already selected by the enemy. Rules allow opposing-team mirrors, and actual v54 games contain mirrored champions in119of130games, so this is a contract mismatch, not a proposed strategy change. Enemy picks should affect model features, not availability. V55_DRAFT_LEGAL removes only the enemy taken-mask loop; no forced lineup, reward funnel or item changes.

Mechanism checks: chosen rosters, pick order and newly available mirrored picks, plus capture income/equipment. Compare all28development maps, both sides, seeds1-12 against v54; faults must0 and count672. Targets before results: no map-specific win claim (a general draft legality correction); transport safeguards concentrated-wealth/big-world/shortcut, brawl set eight/quadrants/gold-rush/rows/rushbait-v2. Preserve the final12maps for one frozen release check; all previously exposed and hooks especially exposed. Do not infer tournament superiority from same-lineage wins alone.

Latest ladder cutoff17:30:08UTC:130games,73wins; ranked20/35, unranked53/95. This does not establish a causal v54 advantage. Available fully audited cohort:48losses through17:10:10UTC. Opponents have1.5x our R500 capture income (450vs283/actor),2.2x big-capture gems (144.5vs65.5), and half the dead-camp waits (40.5vs83). Higher gear converts into a50vs36 damage exchange. Need to explain these through decisions and execution, not merely copy their picks.

## R2: terminate learned camp commitments on capture

Independent base v54 (not R1). Hypothesis: campnet_pick retains an off-base target for40rounds while it remains in the candidate list, even after its reward has been captured and it is respawning. This overrides route_search and can turn a completed sortie into dead-camp waiting. V55_COMMIT_EVENT ends the commitment on the existing respawning-state event and resets its base cache. The network stays enabled; no wait-weight tweak and no added per-group scoring work. Measure R500 dead-camp waiting and captures/actor, plus full12-seed outcome and clustered interval. Diagnostic mechanism claim is provisional until those measurements agree.

Representative ladder routes were reconstructed. On rows (c3ddb0e2...), our Vendetta captured the same160-gold group atR147/R232, while the winner's Marcella alternated180/160-gold groups atR30/R56/R113 and had860capture gold byR250. On shortcut (04333917...), our Marcella spent187/250rounds travelling and earned170capture gold; the opponent's Vesper spent62travelling and earned472. These are cases, not universal policies. They motivate mission-completion and route execution checks rather than more unconditional composition changes.

## R3: coordinated economic clearing pair

Independent base v54. V55_CREW_DRAFT selects Varg then Vesper, Vendetta, Marcella, Heart, while preserving the existing topology-required mobility override. V55_CREW_ROUTE pairs only a healthy Varg/Vesper within8tiles: Varg scores with2staff, Vesper follows its claimed worthwhile job (>=20gems or>=150gold), and others farm normally. V55_CREW_OWNER makes only this pair agree that Vesper receives their capture; no global monopoly. Existing Treasure/Jungle/Durability builds unchanged. Hypothesis: faster early clears and leapfrogging capture handoffs produce the income observed in opponent routes, rather than merely selecting Vesper. Measure first capture, big captures, capture gold, Vesper share, time attacking, waiting and gear. Full12-seed test before ablation/retention. Targets: general economy, with fragment/rows/elkring as declared mechanism diagnostics; no tuning on release maps.

## R2 replication (predeclared before new seeds)

R2 mechanism agrees with its hypothesis: R500 wait124.1vs139.5champion-rounds (-11.1%); capture gold344.4vs331.3per actor (+3.9%). The12-seed gem interval just includes zero. Run ONE independent replication, seeds13-24 (672games). Require a positive replication effect and pooled24-seed clustered interval above zero before retaining it. Do not keep extending seeds until a threshold is crossed.

## R5: runtime cost of invariant work and unused traces

Independent v54 base. V55_HOIST_GOLD computes gold_weight once per scorer/follow-up refresh, instead of repeatedly inside the existing group loops; inputs are unchanged during those calls. V55_TRACE_COLD skips copying the600-byte camp-network training log when ngp::training is false; the normal game never consumes this log, and training mode retains it. Neither changes policy weights. Both are separately switchable; ablate if the combined candidate improves. Hypothesis: more computation reaches useful routing/execution under the official100k budget. Measure fuel-exhausted turns and complete outcomes; a semantic optimization alone is not enough for retention under the clustered rule.
