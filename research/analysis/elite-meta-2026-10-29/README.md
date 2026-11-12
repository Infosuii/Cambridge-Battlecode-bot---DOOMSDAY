# Elite metagame research

Start with [META_REPORT.md](META_REPORT.md). It contains the ten discoveries, strongest conditional compositions/builds, farming/combat/scoring synthesis, DOOMSDAY comparison, priorities and uncertainties.

- [Full 30-match investigations](MATCH_ANALYSIS.md)
- [Team profiles](TEAM_PROFILES.md)
- [Champion meta](CHAMPION_META.md), [synergy/counters](SYNERGY_COUNTERS.md)
- [Items](ITEM_META.md), [farming/economy](FARMING_ECONOMY.md), [combat](COMBAT_META.md)
- [Gem scoring and exact gate interaction](GEMS_OBJECTIVES.md)
- [Maps/movement](MAP_MOVEMENT.md), [other mechanics](OTHER_MECHANICS.md)
- [Algorithm design](META_TO_ALGORITHM.md), [ranked experiments](IMPROVEMENT_PRIORITIES.md)
- [Supplied-v69/current-v71 distinction](DOOMSDAY_GAP.md)
- [Reproduction](REPRODUCE.md), [evidence index](EVIDENCE_INDEX.md), [validation](VALIDATION.json)
- [All 30 score races](figures/score-races.png)

Primary sample:30 games/30 maps/17 teams/26 groups, all 12 snapshot-leading teams; 30,865 actual rounds and 5,226,075 ordered transitions. All 30 pass independent replay/native final-state reconciliation and 834,864 resource-clock checks. The complete 256MB compressed state/action/personal-view ledger is local-only under `artifacts/local-only/elite-meta-2026-10-29`. Reports and research scripts are saved in this new directory; no bot was modified or deployed.

The final ZIP packages this directory's reports, derived tables, charts and scripts. Raw replays, source archives and full state ledgers are excluded under repository policy; use REPRODUCE.md and frozen IDs to reacquire them elsewhere.
