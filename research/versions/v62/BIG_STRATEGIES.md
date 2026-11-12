# Big strategies: learning the meta, reinforcement learning, and what can actually move us (2026-10-26)

Claude Code, second research report (the first is `STRATEGY_RESEARCH.md`, incremental fixes). This one asks
the bigger question: what approach, learned or hand-built, can take us from 21/120 against the top 12 to
competitive? It draws on winners of comparable AI competitions (Kaggle Lux AI, Halite, microRTS, Generals.io),
large-scale game AI (AlphaStar, OpenAI Five), imitation-learning theory, and other CAMBC 2026 teams' public
analyses. All of it is checked against the hard limits of our game.

## 0. Bottom line

1. **Reinforcement learning inside the bot will not work here.** Every RL winner we found ran a network of 5-20M
   parameters with 100 ms to 2 s per turn, usually on GPUs, and trained for weeks of GPU time against a fast
   simulator. We get 100k fuel (about 100k wasm instructions) per champion turn, have no fast simulator, and have
   23 days left (finals 18 Nov). Our own policy-v2 network already showed this: 0 gems, fuel admission refused
   98% of moves.
2. **Imitation learning works, at the level of decisions, not whole policies.** Lux AI Season 3's 3rd and 9th
   places and the #1 Generals.io agent were built from top players' replays. We can do the same where it fits:
   fit *small* models to the top teams' individual decisions (draft, items, opening route, when to engage, whom to
   hit, when to leave, when to bank) and compile them into the C++ bot as tables and weights. These cost tens of
   instructions per turn.
3. **The data is free, fresh and huge.** Any team's ranked matches are listable and downloadable through our CLI
   (`cambc matches list --team "<name>"`, then `matches download`). Intercontinental Fish alone played 100 ranked
   games in 3.2 hours today, all against other top-12 teams. That is roughly 4,000+ top-vs-top games a day.
4. **The big break is a "meta compiler"**: a pipeline that crawls top-vs-top games every day, decodes them, fits
   the decision models, regenerates the bot's tables, and ships through the ladder-duel gate. The meta then
   updates itself as the top teams change.
5. **One structural rewrite is also needed: the fight controller.** Another CAMBC team's measurements of 1,317
   top-team engagements give an explicit rulebook (section 4). Our `handle_enemies` is about 1,000 lines of
   layered, mostly disabled switches. Replace it with one controller that implements the measured rules and is
   driven by the learned engagement model.

## 1. The constraints that decide what is possible

| Constraint | Value | Consequence |
|---|---|---|
| Fuel per champion turn | 100k (2x on the first play turn) | No large network in the bot. A logistic model over 10-20 features costs well under 1k. |
| Draft fuel and memory | 10x fuel on the first draft turn; 1,024 bytes of draft memory, read-only afterwards | Room to plan the opening (route, roles) and broadcast it. |
| Shared memory | 8 bytes, all used (6 claim slots + sighting) | Team coordination must reuse claim codes (fight orders 112-118 exist). |
| Engine | Deterministic; reruns against an unchanged bot replay identically (chamyao) | Paired ladder tests are low-noise; top-team bot changes are detectable. |
| Local throughput | about 4 games/s on 20 cores (168 games in 40 s) | Fine for regression checks and ES on a few parameters; not for deep RL. |
| Local opponents | only our lineage; their predictions don't match the ladder | Self-play cannot be the fitness signal (sections 2 and 6). |
| Ladder testing | 50 match groups (250 games) per rolling hour; `ladder_duel.py` pairs two versions | The only trustworthy fitness: about 2 candidates/hour, about 48/day. |
| Top-team data | about 4,000 top-vs-top ranked games/day, replays downloadable | Enough to fit decision models per map and per hero. |
| Time | 23 days to finals | Weeks, not months. No multi-week GPU training. |

## 2. What won comparable competitions, and what transfers

