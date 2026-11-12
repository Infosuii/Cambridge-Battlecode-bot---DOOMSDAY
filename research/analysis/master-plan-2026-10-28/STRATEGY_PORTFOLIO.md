# Strategy portfolio: 13 candidates plus rejected ideas, ranked by explicit criteria

**Scoring.** Each criterion is scored 1–5. **Priority = G·C·T / (K·R).**
- **G**: expected gain if it works (5 = closes a measured gap of more than 100 gems/game against top teams)
- **C**: confidence in the premise, from evidence
- **T**: testability (5 = sharp offline or idle gate; 1 = ladder only)
- **K**: implementation cost (5 = more than 5 days)
- **R**: risk to proven behaviour (5 = replaces load-bearing tuned code)

The gain column is a prior, not a measurement. Mechanics references are in GAME_MECHANICS_AND_WIN_CONDITIONS.md;
algorithms in ALGORITHM_SPECIFICATIONS.md.

| Rank | ID | Concept | G | C | T | K | R | Priority | Core? |
|---|---|---|---|---|---|---|---|---|---|
| 1 | S7 | Win-race controller, M1 recall fix, endgame altar locks | 2 | 4 | 4 | 1 | 1 | 32.0 | yes (cheap) |
| 2 | S13 | Offline-optimised tables: league re-selection of draft, items and scalars; unseen-map generalisation | 3 | 3 | 4 | 2 | 1 | 18.0 | yes (process) |
| 3 | S6 | Marginal-value gear planner (Prospector, Capture, Treasure, Jungle… valued in GE) | 4 | 3 | 4 | 2 | 2 | 12.0 | yes |
| 4 | S12 | Vision cycling plus sector-coded sighting beacon | 2 | 2 | 3 | 1 | 1 | 12.0 | optional |
| 5 | S8 | Solo cluster circuits (capture-bound routing with Capture/Prospector) | 3 | 3 | 5 | 2 | 2 | 11.3 | yes (inside TEP) |
| 6 | S9 | Banking as optimal stopping; bank-on-route; Marcella banker | 3 | 3 | 4 | 2 | 2 | 9.0 | yes (inside TEP) |
| 7 | S3 | Draft-time opening schedule, validated live | 3 | 2 | 5 | 2 | 2 | 7.5 | optional |
| 8 | S5 | Survival rules (bag- and tempo-aware death cost, respawn re-entry, no trickle-in) | 4 | 3 | 3 | 2 | 3 | 6.0 | yes (inside EE/TEP) |
| 9 | S10 | Robust targeting and opponent-style detection (perma-recall, rusher, turtle) | 2 | 2 | 3 | 1 | 2 | 6.0 | optional |
| 10 | S2 | Team Economy Planner (TOPTW crew auction through claims) | 4 | 3 | 4 | 4 | 3 | 4.0 | **yes (backbone)** |
| 11 | S1 | Engagement Evaluator: one owner, objective-aware, Lanchester analytic, stance portfolio | 5 | 3 | 2 | 3 | 3 | 3.3 | **yes (backbone)** |
| 12 | S4 | Crew protocol and fight leader | 4 | 3 | 2 | 3 | 3 | 2.7 | yes (late) |
| 13 | S11 | XSquare-style per-candidate micro scorer replacing ad hoc executors | 3 | 3 | 3 | 3 | 4 | 2.3 | post-finals unless EE is early |

**How to read it.**
- The highest-priority items are cheap, but they cannot close the main gap alone.
- The two backbones (S2, S1) rank lower because they are expensive and risky. But S3, S5, S6, S8 and S9 are
  *parameters or objectives inside them*, so the schedule builds the backbones first and then fills them in.
- S7 and S13 run in parallel from Day 1.

---

## S1. Engagement Evaluator (EE)

1. **Problem.**
   - Five verdict writers over two booleans; objective-blind.
   - 28% step-away-without-hit; 2.6 reversals; deaths 2×.
