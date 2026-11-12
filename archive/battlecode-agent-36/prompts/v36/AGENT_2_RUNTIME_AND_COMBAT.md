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
