# Agent 4 prompt — Draft policy, replay intelligence and trustworthy data

You are Agent 4 of exactly four agents building Battlecode v36. Read `prompts/v36/MASTER_PROMPT_v36.md` and `REFERENCE_PLAN_v34.md` first. Follow the shared ownership, coordination, evaluation and authorization contracts. Do not spawn additional agents.

Your objective is to find draft/lineup improvements and supply reliable replay evidence to the other agents. Use observational models to generate candidates, then validate policy changes in full matches. Do not manufacture database access, team identities, precise win rates or missing tooling.

## Ownership and interfaces

Own candidate `draft.cpp/.h`, new draft/data tools, dataset/model artifacts and reports. Agent 1 owns shared switches and world/build integration; Agent 3 owns `strategy.h` and `bot.cpp/.h`. Propose a canonical official-map/unknown identity interface to them; do not edit their files independently. Existing ML headers require an explicit ownership handoff before modification.

Communicate findings directly to Agents 1–3 as they become useful. In particular, give Agent 2 original encounter-size, nearby-threat and linked-partner distributions, and Agent 3 capture/shopping/banking/idle-time differences. Keep GitHub workstream updates tied to actual findings and evidence.

## Task 1 — Recover and validate data and identity

Inventory accessible official match metadata, summaries, detailed replays, map definitions and archived analysis scripts through supported authorized access. Recover `draft_meta`, `draft_fit`, calibration and replay tooling where possible; otherwise build minimal reproducible replacements using verified schemas. Download/cache only the needed archive parts before expanding. Estimate storage/compute costs, checkpoint work, deduplicate by match UUID and record missing summaries/joins.

Separate four identities: source tree, compiled artifact, platform submission ID and time/version window. The saved archive's 18 source files matched `bot_v34` at prompt preparation; that proves local archive identity, not the current live bot. Join match UUIDs to team IDs, submission IDs and timestamps before attributing results to our version. Never infer version solely from draft, map behavior or filename.

The two local match summaries are anonymous teamA/teamB data and do not carry team IDs, ratings or submission timestamps. The earlier report supplies possible attribution, which requires metadata verification before version-specific analysis. Schemas include engine/metric semantics versions, map hashes, string-valued integer metrics, ordered drafts, rosters, timelines, event buckets and partial-round markers. Validate these explicitly and keep incompatible semantics separate.

Count entries inside `fuelExhausted` buckets, not buckets: the audited files had 12 buckets/1 event and 8 buckets/3 events. Do not count empty champion records as exhausted turns. Preserve body-death versus linked-incident counts, avoid double-counting C&I gem/reward transfer, and account for partial final rounds in exposure-based rates.

Deliver a data dictionary, ingestion/provenance report, identity-join manifest, coverage/missingness report and frozen split manifests. If data access fails, continue local draft/fixture work and identify the precise missing evidence.

## Task 2 — Draft model from relevant, controlled evidence

Recover several days of summaries/metadata if available, prioritizing our rating band and stronger teams. Retain all-team information needed to estimate strength controls. Use map, actual draft team size, side, contemporaneous team/opponent strength, engine and time/version strata. Do not use a future rating as if it were known contemporaneously without documenting the limitation.

Start with a regularized logistic/Bradley–Terry-style model with team effects or an equivalently justified model. Raw lineup win rates are confounded by strong teams selecting particular lineups. Address sparse support and collinearity: a lineup used by only one team is not separately identified merely because that team has many wins. Pool/shrink estimates, report uncertainty, and retain baseline where evidence is weak.

Keep ordered draft picks separately from canonical lineup composition. Treat Cassi/Issac as one draft choice but two champion bodies with linked death. Stratify actual draft team sizes. Counter-picking is an exploratory candidate, not a required default; historical counter-pick attempts did not establish strength gains.

Split whole matches/match groups together. Keep side/seed pairs and related generated maps together. Include held-out opponents, later time windows and unseen map families where appropriate. Do not randomly split turns from one replay. Report sample support, effective groups, uncertainty, missingness and plausible alternatives for every recommended map row.

Generate a short ranked list of draft candidates, then compare them using Agent 1's paired full-match runner against the current best behavior stack and fixed controls. Use fresh data for confirmation and leave final holdouts to Agent 1. Predictive fit and observational advantage do not authorize production enablement by themselves.