2. **Algorithm.**
   - A portfolio of stances: FIGHT(t1), FIGHT(t2), HOLD, KITE, DISENGAGE, RETREAT, CONTINUE.
   - Each is evaluated by a 4-round focused-fire attrition model (TS-Lanchester style), in an optimistic and a
     pessimistic variant.
   - Value in gem-equivalents: kills, deaths, objective progress, tempo.
   - Hysteresis; free-action rule.
   - Details: ALGO §5.
3. **Why it could win.** It is one coherent value, which the literature supports: Lanchester predictors beat
   simulation in attack/retreat decisions [B10, B11]. It values objectives and commits.
4. **Information.** Visible stats and cooldowns, EnemyBelief, the TEP objective, crew stance.
5. **Interactions.** Owns turns with threat. Calls the executors (or S11). Publishes the crew stance (S4).
6. **Complexity.** O(S·V·H·n) ≤ 7·2·4·11 ≈ 600 unit-steps.
7. **Fuel and memory.** ≤12k fuel on contact turns; <1 KB.
8. **Difficulty.** Medium-high: 3–4 days.
9. **Failure modes.** Miscalibration, so over-commitment; terrain choke points ignored; timidity from phantom
   enemies.
10. **Evidence.** For: E14/E15/E25, external [B10–B12]. Against: local fight changes never transferred.
11. **Cheapest disproof.** Offline replay calibration: 4-round death Brier must beat v76's `in_danger` flag.

## S2. Team Economy Planner (TEP)

1. **Problem.** Per-champion greedy; no crews, timing, follow-up or contest; the opening gap; retention.
2. **Algorithm.**
   - Ledger plus a validated ObjModel.
   - A sequential auction through claims (degenerate CBBA [B18]).
   - Crew sizing.
   - Single capturer; respawn arrival; one-step follow-up (TOPTW insertion [B15]).
   - Progress contract.
   - Details: ALGO §3.
3. **Why it could win.** It models the team problem v76 approximates, with contest probability and item effects.
4. **Information.** Map groups, fields, ledger, claims, EnemyBelief, crew stats.
5. **Interactions.** Supplies V_obj to EE; BANK and SHOP objectives; claims.
6. **Complexity.** O(F·G′) + O(M·F²).
7. **Fuel and memory.** Replan 3–8k (cap 15k), check <1k. Replaces score_groups' ~13k.
8. **Difficulty.** High: 4 days.
9. **Failure modes.** v82 execution contract; stale beliefs; waiting crews.
10. **Evidence.** For: the opening gap, the retention gap, v58 R3 pieces that worked. Against: v58 director 0/20,
    v82 −89..−115, DPLAN −217.
11. **Cheapest disproof.** ObjModel replay gate (offline), then a 140-game idle non-inferiority check.

## S3. Draft-time opening schedule

1. **Problem.** First large receipt R55–82 vs R41–60; R100 gold 278 vs 483 (Fish).
2. **Algorithm.** On the last draft turn (1M fuel on turn 1, 100k after), roll TEP forward 120 rounds with no
   enemies and local-search the first two jobs per crew. Encode ≤32 bytes. At runtime it is a ×1.3 prior, dropped on
   the first mismatch.
3. **Why it could win.** Full map knowledge plus spare draft fuel.
4. **Information.** Full map and lineup.
5. **Interactions.** A TEP prior only.
6. **Complexity.** About 200 rollouts.
7. **Fuel and memory.** Draft turn only; 32 bytes.
8. **Difficulty.** 1 day after TEP.
9. **Failure modes.** Early contest; fades by R250 (as the opening pack did).
10. **Evidence.** For: opening-pack timing worked. Against: R250 was unchanged then.
11. **Cheapest disproof.** Idle R100 +10% and R250 non-inferior.

## S4. Crew protocol and fight leader

1. **Problem.** Split engagements (21.8% vs 13.7%); trickle-ins; no shared stance.
2. **Algorithm.** A typed 22-bit beacon: SIGHTING / CAMP_EVENT / CREW_STANCE / TEAM_MODE. The leader is the lowest
   slot, set to act first with `set_priority`. Members adopt the stance unless personal danger overrides.
