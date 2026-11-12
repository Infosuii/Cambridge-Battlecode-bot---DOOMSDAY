# Cambridge Battlecode 2026 — Elite Metagame Reverse-Engineering Research

## ROLE AND PRIMARY OBJECTIVE

You are an elite competitive-game strategist, quantitative researcher, reverse-engineering specialist, and Battlecode systems analyst.

Your mission is to **discover the strongest currently viable metagame in Cambridge Battlecode Autumn 2026 by performing an extraordinarily deep, round-by-round investigation of approximately 30 carefully selected matches involving the strongest teams on the ladder.**

This is not a conventional replay summary.

I want you to reverse-engineer the strategic principles, tactical decision-making, resource economics, champion compositions, itemisation, combat behaviour, farming priorities, objective control, and adaptive decision policies that explain why the best teams consistently outperform their opponents.

Think like a professional esports coaching and analytics team combined with a scientific research laboratory.

The objective is to answer:

**What are the strongest teams actually doing, why does it work, under which conditions does it work, and how could we reproduce or improve on it algorithmically?**

Your research should be deep enough that its findings could guide the architecture of an entirely new, highly competitive algorithmic Battlecode bot.

Do not start implementing a new bot. This assignment is RESEARCH, ANALYSIS, and META DISCOVERY ONLY.

---

## 1. ENVIRONMENT AND EXISTING RESEARCH

Repository:

https://github.com/Infosuii/neural-networkk-battlecode

Team: DOOMSDAY.

Before conducting any research:

1. Inspect the current repository, including all relevant branches and recent work.
2. Read the README, documentation, research reports, and current handoffs.
3. Identify the current official game engine, SDK, rules, and any recently introduced balance changes.
4. Read the game mechanics from authoritative sources, preferably engine and SDK code rather than relying solely on descriptive documentation.
5. Inspect existing replay extraction and analysis tools.
6. Review previous analyses so that useful findings are retained, but do not assume they remain correct under new patches.

Relevant existing resources may include:

- `docs/handoff.md`
- `docs/setup.md`
- `research/v52/top-teams-2026-10-25/`
- `research/v58/`
- `research/misc/SPRINT3_SDK_FACTS.json`
- `tools/replay/scout_public.py`
- `tools/replay/select_top_replays.py`
- `tools/replay/decode_replays.mjs`
- `tools/replay/winner_playbooks.py`
- `tools/replay/strategic_metrics.py`
- `tools/replay/scout_states.mjs`

These are starting points, not an exhaustive list.

**Critical:** Some historical replay tools are pinned to engine 1.0.3, while current game development uses engine 2.0.0. Verify decoding compatibility and update or create analysis tooling when necessary. Never silently analyse a newer replay using an incompatible engine.

You may create research scripts, data extractors, analytical tests, tables, graphs, and reports. Do not modify existing frozen bots or submitted versions.

---

## 2. SELECT APPROXIMATELY 30 HIGH-VALUE MATCHES

The quality of match selection is extremely important.

Find the strongest currently performing teams based on the latest available rankings and recent performance, rather than relying on historical reputations.

Study their opponents, recent results, champion selections, map performances, and any accessible match history.

### Target match composition

Aim for 30 unique matches:

- **20 elite-versus-elite matches:** Strong teams playing other comparably strong teams. These should reveal the highest-level strategies, counters, optimisations and small strategic advantages.
- **6 elite-versus-competitive-opponent matches:** Strong teams defeating capable but weaker opponents. Analyse how dominant teams systematically convert advantages into victories.
- **4 upset or elite-loss matches:** Matches where a leading team loses, performs abnormally poorly, or is convincingly countered. Investigate weaknesses in supposedly optimal strategies.

Adjust this distribution if necessary to obtain better evidence.

### Selection requirements

Maximise:

