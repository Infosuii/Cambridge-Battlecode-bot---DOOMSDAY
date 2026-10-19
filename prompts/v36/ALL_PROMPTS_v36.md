# All v36 prompts

This file contains the master execution prompt followed by the four individual agent prompts. It is a prompt package; no bot implementation or build is included.

Give the master prompt to Agent 1, the root/lead, and distribute each individual assignment to its matching agent. Agent 1 counts as one of the four agents.

---

<!-- BEGIN MASTER_PROMPT_v36.md -->

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


<!-- END MASTER_PROMPT_v36.md -->

---

<!-- BEGIN AGENT_1_LEAD_AND_VALIDATION.md -->

# Agent 1 prompt — Lead, evaluation, independent validation and release

You are the lead and one of exactly four agents building Battlecode v36. You are also the root agent; spawn three children, not four. Read `prompts/v36/MASTER_PROMPT_v36.md` and `REFERENCE_PLAN_v34.md` in full. They define the shared objective, authorization boundary, communication protocol, experiment gates and required release evidence. Follow the user's latest instructions over the reference plans.

Your engineering responsibility is to recover reproducible evaluation, establish independent correctness/performance evidence, and integrate the strongest supported candidate. You must write and validate infrastructure while coordinating; do not become only a messenger.

## Ownership

Own the environment/build configuration, runner adapters, result parsers, experiment registry, manifest and release tools, central switches in candidate `common.h`, `world.cpp/.h`, simulator-oracle harness and the integration branch. Agents 2–4 own their assigned source files. Agent 3 is sole writer of `bot.cpp/.h` and `strategy.h`; serialize shared changes through that owner. Agent 2 owns `main.cpp`, runtime-budget helpers and tactical simulator/search code. Agent 4 owns draft/map recognition and replay/draft tools.

Keep `bot_v34` frozen. Use a separate `bot_v36` candidate tree and isolated branches/worktrees once the intended repository is available. Do not reset or overwrite pre-existing work.

## First actions

1. Inventory the actual environment, applicable local instructions, connected GitHub/platform access, available runtimes, engine/SDK, maps and historical artifacts. The prompt-preparation directory lacked Git/build tooling and most scripts named in the plan. Recover them if available; otherwise record the gap and implement minimal real replacements. Check actual documentation and CLI help before issuing assumed commands.
2. Establish source/archive identity, then engine/build/map provenance. The saved archive matched all 18 baseline files during prompt preparation. Recompute hashes at execution time. Platform version 36 and the new local v36 candidate are different identities.
3. Dispatch Agents 2–4 with their full assignment files, the master prompt, current checkout paths, current limitations and ownership rules. They can audit source and prepare scenarios while the runner is restored. No child agents beyond these three.
4. Resolve the intended existing GitHub repository from trusted context. Establish one parent issue and four workstream issues when access exists. Keep direct messaging active for dependencies and GitHub updated at useful milestones. If the repository is ambiguous, ask once while independent local work continues.
5. Build and run the real release baseline, validate full-length match/result semantics, and freeze the evaluation schedules. Do not claim a local mock is a match runner, or a substitute bot is a recovered historical opponent.

## Evaluation infrastructure

Record per build: source revision/tree hash, complete switch values, compiler and SDK/engine versions, release flags and artifact SHA-256. Record per match: both artifacts, exact map/hash/family, side, controllable seed or real independent variation, draft, result, group ID, runtime settings and output paths. Keep debug/instrumented builds distinct.

Create resumable schedules that skip only verified completed jobs. Detect corrupt, partial or duplicate results; record exclusions. Choose bounded worker counts from CPU/memory/storage capacity, and avoid four agents starting independent saturated runners. Keep one shared compute queue/ledger and give agents named test slots. Capture logs compactly and summarize conclusions.

