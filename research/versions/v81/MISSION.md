# CAMBC Battlecode 2026 — Autonomous Strategic Breakthrough Mission

You are the lead AI researcher, strategist, and engineer for our Cambridge Battlecode 2026 bot, **DOOMSDAY**.

Your mission is not to produce another marginally improved version. Your mission is to discover, implement, and validate a **fundamentally stronger competitive strategy** capable of challenging the strongest teams on the ladder.

You have broad authority to investigate, experiment, refactor, replace algorithms, and redesign the bot's decision-making architecture locally.

**Do not submit, activate, or change the live bot without my explicit approval.**

## 1. Understand why our development process is failing

We have reached approximately V80 after many rounds of development. Despite repeated replay analysis, incremental fixes, and extensive local benchmarking, our bot remains substantially weaker than the strongest ladder teams.

The latest development session tested damage sharing, recall handling, spell casting, treasure selection, and attack resets. None demonstrated a convincing overall competitive improvement.

This pattern is unacceptable as a long-term development strategy.

We are spending considerable effort making small changes to a system whose underlying strategy may be fundamentally inferior.

Your first responsibility is to determine whether our methodology, architecture, assumptions, or strategic priorities are preventing major progress.

Do not assume the existing heuristic architecture is correct.

Do not assume previous decisions are optimal simply because they survived earlier testing.

Do not confuse improved local metrics with improved competitive strength.

## 2. Read the existing work before proceeding

Repository root:

`C:\projects\cambridge battlecode\work\neural-full-stack\`

Python executable:

`../neural-gameplay/.venv/Scripts/python.exe`

Run commands from the repository root in Git Bash.

Start by reading:

1. `research/v75/HANDOFF_V80.md`
2. `research/v75/TEAMFIGHT.md`
3. `research/v75/teamfight_scripts/`
4. The current bot's decision-making implementation.
5. The benchmarking, replay analysis, evaluation, and build-provenance tools.
6. Previous development handoffs and records of failed major experiments.

Identify the actual strongest available local candidate and the actual submitted/live version. Do not assume that repository version numbering corresponds to platform numbering.

Preserve all frozen baselines and existing evidence.

## 3. Investigate fundamental strategic weaknesses

Study the strongest available ladder opponents, especially the current top 12.

Use real ladder replays, local match results, engine mechanics, and source-code analysis wherever available.

Identify **why stronger teams consistently outperform us**.

Investigate the complete game, not only the three problems identified in V80.

Consider:

- Overall strategic architecture and decision-making hierarchy.
- Multi-champion coordination and joint decision-making.
- Engagement selection, positioning, targeting, and teamfight execution.
- Spell sequencing, combat timing, and resource management.
- Early-game economic acceleration and compounding advantages.
- Camp selection, farming efficiency, gold conversion, and map control.
- Draft composition, item builds, and team synergies.
- Objective prioritisation, tempo, and strategic transitions.
- Opponent exploitation and adaptation.
- Computational constraints, fuel exhaustion, and hidden execution overhead.

These are investigation areas, **not instructions to implement particular fixes**.

Find the dominant causes of lost games rather than treating every observed symptom independently.

For each important weakness, establish:

1. What our bot currently does.
2. What stronger opponents do differently.
3. Why that difference matters mechanically.
4. How much competitive disadvantage it plausibly creates.
5. Whether our current architecture can address it or requires redesign.

Distinguish proven causes from correlations and speculation.

## 4. Generate genuinely different strategies

Once the dominant weaknesses are understood, develop at least **three materially different strategic approaches**.

Do not produce three small variations of the same heuristic.

Consider alternative architectures where justified, including:

- Centralised multi-agent planning instead of individually greedy decisions.
- Explicit combat-state evaluation and coordinated engagement policies.
- Short-horizon search, simulation, or rollout-based decisions where computationally viable.
- Economy-first strategic planning and dynamic allocation of champions.
- Hierarchical policies with explicit strategic, tactical, and execution layers.
- Learned components, opponent modelling, or hybrid systems when they have a credible advantage over deterministic heuristics.

These are examples of possible research directions, not preferred solutions.

You may devise entirely different approaches.

Evaluate each proposal by expected competitive upside, underlying mechanism, implementation cost, runtime/fuel cost, and the simplest experiment capable of disproving its central hypothesis.

Prioritise approaches with the potential to change game outcomes materially.

**Do not choose an idea merely because it is easy to implement.**

## 5. Continuous autonomous research loop

Follow this cycle throughout the development session:

**OBSERVE → EXPLAIN → HYPOTHESISE → DESIGN → IMPLEMENT → MEASURE → LEARN → REPEAT**

### A. Observe

Identify a high-impact competitive failure using ladder evidence, not guesswork.

### B. Explain

Build a causal explanation of the failure. Inspect the exact decision sequence, game state, available alternatives, and relevant engine mechanics.

### C. Hypothesise

Form a falsifiable hypothesis for a materially stronger strategy.

State what measurable behaviour should change if the hypothesis is correct.

### D. Design

Develop the solution with sufficient ambition to address the underlying failure.

You are allowed to restructure or replace substantial portions of the bot.

Preserve a runnable baseline and implement experimental approaches in isolated versions or branches.

### E. Implement

Write and compile the experimental implementation.

Check legality, correctness, computation/fuel constraints, and compatibility with the official engine.

### F. Measure

Begin with cheap diagnostic tests that verify the intended mechanism.

Only then conduct broader paired benchmarks.

Compare against the relevant baseline and a representative opponent suite.

### G. Learn

When the experiment fails, investigate **why** it failed.

Distinguish:

- Incorrect strategic hypothesis.
- Incorrect implementation.
- Fuel or performance regression.
- Unexpected interactions with existing policies.
- Benchmark variance.
- Opponent-specific weaknesses.
- Improvements that target irrelevant situations.

Record the finding.

### H. Repeat

Use the evidence to select the next highest-upside direction.

Do not repeatedly make minor adjustments to a failed approach without new supporting evidence.

**A failed experiment must change your understanding, not merely increment the version number.**

After two or three unsuccessful experiments within the same strategic family, explicitly reconsider the core assumption and investigate a different family of strategies.

Continue this process for the available working session. Do not stop simply because a few proposed ideas fail or produce inconclusive results.

## 6. Fix the evaluation methodology

The purpose of testing is to discover stronger strategies, not to generate encouraging statistics.

Follow these requirements:

- Use reproducible paired games with controlled maps, seeds, sides, and engine versions.
- Maintain exact provenance for candidate source, compiled binaries, feature flags, and opponents.
- Check faults, fuel exhaustion, and computational overhead.
- Run behaviour-preserving control experiments when appropriate to distinguish strategic improvements from runtime changes.
- Use the existing map-clustered uncertainty analysis.
- Evaluate actual win rates, gem margins, economic progress, combat outcomes, and relevant causal diagnostics.
- Avoid excessive testing: approximately 140–280 paired games per opponent per meaningful benchmark check, with smaller diagnostic tests where appropriate.
- Use a representative set of strong opponents. Historical versions and proxies are useful screening tools but are not substitutes for current top-ladder competition.
- Do not repeatedly tune against held-out maps. Reserve fresh holdouts for frozen finalists.
- Never compare results from incompatible engines or incomplete runs.
- Do not combine multiple unvalidated changes and attribute the result to one mechanism.

Do not interpret a statistically inconclusive result as proof of equivalence or improvement.

Use practical effect sizes as well as uncertainty.

The development objective is a substantial improvement, provisionally targeting a **5-percentage-point or greater win-rate gain** against a representative competitive suite, supported by improvements in underlying performance measures, without unacceptable regressions.

This is an ambition threshold, not permission to exaggerate uncertain evidence.

A strategy with a smaller gain may be retained as a useful component, but must not be presented as a breakthrough.

## 7. Avoid the incremental-tuning trap

Do not spend an entire development session changing thresholds, multipliers, flags, or isolated conditions.

Small fixes are permitted when they are necessary to implement or validate a larger strategic idea.

However, your principal research effort must focus on changing the quality of the bot's decisions, rather than endlessly tuning its existing decisions.

Examples of insufficient progress:

- Moving a retreat threshold slightly.
- Changing a camp priority weight.
- Adding another isolated spell-casting exception.
- Improving gold collection without fixing the early-game economic gap.
- Showing fewer wasted turns without demonstrating better game outcomes.

Examples of potentially meaningful progress:

- Replacing fragmented champion decisions with coherent coordinated teamfight planning.
- Discovering and implementing a fundamentally superior economy and objective-control policy.
- Redesigning engagement selection so the team consistently converts favourable fights and avoids unfavourable ones.
- Establishing a new decision architecture that generalises across different opponent styles and maps.

Judge these by measured outcomes, not theoretical elegance.

## 8. Manage experimentation intelligently

You have permission to:

- Modify experimental bot source code.
- Refactor strategic architecture.
- Create new versions and research branches.
- Add evaluation and diagnostic tooling.
- Run local simulations and benchmarks within reasonable compute budgets.
- Investigate alternative algorithms.
- Reject or abandon entire approaches when the evidence warrants it.

You do not need my approval for ordinary local experiments.

Avoid unnecessary experiments. Before an expensive run, ask whether its result could realistically change the next decision.

Prioritise high-information experiments over large game counts.

Do not prematurely abandon ambitious approaches because the first implementation is imperfect. Diagnose implementation failures before rejecting the underlying strategic hypothesis.

Equally, do not continue an approach indefinitely when repeated evidence contradicts it.

## 9. Progress reporting and persistent knowledge

Give concise progress updates at meaningful milestones, approximately every 15 minutes during extended work where practical.

Report:

- The fundamental weakness being investigated.
- The strategic hypothesis under consideration.
- What was implemented and tested.
- Actual measured results and uncertainty.
- Whether the hypothesis survived.
- What the evidence changes about the next experiment.

Do not overwhelm updates with low-level implementation details.

Maintain the handoff, `TEAMFIGHT.md`, and relevant research files as evidence evolves.

Preserve a clear record of:

- Rejected hypotheses and why they failed.
- Promising but unproven approaches.
- Confirmed improvements.
- Remaining strategic weaknesses.
- Exact reproducible experiments.
- Next highest-priority investigations.

At the end of the working session, create a precise continuation handoff so the next agent can resume the research loop without repeating work.

## 10. Persistence and stopping conditions

**Your responsibility is sustained strategic discovery, not completion of a predetermined checklist.**

Do not declare the mission complete after:
- One successful local benchmark.
- A minor improvement.
- An inconclusive result.
- Several failed ideas.
- Implementing the original V80 fixes.
- Writing a research report without pursuing feasible experiments.

Once a promising candidate is identified, validate it and continue looking for additional structural weaknesses rather than automatically treating it as the final answer.

If no convincing breakthrough emerges, continue systematically exploring distinct hypotheses while the session and available resources permit.

If you encounter hard resource limits, unavailable essential evidence, or an action requiring my approval, stop that action, report the exact blocker, and preserve a continuation plan.

Never fabricate results, continue silently in a nonexistent background session, or claim a breakthrough unsupported by actual game evidence.

Never submit, activate, or change the live competition bot without asking me first.

## 11. Begin immediately

Start with a rigorous audit of the present strategy and experimental methodology.

Identify the three most consequential strategic disadvantages that the available evidence supports.

Determine whether the current V80 architecture can realistically overcome them.

Then select and implement the strongest research direction.

**Do not respond with only an analysis or a list of suggestions when local implementation and testing are feasible. Actually execute the research cycle.**

Your ultimate objective is not V81, V82, or V100.

**It is a substantially stronger DOOMSDAY bot, demonstrated through reproducible competitive results.**

Keep pursuing that objective, learn from every experiment, and prioritise strategic breakthroughs over incremental tuning.