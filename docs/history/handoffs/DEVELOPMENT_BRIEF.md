# Cambridge Battlecode — Next-Generation Development: x1 Improvements and botx3

You are an expert competitive game-AI developer, C++ engineer and optimisation researcher working on our Cambridge Battlecode repository:

https://github.com/Infosuii/neural-networkk-battlecode

Your objective is to use the extensive research and experiments already completed to develop a substantially stronger bot, particularly one capable of generalising to completely unseen maps in the competition finals.

Work autonomously, investigate problems thoroughly, implement promising solutions and validate them experimentally. Prioritise actual competitive improvements over adding complexity.

**Do not submit, publish or activate a new bot on the official Battlecode ladder.** Local implementation, testing and commits to dedicated development branches are permitted.

## Phase 1 — Understand the latest results and establish the baseline

Start by inspecting the latest commits across the relevant branches, particularly:

- `build/z-plan`
- `build/z-plan-5060`
- `comms/x1`
- `research/x1-audit-2026-11-02`

Read the existing research, replay analysis, dependency audit, K004–K009 results and any newer findings.

Pay particular attention to the newly introduced `x1c1` candidate, the v92 bot, and the K010 head-to-head and ladder analysis. Check whether K010 has been completed since the last review.

Establish which implementation is actually strongest across different opponents and map styles.

Do not assume x1c1 is better because it passed selected local tests. Its initial ladder results were poor against several strong opponents.

Preserve a frozen reference version of original x1 and identify the best validated alternative for future development.

Avoid repeating tests that already have reproducible results unless new evidence or conditions justify doing so.

## Phase 2 — Resolve important architectural weaknesses

Use the completed x1 replay and dependency audit to investigate and address the most consequential problems.

Priorities include:

1. **Retreat/farming conflicts:** Prevent champions from repeatedly fleeing danger and then returning immediately to the same unsafe objective.
2. **Bush and visibility coherence:** Investigate incomplete bush-component IDs, cached ward information and stale visibility observations.
3. **Incorrect combat and camp models:** Review verified inaccuracies involving champion mechanics, camp danger and candidate pruning.
4. **Banking and resource preservation:** Investigate failures to convert collected gems into banked score and opportunities to coordinate team banking.
5. **Fuel efficiency:** Preserve useful precomputation improvements without introducing incorrect information or excessive fuel usage.

Trace each issue to its source code and use replay evidence to establish the mechanism.

Implement targeted fixes in isolation, then test them. Distinguish between correcting an actual bug and improving win rate: a logically correct fix may still need strategic retuning.

Importantly, investigate interactions between systems. If two features work separately but fail together, determine whether their objectives, thresholds or execution order conflict.

Do not immediately discard promising features after one negative test. Check activation, dependencies, implementation correctness and meaningful parameter alternatives first. However, do not spend unlimited experiments rescuing ideas without evidence of potential.

## Phase 3 — Develop a map-independent economic planner for botx3

This should be the main new development workstream.

The existing research indicates that x1 frequently loses because of insufficient resource collection, inefficient camp allocation, unnecessary waiting and poor conversion of resources into banked gems.

Rather than continuing to optimise individual heuristics independently, investigate a coordinated team-wide planner that can make economically efficient decisions on unfamiliar maps.

### A. Analyse the map

Investigate how the bot can calculate useful strategic information about a completely new map without relying on its identity.

Consider:

- Camp locations, resource yields and respawn cycles.
- Actual travel distances and accessibility.
- Efficient routes between camps and banking locations.
- Chokepoints, obstacles and dangerous regions.
- Differences in resource accessibility between the two teams.
- Champion-specific farming and movement advantages.
- Opportunities to control multiple valuable objectives.

Use the game engine's actual visibility and information rules.

Avoid simplistic map classification unless testing demonstrates that it helps.

### B. Exploit available computational fuel

Investigate how the larger draft-time fuel budget and spare computation in early turns could be used productively.

Potential applications include graph construction, shortest-path precomputation, efficient camp schedules, initial champion assignments, resource-value estimates and simplified strategic simulations.

Determine what information can be calculated during drafting, what can be retained, and what must be computed after the match begins.

For dynamic calculations, consider spreading work across multiple turns or using remaining fuel after essential actions.

Use actual engine measurements to determine whether these approaches are feasible.

### C. Coordinate the team's farming decisions

Investigate team orienteering and scheduling algorithms with travel times, camp respawns and resource constraints.

The system should aim to reduce:

- Multiple champions unnecessarily targeting the same objective.
- Champions waiting at camps when better alternatives exist.
- Excessive travel between low-value objectives.
- Poorly coordinated camp clearing.
- Repeated changes of target without meaningful benefit.
- Farming decisions that ignore future banking costs.

Consider greedy scheduling, local search, assignment optimisation, rolling-horizon planning or other suitable methods.

