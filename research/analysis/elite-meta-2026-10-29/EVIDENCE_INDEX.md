# Evidence index

| Question | Evidence |
|---|---|
| What exactly was selected? | SELECTION_PROTOCOL.md, MANIFEST.json/.sha 256, MANIFEST_INITIAL.json/.sha 256, SELECTION_AUDIT.md |
| Which ladder/branches were current? | LADDER.json, REPOSITORY_REVIEW.json, current-submissions.json in local-only artifacts |
| Where is the full match narrative? | MATCH_ANALYSIS.md, authored analyst_notes.json, MATCH_INDEX.csv |
| How can I inspect every round? | Three compressed ledgers per primary ID under artifacts/local-only/elite-meta-2026-10-29/ledgers; inspect_round.py |
| What supports key decisions? | TURNING_POINTS.csv, 226 full windows under local-only metrics, extended GATE_TRIBUTE_EXACT.json.gz |
| Every item's progression? | PURCHASES.csv, all native events and per-body inventories in the round ledgers |
| Farming assignments and rewards? | FARMING_ROUTES.csv, local per-match metrics, native campClear/gemCollection events, initial static group definitions |
| Full score/economy races? | ROUND_RACES.csv.gz and figures/score-races.png/.pdf |
| Champion frequencies/interactions? | DRAFT_EVIDENCE.md, SYNERGY_COUNTS.csv, COUNTER_COUNTS.csv |
| Team identities and behavioural hypotheses? | TEAM_PROFILES.md and POLICY_DIAGNOSTIC.json, including every exception |
| Current mechanics and exact engine identity? | MECHANICS.json, engine.mjs pins in EXTRACTION.json, official SDK 4 headers; local GameRules.md export |
| Strongest timer interaction? | CAPTURE_DURING_TRIBUTE.json and extended gate trace, GEMS_OBJECTIVES.md |
| Correct bot source? | USER_BOT_IDENTITY.json for exact supplied-v69; CURRENT_SOURCE.json for conditional-v71 |
| What is verified? | VALIDATION.json, EXTRACTION.json, ENRICHMENT.json and source/data SHA values |
| How do I reproduce it? | REPRODUCE.md, acquire.py, extract.mjs, analyse.py, enrich.py, activity.py, deep_cases.py, write_reports.py, audit.py |

## Authoritative sources

- Official ladder snapshot: https://2026a.battlecode.co.uk/api/v1/ladder?page=1&pageSize=100&category=all
- Official rules/SDK exports: https://2026a.battlecode.co.uk/game/docs/agents
- Official patch listing: https://2026a.battlecode.co.uk/game/patch-notes
- Current SDK/API reference: https://2026a.battlecode.co.uk/game/api
- Match source URLs: MATCH_INDEX.csv; each group page exposes its corresponding replay/summary.
- User repository: https://github.com/Infosuii/neural-networkk-battlecode
- Checkout source at 92065d0 on analysis/deep-2026-10-28; remote branch heads/recent work recorded in REPOSITORY_REVIEW.json. No remote branch was changed by this study.

The official 2.0.0 WASM is used in place, pinned to SHA 256d910a59eb8a01e1bc4ad4faed1c1f7ca9258b346f895e36446eb88a4d17f3b18. Native summaries identify engine build 85aa7167b44db7cea97509f55e997750520e33d644e9f4f90d6128c50eba1d21. All primary public patch IDs match it. Both JavaScript decoder assets are also pinned and checked, rather than importing arbitrary new code.

## Confidence and missing information

High-confidence observations are direct state/event identities and current mechanical rules corroborated by the engine. Medium-confidence policies recur plausibly across contexts but remain confounded. Low-confidence hypotheses include hidden intent, exact bank/retreat thresholds, intrinsic champion counter coefficients and new-bot strength benefits. No causal claim is created by thousands of correlated body decisions.

The sample has no weaker-opponent control stratum, only one match per map and 26 groups. Several focal teams appear on both sides, but balance is not perfect; VALIDATION.json records exact counts. Developer status is retained. Opponent source versions/pregame ratings are hidden. The V81 source archive is not independently server-hash verified in this study. Rejected SDK calls/private bot variables and alternative opponent responses are not recovered from accepted replay events.

Raw data, downloaded source and personal turn contexts remain ignored. Report links and local ledgers do not imply public publication. Frozen/submitted bots, evaluation schedules, SDK sources and synced project material were not modified.