- Diversity of top teams and strategic styles.
- Diversity of maps and map archetypes.
- Both team starting sides.
- Champion composition diversity.
- Opponent strength.
- Relevant engine and patch versions.
- Recency of matches.
- Availability of complete, verifiable replays.

Try to include at least six distinct leading teams and eight different maps, where available.

Avoid overrepresenting a single team, map or matchup. Avoid selecting games simply because they support an expected theory.

Capture match IDs, URLs, engine versions, timestamps, map names, team identities, rankings, results, and submission versions where available.

Distinguish known submission versions from inferred versions.

**Lock the selection criteria before examining the detailed replay outcomes.**

Do not substitute 300 shallow matches for 30 deeply studied ones.

The 30 matches form the primary qualitative and quantitative research dataset. You may inspect additional match metadata to evaluate how representative the results are, but clearly distinguish that wider evidence from the core sample.

---

## 3. LITERALLY ANALYSE EVERY ROUND

This is the most important requirement.

**Every single round of every selected match must be processed.**

Do not merely sample rounds 100, 250, 500, 1000 and 1500.

Do not inspect only highlights, final inventories, opening drafts, or score changes.

For every match, reconstruct the match as a continuous sequence of game-state transitions, including all observable champion actions and strategic events.

For each round, record all relevant available information:

### Game state

- Current round and game phase.
- Map and terrain context.
- Every champion's position, health, level and status.
- Living, dead and respawning champions.
- Gold and gem inventories.
- Current equipment, upgrades and other persistent bonuses.
- Visible enemies, allies, neutral camps and objectives.
- Active abilities, cooldowns and other important action constraints.
- Team score and objective status.
- Available resources and threatened resources.
- Relevant structures, wards, teleportation points and other mechanics supported by the current rules.

### Champion decisions

For each champion's turn, record:

- Actions taken, in their actual order.
- Movement and destination.
- Targets chosen or attacked.
- Ability usage and target selection.
- Item purchases and timing.
- Farming actions.
- Combat engagement or retreat.
- Gem collection and submission.
- Positioning relative to allies and opponents.
- Changes in apparent strategic objective.

Where the available data supports it, reconstruct the champion's observable decision context.

Distinguish the full replay state from what the acting bot could actually observe under fog of war.

Never attribute hidden information or unobservable intent to the bot as though it were confirmed.

### Strategic reconstruction

From the continuous action sequence, infer:

- What objective each champion appears to pursue.
- When the team changes strategic priorities.
- How individual champions coordinate.
- Whether apparent role assignments remain stable or adapt.
- Why particular fights or farming routes are chosen.
- What conditions appear to trigger a retreat, recall, purchase, bank, or objective transition.

Label inferred intentions as hypotheses and evaluate alternative explanations.

### Required analytical depth

Process all rounds programmatically, but devote additional scrutiny to strategically important sequences.

For every meaningful turning point, inspect the lead-up, decision, immediate consequences and longer-term impact.

Examples include:

- First important purchase.
- First major camp capture.
- First contested fight.
- First high-value kill.
- First bank or score swing.
- A major route or strategic objective change.
- A champion becoming economically dominant.
- A successful or failed attempt to secure altar access.
- A coordinated attack or withdrawal.
- The point where the losing team becomes unable to recover.

For important decision sequences, reconstruct the exact actions and relevant surrounding state, ideally across several rounds before and after the decision.

**I want a causal narrative supported by the actual round data, not just a chronological event list.**

---

## 4. CHAMPION PICK AND COMPOSITION META

Determine which champions and compositions are strongest, and why.

Investigate every available champion using the current rule definitions.

### Analyse

1. Pick frequency among elite teams.
2. Pick frequency by map and opponent composition.
3. Performance of each champion within different compositions.
4. Which champion combinations appear synergistic.
5. Which combinations are vulnerable to specific counters.
6. How champions are assigned to farming, fighting, carrying, scouting or support roles.
7. How champion effectiveness changes over the game.
8. Whether a champion is selected for a specific map mechanic.
9. Whether teams build around one carry or distribute responsibility.
10. Which champions enable otherwise impossible objectives or strategies.

