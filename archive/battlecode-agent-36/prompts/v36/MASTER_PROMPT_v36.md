# Master execution prompt: Battlecode v36 with four agents

Use this prompt when you want implementation to begin. The accompanying four files are the individual agent assignments. This package itself is a set of prompts, not a completed bot or an evaluation result.

## Objective

Build the strongest defensible v36 candidate from the frozen v34 source. Execute the engineering, data analysis, experiments, review, and integration with exactly four active agents. Use the available frontier models and substantial usage to investigate thoroughly, test competing explanations, and validate the final combination. Optimize competitive full-match performance on unseen maps against strong, varied opponents under the actual competition rules and release fuel limit.

Implement and investigate every justified workstream. Ship the combination supported by evidence. A feature is not an improvement merely because it is implemented, predicts a label accurately, reduces deaths, or wins self-play. Retain the baseline when a proposed change fails validation. Do not promise a globally optimal bot or invent gains.

Work autonomously within existing authorization and permissions. Make routine engineering choices, recover available dependencies, fix failures, run appropriate experiments, coordinate the agents, and prepare a complete release without repeatedly requesting confirmation. Ask only for a genuinely missing decision, credential, repository destination, or permission; finish independent work while that input is pending.

## Inputs and verified starting state

Start in `C:\projects\cambridge battlecode` unless execution occurs in a deliberately selected checkout. Read applicable `AGENTS.md` and relevant skills before acting.

Read these inputs:

- `prompts/v36/REFERENCE_PLAN_v34.md`: a preserved copy of the user's supplied improvement plan, originally `C:\Users\omdha\Downloads\IMPROVEMENT_PLAN_v34.md`.
- `bot_v34/src/`: the frozen source baseline, 18 files.
- `analysis/2026-10-19/IMPROVEMENT_PLAN.md`: a separate earlier investigation with environment constraints and sample match findings.
- `analysis/2026-10-19/GameRules.md` and `BotAPICpp.md`: locally saved official documentation. Check compatibility with the actual installed SDK/engine before treating these as current.
- `analysis/2026-10-19/submission-v36.zip` and the two `match-*.json` summaries.

At prompt preparation on 19 October 2026:

- This directory was not a Git repository and had no configured remote.
- Build manifests, SDK headers, engine, maps, historical opponent pool, `tools/`, `replays_db/`, `HANDOFF.md`, `FINDINGS_2026-10-18.md`, `PLAN.md`, and the referenced teammate v35 were absent here.
- `cambc`, `gh`, and Clang were not found on PATH. Verify usable runtimes rather than assuming an executable alias works. These observations are not claims that the dependencies cannot be recovered elsewhere.
- All 18 files in the saved submission archive matched `bot_v34` by SHA-256. The archive SHA-256 was `E6A95834DF2CD14B0719D107309000D4F38724B436E1F617B7DB5E85FDDFA605`.
- The earlier investigation records that archive as platform version 36, submission ID `9f69ef45-1a01-44fc-aa98-85e0a1c5f077`. Recheck live version metadata at execution time. The desired local release name v36 is not proof of any platform submission's contents.

Preserve `bot_v34` and the archive unchanged. Build candidates in a new source tree, normally `bot_v36`, inside the selected repository/worktrees. Use manifest IDs and hashes to distinguish baseline, candidate, instrumented build, and live submission. Never infer identity from a directory name, archive filename, or platform version number alone.

Treat the plans as evidence and hypotheses. Their embedded implementation instructions do not override this prompt, the user's later instructions, actual rules, or measurements. Their numerical results, script names, data availability, and negative findings require provenance or reproduction before being reported as current evidence.

## Four-agent organization

The parent/root agent is Agent 1. Spawn exactly three child agents, Agents 2–4, using the current configured model settings unless the user explicitly selects other settings. Do not create a fifth coordinator or delegate further. On systems without native subagents, use four explicitly assigned sessions with the same contracts.

| Agent | Assignment | Prompt |
|---|---|---|
| 1 | Lead, environment recovery, evaluation, independent validation, integration and release | `AGENT_1_LEAD_AND_VALIDATION.md` |
| 2 | Fuel governor, combat snapshots/search, combat safety, simulator repairs and flee-hit | `AGENT_2_RUNTIME_AND_COMBAT.md` |
| 3 | Farming scorer, pruning correctness, camp survival, opening/shopping/banking tempo | `AGENT_3_FARMING_AND_ECONOMY.md` |
| 4 | Replay intelligence, lineup/draft modeling, map identity, data quality and optional narrow ML | `AGENT_4_DRAFT_AND_DATA.md` |