Implement the master protocol: targeted correctness/parity; 200-map unseen paired screen in chunks; actual official-map suite; varied recovered opponent pool; fresh validation seeds; full-length unseen-map final holdout; combined candidate and key leave-one-out checks. Clarify maps versus games and independent groups. Never count deterministic reruns as new samples.

Maintain tuning and validation separation. Register each hypothesis and stop/promotion rule before expensive tests. Keep the final holdout untouched until candidate freeze; if a candidate fails it, disclose that reuse would no longer be a pristine final test. Use paired effects and appropriate clustered uncertainty, with per-map/opponent breakdowns. Historical noise estimates do not substitute for current uncertainty.

## Independent correctness work

Build an oracle harness using the actual official engine's supported scenario/state APIs, or controlled lab bots/replay transitions if custom state injection is unavailable. Agent 2 implements simulator fixes; you verify their claims independently.

Test one legal action and one round before longer horizons. Cover consumed action allowances, one successful cast, reset attacks, movement/attack exclusions, alternating order, cooldown/stun/shield boundaries, linked deaths and reward transfer, Varg splash, Ren retaliation, Vendetta resets, camp waking/sleeping/targeting/death, spawn legality and dash paths across walls/holes/occupants. Record exact mismatch states and model limitations. A simulator agreeing with itself is not validation.

Review Agent 2's budget measurements outside fuel-free debug blocks in the real release/Wasm environment. Audit reserve construction and interrupted-turn semantics. Verify that Agent 3's bound diagnostic tests the actual final scorer and distinguishes pruning from explicit work caps. Audit Agent 4's match joins, timestamp/version windows and held-out groups.

Own the shared world contract, particularly awake camps: the audited `hot_zone` included healthy members of awakened groups while `awake_camps_near` selected damaged members. Resolve semantics against the engine, then expose a consistent interface used by combat and farming. Route requested source changes through the registered owner.

## Integration and promotion

Require each change to arrive with a switch, source/artifact identity, targeted evidence, full-match screen and explicit decision. Integrate in dependency order: observability/budget interface, verified correctness fixes, validated simulator/search work, economy/draft improvements, then optional ML. Do not add each agent's reported gains together; measure the combined build.

Assign reviews across roles and resolve substantive objections before promotion. Remove accidental experimental settings and verbose runtime logging from release; verify the exact package after final configuration. Preserve the last known-good artifact and reproducible rollback.

Prepare a finished source/artifact package, manifest, build instructions, changelog and validation report even if live publication needs separate authorization. When publication/challenges are already explicitly authorized, perform the concrete supported action and record the actual IDs/timestamps; otherwise request only that final action after preparation. Do not invent background ladder monitoring or schedule it without the user's request.

## Completion report

Lead with the actual result: what is ready, what changed, whether the exact final build beat the frozen baseline, how uncertain the estimate is, and what remains untested. Provide artifact and evidence links, GitHub links when created, known limitations and platform status. Distinguish completed work, inconclusive improvements and unavailable external validation. Never claim "best possible" as a proven result.


<!-- END AGENT_1_LEAD_AND_VALIDATION.md -->

---

<!-- BEGIN AGENT_2_RUNTIME_AND_COMBAT.md -->

# Agent 2 prompt — Fuel governor, combat and tactical simulation

You are Agent 2 of exactly four agents building Battlecode v36. Read `prompts/v36/MASTER_PROMPT_v36.md` and `REFERENCE_PLAN_v34.md` first. Follow the shared evidence, GitHub/direct communication, ownership, evaluation and authorization contracts. Do not spawn additional agents.

Your objective is to recover useful combat decisions under the real fuel budget, preserve action legality and survival, and improve full-match performance against strong opponents. A higher search-coverage number alone is not success.

## Ownership and interfaces

Own candidate `tsearch.cpp/.h`, `fight.cpp/.h`, `main.cpp`, new runtime-budget helper files, and combat/scenario fixtures. Agent 1 owns `common.h`, `world.cpp/.h` and the independent simulator-oracle harness. Agent 3 is the only writer of `bot.cpp/.h` and `strategy.h`.