| Competition | Winning approach | Compute | Transfers to us? |
|---|---|---|---|
| Lux AI S1 (2021) | Deep RL: IMPALA + UPGO, 24-block ResNet (~20M params), reward shaping then sparse, teacher distillation; beat its own rule-based bot within a month | 2 GPUs, overnight runs; 2-2.5 s inference per turn | No (inference budget) |
| Lux AI S3 (NeurIPS 2024) | 3rd and 9th place: **imitation learning on top teams' replays** (UNet), replaying each step with only the agent's own view | GPU | **Yes, as decision-level IL** |
| Halite IV (2020) | 1st: explicit planning: task assignment, opponent collision models online | CPU | Yes: planning plus opponent models |
| microRTS (IEEE CoG 2023) | First DRL winner: PPO self-play, then fine-tuning against the prior winners; per-map transfer learning | about 70 GPU-days, 1.5B steps; 100 ms/turn | No (compute); the per-map lesson does |
| Generals.io | **Behaviour cloning on expert replays, then self-play PPO**: #1 on the ladder, 199-70 vs the top 2 humans | 260B steps on a simulator 10,000x faster than the game | Partly: BC yes, RL needs a fast simulator we lack |
| OpenAI Five (2018-19) | Large-scale self-play; humans kept net worth even by farming spread out, but lost every big team fight | thousands of GPUs | The lesson: fights decide, not farm |
| AlphaStar | Supervised from replays, then a **league** with main exploiters and league exploiters; plain self-play keeps refining narrow strategies | thousands of TPUs | The league idea, applied to ladder testing |
| MIT Battlecode | Hand-written heuristics: weighted micro scoring over candidate moves, both attack/move orders, follow-first grouping, mass scrimmage A/B | none | **Yes, directly** |
| CAMBC 2026, chamyao | FunSearch with Claude over a policy grammar, exact simulator, genome evolution | EC2 | **A warning**: their sim league predicted 75-93% wins; real games against teams +100 above them gave 30% |

**What transfers**: (1) imitation from top replays, at whatever granularity the runtime budget allows; (2) planning
in the draft turn; (3) a league or ladder fitness rather than self-play; (4) hand-built micro scoring. **What does
not**: big networks at inference, and RL that needs billions of simulated steps.

## 3. Why our earlier learning attempts failed, and how to avoid it this time

- **policy-v2 (BC on 7.3M top-team decisions)** scored 0 gems. The runtime refused 98% of move decisions for
  fuel, and the bank head stayed at the majority-class baseline. Two causes: a network too big for the budget,
  and whole-policy cloning. Small errors move a cloned policy into states its data never covered, and errors
  compound (Ross, Gordon & Bagnell 2011, DAgger).
- **The camp/draft/danger nets** (A2_CAMPNET, A2_MLDRAFT, UB_DANGER) showed no measurable effect, but they were
  judged only in self-play, which we now know cannot see ladder effects.
- **Ladder-fitted heuristics** (`UB_CAMPFIX` camp choice from ladder replays, `UB_QCAMP` offline-RL camp values)
  exist and are off, again rejected by self-play.

**This time**: small models, one decision each, inside the existing controller (which keeps the rest of the
behaviour stable, reducing covariate shift); fitted on *current* top-vs-top data (engine 2); judged by ladder duels.

## 4. The top teams' measured rulebook (from a public CAMBC analysis)

chamyao/battlecodecamb, branch `analysis/sprint1`: `docs/TOP_TEAMS_RULES.md` and `TOP_TEAMS_FIGHTS.md` analyse
1,317 engagements by the top 9 + vc? and 634 decisive fights (engine 1.0.3, 24 Oct). Third-party, older engine,
so re-measure on engine 2 before trusting the exact numbers. Their own bot was rank 410 at the time and went
0-50 against these teams.

1. **Engage healthy, at vision range, with numbers.** At the first hit their HP is 0.90-1.00 (median), the
   target's 0.68-0.87. They start walking at 7-9 tiles and arrive within about 5 rounds. Odds 2v1 by default.
   Early (before R150) 85-89% of our deaths come against 2+ of theirs, with no stat gap.