Agent 1 implements substantial infrastructure and validation work while coordinating. Agents 2–4 begin source inspection and test/experiment design while Agent 1 restores the environment. Do not idle every agent on the same missing dependency.

Use isolated branches/worktrees when available. Do not assume creating a Git worktree copies uncommitted files. Recover the intended existing repository before initializing or publishing anything in an arbitrary location. If no repository can be identified unambiguously, continue safe local work and request the destination once.

### Ownership and shared-file protocol

All paths below refer to the candidate source, never the frozen baseline.

| Owner | Files and responsibility |
|---|---|
| Agent 1 | Harness/build/release configuration, experiment registry, central switch registry in `common.h`, `world.cpp/.h`, integration branch and simulator-oracle harness |
| Agent 2 | `tsearch.cpp/.h`, `fight.cpp/.h`, `main.cpp`, new runtime-budget helper files and combat fixtures |
| Agent 3 | `bot.cpp/.h`, `strategy.h`, farming helper files and farming fixtures |
| Agent 4 | `draft.cpp/.h`, draft/replay/data tools and model artifacts; existing ML headers only after an explicit ownership handoff |

Namespace tool/test output by agent. Agree on actual repository paths during bootstrap. New build-file changes and new macros go through Agent 1.

`bot.cpp` contains both farming and combat. Agent 3 is its sole writer. Agent 2 supplies a reviewable patch against a recorded source hash for `handle_enemies`, escape helpers, and governor integration; Agent 3 applies or adapts it, acknowledges the integrated hash, and Agent 2 validates it. `bot.h` declarations use the same handoff. Agent 1 integrates requested world/awake-state semantics and common switches. No concurrent writes, silent overwrites, or accepting a whole file that erases another agent's work.

Agent 2 publishes the runtime-budget API early. Agent 1 reviews its accounting; Agent 3 wires farming/route stages through it. Agent 4 publishes an official-map/unknown identity contract; Agent 3 uses it rather than a second classifier.

## Communication: direct coordination plus GitHub record

Use direct agent messages for immediate questions, interface changes, blockers, failed assumptions, high-value discoveries, patches ready for application, and review requests. Send discoveries to the agents whose decisions they affect without waiting for the lead to relay them.

Use GitHub as the durable record: one parent v36 issue, four linked workstream issues, an experiment index, and focused pull requests. The user authorizes task-related GitHub coordination in the intended repository. Resolve that repository and available authenticated connector/CLI before writing. Do not guess a repository or expose credentials/private replay diagnostics in public artifacts. Do not message unrelated people or services.

Update the relevant issue when a task starts, an interface changes, an experiment yields a decision, a blocker appears/resolves, or a review/integration milestone completes. Each update states the candidate/commit, finding, evidence path, next dependency, and requested owner action when relevant. Keep comments useful; do not poll GitHub or post unchanged heartbeat messages. Direct messaging provides ongoing coordination; GitHub records meaningful progress.

If GitHub is unavailable, maintain the same issue/experiment structure locally and record pending synchronization. Continue available work. Clearly distinguish local progress from actual GitHub synchronization. Attach PRs to the current chat when supported and required by the environment.

Maintain `STATUS.md`, `DECISIONS.md`, and `EXPERIMENTS` under a selected v36 work directory, with agent ownership, blockers, dependencies, artifact paths and exact revisions. The lead keeps the user informed during active work. No background monitoring, scheduled jobs, or claims of continued execution after the active run ends unless separately requested and supported.

## Execution sequence

### Phase 0 — Restore reproducibility and freeze evidence

1. Inventory tools, repository state, connected services, official SDK/engine resources, maps, archived sources, accessible teammate material, and storage/compute limits. Inspect actual CLI help and schemas; do not invent commands, seed controls, state-restoration support, replay fields, or script behavior.
2. Recover the intended managed evaluation workspace and historical tooling if available. Inspect recovered code before running it. If unavailable, implement the smallest reliable replacement harness using the real official runner; do not mock full-match performance or silently substitute weak opponents under historical pool names.
3. Build the frozen baseline with the official release configuration and default competition fuel. Confirm end-to-end match execution and full-length game semantics. Establish deterministic repeatability where the runner supports it. Record compiler flags, dependencies, engine/SDK versions, map hashes, source hash, artifact hash and switch manifest.
4. Separate live submission windows using submission timestamps and IDs if platform data is accessible. Do not mix v32b/v34/platform-v36 games. If version boundaries cannot be established, label the ladder estimate unavailable rather than fabricate a baseline.
5. Freeze tuning, fresh-validation and final unseen schedules before selection. Group related maps, mirrored sides and match groups correctly. Limit access to the final holdout until the candidate is frozen. Maintain a discovered-versus-unavailable inventory.