Investigate compositional roles such as:

- Dedicated farming specialists.
- Durable gem carriers.
- High-damage neutral-camp killers.
- Frontline combatants.
- Ranged damage dealers.
- Support or control champions.
- Mobility specialists.
- Scaling or economy-oriented champions.
- Objective access specialists.
- Anti-carry and disruption champions.

These are hypotheses to classify, not assumptions about how the game must be played.

### Deeper questions

Is the best draft determined by individual champion strength, or by complementarity between champions?

Do some champions appear powerful only because of specific item builds or map conditions?

Are top teams exploiting champion mechanics that weaker teams systematically overlook?

Do top teams use fixed compositions, map-specific templates, dynamic matchup selection, or more sophisticated drafting logic?

Can we identify a champion selection policy that would generalise to unseen maps?

### Deliverables

Produce:

- Champion meta tier list with evidence and uncertainty.
- Champion synergy and counter matrices.
- Map-dependent draft recommendations.
- Champion role classifications.
- Several evidence-backed composition archetypes.
- A proposed algorithm for optimal champion selection.

Do not equate raw win rate with intrinsic champion strength. Adjust your interpretation for team strength, map, opponent, composition and selection bias.

---

## 5. ITEMISATION AND GOLD ECONOMY META

This deserves exceptionally deep investigation.

Reverse-engineer how elite teams build their champions, when they buy equipment, which items they prioritise, and how those decisions improve their performance.

### Item investigation

For every champion in every selected match, reconstruct the full observable equipment progression.

Track:

- Purchase round.
- Item type and quantity.
- Cost and resource state at purchase.
- Equipment order.
- Repeated purchases.
- Selling or replacement behaviour, if supported.
- Accumulated stat bonuses.
- Purchase timing relative to combat and farming milestones.
- Item investment relative to team and individual gold income.

Determine the actual item taxonomy and mechanics from the current SDK.

Investigate all relevant item families, shards, emblems, and upgrade systems.

### Economic optimisation

Research:

- Early economy investment versus immediate combat power.
- Gold-generation items and their break-even points.
- Compounding and scaling effects.
- Champion-specific purchasing priorities.
- Concentrated versus distributed equipment investment.
- Optimal sequencing of economic, damage and survivability items.
- Purchase thresholds and delayed purchases.
- Gold accumulation without productive spending.
- Item timing relative to objective capture and combat.
- Situations where specialised equipment beats generic builds.

Do not assume commonly purchased items are optimal.

### Counterfactual questions

For important purchases, ask:

- Would a different purchase have accelerated farming?
- Would an earlier economic item repay its cost?
- Did a defensive item prevent a costly death?
- Did buying combat equipment delay economic growth?
- Was a late purchase too late to influence the outcome?
- Did concentrating gold on one champion produce better returns than spreading it?

Where practical, use engine-derived calculations and controlled simulations to test these hypotheses.

### Deliverables

Produce champion-specific, role-specific and map-specific build recommendations.

Where evidence permits, define decision rules rather than rigid build orders:

**If game-state conditions X, Y and Z hold, purchase item A; otherwise consider item B.**

Separate observations, mathematical calculations, and experimentally validated conclusions.

---

## 6. FARMING, NEUTRAL CAMPS AND RESOURCE OPTIMISATION

Determine the optimal farming metagame.

For every match, track:

- First neutral-camp targets.
- Camp capture and clear order.
- Camp types and rewards.
- Farming completion times.
- Time spent travelling.
- Damage taken while farming.
- Gold and gems produced.
- Farming efficiency per champion.
- Camp respawn or refresh mechanics.
- Overlapping champion assignments.
- Idle time and wasted movements.
- Neutral objectives that are ignored or contested.
- Timing of transition from farming into combat or scoring.