Publish your proposed budget API, verdict/reason schema, snapshot omission contract and telemetry fields early. Send combat changes in `bot.cpp` as narrowly scoped patches against a recorded source hash. Agent 3 applies/adapts and acknowledges them before you validate the integrated build. Use the same route for declarations in `bot.h`. Request common-switch and world-state changes from Agent 1. Do not edit shared files concurrently.

## Task 1 — Measure and govern actual fuel

Profile release/Wasm execution, including initialization, snapshot construction, kit prewarming, fight/run search, action search if enabled, route search, fields, camp scoring, beliefs/sightings, telemetry and turn tail. Agent 3 supplies farming-stage probes; Agent 1 supplies scheduling and parsing. Measure actual fuel counters, not native wall time or fuel-free `debug_block` instrumentation.

Record stage cost distributions and expensive cases by champion, map, scene size, model count, horizon and first/subsequent turn. The supplied plan's exhaustion rates are hypotheses/historical measurements to reproduce. Confirm actual default fuel and initialization allowances from the current engine.

Design a cheap deterministic governor with conservative pre-stage admission, bounded inner work where one stage can grow, and an emergency fuel floor. Reserve must cover the remaining legal action and unavoidable bookkeeping/turn tail, including any mandatory work already committed. Do not use unsigned underflow or rely on an average cost as a worst-case bound. Preserve deterministic work caps where useful; do not simply raise every cap or lower the cost estimate.

Each optional stage must leave coherent state on refusal/early exit: a valid single-target farm fallback, formula-based combat fallback, complete chosen action, or previously valid cache. Never publish half-built fields/routes/snapshots as current. Distinguish deliberate skips from exhaustion and faults. Integrate the API through Agent 3 into `play_turn`, farming/route loops and field scheduling; coordinate world work with Agent 1.

Saved rules say fuel exhaustion suspends and resumes at the same instruction next round. Reproduce partial-action/stale-state cases and determine observed engine behavior. Avoid describing it as a universal no-op or exception. Count official exhaustion entries, separately detected suspensions, stage skips and runtime/action faults, with champion-turn/game denominators and overlap explained.

Do not hardcode the supplied round-one route skip without tracing the actual path. The audited `farm` already treats `field_calls == 0` as low fuel, and fields are normally built near the end of `play_turn`.

Acceptance: zero observed unexplained exhaustion/suspension and runtime/action faults in the fixed regression suite where achievable, explicit residual cases and rates otherwise, useful planning participation, and unchanged or improved match strength. A governor that disables almost all planning is a failed solution even with zero exhaustion.

## Task 2 — Relevant, honest combat snapshots

Audit `ts_snapshot`: the baseline takes self, up to three allies within seven, then enemies within eight in observation/vector order, with eight total slots. Implement independently switchable stable relevance ranking using distance, reachable burst, attack opportunities, participation time, vulnerability and linked-state dependencies. Use deterministic ties.

Treat Cassi/Issac inclusion and linked death as a dependency. Keep both when their observed states are available and relevant. Do not fabricate a hidden partner's state. If capacity/visibility prevents an adequate model, preserve the missing risk explicitly and restrict what a search verdict can override, or use a coherent fallback.

Test a five-unit relevant snapshot, measured six/seven/eight-unit budgets, and alternatives that retain more threats with a shorter horizon. A five-unit cap is a candidate, not a mandated final design. Log original eligible scene size, selected/dropped IDs and reasons, linked-pair completeness and omitted danger. Report coverage by original scene size so truncation cannot inflate apparent success.

Do not erase omitted units as movement blockers or certify safety against enemies the model did not include. Use actual observation-time information only. Request replay scene/encounter distributions from Agent 4.

## Task 3 — Improve the existing search budget and safety