3. **Why it could win.** Concentration of force [B13]; consistent commitment.
4. **Information.** The shared word and EE output.
5. **Interactions.** EE stage 4; TEP DEFEND / ESCORT.
6. **Complexity.** O(1).
7. **Fuel and memory.** Negligible; 64 bits re-budgeted.
8. **Difficulty.** 2 days.
9. **Failure modes.** A stale leader; starved sightings; following a bad leader.
10. **Evidence.** For: E14. Against: v79 join/focus layers were negative (but they were layered on top).
11. **Cheapest disproof.** Puppet split-engagement windows: split rounds drop with no extra deaths.

## S5. Survival rules

1. **Problem.** D3 repeated deaths; 2× dead time; bag losses.
2. **Algorithm.**
   - Death cost = bag + λ_gold·100 + λ_tempo·60·ρ̄.
   - After respawn: 25 rounds of a crew-join bonus and pessimistic weighting.
   - Join a fight only if arriving before it ends.
3. **Why it could win.** About 50 GE plus the bag per death avoided.
4. **Information.** Death and respawn state, bag, pressure.
5. **Interactions.** EE and TEP parameters.
6. **Complexity.** O(1).
7. **Fuel and memory.** Negligible.
8. **Difficulty.** Low.
9. **Failure modes.** Timidity (V75_BAG −32; watchdog −126).
10. **Evidence.** For: E9, E11, top teams' 2–5 deaths. Against: caution rules don't transfer by themselves.
11. **Cheapest disproof.** Offline: the share of repeated deaths within 25 rounds of a respawn while alone must
    exceed 25%.

## S6. Marginal-value gear planner

1. **Problem.**
   - The equipment gap: 603 vs 880 at R250, 1463 vs 2334 at R500.
   - A fixed build order ignores role and map.
   - Prospector and Capture are bought but not exploited.
2. **Algorithm.** For each affordable next purchase (shard toward an emblem, emblem completion, consumable),
   estimate ΔGE over the remaining horizon:
   - Strength or Focus shard: Δ camp DPS → Δ ρ; Δ fight value.
   - Health shard: Δ survival.
   - Monster: +15% camp DPS.
   - Jungle: −30% camp damage, so fewer heal trips.
   - Treasure: +10% gold × the champion's expected capture-gold share.
   - Prospector: +25% cluster gems × expected cluster captures.
   - Capture: −2 rounds per capture × capture count.
   - Home: −2 recall rounds × recalls.
   - Hunter: +50 per expected kill.

   Choose by ΔGE per gold, with emblem completion bonuses. Details: ALGO §7.
3. **Why it could win.** Gear compounds. The Sprint-3 item package alone gave +136..+153 locally (I6), so item
   choice matters a lot.
4. **Information.** Engine item metadata, role, TEP plan statistics (captures per round, cluster share, kill rate).
5. **Interactions.** SHOP objective timing (TEP); the stats feed ObjModel and EE.
6. **Complexity.** ≤20 candidates × O(1).
7. **Fuel and memory.** <2k on spawn turns.
8. **Difficulty.** 1.5 days.
9. **Failure modes.** Mis-estimated ΔGE; build thrash. Mitigation: commit to an emblem once 2 shards are bought.
10. **Evidence.** For: Sprint 3 +136; opponents' equipment lead. Against: v66 item openings −8..−58 (fixed orders,
    not a value model).
11. **Cheapest disproof.** Idle: R250/R500 income with the planner ≥ the fixed build.

## S7. Win-race controller, M1 fix, endgame locks

1. **Problem.** The M1 recall restart (exact trace); no time-to-1000 model; few altar locks.
2. **Algorithm.**
   - M1 guard: cancel a winning-bag recall only if banking is enabled.
   - Race estimate: `T_us = (1000 − banked − Σbags·p_bank) / income`, and the same for the enemy.
   - When `T_us` is small or the enemy is close to 1000, switch TEAM_MODE to ENDGAME_RACE: bank, escort, lock enemy
     altars.