2. **Target the closest visible enemy** (87-94%), ties to the lowest HP.
3. **Open with the reach ability on the first hit turn** (0 rounds to the first cast): Heart/Vendetta dash in from
   3, Marcella damage spell from 4, Ryth AoE stun from 4, Prism AoE from 5.
4. **Double-hit every round the reset is ready**: Vesper `basic > reset > basic` (45% of openings), Vendetta and
   Ryth the same. "Four basic hits a round" when two resets line up.
5. **Short chase** (0-2 tiles; 3-6 for Heart/Ryth on kills).
6. **Leave while healthy**: HP at the end of an engagement 0.77-0.94; recall within 10 rounds after 37-47% of
   engagements (Prism 82%: burst once, go home). Fish walks 5 tiles away at half HP, and never recalls within 3
   tiles of a chaser.
7. **Fight in their own half** (62% of engagements, 78% of first fights): our champions walk into them while farming
   their side or going to altars.
8. **Stack one stat per carry**: Fish's Vesper had 36 strength points by round 192 (235 per basic attack vs our
   50-55). willow's Heart had 412 focus (635-damage dash). After round 400, killer vs victim item points 58 vs 12.
9. **Our failure pattern** (identical to our own data): victims ignore enemies visible for 5 rounds, keep hitting
   camps (34%), hit the shielded Heart instead of the carry killing them, and melee champions stand idle against a
   kiting Vesper.

Their sim league predicted 75-93% wins for their bot; real games against teams +100 above them gave 30%. This
is the same miscalibration we found locally.

## 5. Options, ranked

| # | Option | Expected impact | Feasibility in 23 days | Risk |
|---|---|---|---|---|
| **A** | **Meta compiler**: daily top-vs-top crawl, then decision models, then generated C++ tables | Large (copies what wins, continuously) | High: data, decoder and duel gate exist | Medium: decision models must play well together |
| **B** | **Fight controller rewrite** with the measured rulebook + team focus target + spells-ready engagement | Large (fights are the gap: kills 4 vs 12) | Medium: a rewrite of `handle_enemies` | Medium: regressions; gate by duels |
| C | Per-map opening books (first 150 rounds per map, from top teams; broadcast in draft memory) | Medium-large (gold gap starts at R100: 295 vs 353) | High: 70 known pool maps | Low |
| D | Stat-stacking carry build + carry funnel | Medium | High (switches exist) | Low |
| E | Draft from top-vs-top win rates per map | Medium, only once B/D make us play those heroes well | High | Medium (Vesper-first lost -90 locally) |
| F | ES/CMA-ES on a few parameters, ladder fitness | Small-medium | Medium (48 evaluations/day) | Low |
| G | RL in a simulator against top-team clones | Unknown | Low (needs an exact engine-2 simulator plus clones) | High |
| H | Exploiting deterministic opponents | Uncertain, fragile | Medium | High: bots change; not for the tournament |

**Recommended: A + B together, with C and D as the first outputs of A.**

## 6. Design: the meta compiler (option A)

**Crawl** (`tools/meta/crawl.py`, new): every 2-4 hours, for each current top-12 team, `matches list --team
<name> --kind ranked`. Keep games where both sides are top-12 (dedupe by match id), and download replays into
`artifacts/local-only/meta/<date>/`. About 4,000 games/day; sample 500-1,000 per day if bandwidth is limited (the
API rate-limits; our fetcher already retries).

**Decode** (engine 2): extend `tools/replay/fight_review.mjs` and `actor_ledger.mjs` into per-champion-turn records
with features from that champion's own view. `decode_replays.mjs --perspective` does this for engine 1.0.3 only;
port it to the engine-2 decoder (`engine.mjs` already supports 2.0.0).

**Decisions to fit**, each with features our bot already computes at runtime:

| Decision | Label from replays | Model | Runtime cost |
|---|---|---|---|
| Draft | picks per map and team size, win-rate weighted | frequency/win-rate table per map | draft turn only |
| Items | purchase sequence per hero | most common winning sequence per hero | lookup |
| Opening | first 150 rounds of camp targets per slot and role, per map | route table per map (top teams' modal route) | lookup |
| Engage | engagement start yes/no per champion-round with an enemy in vision | logistic regression (hp fraction, allies5, enemies5, spells ready, item-point ratio, distance, own half, carried gems) | about 20 multiply-adds |
| Target | which visible enemy was hit first | conditional logit over enemies (distance, hp, threat/dps, is carry, shielded) | about 10 per enemy |
| Disengage | engagement end / walk-away / recall | logistic regression | about 20 |
| Bank | tribute trip start | logistic regression (bag, altar distance, enemies seen, round) | about 15 |
| Camp choice | next camp group chosen | conditional logit (`UB_CAMPFIX` already has the plumbing) | about 10 per group |

**Fit and compile** (`tools/meta/fit.py`, `tools/meta/emit_header.py`): write `src/meta_tables.h` with a data
stamp. A bot build includes a fixed header, so a release is reproducible. Optional: a VIPER-style distillation of
any larger model into a depth-3 or 4 decision tree.

**Validate offline, without self-play**: hold out the latest day; report each model's accuracy and calibration
against the top teams' actual decisions (an imitation score, not a win rate). Then local safety net (faults, fuel).
Then a ladder duel against the current live version on a top-12 plan.

**Refresh**: nightly. If a top team's bot changes (deterministic reruns diverge), the next day's tables follow it.

## 7. Design: the fight controller (option B)

One function replaces the stack of switches in `handle_enemies`. Each turn, for each candidate (move tile x action
order x target), compute a score from game constants (SPAARK-style): expected damage dealt (with resets and ready
spells), expected damage taken from every enemy that can reach the tile next round (with their ready spells),
kill bonus, distance to the team focus target, own-half bonus, spawn-tile healing. Then add the rulebook:
- **Engage gate**: the learned engage model (or rule 1 until it exists): healthy, at least equal local numbers,
  at least one damage spell or stun ready.
- **Opening**: if this is the first hit turn, cast the reach ability first.
- **Double hit**: basic > reset > basic whenever a reset is ready and a target is in range.
- **Team focus**: publish the target in our claim slot (fight orders 112-118); allies within 8 weight it heavily.
- **Leave rule**: at about 0.8 HP when not clearly winning, walk away (never recall within 3 tiles of a chaser).
  Stop farming as soon as an enemy is visible within 8.
- **Melee vs kiting ranged**: dash in or walk out this turn; never idle.
- **Territory**: don't farm the enemy half when their champions are unaccounted for; fight in our half.

Fuel: about 9 tiles x 2 orders x 2-3 targets x a few enemies is a few thousand operations, within budget if the
expensive parts (threat maps) are computed once per round.

## 8. Twenty-three-day plan

| Days | Work | Gate |
|---|---|---|
| 1-3 | Crawler and engine-2 per-champion decoder; first 2,000 top-vs-top games; re-measure the rulebook on engine 2 | rulebook numbers reproduce within ±10% |
| 2-6 | Fight controller (B) with the rulebook; team focus target; spells-ready gate | duel vs v61 on `duel_top1.json`: paired margin > +50 |
| 4-8 | Meta tables v1: items, draft table, opening routes for the 70 pool maps (C, D) | duel: margin > +50 |
| 7-12 | Learned engage/target/disengage/bank models wired into the controller | imitation accuracy > rule baseline; duel positive |
| 10-20 | Nightly meta refresh; overnight duel queue (2 candidates/hour); ES on the few remaining thresholds (F) | each release beats the previous on a fresh top-12 plan |
| 20-23 | Freeze: no last-minute changes (SPAARK lost twice that way); final release the best of the last 3 duels | — |

## 9. Risks and how to handle them

- **Pieces fit separately may not combine well.** Keep the existing controller as the backbone, add one learned
  decision at a time, and duel each step (2 per hour is enough).
- **The meta of top-vs-top games may not be the best play against us.** Weight training data by winner side, as
  Orbit Wars imitation entries did, and include top-team games against mid-ladder teams.
- **Decoder drift**: if `cambc` updates, the engine-2 asset hashes change; the loader pins hashes and fails loudly.
- **Fuel**: every new block measured with the existing fuel probes before a duel.

## Sources

- [Toad Brigade, Lux AI 2021 (IsaiahPressman/Kaggle_Lux_AI_2021)](https://github.com/IsaiahPressman/Kaggle_Lux_AI_2021)
- [Lux AI Season 3: imitation learning, 3rd place](https://www.kaggle.com/competitions/lux-ai-season-3/writeups/adg4b-imitation-learning-3rd-place-solution)
- [Lux AI Season 3: 9th place](https://www.kaggle.com/competitions/lux-ai-season-3/writeups/team-k-9th-place-solution)
- [Lux AI Challenge](https://www.lux-ai.org/)
- [shmyak-ai/lux-ai (imitation + self-play)](https://github.com/shmyak-ai/lux-ai)
- [Halite by Two Sigma (discussion)](https://www.kaggle.com/c/halite/discussion)
- [Orbit Wars: top-50 imitation learning solution](https://www.kaggle.com/competitions/orbit-wars/writeups/top-50-imitation-learning-solution)
- [A Competition Winning Deep RL Agent in microRTS (arXiv 2402.08112)](https://arxiv.org/html/2402.08112v1)
- [Superhuman AI for Generals.io Using Self-Play RL (arXiv 2606.23348)](https://arxiv.org/pdf/2606.23348)
- [Artificial Generals Intelligence (thesis)](https://dspace.cuni.cz/handle/20.500.11956/202815)
- [Reinforcement learning, Generals.io (Straka)](https://kam.mff.cuni.cz/~straka/blog/generals.html)
- [AlphaStar: grandmaster level using multi-agent RL (DeepMind)](https://deepmind.google/discover/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/)
- [TStarBot-X: league training study (arXiv 2011.13729)](https://arxiv.org/pdf/2011.13729)
- [A Robust and Opponent-Aware League Training Method for StarCraft II (NeurIPS 2023)](https://neurips.cc/virtual/2023/poster/70220)
- [AlphaStar Unplugged: offline RL (arXiv 2308.03526)](https://arxiv.org/pdf/2308.03526)
- [OpenAI Five (alignment newsletter commentary)](https://www.lesswrong.com/posts/WCpv3KH7hvRqLTKqw/alignment-newsletter-19)
- [Ross, Gordon & Bagnell 2011, DAgger (arXiv 1011.0686)](https://ar5iv.labs.arxiv.org/html/1011.0686)
- [DART: noise injection for robust imitation learning](https://bair.berkeley.edu/blog/2017/10/26/dart)
- [VIPER: verifiable RL via policy extraction (arXiv 1805.08328)](https://arxiv.org/pdf/1805.08328)
- [The Art of Drafting: MCTS hero recommendation (arXiv 1806.10130)](https://arxiv.org/pdf/1806.10130)
- [Match outcome prediction with team-fight models (SDU)](https://www.sdu.dk/en/forskning/sdumetaverselab/news/predicting-dota-2-esports-match-outcomes-with-recurrent-neural-networks)
- [Churchill & Buro 2013, Portfolio Greedy Search](https://www.cs.mun.ca/~dchurchill/publications/pdf/combat13.pdf)
- [Cole, Louis & Miles 2004, GA-tuned bot parameters](https://www.cse.unr.edu/~miles/papers/cec2004fps.pdf)
- [chamyao/battlecodecamb (STRATEGY.md; branch analysis/sprint1: TOP_TEAMS*.md, GAP_LIST.md)](https://github.com/chamyao/battlecodecamb)
- [Battlecode 2025 Postmortem, SPAARK](https://battlecode.org/assets/files/postmortem-2025-spaark.pdf)
- [Battlecode 2023 Postmortem, Don't @ Me](https://battlecode.org/assets/files/postmortem-2023-dont-at-me.pdf)
- Earlier report: `research/v62/STRATEGY_RESEARCH.md`