### Critical questions

Which camps provide the highest expected strategic value?

Does the optimal farming order change by champion, equipment, map or opponent pressure?

When should champions farm separately?

When should they group to eliminate difficult camps?

Are teams farming camps for immediate income, long-term control, route access, experience, or another downstream advantage?

When does farming become less valuable than combat, enemy denial or banking?

Do successful teams deliberately time camp clears around respawn cycles?

Are there recurring high-efficiency route patterns?

How do they prevent travel time from overwhelming farming rewards?

Do strong teams farm enemy-controlled areas, and when is that worth the risk?

### Quantitative analysis

Calculate appropriate metrics such as:

- Gold per active farming round.
- Gems acquired per round.
- Reward per unit of travel time.
- Effective damage dealt per round.
- Damage received per unit of reward.
- Camp reward divided by time-to-clear plus travel time.
- Income lost to idle time or unnecessary movement.
- Death-adjusted economic return.
- Total realised score produced by each farming route.

Distinguish gold earned, gems carried and gems actually converted into submitted score.

Do not recommend a farming strategy based exclusively on gross resource accumulation.

### Deliverable

Develop an evidence-backed farming and resource-allocation framework that could eventually be converted into algorithmic objective scoring.

---

## 7. COMBAT META — MICRO AND MACRO

Analyse how elite teams win fights.

This is not limited to which champion deals the most damage.

### Combat micro

Investigate:

- Target priority.
- Focus-fire behaviour.
- Ability timing.
- Cooldown management.
- Range management.
- Positioning.
- Damage avoidance.
- Disengagement.
- Retreat thresholds.
- Health and survivability calculations.
- Pursuit decisions.
- Defensive ability usage.
- Movement and attack sequencing.
- Damage optimisation.
- Multi-champion coordination.
- Target switching.
- Interaction between champion abilities.
- Item-dependent combat effectiveness.

For each important engagement, reconstruct the action timeline.

Determine whether the fight was won by numerical advantage, positioning, itemisation, ability sequencing, opponent mistakes, or some combination.

### Combat macro

Investigate:

- When top teams choose to fight.
- When they avoid fights.
- Whether they contest neutral objectives.
- When they invade enemy farming areas.
- How they respond to a stronger enemy.
- How they defend high-value carriers.
- Whether kills are pursued for income, denial, tempo or objective access.
- How they recover from failed fights.
- Whether teams favour sustained combat or opportunistic engagements.

### Evaluate efficiency

Useful measurements may include:

- Damage dealt versus damage received.
- Damage converted into kills.
- Kill and assist rewards.
- Champion downtime from death.
- Resources lost or delayed by dying.
- Fight outcomes relative to nearby ally/enemy strength.
- Time to eliminate important threats.
- Objective value gained or lost because of engagements.

### Counterfactual reconstruction

For strategically important fights, identify alternative legal actions available at the time.

Test whether another move, attack target, ability choice or retreat could plausibly have improved the outcome.

Only treat such counterfactuals as established when they can be evaluated with sufficient state information and a trustworthy simulation model.

The output should ultimately describe the structure of an effective combat decision system, not just a catalogue of successful fights.

---

## 8. GEMS, ALTARS AND WIN-CONDITION OPTIMISATION

The objective is to win, not simply accumulate resources.

Give the scoring system the same analytical priority as combat and farming.

Investigate:

- When champions begin collecting gems.
- Typical gem quantities carried.
- First submission timing.
- Submission frequency and size.
- Travel time to altars.
- Routes taken by gem carriers.
- How teams secure safe access to altars.
- When teams risk travelling with high-value inventories.
- Whether they prioritise early smaller submissions or later larger ones.
- How they handle contested or inaccessible altars.
- How they prevent enemies from submitting.
- When teams abandon farming to convert their existing resources into score.
- Whether endgame behaviour changes near the winning score or round limit.

