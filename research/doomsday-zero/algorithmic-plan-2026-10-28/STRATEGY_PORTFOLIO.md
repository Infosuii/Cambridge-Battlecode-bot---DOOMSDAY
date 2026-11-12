# Strategy portfolio: 12 candidates (plus 2 rejected for the record), ranked

E-numbers refer to FINAL_DEEP_ANALYSIS.md. "Gain" columns are **priors**, not measurements. Nothing here has been
tested unless an E-number says so.

## Ranking method

Each candidate gets a 1–5 score on five criteria:
- **G**, expected gain if it works: 5 = closes a measured gap of more than 100 gems/game against strong teams
- **C**, confidence the premise is true, from existing evidence
- **T**, testability: 5 = a sharp, cheap gate exists (idle bench or offline data); 1 = only ladder duels can judge it
- **K**, implementation cost: 5 = more than 5 days
- **R**, risk of breaking proven behaviour: 5 = replaces load-bearing tuned code

**Priority = G·C·T / (K·R).** Dependencies are listed separately; a high-priority concept that depends on another is
scheduled after it.

| Rank | Concept | G | C | T | K | R | Priority | Depends on | Track |
|---|---|---|---|---|---|---|---|---|---|
| 1 | S7 Win-condition race controller and endgame bug fixes | 2 | 4 | 4 | 1 | 1 | 32.0 | — | A and B |
| 2 | S9 Unseen-map profile generalisation (offline LOMO first) | 2 | 2 | 5 | 1 | 1 | 20.0 | — | analysis |
| 3 | S5 Survival rules (bag-aware, respawn re-entry, no trickle-in) | 4 | 3 | 3 | 2 | 3 | 6.0 | inside EE/TEP | B core |
| 4 | S6 Gear tempo: shop-trip piggy-backing and emblem completion | 3 | 2 | 4 | 2 | 2 | 6.0 | TEP SHOP objective | B optional |
| 5 | S3 Draft-time opening schedule, validated live | 2 | 2 | 5 | 2 | 2 | 5.0 | TEP | B optional |
| 6 | S2 Team Economy Planner with validated time model (TEP) | 4 | 3 | 4 | 4 | 3 | 4.0 | ledger, ObjModel | B core |
| 7 | S1 Objective-aware single-authority Engagement Evaluator (EE) | 5 | 3 | 2 | 3 | 3 | 3.3 | ledger, ObjModel (V_obj) | B core |
| 8 | S12 Vision and ward control for objectives | 2 | 1 | 3 | 2 | 1 | 3.0 | ledger | optional |
| 9 | S4 Crew protocol and fight leader | 4 | 3 | 2 | 3 | 3 | 2.7 | EE stage 3 | B core (late) |
| 10 | S8 Algorithmic draft (exhaustive utility optimiser) | 2 | 1 | 4 | 3 | 1 | 2.7 | — | optional (unseen maps) |
| 11 | S10 Opponent-adaptive mode switching | 3 | 2 | 2 | 3 | 3 | 1.3 | EE, TEP | post-finals |
| 12 | S11 Bounded tactical micro planner | 3 | 2 | 3 | 4 | 4 | 1.1 | EE | post-finals |
| — | S13 Territory and capture denial | rejected (v84: −886 on 2 games, R300 income −1890) | | | | | | | |
| — | S14 Carry funnel and role economy | rejected (E23, E17: −141, −89, carry prototypes flat) | | | | | | | |

**How to read the ranking.**
- The score measures expected value per unit of effort and risk. It is not a schedule.
- The cheap, sharp items (S7, S9) come first because they are nearly free. They cannot close the main gap.
- S5, S6 and S3 rank high individually, but each needs the TEP/EE substrate: S5 is a set of parameters inside EE and
  TEP; S6 and S3 are TEP objectives and priors.
- **The main gap (contest retention and deaths, E10–E12) is only addressed by S1, S2, S4 and S5.** Those form the
  core of the recommended architecture despite their lower individual priority.
- Within the core, S2 is scheduled before S1: it has the sharp idle gate, and it supplies V_obj, which EE needs.
- S5's parameters ship with them.
- With effort-weighted sums in priority order, the recommended package is:
  - S7 + S9 now
  - S2 → S1 (+S5) → S4
  - S6 / S3 only if time remains