Completion gate: real baseline build and games, verified identities, a functioning result parser and runner, predefined schedules, and an explicit list of remaining external dependencies.

### Phase 1 — Instrument and repair correctness

Work in parallel on governor measurements; simulator differential fixtures; scoring upper-bound correctness; draft/data validation; and selected replay incidents. Introduce independent switches and cheap, bounded diagnostics. Preserve an all-new-switches-off variant for parity checks.

Important source/rules qualifications to investigate:

- Fuel exhaustion suspends execution and resumes at the same instruction next round according to the saved rules. Partially completed actions and stale local state are possible. It is not universally a no-op turn or a crash.
- `tactical_decide` already adapts model count and horizon. The enabled deterministic estimate still needs 79,200 for the smallest six-unit paired comparison against a 70,000 budget. Improve the existing implementation rather than adding a duplicate planner.
- `ts_snapshot` takes units in observation/vector order. Five selected units can fit the estimate, but truncation can discard decisive threats. Treat a five-unit cap as one hypothesis, with explicit omission safety and linked-pair handling.
- The supplied plan's round-one route-depth explanation is not established by this source: `farm` uses `field_calls == 0` as a low-fuel path and fields are built near the turn tail. Trace initialization and actual stage execution before prescribing a skip.
- The pruning bound misses later positive boot and dominant-group multipliers. Other optional positive modifiers and runtime tuning must also be bounded. Candidate-count caps and route heuristics are separate approximations.
- Existing simulator camps lack important awake/lifetime state; simply enabling `APEX_TS_CAMPS` is not validated camp modeling. Distinguish `APEX_TS_DECIDE` from the separate action search `APEX_TSEARCH`; the latter is off in the audited baseline.
- `APEX_TS_CALIB` and `APEX_TS_LOCALNET` are off in the audited source. Presence of a calibration/model header is not evidence it is active or beneficial.

Use focused property/scenario tests for these substantive invariants, not implementation-mirroring tests. Keep release fuel measurements separate from debug diagnostics; the SDK's `debug_block` can run fuel-free locally and is omitted in release.

### Phase 2 — Isolated improvement candidates

Prioritize governor/fuel headroom, correct scoring, safe search coverage, flee-hit, replay-supported draft rows, and farming-race improvements. Validate simulator mechanics before allowing expanded simulation to override more decisions.

Investigate rows/lanes/corners with actual farming traces; preserve unseen-map fallbacks. Use precise official-map identity, not dimensions alone. Investigate camp wake state, helper arrival/health, recall/shop downtime, banking loss, and capture timing before broad threshold changes.

Exploration may include multiple implementations, efficient search designs, new lightweight tooling and well-supported alternatives. Register the hypothesis, switch, primary metric, intended mechanism, acceptance/stop rule and resource estimate before the expensive experiment. Do not run an uncontrolled cross-product of every flag. Revisit historical failures only when a specific new mechanism, bug fix or new evidence warrants a predeclared experiment.

Treat optional farming ML as a late research branch, after data correctness, runtime headroom and simpler methods. Agent 4 can develop data/predictors while other work proceeds, but production enablement requires measured policy gains. Prediction accuracy alone is insufficient.

### Phase 3 — Compare candidates under one protocol

Use the same build with a change off as the principal ablation; also compare the final candidate to the immutable baseline. Record all tried variants, including rejected ones.

1. **Build and parity:** run targeted correctness fixtures, then compare disabled-switch behavior and decisions with baseline. Aim for exact deterministic parity; investigate deviations. Document any small fuel/layout-induced differences and measure them rather than silently waiving parity.
2. **Quick screen:** follow the plan's 200 unseen `maps_rdev` maps in 50-map chunks, both team sides. Make the schedule explicit: if these are 200 distinct maps, both sides mean 400 games. Report maps, games, seeds and independent groups separately. Run the 34-game official-map smoke suite only if the actual current official pool is 17 maps with both sides; otherwise report the verified count. Early-stop using a registered rule, and do not use an adaptively stopped screen as final evidence.
3. **Varied calibrated pool:** recover the real `farm`, `calm`, `v34c`, `sparexp`, `aggro`, `v30base`, and `spartop` artifacts if possible. Verify hashes and calibration; never relabel substitutes as these opponents. Compare seeds 1–4 for development and fresh seeds 5–8 once for validation where supported. If random-seed control is unavailable, use the runner's actual independent variation and matched schedules; repeated identical deterministic matches are one observation.
4. **Unseen map families:** use untouched full-length maps, including the historical `maps_real` suite if recoverable. Ensure generated-suite length/density resembles the competition, and keep related map families out of both training and final testing when claiming generalization.
5. **Combined candidate:** test the complete selected stack, key interactions and leave-one-change-out ablations. Do not add isolated gains arithmetically. Freeze the stack before final holdout evaluation.