3. **Why it could win.** Each endgame error loses a whole game.
4. **Information.** Banked scores (SDK) and visible bags.
5. **Interactions.** BANK priority; altar-lock executor.
6. **Complexity.** O(1).
7. **Fuel and memory.** Negligible.
8. **Difficulty.** 1 day.
9. **Failure modes.** Rare events, so measured gain is small.
10. **Evidence.** M1 exact trace (I2).
11. **Cheapest disproof.** `tests/loss_cases/M1-recall-disabled-bank.json`: the baseline fails and the candidate
    passes.

## S8. Solo cluster circuits

1. **Problem.** Clusters are capture-bound and safe (no damage), yet v76's value/cost scoring treats them like small
   camps, and ignores Capture and Prospector.
2. **Algorithm.** Inside TEP, a cluster objective's service time is `1 + capture_time(c)` (3 with a Capture emblem)
   and its reward is `floor(7·(1 + 0.25·[Prospector]))`.
   - Periodic routing: arrive at `respawn_round`.
   - A champion with Capture plus Prospector gets a CLUSTER_RUNNER role on maps with many clusters (≥4 clusters
     within 25 tiles of a route).
3. **Why it could win.** Mechanics (GAME_MECHANICS §4): 0.57 GE per champion-round, solo, no damage.
4. **Information.** Map group types, respawn timers, items.
5. **Interactions.** TEP objective type; gear planner (S6) buys Capture/Prospector for runners.
6. **Complexity.** Within TEP.
7. **Fuel and memory.** Within TEP.
8. **Difficulty.** 0.5 day once TEP exists.
9. **Failure modes.** Runners get picked off (contest pressure); clusters may be few on some maps.
10. **Evidence.** The Prospector inference (I10); the rate arithmetic.
11. **Cheapest disproof.** Idle: cluster capture count and gems per runner-round vs v76 on cluster-rich maps.

## S9. Banking as optimal stopping

1. **Problem.** Conversion 63% vs 88%; bag losses −103/game.
2. **Algorithm.** The burglar-problem cutoff: bank when `bag · h(p) · T_next ≥ C_trip`.
   - h comes from the pressure model.
   - Bank-on-route insertion: an altar within +4 rounds of the path triggers a bank when the bag is ≥ 10.
   - Prefer Marcella as the capturer of gem-rich groups, since she gets +2 gold per gem banked and is stun-immune.
   - Lock enemy altars against visible enemy carriers whose bag is ≥ 60.
3. **Why it could win.** It directly targets conversion and bag loss.
4. **Information.** Bag, fields, pressure.
5. **Interactions.** TEP BANK objective; EE values the bag.
6. **Complexity.** O(altars).
7. **Fuel and memory.** <1k.
8. **Difficulty.** 1 day.
9. **Failure modes.** Over-banking costs income. The deep analysis warns that "bank earlier" is not proven.
10. **Evidence.** For: conversion gap. Against: the C034 carrier was already banking.
11. **Cheapest disproof.** Idle conversion and income non-inferiority; league bag-loss reduction.

## S10. Robust targeting and opponent-style detection

1. **Problem.** `worth += 0.5` for recalling enemies; perma-recall teams; style diversity.
2. **Algorithm.**
   - Track each visible enemy's channel age: a recall is only "real" after 2 consecutive turn-end observations.
   - Classify the opponent by R100: perma-recall share, contact rate, middle presence.
   - Pick one of three parameter sets for EE and TEP: default, cautious, aggressive.
3. **Why it could win.** It removes an exploitable bias and adapts risk.
4. **Information.** Observed enemy channel states and contact events.
5. **Interactions.** EE target worth; TEP risk.
6. **Complexity.** O(enemies).
7. **Fuel and memory.** Negligible.
8. **Difficulty.** 1 day.
9. **Failure modes.** Misclassification; overfitting to historical teams.
10. **Evidence.** Low (the perma-recall purpose is unknown).
11. **Cheapest disproof.** Offline: deaths following engagements on "recalling" targets vs others.