---

## S1. Objective-aware single-authority Engagement Evaluator (EE)

1. **Problem.**
   - Five verdict writers over two booleans; last writer wins (E25).
   - Objective-blind fight decisions.
   - Per-champion verdicts, giving 28% step-away-without-hit and 2.6 reversals (E14).
   - Deaths dominate outcomes (E11–E12).
2. **Algorithm.** Candidate stances (FIGHT(t), HOLD, KITE, DISENGAGE, RETREAT, CONTINUE), each valued in
   gem-equivalents by a 4-round focused exchange simulation with optimistic and pessimistic variants. The value
   includes kills, deaths (bag + 100 gold + 60 rounds of tempo) and objective progress. Hysteresis and a free-action
   rule apply. Spec: COMBAT_AND_COORDINATION_DESIGN.md §C.2–C.4.
3. **Why it could beat v76.** One coherent value replaces stacked overrides. It values objectives, so it can hold
   captures and avoid dives for nothing. Commitment prevents reversals.
4. **Information.** Visible units' stats, positions and cooldowns (SDK); EnemyBelief for hidden enemies; TEP's V_obj
   and crew; ally stances.
5. **Interactions.** Owns the turn when a threat is present. Calls v76 executors. Reads TEP; writes CREW_STANCE (S4).
6. **Complexity.** O(stances × variants × H × n), with n ≤ 11 units: ≤16k ops.
7. **Fuel and memory.** 8–12k fuel on contact turns only, with a hard deadline and fallback to v76 `handle_enemies`.
   Memory: a few hundred bytes per champion.
8. **Difficulty.** Medium-high: 3–4 days including calibration and shadow mode.
9. **Failure modes.**
   - Miscalibrated damage or escape model leads to over-commitment and deaths.
   - Ignores terrain choke points.
   - Phantom enemies make it too timid.
   - Loses v76's tuned behaviours on edge cases (bush ambush, deny tribute).
10. **Evidence.** For: E14, E15, E25, E11–E12. Against: every local fight change neutral or negative (E17, v79,
    v75), tuned stack load-bearing (E4), local tests don't judge fights (E16).
11. **Cheapest disproof.** Offline calibration (§C.5) on existing replays, with no games. If the analytic model does
    not predict 4-round deaths better than v76's `in_danger` flag (Brier score), the premise "a coherent value is
    better informed than the stack" fails.

## S2. Team Economy Planner with validated time model (TEP)

1. **Problem.** Per-champion greedy camp choice; no crews, respawn arrival, follow-up value or contest probability;
   retention 62–66% (E10); the opening gain not kept (E17, opening pack).
2. **Algorithm.**
   - TeamLedger.
   - ObjModel: travel, clear, damage, capture, reward.
   - Sequential-auction crew assembly with regret-2 and one-step follow-up lookahead.
   - Single capturer.
   - Progress contract.
   - Event plus 8-round replans.
   Spec: DRAFT_AND_ECONOMY_DESIGN.md §A.1–A.3.
3. **Why it could beat v76.** It models the team problem v76 approximates per champion, and it carries the contest
   probability that makes economic choices fight-aware.
4. **Information.** Map groups and fields, ledger timers, claims, EnemyBelief, crew DPS from stats and items.
5. **Interactions.** Supplies V_obj, crews and roles to EE; SHOP / BANK objectives to the executors; claims to other
   champions.
6. **Complexity.** O(F·G) single rates with distance pruning, plus O(M·F²) crews.
7. **Fuel and memory.** Replan 3–8k, check <1k, worst 15k (skipped below the reserve). This replaces score_groups'
   ~13k. Memory O(G) per champion.
8. **Difficulty.** High: 4 days including the ObjModel validation gate.
9. **Failure modes.** v82's execution-contract failures; stale beliefs about unseen camps; crews waiting on late
   members; over-valuing distant rich groups.
10. **Evidence.** For: E10, E22, E8 (the R100 gap); v58 R3's finish-before-reset and single-capturer were retained.
    Against: v58 director 0/20 screens, v82 −89..−115 uncontested, A2_DPLAN −217 (E17); our uncontested farming
    already matches theirs contested (E10).