Design the planner to account for time, gem yield, gold yield, risk and banking requirements.

A major goal is to improve expected successfully banked gems per round, not merely resource collection.

### D. Plan the match as a whole

Investigate how the economic planner should influence the opening, midgame and endgame.

For example, the opening could establish initial farming routes and champion assignments. The midgame could continuously update camp schedules and territorial priorities. The endgame could increasingly prioritise safe banking or enemy denial based on the race to 1,000 gems.

The bot should react to enemy pressure and changing conditions without abandoning productive objectives unnecessarily.

The underlying objective is to maximise victory probability, not simply minimise deaths or maximise farming in isolation.

## Phase 4 — Adaptive strategies for unseen maps

Once the economic planner has a useful working prototype, investigate whether different strategic configurations become preferable under different map and game conditions.

Review the existing `X1_PLAN` system and case-based strategy research.

The previous map-topology analysis found little predictive power for selecting plan 4. Do not assume that more complicated classification will automatically improve this.

Instead, investigate whether features such as accessible resource value, expected farming efficiency, enemy pressure, banking progress and control of contested objectives better predict which strategy is appropriate.

Consider:

- A single robust general-purpose strategy.
- Several specialist strategies selected from map characteristics.
- A lightweight adaptive controller that changes strategic priorities during the match.
- A hybrid system combining economic planning with combat and opponent modelling.

Compare these approaches experimentally.

Avoid designing an elaborate meta-controller before proving that the strategies it selects are meaningfully different and beneficial.

## Phase 5 — Rigorous testing and iteration

Use the repository's existing benchmarking infrastructure wherever possible.

Evaluate improvements across:

- Original official maps.
- Generated ladder-style maps.
- Maze-style maps.
- New map structures and generators not used during tuning.
- Different opponent implementations, including x1, v86h, x2, v92 and relevant stronger bots where available.

Maintain a genuinely untouched set of maps for final validation.

Test both sides of each map and compare candidates against the same reference conditions.

Record win rate, resource collection, banking efficiency, deaths, fuel exhaustion, match duration and other relevant metrics.

Be especially careful with deterministic sensitivity: recent experiments demonstrated that seemingly insignificant code changes can alter many outcomes.

Use paired comparisons, inspect gained and lost games, and avoid declaring tiny win-rate differences meaningful without sufficient evidence.

When a feature fails, investigate whether the problem is its underlying idea, implementation, interactions, fuel cost or inappropriate testing conditions.

Prioritise changes that improve performance across diverse maps and opponents.

## Development principles

- Reuse existing research and code rather than rebuilding solved infrastructure.
- Focus on the highest-impact problems first.
- Prefer structural improvements to endless parameter tuning.
- Keep new features modular and independently testable.
- Investigate dependencies before combining features.
- Avoid unnecessary rewrites of working systems.
- Use existing implementations as references, not permanent architectural constraints.
- Research relevant algorithms when they offer a plausible improvement over existing approaches.
- Explore unconventional solutions when evidence suggests standard heuristics are insufficient.
- Do not blindly copy strategies from the strongest opponents; understand why those strategies work.
- Preserve original bot versions and reproducible benchmark results.
- Do not publish or submit a bot to the official competition.

You have freedom to propose or implement a better approach if the evidence indicates that one of the planned directions is inefficient.

## Expected outputs

Produce:

1. **Baseline assessment:** Which existing bot is strongest, against which opponents and on which map styles.
2. **Architecture fixes:** The important issues resolved, with code changes and measured outcomes.
3. **botx3 economic planner:** A working experimental implementation or prototype, with a clear explanation of its planning method.
4. **Experimental results:** Comparisons against existing bots across diverse maps.
5. **Generalisation analysis:** Evidence of whether improvements transfer to genuinely unfamiliar maps.
6. **Future roadmap:** The most promising next improvements, including adaptive strategy selection and further optimisation.

Maintain a concise development log explaining meaningful experiments, their results and why changes were accepted, revised or deferred.

Do not spend excessive time on documentation or routine status reports. Put effort into investigation, implementation and testing.

## Execution instructions

Begin immediately by inspecting the latest repository state and completing the baseline assessment.

Then address the most important existing issues and begin designing and implementing the economic planner.

Work iteratively:

**Investigate → Implement → Test → Diagnose → Refine → Retest.**

Do not stop after producing a high-level plan. Carry out development wherever the evidence and available tools support it.

Prioritise correctness, competitive performance and generalisation. If a method fails, determine why before replacing it.

The aim is not simply to produce another map-tuned version of x1.

**The ultimate objective is to establish the foundation for botx3: a bot that understands the economic and strategic structure of an unfamiliar map, coordinates its team intelligently, uses available computation effectively, and performs consistently against strong opponents without relying on memorised map configurations.**