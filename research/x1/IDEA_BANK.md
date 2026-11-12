# Idea bank: what is worth developing from v81 (benchmark: v86h)

v81 itself is no longer a target (2026-11-01). Its 437 switches and their comments record many ideas with the
author's reason and, often, a measured result. Toggling the off ones is Phase 1 (sweep 1c, vs v86h on ladder and
unseen maps). This page is for ideas worth *developing further* into something v81 never had. Each item: what v81
does, what is inspiring, how x1 should develop it, and the test (always vs v86h and v86h-s2, ladder + unseen).

| # | v81 idea (switch) | What is inspiring | Develop into | Test |
|---|---|---|---|---|
| 1 | Race posture (`A2_RACE` 1-4): finish-time projection, a learned P(win) (73.6% held out), press ahead / farm behind | Games are races to 1000; a posture layer is cheap and global | A **finish-time model per team** (bank rate + carried + respawning bodies) driving endgame denial, safe banking and when to switch plans; fit on our own and ladder games | Endgame cells (score ≥ 700) win rate |
| 2 | Opponent model (`APEX_OPP_MODEL`): learns the opponent's back-off health in-game | Online adaptation inside one game | **Opponent profile** from cheap observations (back-off HP, aggression radius, bank cadence, lock use) feeding fight thresholds and the style classifier (F5) | vs v86h, v85, sparring bots |
| 3 | Home-side plan (`HOME_SIDE`): found by branching 262 lost games; turned the most losses into wins | Branch search on lost games finds team plans that flip results | **Branch-trained decisions** (Phase 2): exact counterfactual labels at R250-R500, where ladder losses happen | Policy CV gain, then screen |
| 4 | Respawn timers in shared bits (`APEX_EVENTS`) | 8 bytes still carry useful team knowledge | **Team knowledge protocol**: camp respawn times, enemy sightings, bank intents, in a bit budget; plan jobs around known respawns | Camp idle time, gold R250 |
| 5 | Tribute denial (`APEX_TRIB_DENY`), prelock (`APEX_PRELOCK`), locks (`V58_LOCKS`) | Denial of the enemy's bank channel | **Channel interception**: target enemies with long channels (bag ≥ 60 = 6+ rounds) only when we can arrive in time; ladder teams lose bags to it | Enemy banked per game |
| 6 | Carry interception (`V58_HUNT_CARRY`), stale bag watch (`APEX_STALE_BAG`) | Bags are the score in flight | **Carrier tracking**: remember enemy bag sizes from sightings; value a kill by bag + 100 gold | Kills on carriers, margin |
| 7 | Dash over hole gaps (`A2_BRIDGES`), crystal hops (`V54_TP_GAIN`) | Movement shortcuts are map-specific free tempo | **Shortcut graph** precomputed in the 10M draft turn (dash gaps, 3-tile crystal hops), shared via draft memory | Rounds to first job, gold R100 |
| 8 | Burst kill zone (`A2_DANGERMAP`, `A2_BURST2`), early escape (`A3_ESCAPE`) | 19% of deaths are bursts from >50% HP | **Two-turn threat map** of visible + believed enemies (`A2_BELIEF`) for pathing and engage decisions | Deaths, burst-death share |
| 9 | Team fight by local numbers (`A2_TEAMFIGHT`), convergence (v86h) | Fights are won by who arrives | **Arrival-time fight model**: Lanchester strength weighted by arrival turns, per contact; engage only with arrival advantage | Kill/death ratio R250-R500 |
| 10 | Pair/squad farming (`APEX_PAIR`, `APEX_SQUADS`, `APEX_ROLE_SQUAD`) | Isolation causes 51% of deaths | **Draft-time roles + buddy system**: each slot gets a role and a buddy at draft time; buddies stay within 5 when enemies are seen | Isolated-death share |
| 11 | Shop milestones (`A3_SHOP_GOLD`, `APEX_BOOT_ITEMS`, `UB_GOLD_MULT`) | Item timing compounds | **Marginal item value**: value gold by distance to the next item threshold; plan shop trips | First item round, gold R250 |
| 12 | Learned residual on the farm scorer (`learner.h`, 16 weights, starts at zero = exact v81) | Safe learning: starts identical, moves in measured steps | **Residual correctors** on x1's scorers trained by the joint ES search (teammate's method), validated on unseen maps | ES centre vs v86h |
| 13 | Fuel savers (`A2_BUSH_FAST`, `A2_FAST_AMBUSH`, `A2_CMICRO_FAST`, governor `A2_GOV`) | Same decisions, less fuel | **Fuel budget planner**: measured per-stage costs (telemetry), and spend the headroom on deeper fight search / more candidates | Fuel-outs 0, p99, win rate |
| 14 | Per-map ladder tables (`LADDER_TABLES`, v70/v71 lineups and knobs) | The ladder plays known maps | **Refit to x1's play** with seed-level validation, plus a geometric fallback for unseen maps | Ladder + unseen, seeds |
| 15 | Tactical search with learned models (`APEX_TSEARCH`, `A2_ENEMY_NET`, `A2_MOVENET`), off because it lost | Search failed on its fight model, not depth (teammate) | Only after #9: search with the arrival-time fight model as its evaluator | Fight-search vs verdict |

Order: 13 (fuel planner, cheap and exact) and 1 (finish-time model) first; then 3 (Phase 2), 8-10 (deaths), 2,
5, 6 (opponent and denial), 11, 7, 12 (ES), 14 (tables), 15 last.

## Second paper batch (2026-11-01): MAPF, Tribes, EA RL-augmentation