11. **Cheapest disproof.** The ObjModel replay-validation gate (no games). Then a 140-game idle mechanism test, about
    1 minute. If it is not non-inferior uncontested, stop.

## S3. Draft-time opening schedule, validated live

1. **Problem.** Their R100 gold exceeds our uncontested R100 (E8, E24); Claudus' first elk captures at R50 vs our R80
   (E22).
2. **Algorithm.** On the last draft turn, roll TEP forward with no enemies for 120 rounds and local-search the first
   two objectives per crew. Encode ≤32 bytes in draft memory. At runtime it is a ×1.3 prior inside TEP, dropped on
   the first ledger mismatch. Spec: DRAFT_AND_ECONOMY_DESIGN.md §A.6.
3. **Why it could win.** Uses the 10× draft fuel and full map visibility that runtime lacks. Unlike DPLAN, it is
   advisory and re-validated.
4. **Information.** Full map, final lineup, spawn regions.
5. **Interactions.** TEP prior only.
6. **Complexity.** About 200 rollouts × 120 rounds × F champions: ≤600k ops on draft turn 1.
7. **Fuel and memory.** Draft turn only; 32 bytes of draft memory.
8. **Difficulty.** Low-medium once TEP exists: 1 day.
9. **Failure modes.** Enemy rushes invalidate it (handled by dropping it); the gain fades by R250 as the opening pack
   did.
10. **Evidence.** For: E8, E22, the opening pack's timing success. Against: opening pack R250 unchanged, DPLAN −217.
11. **Cheapest disproof.** Idle test: R100 +10% and R250 non-inferior. If R250 is again unchanged, the opening has no
    lasting value on our controller.

## S4. Crew protocol and fight leader

1. **Problem.** Split engagements (21.8% vs 13.7%), late reinforcements (dives 5.1 vs 1.7), no team stance in shared
   memory (E14, E15, E26).
2. **Algorithm.** Beacon re-specified as 2 type bits + 20 payload bits: SIGHTING / CAMP_EVENT / CREW_STANCE /
   TEAM_MODE. The crew leader (lowest slot, set first by priority) writes the stance; members adopt it unless a
   personal-danger override fires. DEFEND objectives come from distress calls with arrival-in-time checks.
   Spec: COMBAT_AND_COORDINATION_DESIGN.md §C.8.
3. **Why it could win.** Makes the team act on one assessment per contact, which top teams' behaviour suggests.
4. **Information.** Shared word, claims, EE output.
5. **Interactions.** Requires EE stage 3; TEP gets DEFEND / ESCORT objectives.
6. **Complexity.** O(1).
7. **Fuel and memory.** Negligible; 64 shared bits re-budgeted.
8. **Difficulty.** Medium: 2 days. Protocol bugs are silent.
9. **Failure modes.** The leader acts last, so the stance is one round stale; message pre-emption starves sightings;
   members follow a bad leader into death.
10. **Evidence.** For: E14. Against: v79 join / focus / commit layers were always negative (E17). The difference is
    that those were added on top of the old verdicts, not one valuation shared by a crew. That still has to be shown.
11. **Cheapest disproof.** Scenario suite: on reproduced split-engagement windows from the puppet harness, the crew
    stance must cut split rounds without increasing deaths within the window.

## S5. Survival rules (inside EE and TEP)

1. **Problem.** Repeated deaths (per-death D3 rate 30.9% vs 18.3%, E9); 2× dead time (E11); bag losses −103/game
   (E9).
2. **Algorithm.**
   - Death cost includes the bag and 60 rounds of tempo.
   - For 25 rounds after respawn: crew-join bonus, pessimistic weighting, no solo objective under pressure.
   - Join only if arrival comes before the predicted fight end.
   - Banking is hazard-based (DRAFT_AND_ECONOMY_DESIGN §A.4).
3. **Why it could win.** Each death costs about 60 champion-rounds of income plus +100 enemy gold plus the bag.
   Removing one death per game is worth roughly 60·ρ̄ + 100λ + bag ≈ 40–80 GE.