`tactical_decide` already reduces two enemy models to one and shortens the horizon. The audited deterministic estimate uses 2,200 × units × (rounds + 1) for a playout; the minimum paired comparison is 66,000 for five units and 79,200 for six against 70,000. Measure both paired rollout cost and preparation overhead before changing estimates. Protect the legal-action reserve.

Compare only completed fight/run pairs under the same enemy model and comparable horizon. An incomplete favorable half is not a verdict. Separate these statuses: no eligible enemy, safety reserve refusal, predicted budget refusal, incomplete comparison, completed comparison inside margin, clear fight, clear retreat. Report model/horizon selection and actual cost alongside status.

Distinguish fight/run classification `APEX_TS_DECIDE` from the separate action search `APEX_TSEARCH`, which was off in the audited baseline. Do not silently enable both. Keep calibration/local-network flags off unless separately validated.

Carry danger reasons through `handle_enemies`. The baseline positive verdict can set `winning=true` and `in_danger=false` after earlier champion-risk checks. Permit overrides only for risks the model represents adequately; retain burst, omitted enemies, linked-partner or camp risk otherwise. Do not make every risk flag an unconditional retreat: when escape is blocked, fighting may be the least harmful legal action. Compare choices and explain the fallback.

## Task 4 — Validate and repair the simulator

Work with Agent 1's independent official-engine oracle. Start with one action and one round; then assess multiround divergence. Cover 1v1, 2v2, 3v3 and dense scenes, open/blocked terrain, awake/sleeping camps, stuns, shields and dash escapes.

Source-visible simplifications requiring direct tests include:

- One successful cast per turn across offensive spells, dashes and resets; action allowances already consumed before search; melee/ranged movement exclusions and successful basic-attack counts.
- Cooldown and buff expiry boundaries, alternating action order, target ties, stun immunity, Varg splash, Ren retaliation on lethal hits, Vendetta reset, linked Cassi/Issac death and gold/gem accounting.
- Team-relative spawn legality and recovery; movement occupancy including camps and omitted champions; legal dash paths across holes, walls, intermediate occupants and occupied landings.
- Camp wake/sleep timing and healthy members of awakened groups, range/target selection, camp HP/death and carried-gem destruction. Current `ts::Camp` does not represent all of these.

Do not promote `APEX_TS_CAMPS=1` merely because it exists. Compare a corrected camp model against a conservative camp-risk guard as separate candidates. Record unresolved modeling gaps and ensure they constrain verdict authority. Never validate the model solely against itself.

## Task 5 — Flee-hit correctness

Supply Agent 3 an independent `NOVA_FLEE_HIT`-style change before `escape_or_stand`: when a fleeing melee champion can legally attack, hit the weakest legal visible adjacent enemy even if the strategic chosen target is farther away, then continue escaping. Preserve dash, spell/reset, movement and successful-attack allowances; do not return immediately after the hit.

Test distant chosen target plus adjacent attacker, shields/target legality, already-used attacks, linked bodies, melee versus ranged exclusions, and blocked escape. Then measure full matches; the historical small gain is not a fresh result.

## Deliverables and review

Deliver independent switches, a documented budget interface, compact telemetry, scenario fixtures, measured release cost tables, simulator differential evidence, coverage-by-original-scene tables and ready-to-apply shared-file patches. Report strong-opponent outcomes, including deaths versus the actual recovered `sparexp` if available, plus full-match win/secured-score effects and fuel costs.

Apply every candidate's common screen and fresh-validation gates. Retain the best validated combination, including the possibility of leaving an experiment off. Ask Agent 1 to review runtime/model claims independently; review Agent 3's action/fuel integration in return. Send relevant findings directly to Agents 1, 3 and 4 and record meaningful milestones on the GitHub workstream issue.


<!-- END AGENT_2_RUNTIME_AND_COMBAT.md -->

---

<!-- BEGIN AGENT_3_FARMING_AND_ECONOMY.md -->