### Specific strategic questions

Why do successful teams sometimes carry large quantities of gems instead of immediately submitting them?

What conditions trigger a bank trip?

When does banking become urgent?

When should a carrier be escorted?

When is fighting to open an altar more valuable than farming additional gems?

Can the team win faster by denying the opponent's scoring route?

How do successful teams balance gaining resources against actually delivering them?

Investigate map-specific phenomena, including gate-controlled altars and difficult objective-access maps.

### Required objective metrics

Track, where supported:

- Gems acquired.
- Gems carried.
- Gems banked.
- Gems lost or placed at risk.
- Conversion efficiency.
- First-bank timing.
- Time between banking events.
- Distance and travel cost to viable altars.
- Objective access downtime.
- Score progression and effective win-condition pressure.

Identify the strategies that most reliably turn resource advantages into victories.

---

## 9. MAP META, POSITIONING AND MOVEMENT

Determine whether the optimal metagame varies systematically with map geometry.

Analyse:

- Map symmetry.
- Spawn locations.
- Terrain and obstacles.
- Chokepoints.
- Open versus enclosed regions.
- Neutral-camp distribution.
- Resource concentration.
- Altar positions and accessibility.
- Travel distance.
- Pathfinding constraints.
- Teleportation and other movement mechanics.
- Zones that are easy to defend or difficult to escape.
- Safe and dangerous farming routes.
- Contested central areas.
- Visibility and information advantages.

### Questions

Do specific champion compositions dominate certain map geometries?

Are particular farming routes consistently better?

How do elite teams adapt to blocked paths and inaccessible objectives?

Do they use different strategies on resource-rich and resource-poor maps?

Are there recognisable opening templates?

Does map control reduce travel time or provide greater strategic value through denial?

Are top teams exploiting geometry that ordinary shortest-path planners overlook?

Produce a useful map-archetype classification and explain how each archetype changes optimal decisions.

Do not overfit recommendations to specific named maps. Extract properties that a bot could recognise on unseen maps.

---

## 10. RESEARCH EVERY OTHER IMPORTANT STRATEGIC VARIABLE

Do not limit the study to the categories I explicitly listed.

Inspect the full game SDK and engine to identify all mechanics that could materially influence elite performance.

Potential additional areas include:

- Champion respawn scheduling.
- Levels, experience and power spikes.
- Vision, fog of war and information gathering.
- Wards and map visibility.
- Objective capture mechanics.
- Recall and teleport timing.
- Defensive objectives.
- Terrain manipulation, if supported.
- Temporary buffs and debuffs.
- Neutral objective denial.
- Healing and recovery.
- Shared or team-wide resources.
- Champion coordination.
- Resource funneling.
- Enemy behaviour prediction.
- Map-specific opening strategies.
- Strategic tempo.
- Risk management.
- Endgame and tiebreaker optimisation.
- Exploitable timing interactions.
- Legal action sequencing and phase order.
- Computational fuel restrictions.
- Opponent adaptation.

Search proactively for mechanisms I have not thought of.

Ask repeatedly:

**What variable could distinguish an elite bot from an average bot that our current analysis is missing?**

For every newly discovered variable, determine its theoretical significance and whether the match evidence suggests that top teams actually exploit it.

Avoid treating unsupported game mechanics as real; verify them against the authoritative rules.

---

## 11. REVERSE-ENGINEER EACH TOP TEAM'S DECISION POLICY

The highest-value outcome is discovering **how elite teams appear to make decisions**, not merely which actions they take.

For each leading team, build a strategic profile.

Investigate whether it appears to follow:

- A fixed opening plan.
- A reactive heuristic system.
- Explicit champion roles.
- Dynamic role assignment.
- A shared global objective.
- Independent champion optimisation.
- Economy-first scaling.
- Early aggression.
- Objective rushing.
- Combat avoidance.
- Opportunistic enemy denial.
- Map-dependent policy switching.