4. **Information.** Death and respawn rounds, bag, EnemyBelief.
5. **Interactions.** Parameters of EE and TEP; no separate layer.
6. **Complexity.** O(1).
7. **Fuel and memory.** Negligible.
8. **Difficulty.** Low once EE and TEP exist.
9. **Failure modes.** Too timid, so income falls (V75_BAG −32, V75_LONE neutral locally and −91 on the ladder).
10. **Evidence.** For: E9, E11, E15. Against: caution rules were neutral locally and did not transfer (E16); the
    death watchdog was rejected.
11. **Cheapest disproof.** From existing replays, measure what fraction of repeated deaths occur within 25 rounds of
    respawn and alone. If it is under 25%, the respawn rule targets the wrong deaths.

## S6. Gear tempo

1. **Problem.** Equipment 603 vs 880 at R250 and 1463 vs 2334 at R500 in losses (E11). First purchase R71 vs R54.
   From R300 they out-stat us (E14).
2. **Algorithm.** SHOP objective in TEP: shop on death, on bank or recall trips, or when spawn is near; prioritise
   completing an emblem whose passive is only granted at 5 shards. Per-role builds are evaluated separately.
3. **Why it could win.** Gear compounds fight and clear power. Wasted walks to spawn cost income.
4. **Information.** Gold, build plan, spawn field.
5. **Interactions.** TEP objective; EE reads stats as they are.
6. **Complexity.** O(1).
7. **Fuel and memory.** Negligible.
8. **Difficulty.** Low: 1 day.
9. **Failure modes.** Income loss from shop detours; v66 item openings were −8..−58.
10. **Evidence.** For: E11, E14. Against: equipment mostly follows income (correlation); "buy sooner" does not follow
    from the deep analysis's purchase labels.
11. **Cheapest disproof.** Idle test: R250 equipment +10% with R250 gems non-inferior. If equipment rises only by
    spending earlier with no later income gain, drop it.

## S7. Win-condition race controller and endgame bug fixes

1. **Problem.**
   - The recall-restart loop on a winning bag: a 736-gem carrier lost on 02guardians (E18).
   - Endgame tribute and lock races.
   - 02guardians gate race.
2. **Algorithm.**
   - Guard: never cancel a recall solely for win-now while banking is disabled (`tribute_off_until`). This is the
     frozen diagnostic spec in deep `TAKEOVER_PLAN.json`.
   - Race arithmetic: when `our_banked + bag ≥ 1000`, route to the nearest free altar with an escort and use an altar
     lock against enemy tributes when `their_banked + their_bags ≥ 900`.
3. **Why it could win.** Each such loss is a whole game.
4. **Information.** Banked scores (SDK), bags.
5. **Interactions.** BANK objective priority; EE values the bag.
6. **Complexity.** O(1).
7. **Fuel and memory.** Negligible.
8. **Difficulty.** Low: 0.5–1 day.
9. **Failure modes.** A rare event, so the measured gain is small and hard to see.
10. **Evidence.** For: E18 (exact reproduction). Against: frequency unknown. M1_SPEC's proxy screen exists but the
    hands-off confirmation must not be done casually.
11. **Cheapest disproof.** The frozen puppet takeover diagnostic (TAKEOVER_PLAN.json): does the guard remove the
    cancel/restart pairs in R1669–1672? Run it under the deep-analysis protocol.

## S8. Algorithmic draft (exhaustive utility optimiser)

1. **Problem.** Draft on unseen maps; the per-map tables do not generalise (E6).
2. **Algorithm.** Exhaustive lineup utility (clear power vs camp mix, sustain, fight power vs revealed picks,
   mobility vs gaps, economy bonus scaled by our controller, synergy, role constraints), fitted by pairwise ranking on
   the v70 league. Spec: DRAFT_AND_ECONOMY_DESIGN.md §B.2.
3. **Why it could win.** It uses map geometry that coarse features miss, and it best-responds to revealed picks
   (non-exclusive draft).
4. **Information.** Draft-phase full map, revealed enemy picks.
5. **Interactions.** Draft memory; independent of runtime.
6. **Complexity.** ≤792 lineups × ~300 ops.
7. **Fuel and memory.** ≤250k on draft turn 1.
8. **Difficulty.** Medium: 2 days including fitting.
9. **Failure modes.** Overfits the league; ignores controller synergies.
10. **Evidence.** For: the per-map oracle is +134 (E6). Against: coarse features give only +17; the meta draft lost.
11. **Cheapest disproof.** Offline LOMO on the existing league data with B.2 features computed from map files. If the
    held-out mean gain is not above the ML net's held-out gain, stop.