## S11. XSquare-style per-candidate micro scorer

1. **Problem.** Executor sprawl: kite, kite-cast, gap-dash, position, flee-hit, caster micro.
2. **Algorithm.** Enumerate (move ∈ 9) × (attack target ∈ ≤3 or none) × (spell ∈ ≤3 or none), respecting the rules
   (ranged: move or attack). Score each by stance-consistent terms: damage dealt now, expected damage taken at the
   tile before our next turn, kill bonus, stun value, distance to the stance goal, ally adjacency. Pick the best.
   Literature [B5].
3. **Why it could win.** One consistent framework; it fixes step-away-without-hit by construction.
4. **Information.** Scene and movement mask.
5. **Interactions.** An executor under EE.
6. **Complexity.** ≤81 candidates × O(enemies).
7. **Fuel and memory.** ≤8k.
8. **Difficulty.** 3 days.
9. **Failure modes.** v81's failure (immediate damage objective). Mitigation: the stance goal plus threat terms come
   from EE.
10. **Evidence.** For: the 2024 postmortem. Against: v81 −532.
11. **Cheapest disproof.** Puppet scenario A/B vs `caster_micro` and the melee executors over 3-round windows.

## S12. Vision cycling plus sector beacon

1. **Problem.** Wards 38–86 vs 94–244 per game; unshared vision.
2. **Algorithm.** Re-place the ward on every recharge at the next objective approach or altar path. Publish
   sightings as sector codes (6+6 bits).
3. **Why it could win.** Better belief for TEP and EE.
4. **Information.** Map geometry and objective.
5. **Interactions.** Ledger and EnemyBelief.
6. **Complexity.** O(candidates).
7. **Fuel and memory.** <2k occasionally.
8. **Difficulty.** 0.5 day.
9. **Failure modes.** Low impact.
10. **Evidence.** For: the ward gap. Against: the D11 normalisation weakens the unseen-killer link.
11. **Cheapest disproof.** Offline killer-first-seen analysis.

## S13. Offline-optimised tables (the process that transferred)

1. **Problem.** New modules have about 15 scalars. Per-map tables won't generalise to unseen maps.
2. **Algorithm.** The v70/v71 league protocol:
   - opponents v65, v61, v58 and proxy, plus 2–3 scripted style opponents (VALIDATION §3)
   - select scalars and per-map lineups on training maps and seeds
   - confirm on fresh seeds and held-out maps

   For unseen maps, use kNN over map features to choose a profile, *only if* held-out LOMO > 0.
3. **Why it could win.** It is the only method demonstrated to transfer to the ladder (E21).
4. **Information.** League runs.
5. **Interactions.** Configuration tables.
6. **Complexity.** Offline.
7. **Fuel and memory.** None at runtime.
8. **Difficulty.** 1–2 days of compute and analysis.
9. **Failure modes.** Overfitting. Mitigated by fresh seeds and held-out maps.
10. **Evidence.** v70–v74 (+15..+169; ladder +142).
11. **Cheapest disproof.** The held-out map gain CI includes 0.

## Rejected (and what would change the verdict)

| Idea | Evidence against | Would reconsider if |
|---|---|---|
| Fixed-guard territory denial | v84 −886, R300 income −1890 | It were run only as a valued CONTEST objective with crew strength |
| Carry funnel and role economy | −141, −89; carry prototypes flat (E23) | TEP showed Vesper capturing at zero time cost |
| Runtime MCTS / tactical search | −366, 16 fuel-outs per game | An analytic model proved insufficient *and* there were 30k spare fuel per contact turn |
| Imitating top teams' actions | v83 −65; mimic 0/120 | Never as a policy; as a diagnostic only |
| Copying perma-recall | −33 ± 40 (proxy) | Its purpose were shown (TOP_TEAM M-E) |
| RL / MARL training | No compute or time; past PPO learned nothing | Post-finals |