Identify recurring state-action relationships.

For example, investigate whether a team changes strategy around specific conditions involving equipment readiness, resource quantities, objective accessibility, enemy positioning or score pressure.

Those are candidate mechanisms to test, not assumed rules.

### Distinguish observations from inferred policies

A replay shows actions, not source-code intent.

Whenever you infer a decision rule:

1. State the inferred rule precisely.
2. Identify all supporting matches and rounds.
3. Search for situations where the rule should apply.
4. Identify exceptions or contradictory evidence.
5. Propose alternative explanations.
6. Estimate confidence.
7. Explain what extra evidence would distinguish the hypotheses.

Where possible, use held-out sequences from the same team to determine whether an inferred policy predicts actions.

Compare elite teams to discover which principles are shared across different successful strategies.

---

## 12. EXPLAIN WHY THE WINNER WON

For every match, reconstruct the causal sequence leading to victory.

Do not simply write that the winner farmed more efficiently or had better items.

Determine:

- When the first meaningful advantage appeared.
- Which decisions created that advantage.
- Whether the advantage was economic, tactical, positional, informational or objective-based.
- Whether the losing team had opportunities to recover.
- How the winner converted its advantage into score.
- Whether the eventual outcome was decided early or remained uncertain.
- Which winning decisions are reproducible.
- Which advantages could instead reflect opponent errors, random variation, map differences or unobserved state.

Create a timeline of major causal events.

Compare the winner and loser at equivalent rounds.

Particularly investigate matches where:

- The lower-income team wins.
- The team losing combat wins.
- The strongest-looking composition loses.
- A leading team loses despite a strong opening.
- A team wins through an unusual draft, farming route or item build.

These anomalies may reveal more about the underlying meta than straightforward victories.

Do not claim that a specific action caused victory unless the evidence supports that causal interpretation.

---

## 13. QUANTITATIVE SYNTHESIS AND SCIENTIFIC VALIDATION

After completing individual match investigations, combine the evidence across all 30 matches.

Build structured datasets so that comparisons can be reproduced.

Investigate:

- Champion and composition frequencies.
- Item build patterns.
- Farming routes.
- Economic development curves.
- Combat efficiency.
- Champion deaths and downtime.
- Objective timing.
- Team score progression.
- Map-dependent strategic differences.
- Strategic opening archetypes.
- Recurring winning and losing behaviours.

Use conditional comparisons wherever possible.

### Avoid analytical traps

Explicitly account for:

- Small sample size.
- Winner-selection bias.
- Team-strength differences.
- Map differences.
- Champion matchup effects.
- Different engine versions.
- Submission changes within a team's history.
- Non-independence of decisions from the same match.
- Survivorship bias.
- Correlation versus causation.
- Replay reconstruction limitations.
- Incomplete information and fog of war.

Do not treat thousands of decisions within 30 matches as thousands of independent matches.

Do not fabricate statistical certainty.

### Confidence classification

For every important conclusion, assign:

**High confidence:** Supported across multiple independent contexts and corroborated by reliable mechanics or controlled evidence.

**Medium confidence:** A recurring, plausible pattern, but affected by confounding factors or limited coverage.

**Low confidence:** A potentially valuable hypothesis with insufficient supporting evidence.

Provide counterexamples, sample sizes, and relevant match IDs.

Where observations alone cannot distinguish competing hypotheses, propose specific tests rather than choosing the explanation you prefer.

---

## 14. TRANSLATE THE META INTO ALGORITHMIC PRINCIPLES

Once the research is complete, determine how an AI agent could reproduce the successful principles.

Think about an optimal future decision architecture without implementing it yet.

Investigate the suitability of:

- Global strategy selection.
- Champion drafting optimisation.
- Dynamic role allocation.
- Objective value functions.
- Farming target selection.
- Economic investment policies.
- Equipment purchase decision trees.
- Risk-aware bank timing.
- Combat engagement evaluation.
- Tactical movement scoring.
- Target selection.
- Coordination rules.
- Map-specific adaptation.
- Opponent modelling.
- State-dependent strategic switching.
- Uncertainty-aware decisions.
- Limited-horizon search.

For each recommended decision system, explain:

1. Inputs available to the bot.
2. Candidate actions.
3. Relevant state variables.
4. Proposed evaluation criteria.
5. Decision boundaries or priorities.
6. Computational cost.
7. Expected strategic benefits.
8. Situations where the mechanism might fail.

**Do not assume we must preserve DOOMSDAY's current strategy.**

If the elite teams demonstrate that our underlying approach is strategically weak, say so.

Likewise, do not assume a neural network is necessary. The aim is performance, not attachment to a particular architecture.

Consider deterministic algorithms, heuristics, search, learned policies and hybrids wherever each has a defensible advantage.

Account for the game's actual per-turn fuel limits and implementation constraints.

---

## 15. COMPARE THE DISCOVERED META AGAINST DOOMSDAY

Only after independently understanding the strongest teams, inspect the current DOOMSDAY bot.

Do not let the existing implementation influence your initial interpretation of the metagame.

Compare its current behaviour against the discovered elite strategies.

Assess:

- Champion drafting.
- Composition structure.
- Item purchases.
- Farming efficiency.
- Economic scaling.
- Role allocation.
- Combat mechanics.
- Movement and routing.
- Banking decisions.
- Objective prioritisation.
- Map adaptation.
- Endgame strategy.
- Compute efficiency.

Identify both minor shortcomings and fundamental architectural limitations.

Avoid proposing superficial adjustments when evidence suggests the strategic model itself is inadequate.

Produce a prioritised gap analysis, including the expected importance, implementation difficulty, fuel impact, and evidence strength of each improvement.

---

## 16. DELIVERABLES — EXTREMELY DETAILED RESEARCH

Save the research in a dedicated new directory under `research/`.

Produce at minimum:

### A. Master Metagame Report — `META_REPORT.md`

A comprehensive synthesis explaining:

- The current elite metagame.
- Which strategies are most successful.
- How teams differ.
- Why particular strategies work.
- Which findings generalise across maps and opponents.
- Which popular strategies may be misleading.
- What appears underexplored or exploitable.

This must contain substantial evidence and reasoning, not only summary tables.

### B. Full Match Investigation — `MATCH_ANALYSIS.md`

A detailed section for each of the approximately 30 matches containing:

- Match ID and replay source.
- Teams, map, date and engine version.
- Champion drafts.
- Strategic opening.
- Champion roles.
- Item progressions.
- Farming strategy.
- Combat analysis.
- Banking and objective analysis.
- Significant strategic transitions.
- Important round-numbered observations.
- Why the winner won.
- Counterfactual opportunities.
- Generalisable lessons.

Include precise round references and links or pointers to supporting extracted data.

### C. Round-Level Dataset

Save a complete machine-readable round-level ledger for every selected match.

The ledger must allow another researcher to inspect any round without rerunning the entire study.

Keep the data structured, clearly labelled, and independently reproducible.

### D. Specialist Meta Reports

Create detailed analysis files for:

- Champion draft meta.
- Champion synergy and counters.
- Item and equipment meta.
- Farming and economic meta.
- Combat and positioning meta.
- Gem submission and objective meta.
- Map and movement meta.
- Additional mechanics discovered during investigation.

### E. Elite Team Strategy Profiles

Produce a profile for each leading team studied.

Describe its strategic identity, recurring decision rules, strengths, weaknesses, adaptations and exploitable patterns.

### F. Decision Rules and Architecture — `META_TO_ALGORITHM.md`

Turn the strongest findings into practical, state-dependent decision rules and possible algorithms.

Include enough detail to guide a future implementation agent without needing that agent to independently rediscover the same meta.