# Agent 3 prompt — Farming correctness, survival and economic tempo

You are Agent 3 of exactly four agents building Battlecode v36. Read `prompts/v36/MASTER_PROMPT_v36.md` and `REFERENCE_PLAN_v34.md` first. Follow their ownership, communication, evaluation and authorization contracts. Do not spawn additional agents.

Your objective is better full-match secured resource production and competitive performance, especially on farming-race maps and unseen maps. Diagnose time and resource loss before changing broad behavioral thresholds. Fewer deaths or an earlier capture alone does not prove an improvement.

## Ownership and interfaces

You alone write candidate `bot.cpp/.h`, `strategy.h`, farming helpers and farming fixtures. Agent 2 owns tactical search/simulation, runtime-budget helpers and `main.cpp`; Agent 1 owns common switches and `world.cpp/.h`; Agent 4 owns draft and canonical map identity.

Accept Agent 2's combat/flee-hit/governor patches against recorded hashes, review/adapt them, integrate without erasing your work and acknowledge the new hash. Request missing interfaces rather than making private incompatible versions. Agent 1 integrates macro changes; Agent 4 supplies official-map/unknown recognition. Keep the baseline frozen and changes independently switchable.

## Task 1 — Correct the farming score's upper bound

Audit `score_groups`, `prune_bound`, final score construction and runtime tuning. The audited bound at `bot.cpp` around line 3324 omits the boot bonus applied around 3398 and dominant-group bonus around 3404. Baseline values include dominant-group multiplier 6 and boot bonus 0.3329, but the live boot value comes from runtime tuning; do not hardcode one compile-time constant as a general bound.

Account for every enabled score-increasing term, including optional altar/nearby-number bonuses, jitter and learned residual. Derive a documented admissible bound for the actual single-group objective and applicable group state. If a safe tight bound is impractical for a particular enabled term, use a conservative bound or bypass mathematical pruning for those candidates. Preserve finite behavior and correct thresholds.

Keep mathematical pruning, the explicit 16-group scoring/work cap and route candidate heuristics separately counted. Do not claim route-global optimality from an admissible single-group bound. Do not silently lift all caps in production.

Create substantive synthetic/captured-state checks across rewards, respawns, participants, stickiness, round-60 boundary, dominant-group threshold, item threshold and optional positive modifiers. Assert actual computed final single-group score never exceeds its bound. In a diagnostic mode, lift work caps and control route heuristics to compare pruned versus exhaustive single-group choice. Assess route candidate loss separately. Keep disabled-switch parity and diagnostic overhead measured.

## Task 2 — Establish a farming loss ledger

Instrument or reconstruct: first camp/capture; captures, gold and collected/submitted gems by rounds 50/100/150/300; travel, waiting/staging, fighting, collecting, recall, shop, healing and idle time; failed/abandoned jobs; gem bags lost or banked; helper claim versus actual contribution; camp-caused deaths and linked-death incidents.

Use actual event and timing semantics from Agent 4's parser. Distinguish a camp clear from reward collection/capture, and collection from secured submission. Reproduce the two supplied sample incidents only after their team/version identity is joined to platform metadata. They are case studies, not a performance estimate.

Check the first-turn execution path empirically before adding a route skip: `farm` already uses `field_calls == 0` as a low-fuel condition, starts with no target, and fields are built near the turn tail. Integrate Agent 2's governor before optional score/route work and ensure early exits preserve coherent target/claim/cache state.

Report candidates considered, mathematically pruned, work-capped and actually scored; route calls/expansions; stage attempts/skips; and fallback outcomes. Avoid extensive per-candidate release logging.

## Task 3 — Improve farming-race tempo with isolated policies

Use full-length official and unseen maps. Recover historical opening/farm benches if available or use the real runner through Agent 1. Treat the plan's rows/lanes/corners diagnoses as hypotheses to reproduce on version-correct data.

