# Competition game bots under tight compute budgets: techniques that won, and their relevance to CAMBC

Scope: Battlecode (MIT), microRTS (IEEE CIG/CoG), StarCraft BW AI competitions (AIIDE), Halite (Two Sigma / Kaggle), Lux AI (Kaggle), Google AI Challenge (Ants 2011, Planet Wars 2010), CodinGame contests, and AlphaStar. CAMBC context: C++ to WASM, ~100k instructions per champion turn (10M on the first draft turn), 3v3 to 6v6, 8 bytes of shared team memory, no runtime network, fast offline simulator (~0.3 s/game).

Budget comparison: Battlecode 2026 allowed 17,500 Java bytecodes per robot per turn ([GST 2026](https://battlecode.org/assets/files/postmortem-2026-generalized-strokes-theorem.pdf)), and historically about 7,500 to 15,000 ([The Kragle 2025](https://battlecode.org/assets/files/postmortem-2025-the-kragle.pdf)). A ~100k WASM instruction budget is the same order of magnitude, a few times larger, so Battlecode practice transfers almost directly. microRTS allows 100 ms per step ([Goodfriend 2024](https://arxiv.org/pdf/2402.08112v1)), which is far more.

---

## Q1. Battlecode winners: what made the difference (pathfinding, bytecode, communication, micro, precomputation, macro), and how did they communicate through tiny shared arrays?

### Takeaway
In Battlecode, the big wins came from micro (fight movement). The "XSquare micro" is copied across the field: score all 9 move options with a small struct of features and compare them with a hand-ordered `isBetterThan`. Next came communication of a few high-value facts (battlefront or combat location, symmetry, enemy sightings) packed into 12-bit coordinates. Pathfinding settled on Bug Nav or a hybrid of Bug Nav and unrolled BFS, and was seldom what decided games. Teams improved macro mainly by copying higher-ranked teams found through scrimmages.

### Cited Findings
**Micro decides games**
- Gone Fishin' (2nd place in 2023) wrote that an improved macro strategy "might increase our win rate by 5%, but micro can do a 30%-50% increase." They tuned it by playing old versions of their bot repeatedly. [Gone Fishin' 2023](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf)
- XSquare micro has three parts. (a) `doMicro`: trigger it when enemies are visible, extensible to low HP or remembered enemies out of vision. (b) `computeMicroArray`: heuristic info for all 9 options (8 adjacent moves plus staying), with loops unrolled. (c) `MicroInfo`: features such as the number of nearby enemies and the distance to the closest enemy, compared pairwise by `isBetterThan`. It only covers movement. Attack targeting stays simple: "target the lowest hp enemy possible, attack whenever possible". "Nearly every other top team has benefited from copying the XSquare micro." [The Kragle 2025](https://battlecode.org/assets/files/postmortem-2025-the-kragle.pdf)
- GST (2nd place in 2026) based their micro on "XSquare Style Micro": evaluate each of the 9 squares on passability and proximity to allies, enemies and neutral cats, then decide with a chain of if/else comparisons. [GST 2026](https://battlecode.org/assets/files/postmortem-2026-generalized-strokes-theorem.pdf)
- Cout for Clout (1st in the high-school division and 2nd on the combined leaderboard in 2024) copied XSquare's 2022 micro in about 20 minutes. Their rating went from the 1850s to the 1950s and later past 2000. Their earlier switch to fully aggressive micro had already gained 130 rating points (1720 to 1850). [Cout for Clout 2024](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf)
- Cout for Clout's micro rules, verbatim in substance:
  - Bucket behaviour by cooldowns and ranges.
  - Move toward lower-HP allies and toward lower-HP enemies.
  - Move toward stunned allies.
  - "Move backwards if the ally behind you has more health than you."
  - Move toward a combat location (Lanchester's laws).
  - Don't clump too much.
  - "Chicken micro" when `health <= 450 + (max(attackLvl, healLvl) - 3) * 150`: avoid enemies and switch to healing.
  - Healer micro: avoid enemies and move toward allies.

  [Cout for Clout 2024](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf)
- Gone Fishin' kiting (2023): launchers attack every turn but move every 2 turns. After attacking, move to the tile that minimizes the number of enemy launchers that can see you, and cache the enemy position so you can re-engage. Result: 3 attacks for every 2 the enemy lands per 4 turns. "ALWAYS kiting back after an attack is better" than conditional kiting, which Super Cow Powers (Sprint winner) corroborated. Tie-break: prefer orthogonal over diagonal moves to keep formation. [Gone Fishin' 2023](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf)
- Gone Fishin' target priority: for each enemy, count the friendlies that can hit it now and compute turns-to-kill from HP divided by friendly attacks. Prefer targets you can one-shot. They chase only when no target is attackable, the target is not a combat unit, or "our team is high (have 2+ more launchers than the other side)". [Gone Fishin' 2023](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf)

**Grouping without communication**
- Gone Fishin' tried a leader/follower scheme (follow the lowest-ID visible ally). They removed it because followers blocked the leader.
- Their final scheme ran for 10 turns after each fight. Pick a visible ally that is closest to the enemy HQ and highest in HP, and move until adjacent. Then, if lower in HP, stop; if higher, continue toward the objective. This keeps the low-HP unit behind.
- Spawning the first 4 launchers in a square with the earliest-spawned outermost (units act in spawn order) "wins about 2/3 of the game" against the same bot without it.

[Gone Fishin' 2023](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf)

**Numbers and concentration (Lanchester)**
- Cout for Clout ran a "squadron" system that summons units to combat locations. Their reason: under Lanchester's square law, one extra unit adds much more to a large army than to a small one.
- They tested "sitting duck" defence by playing 47 against 50 units, and the 47-unit side "lost 90% of the games."
- They replaced 3 static defenders with 1 unspawned unit that reacts to a spawn-pad intrusion signal.

[Cout for Clout 2024](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf)
- The Kragle: communicating the nearest battlefront "gave massive improvements", cutting idle exploration. Units "would always have knowledge of the nearest battlefront". [The Kragle 2025](https://battlecode.org/assets/files/postmortem-2025-the-kragle.pdf)

**Communication with tiny shared arrays**
- 2023 shared array: 64 integers of 16 bits each. Locations take 12 bits because maps are at most 60x60. Gone Fishin' stored symmetry candidates (scouts eliminate them), the closest 5 wells of each resource, carrier counts, and a congestion flag. Each unit keeps a local copy and syncs it when it can write. [Gone Fishin' 2023](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf)
- "No thoughts head empty" (2023) also describes 64 items of 16 bits each. Switching message storage from an ArrayList to a fixed-length array saved about 2,000 bytecode. [No Thoughts 2023](https://battlecode.org/assets/files/postmortem-2023-no-thoughts.pdf) (search-snippet level)
- Just Woke Up (2025) encoded messages in 32 bits: a 3-bit type and 12 bits for x,y. [Just Woke Up 2025](https://battlecode.org/assets/files/postmortem-2025-just-woke-up.pdf) (search-snippet level)
- GST (2026) barely used the shared array, keeping only king locations, symmetry, mines and formation coordinates in it. They used local "squeaks" with a 3-bit type header. During micro, every unit squeaked its HP, its nearest enemy's HP, and that enemy's direction and location, to build a local picture. This went over bytecode in crowded fights, which they judged "a very worthy tradeoff". [GST 2026](https://battlecode.org/assets/files/postmortem-2026-generalized-strokes-theorem.pdf)
- Cout for Clout (2024): the shared array was split into fixed sections (ally status parsed every turn) plus a message queue for rare message types. The queue needs no slot clearing, saving 75 bytecode per write. [Cout for Clout 2024](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf)

**Pathfinding and bytecode**
- Top teams use Bug Nav when passability is binary and greedy movement when it is variable. Many top teams also use "unrolled" BFS or Dijkstra, with code generated by scripts (for example Just Woke Up's Python generator). Loop unrolling means writing every iteration out by hand, which looks "horrific" but is bytecode-efficient. [The Kragle 2025](https://battlecode.org/assets/files/postmortem-2025-the-kragle.pdf)
- GST's "BugBFS": run unrolled BFS in a fixed radial order. If it makes no progress, hand control to stack-based Bug Nav (from Gone Fishin' 2023), which simulates left and right turns and picks the one closer after N steps, plus loop detection on turn locations. Switch back to BFS once it can make progress again. [GST 2026](https://battlecode.org/assets/files/postmortem-2026-generalized-strokes-theorem.pdf)
- The Kragle's custom pathfinder wasted time. "Traditional BugNav from XSquare's codebase was a more reliable solution." They updated the map incrementally, touching only newly visible tiles, to save bytecode. [The Kragle 2025](https://battlecode.org/assets/files/postmortem-2025-the-kragle.pdf)

**Macro and code structure**
- GST: "macro is best improved by scrimmaging against good teams, and copying what they do". They queue scrimmages against teams ranked above them, reverse-engineer their macro (easier than micro), and keep what helps. Their unit-count "magic numbers" came from this. [GST 2026](https://battlecode.org/assets/files/postmortem-2026-generalized-strokes-theorem.pdf)
- The Kragle: "the easiest way to improve is to copy what they do better than you". Their late discovery that other teams never refilled paint taught them to "pay careful attention to other team's strategies". They recommend a Goal Priority Queue with `shouldStartGoal` / `executeGoal` / `shouldStopGoal` per goal, instead of tangled if-statements, so that fights do not erase long-term tasks. [The Kragle 2025](https://battlecode.org/assets/files/postmortem-2025-the-kragle.pdf)
- GST used a Strategy pattern: a State Updater picks a singleton Behavior (micro, explore, scavenge) each turn. [GST 2026](https://battlecode.org/assets/files/postmortem-2026-generalized-strokes-theorem.pdf)

### Inferences
- An XSquare-style 9-candidate scorer runs comfortably in ~100k instructions. CAMBC's movement set may differ, but the pattern is: enumerate every legal move tile, compute about 6 to 10 features, and compare them lexicographically. The trigger can include "low HP" and "remembered enemies", so retreat runs through the same scorer and is not a separate flee routine.
- With only 8 bytes, the highest-value shared facts in Battlecode were a battlefront or combat location and an enemy sighting. One coordinate (12 to 16 bits) plus a timestamp or type field fits in 3 to 4 bytes.
- The "move backwards if the ally behind has more health" and "low-HP unit stops behind the higher-HP one" rules directly address dying alone. They make retreat go toward allies, not just away from enemies.

### Gaps
- I could not read the official winners' postmortems for Battlecode 2023 (Producing Perfection), 2024 or 2025. The best-documented sources are 2nd-place teams and XSquare-derived code. XSquare's micro source file was not fetched, so its exact feature ordering is not cited here.

---

## Q2. Micro (fight) heuristics that won: kiting, focus fire, retreat thresholds, micro scoring, simultaneous moves

### Takeaway
The winning recipe is consistent: focus fire on the lowest-HP target or the one with the fewest turns-to-kill, always kite back after attacking when cooldowns allow, apply an HP-threshold retreat ("chicken") that moves toward allies or healing, and fight only with a local numbers advantage. Simultaneous moves are handled by scoring tiles on worst-case enemy threat (how many enemies can hit or see a tile), not by game-tree search.

### Cited Findings
- **Focus fire:** "target the lowest hp enemy possible, attack whenever possible" (the XSquare convention) ([The Kragle 2025](https://battlecode.org/assets/files/postmortem-2025-the-kragle.pdf)). Gone Fishin' prioritised one-shot kills, then fewest turns-to-kill ([Gone Fishin' 2023](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf)).
- **Kiting:** move to the tile that minimizes the number of enemies that can see or attack you after you act, and do it always rather than conditionally ([Gone Fishin' 2023](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf)).
- **Retreat threshold:** Cout for Clout's level-scaled HP threshold, `450 + (lvl - 3) * 150`, triggers avoid-enemies and heal mode. Low-HP units move behind healthier allies ([Cout for Clout 2024](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf)). Gone Fishin' sent injured carriers (at or below 120 HP) to friendly islands to heal, which produced "a favorable situation where our launchers fight and heal around friendly islands" ([Gone Fishin' 2023](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf)).
- **Engage only with an advantage:** chase only with 2 or more extra units ([Gone Fishin' 2023](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf)). Concentrate at combat locations, citing Lanchester's square law ([Cout for Clout 2024](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf)).
- **Threat-aware positioning against neutral threats:** GST avoided the "cat path" (the 2 to 3 tiles in front of a cat), but weighted enemy avoidance above cat avoidance ([GST 2026](https://battlecode.org/assets/files/postmortem-2026-generalized-strokes-theorem.pdf)).
- **Combined action enumeration:** GST scored every reasonable move + turn + throw combination by its outcome (hit cat, enemy, wall or ally, or leave vision). They found that some combinations were net-negative and pruned them ([GST 2026](https://battlecode.org/assets/files/postmortem-2026-generalized-strokes-theorem.pdf)).
- **How micro is improved:** "by far the best way to improve micro is to watch a lot of games", following individual units into combat and fixing each "stupid decision" in a way that minimally affects good decisions ([GST 2026](https://battlecode.org/assets/files/postmortem-2026-generalized-strokes-theorem.pdf)).
- **Ants 2011:** the winner xathis kept combat simple and local, treating "all enemies the same, even in combat situations". He partitioned the board into local combats so fight code ran on small groups. A competitor (about #300) who wrote minimax combat said it "only ran when small numbers of ants were fighting" and that he "spent too much time writing the combat code for the benefit". The winner's strength was "a lot of little pieces done well". [LessWrong Ants post-mortem](https://www.greaterwrong.com/posts/ELCsD7MYaqnkarPBi/ai-challenge-ants-post-mortem); [i-programmer](https://i-programmer.info/news/105-artificial-intelligence/3534-ants-ai-challenge-winner-announced.html)
- **Planet Wars 2010:** bocsimacko (#1) was "far stronger than #2". It was characterised as strategically brilliant but tactically sloppy, and it "understands suppressing attacks". [satirist.org Planet Wars styles](https://satirist.org/ai/planetwars/playing-styles.html)

### Inferences
- For CAMBC's "dying alone while fleeing", Battlecode suggests three changes:
  1. Retreat toward allies, using an ally-weighted score that also accounts for threat count, not distance from enemies alone.
  2. Trigger retreat earlier, using an HP threshold scaled by level or items.
  3. Never chase without a numbers lead.
- These are cheap rule changes evaluated inside the same per-tile scorer.

### Gaps
- No source found gives a winner's exact handling of simultaneous-move prediction beyond threat-count tiles. The xathis write-up at xathis.com, which has the details of his local combat, was not retrieved.

---

## Q3. Search under tight budgets: when does search beat rules?

### Takeaway
Search beat rules in continuous-physics, few-agent, fully simulable games (CodinGame racing and sports: GA or beam search over a few turns using a full engine copy). It also beat rules in isolated combat subproblems (Portfolio Greedy Search, PGS, under 40 ms). In large-scale RTS-like team games with partial information, scripted or rule bots won most editions (microRTS before 2023, AIIDE 2018, Halite, Kore, Lux S2). Successful search under small budgets searches over a portfolio of scripts or a short horizon, uses a crude opponent model, and keeps the previous best plan, shifted, as a warm start.

### Cited Findings
- **Portfolio Greedy Search** (Churchill and Buro, 2013): greedy hill-climbing over per-unit choices drawn from a portfolio of scripted behaviours, evaluated by playouts in the SparCraft combat simulator. It beat Alpha-Beta and UCT in scenarios up to 50 vs 50 units with 40 ms per search episode. [Churchill & Buro, combat13](https://www.cs.mun.ca/~dchurchill/publications/pdf/combat13.pdf); [AIIDE analysis](https://ojs.aaai.org/index.php/AIIDE/article/view/12962)
- **CodinGame Coders Strike Back:** Jeff06 won with a genetic algorithm. The genome was a sequence of [thrust, angle] for the next 6 turns plus a shield turn, and fitness came from a physics engine simulating 6 turns. Magus (winner of Fantastic Bits) built a full simulation engine and reused the CSB collision code. [CodinGame blog](https://www.codingame.com/blog/best-programmers-reveal-magic-code/) (search-snippet level; the page returned 503 on fetch)
- **CodinGame Fall Challenge 2020:** a top player used beam search with iterative deepening and "a stupid dummy for the opponent used only at the first turn". Another used Monte Carlo with 1k rollouts only for opponent prediction. In Spring Challenge 2021, a 12th-place player ran beam search with a blended opponent model (2/3 waiting, 1/3 growing). Searching the opponent explicitly was "on par at best". [CG Fall 2020 thread](https://forum.codingame.com/t/fall-challenge-2020-feedbacks-strategies/187846); [CG Spring 2021 thread](https://forum.codingame.com/t/spring-challenge-2021-feedbacks-strategies/190849) (search-snippet level)
- **CodinGame Bomberman paper (2022):** beam search with a bitboard state, pruning by simulated survival estimates, reached #1 of about 2,300 arena agents. It was compared against MCTS and Rolling Horizon Evolution. [Developing a Successful Bomberman Agent](https://www.scitepress.org/Papers/2022/108402/108402.pdf)
- **microRTS:** "Scripted agents have predominantly won the five previous iterations" of the IEEE microRTS competition. RAISocketAI was "the first DRL agent to win" (CoG 2023). [Goodfriend 2024](https://arxiv.org/pdf/2402.08112v1). The framework includes PortfolioAI, which tries a set of hard-coded strategies at run time and picks the best. [microRTS wiki](https://github.com/Farama-Foundation/MicroRTS/wiki/Artificial-Intelligence)
- **AIIDE StarCraft 2018:** won by SAIDA (Samsung), a rule-based, hand-crafted bot that chose strategy based on the opponent's approach. The Facebook and Chinese entries, which used more ML, placed 2nd and 3rd. [MIT Technology Review](https://www.technologyreview.com/2018/11/16/139045/an-old-fashioned-ai-has-won-a-starcraft-shootout/)
- **Ants 2011:** minimax combat was feasible only for small fights, and its author regretted the time spent on it ([LessWrong](https://www.greaterwrong.com/posts/ELCsD7MYaqnkarPBi/ai-challenge-ants-post-mortem)).

### Inferences
- At ~100k WASM instructions, a full-game rollout is impossible. A portfolio search over a few local fight scripts (engage, kite, retreat-to-ally, hold) evaluated with a tiny 2 to 4 turn local fight model might fit, but it competes with the cheaper XSquare scorer. PGS evidence suggests that portfolio search helps most in large fights. CAMBC fights are 3 to 6 per side, which is small.
- CAMBC's 10M-instruction first turn is a natural slot for precomputation or one-off search, for example the draft, distance tables and a fight lookup table, in the spirit of offline-generated unrolled code.

### Gaps
- I did not retrieve per-edition microRTS reports to confirm which scripted bots (Mayari 2021, CoacAI 2020) won and with what techniques. I also did not find NaiveMCTS competition placements.

---

## Q4. Lux AI / Halite / Kore: rule-based vs imitation learning vs RL; did imitation of top replays win; how were policies distilled to fit limits?

### Takeaway
Rule-based bots won Halite, Kore and Lux AI Season 2. Deep RL won Lux AI Season 1 (2021, Toad Brigade) and microRTS 2023. Learned agents won only with large compute (70 GPU-days for RAISocketAI), fine-tuning against the actual prior champions, and inference engineering to meet per-turn limits (small or downscaled backbones, per-map-size networks, teacher to student). Imitation learning was mainly used to bootstrap or to choose an architecture, not as the winning policy.

### Cited Findings
- "Rules-based agents won Halite, Kore, and Lux AI Season 2." The Lux S1 winning DRL agent (Pressman et al. 2021) used IMPALA plus UPGO/TD(λ), shaped rewards on small maps, then sparse win/loss rewards on full-size maps. [Goodfriend 2024](https://arxiv.org/pdf/2402.08112v1)
- Toad Brigade won Lux AI S1 (Kaggle 2021) using deep RL. [arXiv 2301.01609](https://arxiv.org/abs/2301.01609v1); [speakerdeck summary](https://speakerdeck.com/kenmatsu4/lux-ai-season-2gashi-matutanode-season-1wozhen-rifan-ru)
- **Lux S2 (2023):** flg placed 4th with deep RL. Their pipeline:
  1. Simplify the action and observation spaces.
  2. Use imitation learning plus small-map RL to choose an architecture balancing CPU cost and receptive field.
  3. Train a small RL model as the teacher for a larger model.
  4. Optimize for CPU inference, emitting 6 to 8 queued actions per prediction.

  A secondary summary says the top 3 were logic or planning bots. The 3rd-place entry was a parameter-tuned C++ logic bot. [flg writeup](https://www.kaggle.com/competitions/lux-ai-season-2/writeups/flg-flg-s-approach-deep-reinforcement-learning-wit) (title and search snippet only; Kaggle body not fetchable)
- The top Lux S2 DRL agent (Limburg 2023) used a "DoubleCone" backbone, with middle residual blocks downscaled 4x to cut inference time. [Goodfriend 2024](https://arxiv.org/pdf/2402.08112v1)
- **RAISocketAI (microRTS 2023 winner)** shipped 7 networks and chose one per map or map size. It used a cheaper architecture ("squnet") on large maps because DoubleCone "would likely exceed 100 milliseconds". Training took 1.5B steps on 10 maps in 70 GPU-days. Map-specific transfer learning lifted per-map win rates above 90%. It still lost some matches to timeouts in the competition. [Goodfriend 2024](https://arxiv.org/pdf/2402.08112v1)
- Behaviour cloning plus DRL fine-tuning was shown after the competition to be a cheaper way to reach a competitive agent ([Goodfriend 2024](https://arxiv.org/pdf/2402.08112v1)). AlphaStar's initial agents came from supervised imitation of human replays before league RL ([Goodfriend 2024](https://arxiv.org/pdf/2402.08112v1); [DeepMind blog](https://deepmind.google/discover/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/)).
- **Halite III (2018-19), won by teccles:** a rule-based Java bot.
  - Greedy target assignment (ships claim their best-scoring square, closer ships first).
  - Per-ship Dijkstra over turns and halite burned to score squares by halite per turn.
  - Collision decisions valued by square ownership and cargo.
  - 2-player vs 4-player-specific safety rules.
  - Spawning rules: spawn when behind, stop when well ahead.

  His regrets: build a custom replay viewer; "keep the bot principled", because chasing the leader led to short-term hacks, and the dropoff logic was "a bit of a mess". [teccles halite3-bot README](https://github.com/teccles-halite/halite3-bot)

### Inferences
- For CAMBC, offline RL or IL with a policy distilled into ~100k instructions per turn is plausible only for a tiny model (a linear or small MLP scorer over hand features). Winners' experience says hand rules with tuned parameters usually beat it unless large compute is available.
- The most transferable learned approach is to learn or tune the weights of a rule-based scorer from simulator games or top-team replays. This is like Lux S2's parameter-tuned C++ logic bot, or behaviour cloning used only for priors.

### Gaps
- I could not fetch Kaggle writeup bodies (JS-rendered) for the Lux S2 winner, the Kore 2022 winner, the Halite IV winner, or the Lux S3 (2024-25) winner. Their exact methods are unverified here. The Lux S3 1st-place claim found was only a LinkedIn self-report.

---

## Q5. Evaluation practice: avoiding self-play overfitting and measuring improvement

### Takeaway
Winners measured progress against diverse, strong opponents: scrimmages against higher-ranked teams, prior champions, and multiple maps. They treated self-play gains as unreliable. The clearest datum: RAISocketAI won 91% against standard baselines after self-play but beat the previous champion only 20% of the time, until it was fine-tuned against prior winners.

### Cited Findings
- RAISocketAI reached a 91% win rate against benchmark bots via self-play and prior-self play, but "only beat CoacAI (the 2020 competition winner) in 20% of games". Fine-tuning with half of the environments against CoacAI and Mayari raised this to about 90% against each. [Goodfriend 2024](https://arxiv.org/pdf/2402.08112v1)
- **AlphaStar league:** main agents train against all past players and themselves. Main exploiters target the main agents; league exploiters target the whole league. Without exploiters, a naive RL agent "tends to focus on strategies that are easier to improve". A small-scale reproduction (TStarBot-X) found the strategic diversity of the league "significantly limited". [DeepMind blog](https://deepmind.google/discover/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/); [KDnuggets summary](https://www.kdnuggets.com/2019/11/reinforcement-learning-methods-alphastar-outcompete-human-players-starcraft.html); [TStarBot-X](https://arxiv.org/pdf/2011.13729v1)
- GST built their macro by scrimmaging teams above them on the leaderboard and keeping what improved them ([GST 2026](https://battlecode.org/assets/files/postmortem-2026-generalized-strokes-theorem.pdf)). The Kragle tracked head-to-head scrimmage records against specific seeds (for example "5 for 17" against one opponent) to predict tournament matchups. They noted that teams ranked 9th to 16th were "separated more by auto-scrim luck than strength" ([The Kragle 2025](https://battlecode.org/assets/files/postmortem-2025-the-kragle.pdf)).
- Cout for Clout dropped features that "only did better against a few teams", and kept or dropped others based on what top teams did ([Cout for Clout 2024](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf)).
- Battlecode 2013 winners (Teh Nubs) found that a micro idea looked better only on the one case they had tested. They re-tested across many maps and situations. [tehnubs blog](http://tehnubs.blogspot.com/2013/02/battlecode-2013.html) (search-snippet level)
- Teccles (Halite III winner): new version vs previous version (in 4-player, 2 copies vs 2 copies). He also tried aggressive and passive constant variants, tested parameters online, reviewed losses in a replay viewer, used a community statistics site, and tuned with CLOP, with "mixed" results. [teccles README](https://github.com/teccles-halite/halite3-bot)
- Gone Fishin' tuned micro by "playing against an older version of the bots a million times", but also corroborated choices with the Sprint winner's findings ([Gone Fishin' 2023](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf)).
- microRTS competitions use 8 open and 4 hidden maps, so map overfitting is penalised by design ([Goodfriend 2024](https://arxiv.org/pdf/2402.08112v1)).

### Inferences
- This matches CAMBC's own finding that self-play does not predict the ladder. Winners use opponents that resemble the field: copies of top-team behaviour, frozen prior bests, and exploiter-style counter-bots. They validate on held-out maps and on ladder or scrimmage data.

### Gaps
- No winner reported formal statistics, such as confidence intervals or the number of games needed per comparison. Most practice is informal.

---

## Q6. Ranking for CAMBC (weaknesses: dying alone while fleeing, poor grouping, buying economy items instead of combat stats)

### Takeaway
The highest expected gains, by evidence strength and fit to ~100k instructions per turn with 8 bytes of shared memory:
1. XSquare-style per-tile fight scorer with ally-aware retreat.
2. Shared rally or battlefront point in the 8 bytes, plus local-advantage engage rules (Lanchester).
3. Copying top teams' macro and item builds from ladder replays (combat stats over economy).
4. Opponent-pool evaluation against frozen bests and replay-derived opponents.
5. Offline tuning of scorer weights in the simulator.

Search (PGS or beam) and learned policies are lower-priority under this budget.

### Cited Findings (evidence underpinning each rank)
1. **Fight-movement scorer with retreat as part of it.** Micro was worth "30%-50%" against 5% for macro ([Gone Fishin' 2023](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf)). Copying XSquare micro moved a team from 1850 to more than 2000 rating ([Cout for Clout 2024](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf)). Retreat rules that avoid dying alone include: "Move backwards if the ally behind you has more health", a level-scaled chicken threshold, and moving toward allies when low ([Cout for Clout 2024](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf)), and healing near friendly zones ([Gone Fishin' 2023](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf)).
2. **Grouping through a shared combat location and numbers-gated engagement.** Battlefront communication gave "massive improvements" ([The Kragle 2025](https://battlecode.org/assets/files/postmortem-2025-the-kragle.pdf)). Squadron summoning was justified by Lanchester's law, and 47 vs 50 units lost 90% of games ([Cout for Clout 2024](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf)). Post-fight regrouping on the healthiest ally nearest the objective, plus "chase only with a 2+ advantage" ([Gone Fishin' 2023](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf)). Locations pack into 12 bits ([Gone Fishin' 2023](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf)).
3. **Copying top teams' macro and builds.** Macro is "best improved by scrimmaging against good teams, and copying what they do" ([GST 2026](https://battlecode.org/assets/files/postmortem-2026-generalized-strokes-theorem.pdf)). "The easiest way to improve is to copy what they do better than you" ([The Kragle 2025](https://battlecode.org/assets/files/postmortem-2025-the-kragle.pdf)). Going fully aggressive gained 130 rating points ([Cout for Clout 2024](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf)).
4. **Evaluation against strong, diverse opponents.** Self-play bots beat the previous champion only 20% of the time until fine-tuned against it ([Goodfriend 2024](https://arxiv.org/pdf/2402.08112v1)). The AlphaStar league used exploiters ([DeepMind](https://deepmind.google/discover/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/)).
5. **Parameter tuning.** The CLOP tuner gave "mixed" results for the Halite III winner ([teccles](https://github.com/teccles-halite/halite3-bot)). The 3rd-place Lux S2 entry was a parameter-tuned C++ logic bot ([flg/Kaggle snippet](https://www.kaggle.com/competitions/lux-ai-season-2/writeups/flg-flg-s-approach-deep-reinforcement-learning-wit)).
6. **Lower priority: search.** PGS is strong in large fights (≥32 units) under 40 ms ([Churchill & Buro](https://www.cs.mun.ca/~dchurchill/publications/pdf/combat13.pdf)). GA and beam search won in few-agent, fully simulable physics games ([CodinGame blog](https://www.codingame.com/blog/best-programmers-reveal-magic-code/); [Bomberman paper](https://www.scitepress.org/Papers/2022/108402/108402.pdf)). Minimax combat in Ants was not worth its cost ([LessWrong](https://www.greaterwrong.com/posts/ELCsD7MYaqnkarPBi/ai-challenge-ants-post-mortem)).
7. **Lower priority: learned policies.** These needed 70 GPU-days and per-map networks to win microRTS ([Goodfriend 2024](https://arxiv.org/pdf/2402.08112v1)). Rule bots won Halite, Kore and Lux S2 (same source).

### Inferences
- "Dying alone while fleeing" maps most directly to rank 1. Flee via the per-tile scorer, with features for allies within support range, enemy count able to reach the tile next turn, and distance to the healing or altar zone. The retreat trigger should be HP-scaled and should fire earlier, with no separate flee routine that ignores allies.
- "Poor grouping" maps to rank 2. Use 2 to 4 of the 8 bytes for a rally or battlefront coordinate plus a short TTL or type. Gate engagement on a local count advantage, and regroup on the healthiest ally nearest the objective after fights.
- "Economy items over combat stats" maps to rank 3. Treat builds as macro and copy them from ladder replays of top teams (Battlecode winners reverse-engineered macro from scrimmages). Validate with pool evaluation (rank 4), not self-play.
- The 10M-instruction first turn could host one-off precomputation, such as a table of fight outcomes by HP and count, or a draft search. This is an inference from Battlecode's offline codegen practice, not a cited technique.

### Gaps
- No source directly studies MOBA-like 3v3 to 6v6 bots with an 8-byte shared memory. The ranking extrapolates from Battlecode (most similar budget), RTS and Kaggle evidence.
- AlphaStar specifics beyond the league structure, such as its imitation-learning win rates, were taken from secondary sources. The Nature paper was not fetched.