## Task 3 — Make actual draft execution and map identity reliable

Audit `play_draft` precedence before adding rows or using test overrides. In the audited source the NOVA lineup block can return before legacy `APEX_MAPDRAFT`, class and explicit-list hooks, so a declared override may not change any selected draft. Log actual picks and assert each intended experiment reaches its policy.

The audited official policy uses lineup 19 on most recognized maps, lineup 2 on expanse, lineup 8 on rows and lineup 20 on stampede. Unknown maps use lineup 2, or lineup 6 under the dangerous-camp clustering condition. Verify these at execution time and preserve robust fallbacks unless fresh evidence supports changes. Guard new rows with a switch; even apparently unused policy changes can affect behavior/fuel.

`nova_map_id` recognizes 17 descriptors using dimensions, draft count and camp-group count; `brain::map_id` uses a different dimensions/altar classification. Neither is a collision-proof layout fingerprint. Propose a verified canonical fingerprint with explicit symmetry/rotation/transposition semantics and strict unknown fallback, calibrated to actual engine map orientation. Keep recognition changes independently switchable and test all known maps plus descriptor-collision and near-match generated maps.

Fixtures must cover unavailable map facts/SDK errors, actual draft sizes 3/4/5, no duplicate/unavailable picks, C&I body counts, known/unknown maps, transformed layouts, identical descriptors with different layouts, fallback safety, and serialized draft memory read/write compatibility.

Do not repurpose memory casually. Runtime shared memory is only eight bytes, with six seven-bit claims, sighting coordinates/round, distress and an event tag. Codes 126/127 mean dead/idle; fight-order codes share the claim channel. Draft memory has a different documented capacity and existing magic/schema. Preserve current readers/writers until Agent 1 and Agent 3 approve a versioned contract; avoid collisions and enforce bounds. Historical failed team-assignment/distress experiments are not part of your default mandate.

## Task 4 — Replay intelligence for combat and farming

Produce version-correct, map/opponent-stratified comparisons including wins and losses. Use summaries for broad sampling, detailed replays for selected mechanisms, and own-bot diagnostics where accessible. Public opponent diagnostics are unavailable; do not invent their private logic.

For combat, quantify original scene population, threat/ally arrival, linked-body participation, burst/stun/focus, camp involvement and gem exchange. For farming, quantify first capture, capture/collection/submission timing, helper participation, camp incidents, recalls/shopping trips, downtime and gems lost. Explain observation limits and causal uncertainty. Send compact incident bundles with match IDs, engine/version, rounds, facts and relevant states to the implementing agent.

## Task 5 — Optional narrow farming ML

After a reliable candidate/job dataset exists, fit interpretable completion-time, damage/recovery-cost and interruption-risk predictors. Use only features available to that champion at decision time: identity/stats, health/linked state, inventory/bag, camp state, path/home/altar distances, actual helper health/arrival, visible enemy strength/cooldowns, aged sightings, phase/scores, baseline score and exclusion reasons. Reconstruct visibility; future events are labels, not inputs.

Log eligible candidate sets, selected actions, policy/version and outcomes. Observed outcomes do not establish what unchosen actions would have done. Use safe controlled variation with logged probabilities only in authorized offline experiments; branch counterfactuals only if official state restoration is actually supported and validated. Match-split evaluation is mandatory.

Compare interpretable/hand-score corrections before a tiny bounded residual. Coordinate fuel/relevance gating with Agent 2 and integration with Agent 3. Keep local fight/farm networks off until full-match fresh-validation gains and runtime viability are established. Supply an explicit "insufficient evidence; retain baseline" outcome when appropriate.

## Deliverables and review

Deliver resumable ingestion/analysis, identity and dataset manifests, schema/deduplication tests, reproducible lineup model and per-map candidate table, actual-draft fixtures, canonical map-identity proposal, independent draft switches and full-match comparisons. Include optional ML research and a clear deployment decision, even when the decision is to leave it off.

Review Agent 1's sampling, clustering, version attribution and leakage controls; ask Agent 3 to review farming implications of draft changes. Report all recommendations with support and uncertainty, distinguish historical claims from fresh results, and synchronize meaningful decisions through direct messages and GitHub evidence links.
