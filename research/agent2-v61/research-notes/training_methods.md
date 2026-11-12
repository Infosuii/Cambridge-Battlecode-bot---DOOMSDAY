# Offline training and evaluation methods for a tiny-compute game bot (CAMBC)

Scope: CAMBC is a turn-based MOBA-like team game. The bot is C++ compiled to WASM, gets about 100k instructions per champion turn, and has no GPU. A local simulator runs at about 0.3 s per game. Team history: ES tuning of 48 to 160 knobs gained +5 to +29 points in training but about 0 on fresh seeds and held-out maps. A fight/flee learner trained on about 4,200 situations found "nothing learnable". The two reference opponents play almost identically to the bot. Ladder losses come from stat-stacking and grouped opponents picking off lone champions.

Note on numbers: some figures below are derived with standard statistics, not taken from a source. They are labelled "(derived)" and the formula is shown, so the report writer can check them.

---

## Q1. Why do ES / black-box tuning gains vanish on held-out evaluation, and what are the published remedies?

### Takeaway
Most likely, the vanishing gains are a winner's curse (the "optimizer's curse"): picking the best of many noisy candidates guarantees an inflated training score, even when each individual estimate is unbiased. On top of that, the tuner can overfit to the fixed map, seed and opponent sample. Published remedies:
- re-evaluate the selected candidate on fresh seeds and maps;
- adapt how many times each candidate is re-evaluated, as in CMA-ES uncertainty handling;
- use paired, common-random-number comparisons;
- use sequential tests (SPRT);
- or move tuning off game outcomes entirely, onto a regression loss over logged positions, as in Texel tuning.