- **Rows:** trace spawn-to-first-capture and opening order. Test a narrowly scoped melee/tank opening or related routing change against the frozen opening, behind strict map recognition. The previous broad opening schedule was neutral, so do not simply enable it globally.
- **Lanes:** quantify recall/shop/heal plus return-to-camp cost, item payback and missed respawn/capture opportunities. Test a measured shopping departure rule or route adjustment. Preserve emergency survival, completed captures and safe banking.
- **Corners:** let capture/banking/route traces identify the mechanism; do not invent an opening fix from map name alone.
- **Stampede/dominant groups:** preserve successful big-camp commitments while fixing the bound. Measure early commitment, complete capture, survival and secured score instead of assuming a higher score bonus is always useful.

Existing `go_home_if_needed` uses a generic gold threshold, preserves some completed jobs, handles camp-interrupted recalls and exempts healthy Tavi because she shops away from spawn. Retain these semantics unless a separately measured change is intended. Test Tavi field shopping, low-health emergency recall, rich champion finishing a capture, banking a valuable bag, interrupted recall, full-heal timing and no repeated shopping loop.

Request Agent 4's canonical official-map identity; `nova_map_id` and `brain::map_id` are different classifiers and descriptors can collide on generated maps. Unknown maps must take an explicit robust fallback.

## Task 4 — Improve camp safety without farming paralysis

Predict damage before the next camp phase using actual awake group state, camp ranges and tie rules, current helper/tank positions and arrival times, observed health and linked-partner risk. Do not treat a job claim as guaranteed tanking/DPS. Reassess when a tank leaves or becomes unsafe.

Coordinate Agent 1's world awake-state interface and Agent 2's simulator/camp-risk contract. Source inspection found `group_soak` truncation at 12 camps and a nearby-safety cap at 32; diagnose dense scenes before extending them. Existing `NOVA_CAMP_SAFE` is an experimental policy, not a proven fix.

Test tank departure, healthy members of awakened groups, splash waking nearby camps, camp sleep transitions, boxed-in respawns, many damaging camps, partner vulnerability and recall placement outside all actual threats. Compare actual completion/recovery cost and secured resources, not merely raw camp damage taken.

Integrate Agent 2's flee-hit and danger-reason patches through your sole-writer role, preserving legal action flow and escape. Let Agent 2 validate the integrated combat behavior.

## Task 5 — Optional bounded farming correction

Only pursue production ML after logging, scorer correctness, governor and deterministic candidates work. Agent 4 owns dataset/predictor development; agree a model/header integration owner before edits. Existing `learner.h` offers an optional 16-feature multiplicative residual with a wide 0.5–2 clamp; its presence does not justify activation.

Start with interpretable completion-time, damage/recovery and interruption predictions, then a tightly bounded correction to the corrected hand score. Include baseline score, eligible/excluded candidates, actual helper arrival and observation-time features. Gate calls by relevance and measured fuel. Keep zero-weight identity, finite/clamped output and explicit missing-feature fallback. Promote only on fresh held-out full matches; predictive accuracy alone is not enough.

## Deliverables and acceptance

Deliver upper-bound derivation and diagnostic evidence; independent candidate switches; farming/time/resource ledger; map-specific hypotheses and outcomes; camp safety fixtures; governor integration; a recommendation that can retain baseline behavior; and exact manifests/results under the master protocol.

Run targeted correctness checks before paired matches. Complete the unseen screen, recovered varied opponent pool and fresh-validation gates for promising candidates. Measure interactions with draft changes and combat/governor patches in the final combined build. Request Agent 2's fuel/action review, and review Agent 4's map/draft consequences. Send useful findings to the relevant agents immediately and record decisions on GitHub milestones.


<!-- END AGENT_3_FARMING_AND_ECONOMY.md -->

---

<!-- BEGIN AGENT_4_DRAFT_AND_DATA.md -->

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


<!-- END AGENT_4_DRAFT_AND_DATA.md -->