## S9. Unseen-map profile generalisation

1. **Problem.** On a map outside the V71 table only the global knobs act (E4: map knobs are worth 100–171 in-sample).
2. **Algorithm.** Offline LOMO over the existing knob-table league runs (research/v71 round runs): predict a held-out
   map's profile by nearest neighbours on map features, and compare with global knobs.
3. **Why it could win.** Cheap; if it generalises at all it covers unseen finals maps.
4. **Information.** Existing league runs and map keys.
5. **Interactions.** Knob layer only.
6. **Complexity.** Offline only.
7. **Fuel and memory.** None at runtime beyond one lookup.
8. **Difficulty.** Very low: analysis only.
9. **Failure modes.** Like the draft (E6), it may not generalise.
10. **Evidence.** For: map knobs matter (E4). Against: E6.
11. **Cheapest disproof.** The LOMO analysis itself, with no games: is the held-out gain CI above 0?

## S10. Opponent-adaptive mode switching

1. **Problem.** One controller plays aggressive rushers, passive farmers and perma-recall teams (E19) alike.
2. **Algorithm.** Classify the opponent from observations by R100: early contact count, enemy channel patterns,
   drafts. Switch TEP's risk and contest parameters among three profiles.
3. **Why it could win.** Top-12 styles differ (Mite / Trzy win with less gold; research/v81).
4. **Information.** EnemyBelief statistics.
5. **Interactions.** Parameter sets for EE and TEP.
6. **Complexity.** O(1).
7. **Fuel and memory.** Negligible.
8. **Difficulty.** Medium; data are scarce.
9. **Failure modes.** Misclassification; overfitting to 12 teams.
10. **Evidence.** For: style diversity. Against: no local opponent reproduces the styles (proxy, E20).
11. **Cheapest disproof.** On ladder replays, check whether an R100 classifier predicts a later style better than
    chance.

## S11. Bounded tactical micro planner

1. **Problem.** Contact-round action use (E14) and caster positioning.
2. **Algorithm.** Enumerate move × attack × spell (≤9×3×3), scored by immediate damage, position safety and stance
   consistency, with an anytime budget of ≤8k.
3. **Why it could win.** It could replace several micro executors with one consistent scorer.
4. **Information.** Scene.
5. **Interactions.** An executor under EE.
6. **Complexity.** ≤81 candidates.
7. **Fuel and memory.** ≤8k.
8. **Difficulty.** High (v81 experience).
9. **Failure modes.** v81: complete sequences and damage were not a sufficient objective; −532.
10. **Evidence.** For: E14. Against: v81.
11. **Cheapest disproof.** Scenario A/B vs `caster_micro` on puppet windows: damage dealt and taken over 3 rounds.

## S12. Vision and ward control for objectives

1. **Problem.** Wards 30 vs 77 by R500 (E11); unseen threats.
2. **Algorithm.** Place wards on approach paths to the crew's objective and on altars on carry trips; share
   sightings via the beacon.
3. **Why it could win.** Better EnemyBelief, so fewer surprise deaths.
4. **Information.** Map geometry, objective.
5. **Interactions.** Ledger and EnemyBelief.
6. **Complexity.** O(candidate tiles).
7. **Fuel and memory.** ≤2k occasionally.
8. **Difficulty.** Low.
9. **Failure modes.** Little value since vision isn't shared; only the beacon carries it.
10. **Evidence.** For: the ward gap. Against: the D11 unseen-killer gap weakens after exposure normalisation (deep
    analysis); wards are not shared.
11. **Cheapest disproof.** From existing replays, measure the fraction of our deaths whose killer was first seen 2 or
    fewer rounds before the death. If it is small, drop the idea.

## Rejected for the record

- **S13 Territory and capture denial** (v84): starving our own development does not convert to wins. It could only
  return as a TEP objective with an explicit value and crew strength, never as fixed guards.
- **S14 Carry funnel and role economy** (UB_GOLD_FUNNEL, V58 route, carry prototypes in this audit): raises Vesper's
  share without raising team gold (E23). It would only make sense if TEP's single-capturer rule shows that Vesper
  captures at no time cost.