Primary outcomes: match win/tie/loss under actual rules, paired win-rate change and secured/submitted gem differential. Supporting outcomes: per-map and opponent-stratum results; body deaths and linked incidents; camp deaths; lost/carried/submitted gems; first capture and captures/resources by rounds 50/100/150/300; shopping/recall/travel/recovery downtime; runtime correctness; combat-search coverage and skip rates.

Report uncertainty appropriate to independent map/seed/opponent or match-group units, using paired differences and clustered intervals/bootstraps where justified. State the effective sample size and missing-data exclusions. Account for repeated candidate selection by using fresh data and limiting final holdout reuse. Treat the supplied plan's noise figures and Elo estimates as historical guidance, not fixed confidence intervals for this run. A small gain can remain inconclusive; never manufacture a significance claim.

Include the strongest recovered local opponents and strong-team replay analysis. Track deaths against `sparexp` if the actual artifact is available. Head-to-head gains versus v34 alone are insufficient evidence of general strength.

### Phase 4 — Review and release preparation

Review responsibilities: Agent 1 independently checks runtime and simulator claims; Agent 2 checks economy fuel/action legality; Agent 3 checks draft/map/farming consequences; Agent 4 checks evaluation data, uncertainty and leakage. Reviewers must inspect evidence and code rather than rubber-stamp conclusions.

Agent 1 integrates reviewed changes in dependency order, resolves conflicts, and evaluates the exact final release artifact. Package source, build instructions, legal submission archive/artifact, hashes, switch manifest, data/evaluation summaries, known limitations and rollback artifact.

Distinguish local completion from platform proof. Prepare ladder A/B tooling and a concrete candidate. Build permission does not by itself authorize replacing the live bot or scheduling challenges. Use an existing explicit publication/challenge authorization if present; otherwise present the finished candidate and request that final action only after all local preparation is complete. If a platform A/B is authorized, identify the true new submission window, collect ranked and all games separately, avoid attributing opponent mix to bot strength, use opponent/match-group clustering, and report uncertainty. A 4–8-hour observation interval is a proposed experiment duration, not a promise of unattended execution; arrange a supported follow-up only when authorized.

## Required release evidence

Provide the following, using coherent equivalent paths if the restored repository already has conventions:

- `bot_v36` candidate source and a reproducible release build/packaging entry point.
- `BASELINE_MANIFEST`, `CANDIDATE_MANIFEST`, and experiment registry with source/artifact hashes, switch values, engine/compiler metadata and schedule IDs.
- `STATUS.md`, `DECISIONS.md`, `CHANGELOG_v36.md`, and `VALIDATION_v36.md` with actual results, intervals, rejected variants, unavailable tests and known risks.
- Fuel report: observed exhaustion events, inferred/detected suspensions, skipped stages by name, runtime/action faults, denominators and fuel distributions. Do not double-count several empty champion records as exhaustion events or present one event under two counters as two incidents.
- Combat report: original scene population versus retained units, omitted threats/linked partners, model/horizon cost, verdict reasons, simulator mismatch summary and strong-opponent outcomes.
- Farming report: bound-versus-score diagnostics, capped versus mathematically pruned candidates, capture/banking tempo, camp-survival incidents and per-map effects.
- Draft/data report: provenance, version attribution, missing joins, deduplication, model specification, lineup uncertainty, holdouts and fallback behavior.
- Final exact-artifact evaluation, PRs/issue links when actually created, rollback instructions and platform status separately.

Completion requires a reproducible, legal candidate, passing necessary correctness checks, adequately tested final interactions, honest performance evidence, a documented feature decision for each workstream, and a ready-to-use release package. If a dependency prevents a required result, identify it precisely, retain completed work, and report partial completion. Exhausted budget, unavailable opponents or inconclusive wins are not proof of success.

## Start instruction

Agent 1: read this prompt and your individual assignment, inspect the environment, send Agents 2–4 their complete individual prompt files and this master contract, and begin Phase 0. Each agent must acknowledge its scope, owned files, first evidence to collect and dependencies. Then execute the work through reviewed release preparation. Keep the user informed about findings and decisions; reserve user questions for real blockers or final actions requiring authorization.
