# External research: what transfers to Cambridge Battlecode 2026 and what doesn't

> **Carried forward into the DOOMSDAY Zero (clean-slate) package, 2026-10-28.**
> - "TEP" means DZ's economy planner, and "executors" means DZ's action scorer (ALGORITHM_SPECIFICATIONS §6).
> - v76 appears only as a benchmark and as the source of lessons. DZ reuses no v76 code.
> - Where this text mentions a v76 fallback path, DZ uses its own SafeMode (MASTER_ARCHITECTURE §3).


Each finding is mapped to the actual mechanics in GAME_MECHANICS_AND_WIN_CONDITIONS.md, with the differences that
could invalidate it. Full references are in RESEARCH_BIBLIOGRAPHY.md (cited as [B#]). Category labels:
- **[EXT]**: externally supported technique
- **[HYP]**: our architectural hypothesis built on it

## 1. Cambridge Battlecode itself

**Official site.**
- `battlecode.cam` redirects to `2026a.battlecode.co.uk`, a JavaScript-rendered app. A fetcher gets only the title,
  so rules, ladder and team pages are not accessible without the authenticated client [B1].
- The repository already holds the official rules text, SDK, CLI and engine-probed metadata, which this plan treats
  as authoritative.

**Public event page** [B2].
- Finals are a 16-team double-elimination bracket at the Cambridge Union, after weeks of ladder play and qualifiers.
- A participant post [B3] describes an earlier Cambridge edition as Python-based, so it is not the same game.
- **Finals format implication.** A double-elimination bracket of best-of matches rewards *consistency across maps and
  opponents*, not peak margin. The 70-map pool and seeds will vary between games, so a design with fewer catastrophic
  maps (one-sided losses) is worth more than a few big wins.

**Public bots.**
- No public current-rules bot from a top team was found [B4].
- Previously downloaded public bots (Midnight Wardens, gamebot) ran out of fuel heavily and were invalid opponents
  (`research/v81/RESEARCH.md`).
- **Limitation recorded:** top-team internals can only be inferred from replays (TOP_TEAM_REVERSE_ENGINEERING.md).

## 2. MIT Battlecode (related competition, different game)

**Battlecode 2024, "Cout for Clout" postmortem** [B5]:
- **Micro.** The team abandoned "lots of if statements and a combat BFS" for **XSquare-style micro**: score each of the
  9 candidate move directions with a heuristic (damage potential, threat, ally and enemy health, cooldown buckets),
  then take the best. They report the clean framework "proved to be a crucial advantage" and moved them from about
  1850 to 1950+.
  - Maps to our game: per-turn movement choice in a fight, with damage-reach and threat per tile.
  - Differences: our champions have heterogeneous kits and spells. Ranged champions cannot move and attack in the
    same turn, so the candidate set is (move, attack, spell), not just a direction.
- They made micro *more aggressive* after measuring that defensive "sitting" lost Lanchester-style numbers battles.
- They tuned by careful scrimmage analysis: "it's the execution of those ideas that make most of the difference."

**Battlecode 2023, "4 Musketeers" strategy guide** [B6]:
- **Sector system.** Encode locations as coarse sectors to save communication bits.
- **Staleness.** Reset combat information every N rounds.
- **Buffer pool.** Batch writes to the shared array to avoid write amplification.
- **Run home when threatened.** Carriers near-death go home to deposit, or drop resources and run.
- Testing: automated cross-version matches through CI.
- **Mapping to our game:**
  - Sectors map directly to our 20-bit beacon payloads.
  - "Carrier runs home to deposit" is our BANK hazard rule.
  - Our shared memory is 8 bytes, not 64 × 16 bits, so encoding discipline matters even more.

**Lesson [HYP].** In Battlecode-style ladders, the teams that won had *simple, consistent, well-executed* per-unit
decision frameworks and exploited the rules. They did not run deep search. This argues against big search and for
clean scored micro plus good macro.

## 3. MOBA research (closest genre: champions, gold, items, farming, teamfights)

**OpenAI Five** (Dota 2) [B7]:
- **Scripted, not learned:** item purchasing and ability builds followed fixed, hand-written schedules (randomised in
  training), as did courier control and item swaps. The authors reached superhuman play without learning these.
  - Lesson: a **deterministic item and ability planner is not a weakness**. Even the strongest learned MOBA agent
    used one.
- **Team spirit** interpolates each hero's reward between selfish and team-shared. They annealed it from 0.3 towards
  1.0, so later training valued team outcomes fully.
  - Lesson [HYP]: our value function should be **team-level gem-equivalents**. Credit splitting matters only for
    learning, which we are not doing.
- **Time-weighted shaped reward.** Rewards were scaled by about 0.6^(T/10 min), because late-game rewards are larger.
  - Lesson: the exchange rates between gold, kills, deaths and gems must be **time-dependent**: λ_gold(t) and death
    cost(t) in ALGORITHM_SPECIFICATIONS.md §2.
- A hand-coded scripted bot reached TrueSkill about 100; the learned agent far exceeded it, at enormous compute (10
  months of training). **Not feasible in two weeks with a fuel-limited wasm runtime**, and our learned components have
  never generalised beyond our lineage.

**Tencent "Hierarchical Macro Strategy" model for Honor of Kings** [B8]:
- A **phase layer** (game-phase recognition) plus an **attention layer**, which predicts which map region each hero
  should go to.
- Agents decide individually but coordinate through an imitated cross-agent communication signal.
- Lesson [HYP]: macro = *where each champion should be*, conditioned on phase. This is exactly a
  champion-to-objective assignment, done algorithmically by TEP with phase-dependent value.
- Difference: they learned from human replays; we have no comparable dataset for top teams' intents.

**"Towards Playing Full MOBA Games with Deep RL"** [B9]: curriculum self-play, policy distillation and MCTS for the
draft, with huge compute. Lesson: draft is treated as **search over picks with a learned value**. Our draft is
small enough (≤792 lineups) for exhaustive deterministic evaluation.

## 4. RTS research: combat prediction and bounded search

**Lanchester-based combat models.**
- Stanescu, Barriga and Buro [B10] learn unit strengths from replays.
  - Their Lanchester predictor **beat a simulation-based version in tournament games** when it was used for
    attack/retreat decisions.
  - It is also much faster.
- Uriarte and Ontañón [B11] propose "TS-Lanchester²", the Square Law plus a target-selection policy, to predict which
  units survive.
  - It gave higher winner-prediction accuracy than the SparCraft simulator, and final-state prediction **19–145×
    faster**.
  - Static (known) DPF beat learned DPF.
- **Mapping.** Our engagement decision is "fight or avoid". We know exact stats (DPF = strength + spell DPS) at
  runtime, which is their "static DPF" case, the better one.
- **Differences:**
  - burst spells (8-round cooldowns)
  - stuns
  - kill-reset (Vendetta)
  - linked fates (C&I)
  - very small armies (3–5 per side)

  So we use a **discrete short-horizon focused-fire attrition model** (ALGORITHM_SPECIFICATIONS §5) rather than the
  continuous ODE.

**Portfolio Greedy Search (Churchill and Buro)** [B12].
- Searching over a **portfolio of scripted behaviours** (attack-closest, kite and so on) per unit, with hill-climbing
  and playout evaluation, beats Alpha-Beta and UCT in large battles under 40 ms.
- Later work found PGS "relies heavily on the accuracy of the underlying model".
- **Mapping.** Our EE stances are exactly a portfolio: FIGHT(t), HOLD, KITE, DISENGAGE, RETREAT.
- **Difference.** We cannot afford playouts within fuel (our tactical search: 16 fuel-outs per game, −366 gems). We
  evaluate portfolio members with the analytic model instead (Uriarte and Ontañón's speed result).

**Lanchester's square law** [B13].
- With aimed fire, effective strength ∝ numbers² × per-unit effectiveness, so **concentration of force** and focus
  fire dominate.
- Caveat: real air combat did not fit the square law.
- Mapping: with 3–5 champions per side the square-law "numbers" effect is strong. Getting 3v2 locally is decisive,
  which supports crew-based movement and the no-trickle rule.

**AlphaStar** [B14]: league training with exploiters to find weaknesses.
- Lesson for **evaluation**, not runtime: test against a *league* of diverse opponents, including deliberately
  exploitative ones.
- Our local league is all our own lineage (E20), which is why fight changes never showed locally. We cannot train
  exploiters in two weeks, but we can **build 2–3 cheap scripted "style" opponents**: rusher, perma-recall turtle,
  cluster farmer. VALIDATION_PLAN.md.

## 5. Operations research: routing, assignment, allocation

**Team orienteering problem with time windows (TOPTW)** [B15, B16].
- Multiple vehicles collect profits at nodes within time windows, maximising total profit under a time budget.
- Mapping: champions are vehicles; camp groups are nodes with profit (gems + λ·gold) and time windows (alive from
  `respawn_round`). Service time is the clear time (depends on crew) plus capture.
- **Differences:** nodes *recur* (respawn); service time depends on how many vehicles serve together; there are
  adversaries and stochastic loss.
- TOPTW heuristics (insertion, local search) are fast. A **greedy insertion with one-step lookahead** captures most of
  the value at our scale (≤112 nodes, ≤5 vehicles). That is TEP.

**Assignment and auctions.**
- Bertsekas' auction algorithm [B17]: ε-complementary slackness; equivalent to ε-relaxation min-cost flow.
- CBBA (Choi, Brunet, How) [B18]: decentralised bundle auctions under inconsistent situational awareness, converging
  to conflict-free assignments with a 50% optimality bound.
- **Mapping.** Our champions have *inconsistent beliefs* (unshared vision) and can exchange only 7-bit claims. A
  **sequential single-item auction through claims** is a degenerate one-round CBBA. Each champion bids its own best
  task given others' published claims, and conflicts resolve by claim priority (turn order). That is enough and costs
  O(F·G).
- CBBA's robustness to inconsistent awareness is the property we need. Its multi-round consensus is not available
  within one turn and is unnecessary at 3–5 agents.

**Optimal stopping: the burglar problem** [B19, B20].
- Each period adds loot; capture loses everything; decide when to retire. There is a cutoff wealth level.
- Mapping: carrying gems is exactly this. Each capture adds to the bag, and death loses it to the enemy.
- **Bank when** `bag × hazard(t) × (time to next bank opportunity) ≥ cost of the bank trip`. A wealth threshold
  that depends on hazard (enemy pressure) and altar distance follows (ALGORITHM_SPECIFICATIONS §4).

**Queueing and bottleneck analysis** [EXT, general].
- Each objective is a server: a capture-bound cluster has service time `capture_time`; a damage-bound camp has
  service time `HP / DPS`.
- **Bottleneck view:** income is limited by champion-time. Every round spent walking, waiting for a respawn, dead or
  channelling is lost capacity. Our time-use measures (dead 2×, travel more) quantify the loss.

## 6. Game-AI architecture patterns

- **Utility AI (Infinite Axis Utility System, Dave Mark)** [B21]. Score each candidate action by multiplying response
  curves over considerations. Data-driven and debuggable; used for NPCs, squads and armies.
  - Mapping: EE and TEP are utility systems, but our utilities are **derived from game quantities** (gem-equivalents)
    instead of designer curves. This avoids arbitrary weights.
- **Influence maps** [B22]. A grid summarising spatial features: threat, control, history and predictions.
  - Mapping: the per-tile enemy-reach "danger" used by micro and pathing, and the group-level pressure used by TEP.
  - A full-map influence grid every turn is too expensive (100×100 tiles, ~41k fuel already used). Use a local 17×17
    window around the champion, plus per-group scalars.
- **Behaviour trees and hierarchical state machines** [EXT].
  - Good for *execution* sequences (go to altar, then tribute, then recover).
  - Poor for *arbitration*: hidden priorities are exactly v76's override ladder.
  - Use a small explicit state machine per *role*, and a single utility arbiter for *choices*.
- **Simultaneous-move search (Bošanský, Lisý, Lanctot et al.)** [B23]. Exact and sampling algorithms for zero-sum
  simultaneous-move games.
  - Our turns are sequential per champion but effectively simultaneous per round.
  - **Rejected for runtime:** a branching factor in the hundreds per champion, and partial observability. Use only
    offline, e.g. to sanity-check EE on toy 1v1 or 2v2 states.

## 7. Methods evaluated and rejected or deferred (and why)

| Method | Decision it could improve | Why not now |
|---|---|---|
| MCTS / UCT at runtime | Fights | Fuel: playouts at about 1k ops per step × hundreds of playouts exceed 100k. Model inaccuracy; tsearch evidence (E27) |
| Alpha-beta / minimax | 1v1 duels | Simultaneous moves and hidden information; tiny benefit over the analytic model |
| MARL / PPO | Everything | No compute and time; earlier PPO runs learned nothing (memory: first role experiment, top-team long run) |
| Imitation of top teams | Intent | v83 −65; mimic 0/120; labels lack value context |
| Mixed-integer or constraint programming | Assignment | Overkill at ≤5 agents; greedy plus regret is near-optimal at this scale |
| Full influence-map pathing | Movement | Fuel; v76 distance fields plus a local danger window suffice |
| Policy distillation from search | Fights | Requires an offline search oracle we don't have. Post-finals idea: distil an offline EE+search into tables |

## 8. Added for the clean-slate plan

- **Wasmtime fuel semantics [B24].**
  - Fuel is consumed per guest wasm operator, with configurable operator costs. Exhaustion traps or yields; cambc
    suspends and resumes.
  - Work inside host imports is not metered by Wasmtime itself. The engine *can* charge it (cambc exposes
    `fuel_adjust`).
  - Implication: engine-side primitives (distance fields, BFS, shadowcast, `move_towards`) may be far cheaper
    than doing the same work in guest code. CT-1 measures this on Day 1, and the fuel plan has two scenarios.
- **Release cadence [B25].** cambc 2.1→4.0 shipped within 12 days. Sprint 3 (4.0.0) changed item rules and
  champion stats. A clean-slate bot must read every value at runtime and re-run its conformance suite on each
  release.
- **No public engine source [B26]**, so the conformance suite is the only way to settle engine questions.