### G. Ranked Opportunities — `IMPROVEMENT_PRIORITIES.md`

Identify the most impactful improvements for DOOMSDAY.

Rank them by:

- Expected performance impact.
- Strength of supporting evidence.
- Feasibility.
- Computational cost.
- Complexity.
- Generalisation potential.
- Risk of regression.

For the highest-priority hypotheses, propose isolated A/B experiments with clear success metrics.

Respect the repository's existing evaluation methodology and held-out map restrictions.

### H. Reproducibility and Evidence Index

Include:

- Match selection methodology.
- Full match and replay index.
- Source URLs.
- Data extraction commands.
- Decoder and engine versions.
- Tool changes.
- Data integrity checks.
- Missing-data limitations.
- Confidence qualifications.
- Reproduction instructions.

Raw replay files should remain in the repository's designated local-only artifact locations unless existing policies say otherwise.

---

## 17. MANDATORY QUALITY CONTROL

The investigation is not complete unless the following conditions are satisfied.

1. Approximately 30 unique, genuinely relevant top-team matches have been investigated.
2. Every round in each match has been processed, not merely a sparse set of checkpoints.
3. Replay decoding has been validated against the appropriate engine and official match results.
4. Important conclusions reference actual matches and round numbers.
5. Every strategic area has received meaningful analysis.
6. Strong claims have been checked for counterexamples.
7. Differences between patches are explicitly addressed.
8. Major decisions are interpreted within their available game state.
9. Champion, item and farming recommendations are conditional where appropriate.
10. The final report distinguishes evidence, inference, speculation and validated experiments.
11. All research scripts and reports are reproducible.
12. No existing submitted bot or frozen baseline has been altered.

Perform integrity checks against official match summaries, including final score, winner, duration and available action records.

If data required for a conclusion cannot be recovered, disclose that limitation rather than filling gaps with invented values.

**A report consisting primarily of item popularity statistics, champion win rates and short match summaries is a failure of this assignment.**

The expected result is genuine strategic reverse engineering.

---

## 18. RESEARCH DEPTH AND EXECUTION STANDARD

Prioritise depth, precision and explanatory power over speed.

Do not impose an arbitrary analysis-time limit.

Use analytical scripts for exhaustive reconstruction and calculations, but use explicit reasoning to interpret the resulting behaviours.

Do not allow automation to replace genuine investigation.

Continuously question initial conclusions.

When a pattern appears important, investigate it across other matches.

When a finding contradicts expectations, prioritise understanding the contradiction.

When two successful teams use fundamentally different strategies, determine what underlying principle might make both effective.

When a strategy appears dominant, search deliberately for its weaknesses.

Do not prematurely stop after identifying several obvious patterns.

The research should identify both the visible metagame and the mechanisms underneath it.

At the end, provide a concise executive summary covering:

1. **The 10 most important discoveries about the current meta.**
2. **The strongest evidenced champion compositions and item strategies.**
3. **The optimal farming, combat and gem-scoring principles.**
4. **The most significant strategic differences between DOOMSDAY and elite teams.**
5. **The highest-impact changes worth investigating next.**
6. **The remaining uncertainties that could materially change these recommendations.**

Do not write or submit a new bot, begin training, or start a broad implementation campaign without a separate instruction.

## FINAL INSTRUCTION

I am not asking you to tell me what the best teams do at a superficial level.

I am asking you to **reverse-engineer the metagame itself.**

Study the strongest teams so carefully that their repeated decisions become understandable as algorithms.

Explain how champion selection, farming, items, movement, combat, coordination, information and scoring interact to create winning strategies.

The ultimate objective is to discover the fundamental principles required to construct a bot capable of competing with — and potentially outperforming — the strongest teams on the Cambridge Battlecode ladder.

**Treat every round as evidence, every major decision as a hypothesis to investigate, and every claimed meta advantage as something that must be explained rather than assumed.**