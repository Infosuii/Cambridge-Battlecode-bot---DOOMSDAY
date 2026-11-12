# Paper batch 2: full read-through notes (2026-11-01)

Every page read; each idea mapped to Battlecode/x1, with an implementation sketch. Status: [T] testing, [S] in a
running sweep, [P] planned, [I] idea only.

## 1. Hagelbäck & Johansson, "A Multi-Agent Potential Field-Based Bot for a Full RTS Game Scenario" (AIIDE 2009)

| # | Idea in the paper | x1 version | Status |
|---|---|---|---|
| 1.1 | Total field = weighted sum of layers (navigation, strategic, exploration, tactical, spatial planning); influence-map layers (Tozour) | A layered **tile-score map** for "where to stand": camp value, danger, ally cover, altar access, combined once per turn and reused by staging, waiting and ward choice | [I] |
| 1.2 | Attackers seek the ring at their max shooting distance (MSD) from each enemy; ring radius differs by unit type | **Range-ring positioning**: ranged champions hold distance = their range; melee closes | [S] `APEX_KITE`, `APEX_POSITION` |
| 1.3 | After firing, in cooldown, enemies become repelling slightly beyond their MSD: retreat out of reach, re-enter when ready | **Cooldown kiting**: step out of the enemy's reach on turns our attack/spell is down | [P] P2 |
| 1.4 | Exploration: per-tile staleness E += 1 each frame unseen, reset to 0 when seen; importance = 2.4E − 0.1d; go to the single best tile (all-unexplored attraction strands units mid-map) | **Staleness map** for wards and scouting: ward the stalest tile on our route; know which camps' states are old | [P] |
| 1.5 | Tactical field: a small repelling charge at each ally's *next* tile stops two units choosing the same tile | **Move reservation**: claim the next tile in Memory/shared order; bodies avoid tiles allies just chose (fewer blocked moves) | [I] |
| 1.6 | Battleplan as subsumption posts in order; when a completed post stops holding (unit or building lost), restore it before continuing | **Invariant plan**: keep "every body has its first item", "two bodies near the contested altar late", "one ward on each route"; repair broken invariants first | [I] |
| 1.7 | CommanderInField reassigns goals mid-game (worker builds, then returns to mining) | **Temporary role switch**: a farmer becomes the interceptor or banker for one task, then returns | [P] (roles) |
| 1.8 | GlobalMapAgent: remembers every spotted enemy building/unit until destroyed and distributes positions to all units | **Persistent enemy memory** (positions, bags, last seen) shared through the 8-byte team word | [P] (#6, `A2_BELIEF` [S]) |
| 1.9 | AttackCoordinator: assign attacks so targets die (example: weakest-first leaves both enemies alive; coordinated kills one) | **Kill-securing coordinator** | [T] `X1_SECURE` |
| 1.10 | SpatialPlanner: build-spot field with inner repulsion, outer attraction, enemy/cliff/edge repulsion; search rings outward (4, 8, ... 200) for the best point | **Ring search over a composite tile score** for staging, ambush and ward tiles (cheap: a few hundred tiles) | [I] |
| 1.11 | Benchmark in open tournaments, not against self-made bots; wins are intransitive (rock-paper-scissors) | League with diverse styles; real ladder and top-team-style sparring bots | [P] |
| 1.12 | Future work: choose the battleplan by opponent type and skill; their fixed tank plan lost to an early marine rush; don't rebuild blindly, clear the threat first | **Opponent-adaptive plan** (F5); an **early-aggression response** (detect a rush, regroup, defend, then farm) | [P] |

## 2. Perez-Liebana et al., "Tribes: A New Turn-Based Strategy Game for AI Research" (AIIDE-20)

Results (500 games per pair, 25 generated levels, both tribes): RHEA 74.8% overall (beats Rule-Based 58.6%, MCTS 63%,
MC 77.8%, OSLA 74.8%); Rule-Based second (65.8%) despite no lookahead; all lose 100% to a moderate human.

| # | Idea in the paper | x1 version | Status |
|---|---|---|---|
| 2.1 | RHEA with population 1 (a random-mutation hill climber) beat larger populations; a **shift buffer** carries last turn's best plan forward one step and appends a random gene | **Anytime team planner** (P3): keep last turn's best team job plan, shift it, mutate while fuel lasts, publish the first step | [P] P3 |
| 2.2 | State value = weighted *relative progress* (own feature deltas minus the opponents' average): production, tech, score, cities, units, kills, city levels; weights {5,4,0.1,4,2,3,2} | Plan and fight evaluation by **relative progress vs the enemy**: banked + carried gems, gold, kills, bodies alive, items, respawns pending; weights fitted on our games (F1 model) | [P] |
| 2.3 | Budget counted in forward-model calls, not time, so results compare across hardware | **Fuel-denominated budgets**: each planner/search counts model evaluations against measured fuel per evaluation | [P] (fuel planner #13) |
| 2.4 | Root prioritisation (restrict the first action to one category per iteration, a simple progressive widening) helped MC and MCTS | In any team search, **search one decision class at a time** (jobs, then fights, then banking) instead of the joint space | [I] |
| 2.5 | Skipping rollouts and evaluating the expanded state directly beat random rollouts (as in AlphaZero) | Fight and plan search with a **static evaluator, no random playouts** (matches the teammate: the fight model, not depth, failed) | [I] |
| 2.6 | The rule-based agent's weakness: actions scored independently, so no coordination or resource planning | Keep x1's strong heuristics; add **joint coordination on top** (kill securing, team planner) rather than replacing them | [T]/[P] |
| 2.7 | Rule-based details: never step into range of stronger units; attack when the target is weaker in defence and HP (counter-attack risk); captures always top priority | Check x1's step safety against **stronger-unit reach** and retaliation-aware attack choice; **captures/regions top priority** when safe | [I] |
| 2.8 | Winners had larger action spaces late (more cities, techs, units): options grow with economy | Track **option growth** (items, gold, bodies alive, altars reachable) as a mid-game health indicator in the value model | [I] |
| 2.9 | Planning horizon 20 beat 5 and 10 | Longer **horizons for the job planner** (whole job chains: clear, capture, bank) rather than one job | [P] |
| 2.10 | Evaluated on 25 generated levels with side swaps; full vs partial observability | Already doing ladder + unseen generated maps, both sides | done |
| 2.11 | OEP (Justesen) and EvoMCTS (Baier & Cowling) for multi-unit turns | Candidate algorithms for P3 if the hill climber plateaus | [I] |

## 3. Sestini et al. (EA), "Augmenting Game AI with Deep Reinforcement Learning" (arXiv 2606.20210, 2026)

Two production cases: EA SPORTS FC 25 goalkeeper positioning (an FSM state replaced by a SAC policy; +10% save
ratio, more human-like) and Battlefield 6 soldier locomotion (a BT leaf replaced by a PPO policy; 11/20 vs the
hand-coded bot, smoother paths). Seven requirements: short training, controllability, modularity, maintainability,
bug fixing, authenticity, runtime inference limits (compute shared with the non-RL parts).

| # | Idea in the paper | x1 version | Status |
|---|---|---|---|
| 3.1 | Replace **one leaf / one FSM state** with a learned module, keep the rest hand-coded; independent leaves already work, joint training of several leaves is open | Learn **one x1 decision at a time** (camp choice, fight/run, bank timing, recall), each behind a switch, exact paired screen per module; never an end-to-end policy | [P] P4, Phase 2 |
| 3.2 | Behaviour defined by an expert-designed reward rather than state transitions | Phase 2 label = **branch margin** (exact counterfactual), the "reward" designed from the game's race structure | [P] Phase 2 |
| 3.3 | Short training: overnight; high update-to-data ratio with network resets, pre-collected offline data, scenario-based training (4 days → 12 h) | **Scenario training**: start branches from saved R250-R500 states of lost games (drill arena), reuse logged games as offline data, small models refit nightly | [P] Phase 2 |
| 3.4 | Fine-tuning for exploits in 2-4 h via scenario learning + Replay across Experiments (reuse old experience); repeated fine-tunes risk forgetting | When a ladder opponent exploits x1, **targeted scenario fixes** that keep earlier data in the training set; gate every fix on the full ladder + unseen screen (forgetting check) | [P] |
| 3.5 | Strict inference budget (200 µs incl. observation collection); small 5-layer MLP | **Fuel budget per module** includes feature extraction; tiny linear/MLP models in fixed point; meter in A2_TEL | [P] (fuel planner #13) |
| 3.6 | Observation cost dominates: occupancy map from a cached level-wide grid (14 µs) vs 24 raycasts (27 µs), same performance | **Precompute static map grids in the 10M draft turn** (passability, LOS opacity, region ids), and read local windows at run time; the X1_FAST_SIEGE precompute is the same idea | [T] done for siege, extend to threat map / kiting |
| 3.7 | Out-of-range target mapped to the border of the local map as a direction indicator | Local feature windows with **far targets clamped to the edge** (bearing feature) for any learned move/fight model | [I] |
| 3.8 | Asymmetric actor-critic: a big critic for training, a small actor for deployment | **Big offline value model** (branch labels, many features) trains a **small in-bot rule or table** (distillation of decisions, not of evaluations: NNUE lesson) | [I] |
| 3.9 | Designers-in-the-loop, controllability, bug fixing | Every learned module has a **knob and a kill switch**, and its decisions are logged with telemetry so a bad call can be found in replays | [P] |
| 3.10 | Behaviour evaluation is underexplored; black boxes need quantitative + qualitative checks | Our evaluation set: ladder + unseen maps, seed builds, per-phase stats (deaths, gold R250, finish round), replay review of the worst cells | done/[P] |
| 3.11 | Authenticity is not our goal; strength is | Ignore the authenticity requirement; keep the engineering ones | n/a |
| 3.12 | Policy switching handover in a BT is an open problem | When a learned module hands back to x1's heuristic, **hysteresis** (minimum rounds per mode) to stop dithering | [I] |

## 4. Hagelbäck, "A Multi-Agent Potential Field based approach for RTS bots" (licentiate thesis, 2009; Papers I-V), every chapter

The thesis has the full detail behind section 1. Its strongest evidence is the **Paper III ablation**: the same bot
against the four 2007 top teams, adding one change at a time (100 games per opponent, seeds and sides paired):

| Version | Change | Win % (avg of 4) | Delta |
|---|---|---|---|
| V.1 | original (8x8 tiles) | 14% | |
| V.2 | full resolution, potentials only at move candidates | 18.75% | +5 |
| V.3 | **defensive field: retreat while the weapon cools down, advance when ready** | 64.25% | **+45** |
| V.4 | avoid-past trail (last 20 positions, -0.5 each) | 76.5% | +12 |
| V.5 | **max instead of sum of enemy fields** (engage the nearest enemy at max range, not the cluster centre) | 99.25% | **+23** |

The two biggest gains are both *engagement geometry*: when to be in range, and around which enemy.

| # | Idea in the thesis | x1 version | Status |
|---|---|---|---|
| 4.1 | Cooldown-aware stepping (V.3): out of reach during cooldown, back in when ready | **Cooldown kiting** for every champion with a recharge: after casting, the move scorer prefers tiles outside enemy reach until the next cast is ready (P2 generalised beyond ranged champions); compare with `APEX_KITE` from sweep 1c | [T] next |
| 4.2 | Max not sum (V.5): the attack goal is set by the nearest enemy, so units ring the enemy instead of diving its centre | Check x1's **approach target**: if its positioning sums enemy attraction, change the attack-tile score to the best single enemy; danger stays summed | [I] audit then [T] |
| 4.3 | Avoid-past trail (V.4) | Anti-oscillation penalty on a champion's last N tiles when no fight or job progress (check v81's stuck handling; telemetry on repeated tiles first) | [I] measure first |
| 4.4 | Fog-of-war bot beat the perfect-information bot 66/100 because the long detection range made **single units attack alone**; cutting the range to 450 dropped it to 55 | **Engage radius cap for lone champions**: no hunting beyond r tiles unless an ally can arrive in time (ties to X1_ALONE: 51% of deaths isolated) | [T] after ALONE result |
| 4.5 | Exploration field gave no significant gain (20-0 vs 19-1) | Low priority for ward/scouting work; spend effort on fights and economy | noted |
| 4.6 | Attack coordinator detail: expected damage = min + 0.75(max-min); tie → target reachable by most attackers; surplus attackers with the most options are released; then one target per remaining attacker | Refinements for `X1_SECURE` v2: count *all* allies who can hit this round, release surplus, prefer focusable targets | [P] after SECURE result |
| 4.7 | Three-level reachability check: Manhattan, then Euclidean, then LOS (cheap to expensive) | **Fuel cascade** in x1's target and threat loops: bitboard/Chebyshev filter before LOS and simulators | [I] (fuel planner #13) |
| 4.8 | Numerical-advantage objective switch: attack bases too only if 2x units, enemy < 6 units, or one base left | **Objective switch on body count**: with enemies dead (respawn timers) and ours alive, push denial (enemy altar lock, carrier hunt) or a big bank; else farm | [P] Phase 4 |
| 4.9 | Agent field negative close, positive further out: keeps units together and surrounds (the early bot's weakness was spread units picked off one at a time) | **Cohesion term**: mild attraction to allies beyond ~5 tiles when enemies are near (complements spacing for area damage) | [T] with ALONE |
| 4.10 | Weakest-spot field from a tactical decision; commander picks targets to split enemy groups or flank | Team target selection that prefers **isolated enemies** (no ally within 5) over grouped ones | [I] |
| 4.11 | Dead-end filling (16 rays, ≥9 blocked within 5 → impassable) and narrow-passage clearing; cliff fields combined by min, not sum | Draft-time map analysis: **dead-end and choke maps** (retreat never into dead ends; chokes as ambush/denial spots) | [I] |
| 4.12 | Non-symmetric fields: avoid the line of fire, attack flanks | Skillshot/line abilities: prefer tiles off the enemy's cast line | [I] |
| 4.13 | Caching potentials per agent state; potentials computed only at the 9 move candidates | Same: score only candidate tiles; precompute static parts | done in x1 |
| 4.14 | Subsumption battleplan: redo an earlier post if it is undone (worker died) before continuing | Team plan with **invariants** (e.g. "two farmers alive and farming", "one denier when enemy ≥ 800") repaired first | [P] Phase 4 |
| 4.15 | Spatial planner: rings at distance 4, 8, ..., 200 around the worker; pick the best spot | Ward and staging-tile search on rings | [I] |
| 4.16 | GA tuning failed for them (random damage); fields tuned by relative importance of objects | Our games are deterministic: ES works (teammate's v86h); keep tuning **relative weights** of few terms | done (Phase 6) |
| 4.17 | Own game score (units + 5 x bases left) as a finer measure than win/loss | We use banked-gem margin; also log **finish round** as a secondary score | done/[P] |
| 4.18 | Results not transitive (rock-paper-scissors); benchmark against tournament entries, not self-made bots | Ladder top teams and their sparring stand-ins in the league; never judge on one opponent | done/[P] |
| 4.19 | Future work: battleplan per opponent skill/type; do not blindly rebuild after a loss (deal with the raiders first) | Phase 4: opponent-dependent plan; after a death near our altar, **clear the threat before resuming the job** | [P] |