| Paper | Key result / mechanism | Fit here | Plan item |
|---|---|---|---|
| Hagelbäck & Johansson, *MAPF bot for a full RTS game* (AIIDE 2009); Hagelbäck thesis (2009) | Potential-field agents, no path planning, won ORTS 2008 82.5% (330/400). Attack ring at max shooting distance; retreat beyond enemy range while reloading; small repelling field at each ally's next tile (no crowding); coordinator assigns attacks so targets die (no overkill/underkill); decaying fog-of-war memory; pheromone trail against local optima | High for fights and positioning; pathing is already exact here | **P1 kill-securing coordinator** (new, see below); **P2 range-ring kiting** for ranged champions (v81 `APEX_KITE` in sweep 1c); spacing (`SPACING`, neutral) and belief (`A2_BELIEF`, in sweep) as baselines |
| Perez-Liebana et al., *Tribes* (AIIDE-20) | Turn-based strategy testbed with a forward model; RHEA beats MCTS 63% and rule-based 58.6%; OEP handles many-unit turn planning better than tree search | Medium: no engine forward model in-bot, but our internal economy/fight models can be the simulator | **P3 anytime evolutionary team job planner** on spare fuel (baseline: v81 `A2_PLAN` greedy, in sweep) |
| Sestini et al. (EA), *Augmenting game AI with deep RL* (2026) | RL should augment, not replace, scripted AI: modular, controllable, inside a shared compute budget; reward functions designed by experts; occupancy maps as cheap spatial observations | High as a principle; deep RL itself too costly here | **P4 learned residual correctors** (idea #12: start at zero, train by joint ES, validate on unseen maps); occupancy-style local grids as their features |

### New development items

- **P1 kill-securing coordinator.** Each body computes the same team attack assignment from what it sees (allies'
  positions, damage and range; enemy HP): first targets the reachable allies can kill this round, highest value
  first (bag + 100 kill gold, threat removed); then the lowest-HP target. No communication needed. Test vs v86h.
- **P2 range-ring kiting.** Ranged champions hold distance = their range against melee and step out while their
  attack or spell recharges; melee targets stay in reach. Compare with `APEX_KITE` from the sweep.
- **P3 anytime evolutionary team planner.** With fuel left after the turn's decision, evolve the team's job
  assignment (one gene per body) against a cheap income model with claim conflicts, keep the best in Memory and
  publish its first step; stop well before the reserve. Fuel-maximising by design.
- **P4 residual correctors.** On x1's camp and fight scores, starting at zero (identical play), trained by ES.

### Further avenues

- A potential-field *sparring opponent* (diverse style for the league, AlphaStar-style exploiters).
- Fog-of-war memory of enemy bags and positions, feeding P1 and carrier tracking (#6).
- Kiting plus the arrival-time fight model (#9) as one "engagement geometry" package.

### Thesis, second pass (Hagelbäck 2009, fog-of-war and design chapters)

- **Shared enemy memory:** a global map agent remembers every enemy spotted by any unit and shares it. Here: an
  out-of-sight enemy and bag memory through the 8-byte team word (with carrier tracking, #6).
- **Avoid-past trail:** a negative potential on each unit's last 20 positions breaks local optima. Here: an
  anti-oscillation term for champions that dither between tiles or targets (check v81's stuck handling first).
- **One exploration target at a time:** attracting to every unexplored edge strands explorers mid-map; pick one
  target by importance. Here: ward and scouting placement.
- **Evaluate against tournament opponents, not self-made bots:** matches our ladder finding; ladder replays and
  sparring bots modelled on top teams belong in the league.

### Full read-through of batch 2 (2026-11-01 night): research/x1/PAPERS_BATCH2_NOTES.md

Every page of the four papers is logged there (53 items: MAPF bot 1.1-1.12, Tribes 2.1-2.11, EA 3.1-3.12, thesis
4.1-4.19). What changed the plan:

- **Engagement geometry is where MAPF's wins came from** (thesis ablation: cooldown retreat +45 points, nearest-enemy
  ring instead of cluster centre +23, avoid-past trail +12). x1 already has both of the big two in its own form
  (`APEX_KITE` 3 for casters, single-target `position_and_attack`), so the remaining geometry gains are in
  cohesion (4.9), isolated-enemy targeting (4.10) and dead-end/choke maps (4.11).
- **Lone units attacking** cost the perfect-vision bot 66/100 vs its fog twin: tested as `X1_HUNT_SOLO` (cap the
  hunt range when no ally is within 5).
- **Tested and parked vs v86h:** `X1_SECURE` (kill-securing, 77+59 vs x1's 79+59 on ladder+unseen) and `X1_ALONE`
  (regroup when isolated, 75+59). Coordinator v2 (4.6: count all hitters, release surplus) is the only SECURE
  follow-up worth a try.
- **Planner (Tribes):** population-1 hill climber with a shift buffer, horizon long enough for whole job chains,
  relative-progress evaluation, no random rollouts, one decision class at a time (2.1-2.5, 2.9). This is P3.
- **Learning (EA):** one module at a time behind a switch, scenario training from saved mid-game states, fuel budget
  that includes feature extraction, static grids precomputed in the 10M draft turn, hysteresis on hand-back (3.1-3.12).
- **Method fix found while doing this:** 10 of the first 15 sweep-1c switches build a binary identical to x1 (dead
  code in this tree), so their games were replays. `tools/x1_flag_hashes.py` now builds each switch first; only
  switches with a new binary are played, and switches sharing a binary are played once.