### Cited Findings
- **Optimizer's curse.** If you choose the option with the highest estimated value, its realised value tends to fall short of the estimate, even when every estimate is unbiased. The disappointment comes from the selection step, can be "substantial", and the authors recommend Bayesian shrinkage ("disciplined skepticism"). — [Smith & Winkler 2006, Management Science (Duke record)](https://scholars.duke.edu/publication/798952); [PDF](https://www.gwern.net/doc/statistics/decision/2006-smith.pdf)
- **Curse grows with candidate count.** A secondary summary says the curse grows with the number of alternatives: roughly 1 SD of disappointment with about 3 options and about 2 SD with about 30. These numbers were not checked against the paper. — [LessWrong summary](https://www.greaterwrong.com/posts/5gQLrJr2yhPzMCcni/the-optimizer-s-curse-and-how-to-beat-it)
- **When noise breaks rank-based ES.** Noise is a problem for a rank-based ES "if and only if" the noise between two candidates exceeds their true difference, so their order flips. — [Dinu et al. / Leiden thesis summarising Hansen et al.](https://arxiv.org/html/2409.16757v3)
- **UH-CMA-ES (Hansen, Niederberger, Guzzella, Koumoutsakos).**
  - Mechanism: re-evaluates a few candidates and measures how much their ranks change. If ranks change significantly, it multiplies the number of re-evaluations M (or raises step size), which prevents premature convergence.
  - Cost: "only a small number of additional function evaluations".
  - Related finding: a Leiden thesis found that splitting evaluation into two rounds and measuring the rank differences is the most promising way to quantify uncertainty.
  - Sources: [ar5iv 2409.16757](https://ar5iv.arxiv.org/html/2409.16757); [IP Paris record](https://researchportal.ip-paris.fr/en/publications/a-method-for-handling-uncertainty-in-evolutionary-optimization-wi/); [Leiden thesis](https://scholarlypublications.universiteitleiden.nl/access/item%3A2956089/view)
- **Texel tuning: fit to logged games instead of playing new ones.** Tuning fits evaluation parameters by minimising the mean squared error between the game result and sigmoid(K·qsearch score), using positions from games already played.
  - Data: 64,000 games gave about 8.8M positions.
  - Search: coordinate search with ±1 steps (Gauss-Newton is also suggested), about 400 parameters, a local minimum in about 6 hours.
  - Result: about 99.6 Elo in total over successive rounds, each verified with 32,000-game matches.
  - Why it matters here: the games "have already been played", so no new noisy games are needed per candidate.
  - — [Chessprogramming wiki: Texel's Tuning Method](https://www.chessprogramming.org/Texel%27s_Tuning_Method)
- **Fishtest practice.**
  - Parameter tuning runs use a fixed stopping rule of 20,000 games (TC 10+0.1).
  - Error bars "are designed to be right 95% of the time", so about 1 in 20 runs is an outlier.
  - A difference between two Elo estimates has "nearly double the statistical error".
  - Cost scales roughly as game duration / (normalised Elo)².
  - Retrying a test is capped at "four or five tries", which implicitly limits the multiple-testing curse.
  - — [Fishtest FAQ](https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-FAQ.html)
- **OpenAI ES noise controls.** Salimans et al. use antithetic (mirrored) sampling and rank-based fitness shaping to control noise. — [Salimans et al. 2017, arXiv:1703.03864](https://arxiv.org/abs/1703.03864). (I did not fetch the full text in this session. These two techniques are well known from the paper, but treat the details as background knowledge.)

### Inferences
- **(derived) Winner's curse size.** The expected maximum of K independent N(0,1) draws is about 0.56 (K=2), 1.16 (K=5), 1.54 (K=10), 1.87 (K=20), 2.25 (K=50) and 2.51 (K=100). A candidate scored on n=200 games has SE ≈ 0.5/√200 ≈ 3.5 points. Picking the best of 100 such candidates therefore shows about +8.8 points from noise alone. Across an ES run that keeps the best-ever candidate over thousands of evaluations, the inflation reaches +10 to +15 points or more. That alone explains CAMBC's "+5 to +29 in training, ~0 held-out".
- **Map and seed overfitting.** A fixed set of training maps and seeds is a second source of optimism. With 48 to 160 knobs and a few dozen maps, the tuner can memorise map-specific quirks.
  - Remedy: resample maps and seeds every generation, and validate on a held-out map set never seen during tuning.
- **Practical recipe for CAMBC:**
  1. Use CRN. All candidates in a generation play the same (map, seed, opponent) tuples, with mirrored sides.
  2. Resample those tuples each generation.
  3. Use racing or successive halving: cheap screens on about 100 games, then promote the top 10–20% to 1,000+ games.
  4. Run a final SPRT on fresh seeds and maps against the incumbent before accepting anything.
  5. Shrink reported gains toward 0. A simple rule is to report the held-out number only.
- **Prefer SPSA-style small perturbations.** Small perturbations around the incumbent, with a modest number of knobs per run (around 10–20 rather than 160), lower both the dimensionality and the winner's-curse inflation. Stockfish tunes through fishtest SPSA runs in this style (details not retrieved here).
- **Texel-style regression may beat game-outcome tuning.** CAMBC already logs events and replays. Many knobs feed a value-like score, for example target or position evaluation. Fitting those to logged game outcomes or future-HP differentials gives a low-noise loss that does not need new games per candidate. Only the final model then needs an SPRT.

### Gaps
- Exact UH-CMA-ES update constants were not retrieved; only secondary summaries were used.
- No quantitative study was found comparing ES training gain against held-out gain in game-bot tuning specifically.
- Racing / irace / successive-halving papers were not fetched (known from the literature: Birattari's F-Race and irace; Jamieson & Talwalkar's successive halving).

---

## Q2. How to build opponent diversity when only self-similar opponents exist

### Takeaway
Plain self-play and play against near-identical opponents leads to forgetting, strategy cycles and overfitting to the training partner. AlphaStar's answer was a league that adds exploiter agents (opponents trained only to beat the main agent) and past versions. PSRO and fictitious play generalise this as best responses to mixtures of opponents. For CAMBC, the cheap equivalent is a pool of:
- frozen past versions;
- hand-scripted archetype bots, especially stat-stack and 3-to-5-man deathball bots that mimic the ladder's real threats;
- and exploiters tuned to beat the current bot.

### Cited Findings
- **AlphaStar League design.**
  - Main agents try to beat everyone. Exploiter agents instead "expose the main agent's flaws"; DeepMind says this surfaces more valid strategies and makes the main agent more robust.
  - The League "extends fictitious self-play", playing against a mixture of earlier strategies.
  - Naive self-play fails through forgetting (an agent improves while losing to its old versions), rock-paper-scissors cycles "never converging", and a narrow focus on easy-to-improve strategies.
  - — [DeepMind AlphaStar blog 2019](https://deepmind.google/discover/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/)
- **AlphaStar results.** AlphaStar ranked above 99.8% of active players. The imitation-learned initial policy alone beat 84% of active players. — [DeepMind AlphaStar blog](https://deepmind.google/discover/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/)
- **AlphaStar league composition.** Per race: one main agent, one main exploiter and two league exploiters. Only the main agent is output. A NeurIPS 2023 follow-up builds a "robust and opponent-aware" league on top of this. — [Huang et al., NeurIPS 2023](https://papers.neurips.cc/paper_files/paper/2023/file/94796017d01c5a171bdac520c199d9ed-Paper-Conference.pdf)
- **PSRO (Lanctot et al. 2017).**
  - Problem: independent RL policies "can overfit to the other agents' policies during training".
  - Measurement: the joint-policy correlation (JPC) metric quantifies this.
  - Method: train approximate best responses to meta-strategy mixtures computed by empirical game-theoretic analysis. This generalises independent RL, iterated best response, double oracle and fictitious play.
  - — [Lanctot et al., arXiv:1711.00832](https://arxiv.org/abs/1711.00832)
- **Spinning tops (Czarnecki et al., NeurIPS 2020).** Real-world games have a "spinning top" geometry: a transitive strength axis plus non-transitive cycles that are widest at mid-strength. This geometry explains why populations of strategies are needed. The paper studies population size against convergence on nine games. — [arXiv:2004.09468](https://arxiv.org/pdf/2004.09468)
- **Non-transitivity in chess.** A follow-up measuring non-transitivity in real chess play reads these results as support for large, diverse training populations. — [Sanjaya et al., Measuring the Non-Transitivity in Chess](https://ar5iv.labs.arxiv.org/html/2110.11737)
- **OpenAI Five past-version play.** Self-play was mixed with play against past versions: the blog reports about 80% current self and 20% past versions. — [OpenAI Five blog](https://openai.com/index/openai-five/). (Split recalled from the blog and paper; not re-verified in this session.)

### Inferences
- **Why CAMBC's references add nothing.** They "play almost identically to the bot", which makes them the same point in strategy space. Gains against them measure nothing about the ladder's stat-stack and grouping archetypes. This is exactly PSRO's JPC overfitting.
- **Cheapest useful diversity, in priority order:**
  1. Scripted archetype bots that copy observed ladder failure modes: a full-group deathball that hunts isolated champions, a stat-stacker that farms then fights late, and a split-pusher.
  2. Exploiters. Run ES or CMA-ES on a copy of the bot's knobs, with fitness equal to win-rate against the current main bot only. Training-set overfitting is acceptable here, because the exploiter's job is to find holes. Then add the exploiter to the pool.
  3. Frozen past versions to stop regressions and cycles.
- **Weighting the pool.** Weight the pool to match ladder composition (calibrated pool weights). Alternatively, sample opponents in proportion to how often they beat the main bot (PFSP-like), so effort goes to holes.
- **No CAMBC-sized diversity study.** I found no quantitative "diversity → held-out gain" number for small heuristic bots. The evidence is qualitative: AlphaStar's exploiter rationale, PSRO's JPC and the spinning-tops geometry.

### Gaps
- AlphaStar's PFSP weighting function and its main-agent opponent mix (about 35% self-play / 50% PFSP / 15% past main agents, from my memory of the Nature paper) were not verified in this session.
- PSRO's JPC numbers (the size of the performance drop with unseen partners) were not retrieved; only the abstract was available.
- No ablation of league components was available from the sources fetched.

---

## Q3. Learning a fight/retreat value: Monte Carlo vs TD, features, horizon, and why "nothing learnable" happens

### Takeaway
A finite-horizon Monte Carlo target is a sound default. It is unbiased and was shown not to be worse than TD, even with sparse or delayed rewards. The more likely culprits behind CAMBC's "nothing learnable" result:
- labels that are too noisy relative to the 4,200-sample size (a win/loss many turns later);
- a horizon mismatched to how long a fight lasts;
- confounding: the bot's existing policy already chose fight or flee, so outcome differences mostly reflect situations rather than the decision;
- missing features: ally and enemy grouping, and stat totals, which are exactly the ladder failure modes.

### Cited Findings
- **TD or not TD (Amiranashvili et al. 2018).**
  - The classic TD > MC result holds against infinite-horizon MC.
  - However, "finite-horizon MC is not inferior to TD, even when rewards are sparse or delayed", making MC "a viable alternative to TD in deep RL".
  - — [arXiv:1806.01175](https://arxiv.org/abs/1806.01175)
- **OpenAI Five horizon schedule.** The discount was annealed from γ=0.998 (half-life about 46 s) to γ=0.9997 (half-life about 5 minutes). Short horizons came first, and the horizon was lengthened as the policy improved. — [OpenAI Five blog](https://openai.com/index/openai-five/)
- **Texel-style outcome regression works on a few million positions.** Fitting sigmoid(eval) to final outcomes succeeds with millions of labelled positions (8.8M from 64k games). Very noisy, delayed labels therefore need roughly 10³ times more samples than CAMBC's 4,200. — [Chessprogramming wiki](https://www.chessprogramming.org/Texel%27s_Tuning_Method)

### Inferences
- **(derived) Sample size versus label noise.** A binary outcome label has SD 0.5. To detect a decision effect of Δ=0.05 in a fight win-probability with a simple two-group comparison takes about 2×(2.8·0.5/0.05)² ≈ 1,600 samples per arm (two-sided α=0.05, power 0.8). Conditioning on 10+ features multiplies the need. So 4,200 situations is enough to find one strong main effect, not a feature-conditioned value function.
- **Shorten the label.** Use a short-horizon, dense target, for example ΔHP, kills, or gold advantage within N turns (N ≈ the typical fight length), instead of game outcome.
- **Use counterfactual rollouts to remove confounding.** The simulator allows this: from each situation, branch both "fight" and "retreat" with several seeds each (common random numbers) and regress on the difference. This turns an observational problem into a controlled experiment, and it cuts variance by pairing.
- **Two explanations for "nothing learnable".** Either the decision genuinely does not matter much in those states, which is consistent with "top-team fight choices ≈ ours", or the labels confounded state with action.
  - The CRN branch-and-compare design separates the two. If the paired difference is near 0 with tight error bars, the fight/flee choice is truly not the lever, and positioning or grouping is.
- **Features likely to matter for the reported ladder losses:**
  - local numerical superiority: allies vs enemies within k tiles, HP-weighted;
  - stat totals: summed attack and defence of each side;
  - distance to nearest ally;
  - turns until enemy reinforcements arrive.
- **"Lone champion" isolation.** A feature like "nearest ally > R tiles while ≥2 enemies are visible" may matter more as a positioning penalty than as a fight/flee classifier.

### Gaps
- No source was found that specifically diagnoses "nothing learnable" in game fight models.
- Confounding and counterfactual-rollout arguments are standard causal-inference reasoning, not taken from a fetched game-AI source.

---

## Q4. Distillation into tiny runtime models: decision trees (VIPER), quantised MLPs (NNUE), lookup tables

### Takeaway
Very small models can match a teacher when the decision is low-dimensional:
- VIPER matched a DQN on symbolic Pong with a 769-node tree, and on cart-pole with a 3-node tree. That is about 10× smaller than plain DAgger trees for the same reward.
- NNUE shows a quantised int8/int16 MLP can be evaluated in very few operations when the first layer is updated incrementally.

At 100k instructions per turn, CAMBC can afford a tree, a small lookup table, or an integer MLP of a few thousand weights per evaluated option.

### Cited Findings
- **VIPER method.** VIPER (Bastani, Pu, Solar-Lezama 2018) extracts decision-tree policies from a DNN oracle and its Q-function. It combines model compression and imitation learning, using DAgger with Q-value-gap-weighted resampling. The trees match DNN performance and can be formally verified. — [arXiv:1805.08328](https://arxiv.org/abs/1805.08328)
- **VIPER on symbolic Pong.** 80 iterations × 10 traces gave a 769-node tree with reward 21.0 (= the oracle's 21.0). Smallest tree for a given reward, VIPER vs DAgger with 0-1 loss:
  - R=0: 31 vs 127 nodes
  - R=20: 127 vs 3,459 nodes
  - R=21: 769 vs 7,967 nodes

  The paper calls its trees "an order of magnitude smaller". — [ar5iv VIPER](https://ar5iv.labs.arxiv.org/html/1805.08328)
- **VIPER on cart-pole.** A 3-node tree reaches 200.0 (= the oracle). Fitted Q-iteration reached only 104.3 after 200k rollouts. — [ar5iv VIPER](https://ar5iv.labs.arxiv.org/html/1805.08328)
- **NNUE (HalfKP-era Stockfish).**
  - Size: 2 × 41,024 sparse binary inputs → 256 per side (about 10.5M input weights), then 512 → 32 → 32 → 1.
  - Arithmetic: 16-bit accumulators clamped to 0..127 and turned into int8; int8 weights accumulate into int32, then divide by 64 and clamp.
  - Efficiency: the big first layer is updated incrementally, so a full evaluation is dominated by the small 512×32 layer, about 16k MACs.
  - — [Chessprogramming wiki NNUE (diff)](https://www.chessprogramming.org/Special:MobileDiff/21009...23987)
  - The wiki notes HalfKP is the older design; current Stockfish uses different input features.
- **Policy distillation (Rusu et al. 2015).** Distilled student networks perform "at the expert level while being dramatically smaller and more efficient". The multi-task distilled agent beat its single-task teachers. — [arXiv:1511.06295](https://arxiv.org/abs/1511.06295)

### Inferences
- **(derived) Inference costs, in WASM instructions** (rough, assuming about 2–3 instructions per scalar multiply-add without SIMD):
  - Decision tree of depth d: about 5–10 instructions per level, so depth 10 ≈ 100 instructions. Even a 1,000-node tree is negligible.
  - MLP of 32 inputs → 32 → 32 → 1: about 2.1k MACs ≈ 5–7k instructions. That allows about 15 candidate actions or positions scored per turn within 100k.
  - MLP of 16 → 16 → 1: about 270 MACs ≈ under 1k instructions. That can score hundreds of candidate tiles per turn.
  - Lookup table over discretised features (e.g. 4 features × 8 bins = 4,096 entries): about 20 instructions.
- **WASM SIMD.** WASM SIMD128 (i8x16 / i16x8 dot products) would cut MLP costs by about 4–8×, if the CAMBC toolchain allows it. Not verified.
- **Recommended sequence:**
  1. Learn a value or policy offline: a large model, or rollout-labelled data from the simulator.
  2. Distil into a depth-6 to 10 tree (VIPER-style, weighting states by the value gap between best and worst action) or into an int8 MLP with 16–32 hidden units.
  3. SPRT the distilled bot.
- **Trees as a diagnostic.** A tree also makes the learned rule human-readable, which helps diagnose whether it learned "stay grouped" or a map artefact.

### Gaps
- No primary source was retrieved on the exact NNUE instruction counts, or on WASM-specific inference benchmarks.
- No published distillation results for MOBA or team-game micro were found in this session.

---

## Q5. Reward-shaping lessons

### Takeaway
Shaping that is potential-based (the difference of a state potential, γΦ(s')−Φ(s)) provably leaves the optimal policy unchanged. Arbitrary dense bonuses can be exploited instead. OpenAI Five used a hand-weighted dense reward table plus three devices:
- "team spirit", which blends individual and team reward;
- a zero-sum adjustment;
- a lengthening horizon.

For CAMBC, team spirit and potential-based grouping terms are the transferable ideas.

### Cited Findings
- **Potential-based shaping theory.** Ng, Harada & Russell, "Policy invariance under reward transformations: Theory and application to reward shaping", ICML 1999, is the foundational result. (Cited via the search listing; full text not fetched.) — [search result listing referencing Ng et al. 1999](https://arxiv.org/pdf/2011.02669)
- **OpenAI Five team spirit.** A hyperparameter from 0 to 1 balances each hero's own reward against the team average, and it was annealed from 0 to 1 during training. — [OpenAI Five blog](https://openai.com/index/openai-five/)
  - An aiwiki summary claims 0.2 → 0.97 instead; the primary source is preferred. — [aiwiki](https://aiwiki.ai/wiki/openai_five)
- **OpenAI Five reward weights.** A last hit is rewarded +0.16 and a hero death −1 (secondary analysis). — [evanthebouncy, Understanding OpenAI Five](https://evanthebouncy.medium.com/understanding-openai-five-16f8d177a957)
  - Grokipedia lists −0.16, which is likely a sign error.
- **OpenAI Five horizon.** γ was annealed from 0.998 (half-life about 46 s) to 0.9997 (about 5 min). — [OpenAI Five blog](https://openai.com/index/openai-five/)

### Inferences
- **Grouping as a potential.** Express grouping as a potential function, for example Φ = −Σ max(0, dist_to_nearest_ally − R) or Φ = local HP-weighted numerical advantage. Shaping then rewards moving toward cohesion without changing which outcomes are optimal. This targets the "lone champion picked off" failure directly.
- **Team spirit for CAMBC.** CAMBC's heuristic knobs already behave like hand-set reward weights. Team spirit maps to scoring a champion's action by a mix of its own and the team's expected gain, which discourages solo farming that creates pick-off targets.
- **Zero-sum trick.** OpenAI Five's zero-sum adjustment (subtract the enemy team's mean reward) stops shaped rewards from being farmable by both sides. Its exact wording was not verified in this session.
- **Dense vs sparse.** Dense shaping speeds up learning but invites reward hacking. Always validate on true win-rate, never on shaped return.

### Gaps
- The full OpenAI Five reward table (Appendix of arXiv:1912.06680) could not be extracted: the PDF could not be parsed locally. From memory, unverified, the weights include win 5, hero death −1, gold 0.006, XP 0.002, last hit 0.16, deny 0.15 and tower values 2.25–6. The report writer should flag these as unverified.
- Ng et al. 1999 was not fetched directly.

---

## Q6. Statistical methods to detect small win-rate gains (SPRT, Elo error bars, games needed)

### Takeaway
Detecting +2 points of win-rate needs about 5,000 games head-to-head, or about 10,000 per bot when each is measured separately against a pool. +5 points needs about 800 games; +10 needs about 200 (derived). SPRT, as used in fishtest, stops early on clear results and controls false positives. Paired and pentanomial designs, where each map/seed is played from both sides, cut the variance further.

### Cited Findings
- **How SPRT works.** It tests H0: Elo = Elo0 against H1: Elo = Elo1 with error rates α and β. The log-likelihood ratio (LLR) is updated after each game, and the test stops when the LLR crosses a bound derived from α and β. It is "generally regarded as the most important process in modern engine development". — [Chessprogramming wiki: SPRT](https://www.chessprogramming.org/Sequential_Probability_Ratio_Test)
- **Typical SPRT bounds** (garbled table, with mapping caveats):
  - Stockfish STC: [0, 3] gainer, [−3, 1] non-regression.
  - Stockfish LTC: [0, 2] gainer, [−1.75, 0.25] non-regression.
  - Top-30 engines: [0, 5] and [−5, 0].
  - Top-200 engines: [0, 10] and [−10, 0].
  - Example: elo0=0, elo1=5, α=β=0.05 with a cap of 15,000 rounds.
  - Fishtest bounds are in normalised Elo.
  - Pentanomial statistics "can make tests finish faster".
  - — [Chessprogramming wiki: SPRT](https://www.chessprogramming.org/Sequential_Probability_Ratio_Test)
- **Fishtest error bars.**
  - "Designed to be right 95% of the time".
  - The difference of two independent Elo estimates has "nearly double the statistical error".
  - Cost is about duration / (nElo)².
  - Do not draw conclusions from unfinished tests.
  - — [Fishtest FAQ](https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-FAQ.html)

### Inferences
- **(derived) Elo conversion.** Near a 50% win-rate, dElo/dp = 400 / (ln10 · p(1−p)) ≈ 695 Elo per unit, so about 7 Elo per win-rate point. +2 points ≈ 14 Elo, +5 ≈ 35 Elo, +10 ≈ 70 Elo.
- **(derived) Games needed for a fixed-sample test.** Win/loss outcomes with no draws, per-game SD 0.5, two-sided α=0.05, power 0.8: n ≈ (2.8 · 0.5 / Δ)².

  | Gain | Head-to-head A vs B (vs 50%) | Unpaired A-vs-pool minus B-vs-pool |
  |---|---|---|
  | +2 points | ≈ 4,900 games | ≈ 9,800 games per bot |
  | +5 points | ≈ 780 | ≈ 1,570 per bot |
  | +10 points | ≈ 200 | ≈ 390 per bot |

  - CRN / paired seeds cut the unpaired variance by a factor of (1−ρ), where ρ is the correlation of outcomes on the same map/seed. ρ can be large in deterministic simulators with shared seeds.
- **(derived) 95% confidence-interval half-widths:** n=400 → ±4.9 points; n=1,000 → ±3.1 points; n=5,000 → ±1.4 points.
- **Throughput.** At 0.3 s per game on one core, 5,000 games take about 25 minutes, and 10–15 minutes with parallel cores. Testing +2-point changes properly is therefore affordable. Testing 100 candidates at that depth (about 40 hours single-core) is not, which is why racing plus a final SPRT is needed.
- **SPRT bounds for CAMBC.** In win-rate points:
  - Gainers: [0, +3] or [0, +5], α=β=0.05.
  - Non-regression: [−3, 0] or [−3, +1].
  - Run against a weighted multi-opponent pool on fresh seeds and maps.
  - Expected SPRT length is usually well below the fixed-sample n when the true effect is far from the bounds. (Exact expected lengths were not retrieved.)
- **Multiple testing.** Testing many variants at α=0.05 means about 1 in 20 null changes will "pass". Fishtest's retry cap and SPRT's explicit α bound this.

### Gaps
- Exact expected SPRT run lengths for given bounds and the normalised-Elo formula were not retrieved.
- Pentanomial variance-reduction factors were not retrieved.

---

## Q7. Ranking of approaches for CAMBC (synthesis)

### Takeaway
Best expected value per engineering hour:
1. Fix evaluation first: CRN, held-out maps and seeds, SPRT, shrink tuning gains.
2. Diversify opponents with scripted archetypes and exploiters.
3. Use simulator-branched counterfactual labels plus Texel-style regression for value terms.
4. Distil into small trees or int8 MLPs.

Large-scale RL league training (AlphaStar / OpenAI Five scale) is out of reach. Its transferable pieces are exploiters, past-version pools and team-spirit / potential shaping.

### Cited Findings
- **Exploiters.** Exploiter agents in a league expose main-agent flaws and increase robustness. — [DeepMind AlphaStar blog](https://deepmind.google/discover/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/)
- **Partner overfitting.** Independent learners overfit to training partners, and PSRO's mixture best-responses address this. — [arXiv:1711.00832](https://arxiv.org/abs/1711.00832)
- **Outcome regression.** Texel-style regression on logged positions gave about 100 Elo without per-candidate game noise. — [CPW Texel](https://www.chessprogramming.org/Texel%27s_Tuning_Method)
- **Small trees.** VIPER trees match teacher policies at tens to hundreds of nodes. — [ar5iv VIPER](https://ar5iv.labs.arxiv.org/html/1805.08328)
- **Finite-horizon MC labels.** These are competitive with TD. — [arXiv:1806.01175](https://arxiv.org/abs/1806.01175)

### Inferences
Proposed ranking for CAMBC (judgement, based on the findings above and on the team's own history):

| Rank | Approach | Expected impact | Cost | Notes |
|---|---|---|---|---|
| 1 | Evaluation hygiene: CRN, mirrored sides, held-out maps and seeds, SPRT, shrinkage | Stops chasing phantom +5 to +29 gains | Low | Prerequisite for everything else |
| 2 | Opponent pool with scripted ladder archetypes (deathball / pick-off, stat-stacker) plus exploiters plus past versions | High: targets the stated ladder failure modes | Medium | Exploiter = ES on a bot copy against the main bot only |
| 3 | Targeted behaviour for grouping and isolation, e.g. a potential-style cohesion term or "never be alone near ≥2 enemies" | High if the ladder diagnosis is right | Low–medium | Test with SPRT against the archetype pool |
| 4 | Counterfactual rollout labels → short-horizon value model (MC) → distilled tree or int8 MLP | Medium; also diagnostic | Medium–high | Separates "decision doesn't matter" from "confounded labels" |
| 5 | Low-dimensional SPSA / CMA-ES (≤20 knobs) with UH-style re-evaluation and racing | Small but real | Medium | Only after 1–2; keep the final held-out SPRT |
| 6 | Behaviour cloning from top-team replays | Low (top-team fight choices ≈ ours per the team's notes) | Medium | Useful for positioning features, not fight choice |
| 7 | Full RL / league self-play training of a neural policy | Unclear, high variance | Very high | 0.3 s/game is fast, but RL sample needs are typically 10⁶–10⁹ steps; distillation needed after |

- The team's own history fits these sources: high-dimensional ES with self-similar opponents produced winner's-curse gains, so items 1–2 should come before any more tuning.

### Gaps
- No published head-to-head comparison of these methods on a small turn-based team game was found. The ranking is an informed judgement, not an empirical result.
