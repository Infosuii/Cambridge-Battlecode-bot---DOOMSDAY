# Published MOBA AI systems: techniques, ablations, and transfer to CAMBC

Scope: OpenAI Five (Dota 2, arXiv 1912.06680, Dec 2019), Tencent Solo / "Mastering Complex Control" (HoK 1v1, AAAI 2020, arXiv 1912.09729), JueWu "Towards Playing Full MOBA Games" (HoK 5v5, NeurIPS 2020, arXiv 2011.12692), JueWu-SL (IEEE TNNLS 2020, arXiv 2011.12582), Tencent HMS (AAAI 2019, arXiv 1812.07887), JueWu-Draft (arXiv 2012.10171, Dec 2020), DraftArtist (Chen et al., arXiv 1806.10130, 2018), Valve Dota scripted bots, and Riot's LoL bots. I took the numbers from the paper PDFs, read in full with pdftotext. Some press items come from news articles, and I flag those where I use them.

System-at-a-glance (all numbers cited in the sections below):

| System | Learning | Hero pool | Headline result | Compute |
|---|---|---|---|---|
| OpenAI Five (2019) | PPO self-play, shaped reward | 17 | beat OG (world champs) best-of-3; 99.4% of 7,257 Arena games | 770±50 PFlops/s·days, 10 months |
| Rerun (2019) | same, no surgery | 17 | >98% vs OpenAI Five Final | 150±5 PFlops/s·days, 2 months |
| Tencent HMS (2019) | supervised on 300k pro replays | n/a | 48% vs top-1% human teams (250 games) | 8 GPUs, ~12 h |
| JueWu-SL (2020) | supervised, macro intents + micro | per-hero models | ≈High King level; 100%/86%/92% vs BT/HMS/two-stage | 16 P40 GPUs × 36 h per hero |
| Tencent Solo 1v1 (2020) | dual-clip PPO self-play | 1v1 heroes | 99.81% over 2,100 public games | 600k CPU cores + 1,064 GPUs total |
| JueWu full (2020) | CSPL + distillation + MHV + MCTS draft | 40 | 95.2% vs pros (42 games); 97.7% over 642,047 top-player games | 320 GPUs + 35k CPUs per "resource unit" |

## 1. Macro strategy / objective selection: how did they decide where to go, and what did it gain?

### Takeaway
Tencent's systems made "where to go" an explicit prediction. The map is cut into a coarse grid (HMS 12×12 = 144 regions; JueWu-SL 24×24 = 576), and the label is the region where the player's *next attack* happens. A phase signal (which major objective is next) conditions that prediction. Removing the macro layer lost 75–25 head-to-head, and removing the phase layer lost 65–35. OpenAI Five used no explicit macro module: its LSTM learned macro implicitly from reward over long horizons, and longer horizons helped up to 6–12 minutes. With CAMBC's compute budget, the HMS/JueWu-SL recipe is the one that transfers: supervised labels from replays fitted into a lookup over coarse regions, conditioned on phase.

### Cited Findings
- **HMS architecture**: two layers, "phase recognition → attention prediction → execution". The attention layer predicts the best map region to go to. The phase layer recognises the current game phase so the attention layer knows where to focus. Both are trained as one multi-task CNN+FC net: attention is the main task, phase is auxiliary, and both have loss weight 1. — [HMS, Wu et al. AAAI 2019](https://arxiv.org/abs/1812.07887)
- **HMS labels**: the attention label is the region where the player conducts its *next attack* (the destination within each "session"). The phase label is the *next major resource* to be taken. There are 14 major resources (turrets, base, dragon, baron), and phase ground truth comes from those resources because game phases are hard to label directly. Output is 144 regions (12×12), the same resolution as the blurred visual input. — [HMS](https://arxiv.org/abs/1812.07887)
- **HMS data and compute**: about 300k replays of King Pro League competition and training records, giving 250M training instances. Features: 85 visual features blurred to 12×12, plus 181 attribute features (hero roles, game time, gold, level, KDA). Trained on 8 GPUs in about 12 h. — [HMS](https://arxiv.org/abs/1812.07887)
- **HMS ablations (40 games each)**:
  - Full HMS beats "AI Without Macro Strategy" 75%–25%. The no-macro AI "mainly focused on nearby targets", spent most of its time on neutral and nearby lane creeps, and did not back up teammates. Turrets 6.1 vs 3.2, engagement rate 49% vs 42%.
  - Full HMS beats "Without Phase Layer" 65%–35%. Without the phase layer, agents were "no longer accurate about timing when baron first appears", whereas full HMS was ready at 2:00 to take it.
  - — [HMS](https://arxiv.org/abs/1812.07887)
- **HMS vs humans**: 48.3% win rate over 250 games against teams averaging King rank (top 1%). The AI destroyed 2.5 more turrets than humans on average in the first 10 minutes, but made about 15% fewer kills and was weaker at teamfights later. — [HMS](https://arxiv.org/abs/1812.07887)
- **JueWu-SL multiview intents**:
  - The global intent is a 24×24 grid (576 classes). The label is "the numbered region on the map where the next series of attacks happen".
  - The local intent is a 12×12 grid on the local view, with each cell about one hero-width. Its label is the halfway position between two attack events (gathering in a bush, retreating to a turret, waiting for a target).
  - Intent softmaxes are fed as auxiliary features into the action head. The action labels are the outputs; the intent labels serve as an auxiliary task.
  - — [JueWu-SL, Ye et al. TNNLS 2020](https://arxiv.org/abs/2011.12582)
- **JueWu-SL ablations (100 matches each vs full version)**: without macro-intent auxiliary task 31% win rate; without vector features 17%; without scene-based sampling 21%. — [JueWu-SL](https://arxiv.org/abs/2011.12582)
- **JueWu-SL vs other macro designs**: it beat a behaviour-tree AI 100%, HMS-embedded-into-micro 86%, and a "two-stage" design 92%. In the two-stage design, a macro model picks the destination and a separate micro model acts after arrival. Integrating macro as an auxiliary task end-to-end beat that decoupled approach. — [JueWu-SL](https://arxiv.org/abs/2011.12582)
- **JueWu-SL scene-based sampling**: each game is segmented into 6 prioritised scenes (combat, push-turret, … , navigation as the remainder). Each scene is downsampled to balance the data, with the ratio tuned per hero. Move labels use the displacement to a *future* frame instead of the single-frame direction, because single-frame directions were noisy. — [JueWu-SL](https://arxiv.org/abs/2011.12582)
- **OpenAI Five horizon**: there is no explicit macro model. It resumed from an agent trained at a 180 s horizon (γ = 0.9993), and longer horizons improved win rate "up to the longest horizons we explored (6-12 minutes)". The final OpenAI Five horizon was 840 s. — [OpenAI Five paper](https://arxiv.org/abs/1912.06680)
- **OpenAI Five playstyle**: compared with humans, it "moved heroes back and forth across the map much more frequently". Early in training it prioritised big group fights and "had no way to recover from falling behind". — [OpenAI Five paper](https://arxiv.org/abs/1912.06680)
- **OpenAI Five participation predictions**: auxiliary prediction heads (win probability, and whether each hero will participate in a tower kill) gave interpretable plan signals that changed when the plan was disrupted. — [OpenAI Five paper](https://arxiv.org/abs/1912.06680)

### Inferences
- For CAMBC the HMS/JueWu-SL idea reduces to: **label each logged state with the region (and objective type) where that champion next scores** (gem pickup, camp hit, altar bank, kill). Then fit P(next-region | coarse features: phase/time bucket, own gems, HP bucket, camp timers, role) from top-team replays already in the replay DB. That table can be evaluated in well under 100k instructions. The 75–25 and 65–35 ablations suggest destination choice is high-leverage. That matches the project's earlier finding that the gap is *positioning*, not fight choice.
- The phase lesson transfers almost directly. HMS's gain came from *timing* (being at Baron at 2:00), so camp-respawn-aware pre-positioning (be at the camp at respawn time) is the CAMBC analogue.
- JueWu-SL's "next attack region" label is cheap to compute from CAMBC event logs and avoids hand-defining "macro".

### Gaps
- None of the papers give how often the predicted region was right as a *standalone* accuracy linked to win rate. Only end-to-end win rates are reported.
- HMS ablations use only 40 games each, so confidence intervals are wide (roughly ±15 points).

## 2. Team coordination without explicit communication

### Takeaway
None of these systems used learned explicit messaging at test time. OpenAI Five coordinated through **identical policy replicas over nearly identical shared observations**: each hero runs the same network plus a "which hero am I" input, so every agent effectively knows what its teammates' policy will do. Team spirit shaped the incentives. HMS added "imitated cross-agent communication": it feeds the *predicted* intents of allies, computed locally by each agent, as input features. This worth 62.5–37.5 and lifted "reasonable openings" from 22% to 83%. That trick needs no channel, so it transfers fully to CAMBC.

### Cited Findings
- OpenAI Five uses separate replicas of the same policy, with identical parameters, for all five heroes. Visible information and fog of war are shared across the team, so "the observations are nearly identical for each hero". An extra LSTM input indicates which hero is being controlled. — [OpenAI Five paper](https://arxiv.org/abs/1912.06680)
- **HMS imitated cross-agent communication**: in training, the allies' attention *labels* are input features. At test time, the allies' attention *predictions* are used in their place. HMS beat HMS-without-communication 62.5%–37.5% over 40 games. "Rate of reasonable opening increased from 22% to 83% according to experts' evaluation". — [HMS](https://arxiv.org/abs/1812.07887)
- JueWu-SL removed both the explicit cross-communication and the phase attention of HMS. Its macro-intent component "serves as a coordination signal for AI heroes" because it is an auxiliary task inside each hero's model. With one JueWu-SL AI plus four King-level humans against five King-level humans, the DiaoChan model won 70% of 40 matches. — [JueWu-SL](https://arxiv.org/abs/2011.12582)
- **Team spirit**: the final reward is r_i = (1−τ)·ρ_i + τ·mean(ρ). Very early in training τ = 0 is best (TrueSkill < 125); the best value quickly moves to about 0.5 at TrueSkill 150–175. Rerun's schedule raised τ from 0.3 to 0.8, and OpenAI Five's final value was 1.0. — [OpenAI Five paper, App. G/O](https://arxiv.org/abs/1912.06680)
- **Lane-assignment randomisation**: OpenAI Five agents had settled into a local minimum of all five grouping in one lane. Lane assignments were introduced, with a penalty for leaving the assigned lanes, but the ablation "indicates that this may not have been necessary in the end". — [OpenAI Five paper, App. O](https://arxiv.org/abs/1912.06680)
- JueWu uses one model with shared weights to control all heroes, like OpenAI Five. Its value function sees full game state, including invisible opponent information, during training only. — [JueWu NeurIPS 2020](https://arxiv.org/abs/2011.12692)
- **Valve Dota bots**: team-level code sets desires to push, defend or farm each lane and to take Roshan. These are advisory and do not directly control any bot. Each bot scores its own modes, and the highest-scoring mode becomes active. — [Valve Dota Bot Scripting wiki (via search summary; direct fetch blocked)](https://developer.valvesoftware.com/wiki/Dota_Bot_Scripting); a 2017 patch added `TeamThink()` to team_desires.lua — [Dota 2 Wiki, Feb 23 2017 patch](https://dota2.fandom.com/wiki/February_23,_2017_Patch)

### Inferences
- The CAMBC constraint (separate programs, 8 bytes of shared memory, no talking) is close to OpenAI Five's *test-time* situation. That coordination came from **shared deterministic policy plus shared observation**. In CAMBC, each champion can run the *same* decision function for every ally, using the ally's visible state and the same tie-breaks, and so derive the team's joint assignment consistently. That is HMS's imitated communication done analytically instead of learned.
  - This only works to the extent that allies see the same state. It breaks under divergent vision, such as bushes or private wards, or under inputs that differ between allies, such as RNG or per-unit memory.
- The 8 bytes are best spent on things that are *not* reconstructible from shared observation, such as committed targets/claims or last-seen enemy positions. Anything every ally can recompute should not use memory. The memory notes record a dedup rule that farmed +1% but lost 1.6 pts in the pool; this suggests "claims" that suppress useful duplication can hurt, consistent with OpenAI Five's lane-assignment result.
- Team spirit translates to **objective weighting** in a rule bot. Score a champion's options by team gain, not personal gain, once basic competence is reached. Example: banking gems by whoever is nearest the altar versus whoever carries them.

### Gaps
- None of the papers quantify OpenAI Five coordination without the shared-replica design. There is no ablation with heterogeneous policies.
- I found no published MOBA result in which agents coordinate under *divergent* team vision with zero communication.

## 3. Fight/retreat and target selection: learned or scripted, and what failure modes were reported?

### Takeaway
In both RL systems, fight, retreat and targeting were fully learned. Tencent's best component for targeting was **target attention** (the LSTM state as query, unit encodings as keys), together with an **action mask** that prunes unreasonable actions. Reported failure modes cluster around *macro/out-of-distribution* play, not micro. OpenAI Five lost to sustained split-pushing, players avoiding fair fights, creep-cutting, invisibility, and weak base defence. In supervised data, target choice was biased toward tanky targets until the samples were rebalanced.

### Cited Findings
- **Tencent Solo (1v1) components**: action mask (AM), target attention (TA), LSTM for skill combos, and dual-clip PPO. Ablation table (win rate vs Base, then time to converge):
  - Win rates reported: 50.5%, 75%, 73%, 90%. Times: 80 h, 65 h, 90 h, 100 h, 80 h for Base, +AM, +TA, +LSTM, Full.
  - I read the win rates as +AM 50.5%, +TA 75%, +LSTM 73%, Full 90%. That mapping is inferred from column order in the extracted PDF text.
  - So AM mostly sped convergence (65 h vs 80 h) rather than raising strength.
  - With about 6 h of training the agent already beat the internal behaviour-tree AI 100%.
  - — [Ye et al. AAAI 2020](https://arxiv.org/abs/1912.09729)
- **Solo action mask**: prunes using prior knowledge of experienced players, for example physically forbidden map areas. Solo results: 99.81% over 2,100 public matches (4 losses) at ChinaJoy 2019; it beat pros best-of-5 on several hero types. The discount is about a 46-second half-life. — [Ye et al. AAAI 2020](https://arxiv.org/abs/1912.09729)
- **JueWu (5v5) hierarchical action heads**: *what* (move/attack/skill/return home), then *who* (target via target attention over unit encodings), then *how* (discretised direction or offset). It also uses an action mask "to eliminate unnecessary RL explorations". — [JueWu NeurIPS 2020](https://arxiv.org/abs/2011.12692)
- **JueWu-SL attack sample normalisation**: in raw human data, attacks on low-damage-high-health (LDHH) heroes and high-damage-low-health (HDLH) heroes were imbalanced. "Without downsampling, the model will prefer to attack the LDHH hero". — [JueWu-SL](https://arxiv.org/abs/2011.12582)
- **OpenAI Five low-HP behaviour**: it "seemed to have a very finely-tuned understanding of when an aggressive attack with a low-health hero was worth a risk". It also spent consumables and long-cooldown abilities more readily than humans. — [OpenAI Five paper](https://arxiv.org/abs/1912.06680)
- **Health reward shape**: the health reward is quartically interpolated, with value x + 1 − (1−x)^4/2 at HP fraction x. Each unit of HP is therefore worth more when low. This was set once and never tuned. — [OpenAI Five paper, Table 6](https://arxiv.org/abs/1912.06680)
- **Arena (Apr 18–21, 2019)**: 7,257 games against 3,193 teams, 99.4% won. 29 teams beat it, in 42 games total. Abandoned games (3,140 of the 7,215 wins) were counted as wins. — [OpenAI Five paper](https://arxiv.org/abs/1912.06680). One team won 10 straight with split-pushing (each player in a different lane, avoiding teamfights), creep-cutting to block backdoor protection, and invisibility to escape ganks; the AI "was also not reactive enough to understand that it had to protect its Ancient" — [ONE Esports, Apr 22 2019](https://www.oneesports.gg/dota2/openais-bots-trounced-humans-7215-to-42-in-dota-2/). Brockman said winners "never engage Five in a fair fight" and exploited scripted parts; bots "never try to deny towers" and handled split-push poorly — [Vice/Motherboard, Apr 19 2019](https://vice.com/en/article/we-will-win-openais-dota-2-team-is-crushing-humans-online-but-players-are-not-giving-up). Brockman also said nobody found "the kinds of easy-to-execute exploits that human-programmed game bots suffer from" — [GamesBeat, Apr 22 2019](https://gamesbeat.com/openais-dota-2-bot-defeated-99-4-of-players-in-public-matches/)
- OpenAI Five lost both games against pros at The International (August 2018), before its final version. — [OpenAI Five paper, App. Q](https://arxiv.org/abs/1912.06680)
- **HMS failure mode**: weaker teamfight than humans (about 15% fewer kills) despite equal or better macro. — [HMS](https://arxiv.org/abs/1812.07887)
- **Riot LoL bots**: the 2014 rework focused on bots judging "their strength compared to nearby allied and enemy champions", reacting to being outnumbered, laning and farming. A later news report says bots measure incoming damage to assess threat. Riot later built a new Behavior Tree system for bot decision-making. — [RiftFeed](https://riftfeed.gg/lol-news/bots-update); [LoL Fandom Co-op vs AI](https://leagueoflegends.fandom.com/wiki/Co-op_vs._AI); [Riot /dev: Leveling Up Bots](https://www.leagueoflegends.com/en-us/news/dev/dev-leveling-up-bots/) (details not retrieved)

### Inferences
- Target selection: JueWu-SL's LDHH bias is a warning for any CAMBC target table fitted to replays. Rank by *time-to-kill × threat* (damage-per-turn / effective-HP), not raw HP or hit frequency, and reweight samples by target type when fitting.
- The OpenAI Five exploits map onto CAMBC risks: (a) opponents who avoid fights and farm or bank elsewhere (an analogue of split-push), and (b) an under-defended altar or banked gems. A bot that is good at fights should still have an explicit "nobody is fighting us, contest their economy" trigger.
- Using an action mask in a rule bot means hard-coding never-do rules: never walk into a known 2-vs-1, never leave gems unbanked past threshold X. The Solo ablation shows this mainly speeds learning or tuning. It is worth having so that offline knob search does not waste games.
- The quartic HP valuation is a ready-made, untuned *risk curve* for retreat scoring. The memory notes say a death-risk flee trigger was neutral or harmful, so a smooth HP-value term inside the objective score may work better than a hard flee threshold.

### Gaps
- None of these papers report quantitative OpenAI Five or JueWu fight/retreat accuracy. Exploit evidence is press-level anecdote, except the official Arena totals.
- The Solo ablation column mapping is inferred from the PDF text layout and is not fully certain.

## 4. Item builds and drafting: learned vs scripted, and the measured win-rate impact of draft models

### Takeaway
OpenAI Five **scripted** item purchase order, ability builds, inventory swapping and courier use, and still reached superhuman level. It randomised builds in training only for robustness. For drafting, OpenAI Five used a **precomputed win-probability table over all lineups plus minimax/DP**. JueWu and DraftArtist used **MCTS with a learned lineup win-rate predictor**. Draft gains are reported mostly as *predicted* win rate from the same predictor, so the evidence is partly circular. The cleanest number is JueWu's MCTS drafter at 0.86 vs random picks and 0.68 vs highest-win-rate picking.

### Cited Findings
- **OpenAI Five scripted pieces** (Appendix F.1):
  - Ability builds: a fixed schedule, randomised around in training.
  - Items: consumables via simple top-up logic, stopping after a set game time; non-consumables follow a fixed build order, randomly perturbed in training by deleting items and inserting ones sampled from human build distributions. This was "the only place in our system which relies on data from human games."
  - Item swap: a heuristic keeps the most valuable items active.
  - Courier: a state machine.
  - "We achieved superhuman performance before" un-scripting these.
  - — [OpenAI Five paper](https://arxiv.org/abs/1912.06680)
- **Un-scripting risks**: adding new model-controlled actions caused instabilities (the agent "might quickly learn never to take a new action"). Buyback went from scripted to learned and was "at first worse than the scripted version". OpenAI annealed new actions in gradually. — [OpenAI Five paper, App. B](https://arxiv.org/abs/1912.06680)
- **OpenAI Five draft**: no separate drafting agent was trained. Win probability at game start, from the value/aux head, estimates matchup strength. All 4,900,896 two-team combinations from 17 heroes were precomputed, and dynamic programming / minimax picks the hero that maximises the worst case. In the OG Finals game 1 example, the drafter moved its estimate from 52.8% to 65.1% after a human pick it judged suboptimal. — [OpenAI Five paper, App. D.2](https://arxiv.org/abs/1912.06680)
- **JueWu MCTS drafter**:
  - UCT with a value network in place of random rollouts. The terminal value comes from a lineup win-rate predictor: a 3-layer MLP on a one-hot of the 10 heroes, trained on 30M self-play matches of the converged RL agent. The value net was trained on 100M samples from 10M MCTS-drafted lineups.
  - Results over 1,000 matches per pair: MCTS vs random drafting 0.86, MCTS vs highest-win-rate drafting 0.68, HWR vs random 0.773.
  - — [JueWu NeurIPS 2020](https://arxiv.org/abs/2011.12692)
- **JueWu-Draft (best-of-N)**:
  - MCTS with policy and value nets, plus "long-term value propagation" across rounds in BO3/BO5 where heroes cannot be re-picked.
  - The NN win predictor beat logistic regression by 16.8% accuracy and 17.8% AUC on AI self-play data, and by 8.6% accuracy and 8.1% AUC on top-5% human data.
  - Against the second-best method (DraftArtist), JueWu-Draft won 54.8% (AI data) and 52.5% (human data) in single-round, *by predicted win rate*.
  - MCTS budget was about 1 s per pick.
  - — [JueWu-Draft](https://arxiv.org/abs/2012.10171)
- **DraftArtist (Dota 2)**: UCT over picks, with the reward being a lineup win rate from a classifier trained on historical matches (about 5M ranked matches from 2016, filtered to normal skill). Evaluated in simulation against frequency- and win-rate-based baselines. — [Chen et al. 2018](https://arxiv.org/abs/1806.10130)
- HMS's own ban-pick module "was implemented using simple rules". — [HMS](https://arxiv.org/abs/1812.07887)
- In JueWu's human tests, players could build any item. The paper does not describe how JueWu itself chose items. — [JueWu NeurIPS 2020](https://arxiv.org/abs/2011.12692)

### Inferences
- **Items**: superhuman MOBA play has been reached with *fixed per-hero build orders*. For CAMBC, a per-champion build/emblem order tuned offline is near the ceiling of what learning bought these systems. Effort is better spent on *when* to shop (time lost) than *what*.
- **Drafting**: OpenAI Five's method fits CAMBC's 10M-instruction first turn very well. Precompute a lineup-value table offline from simulator self-play, then run exact minimax/DP over the remaining picks at draft time.
  - The memory notes say counters are noise once per-size values are fitted. The table can therefore be additive (per-champion × team-size value plus a few pair terms). Full minimax over a small pool then fits easily in 10M instructions.
  - The JueWu numbers suggest search over a decent predictor beats greedy "highest win rate" by about 18 points of *predicted* win rate. That is an upper bound on realised gain, since it is measured by the same predictor.
- Train-time **opponent build randomisation** (OpenAI Five) maps to robustness testing. Spar against opponents with perturbed builds and drafts so tuned knobs do not overfit one meta.

### Gaps
- None of the papers report *realised* (played-out) win-rate gains of a draft model against human drafting. All draft comparisons are in predicted win rate or bot-vs-bot.
- The JueWu (RL) item-selection method is not described in the paper.

## 5. Reward shaping: OpenAI Five reward table, zero-sum normalisation, team-spirit schedule, and what mattered

### Takeaway
OpenAI Five used a hand-set, loosely potential-based shaped reward. It was made zero-sum by subtracting the enemy average, decayed over game time by 0.6^(T/10 min), and blended by team spirit. The reward was set once and barely changed. A sparse-reward-only ablation still beat a scripted bot, but with much worse sample efficiency. JueWu split the rewards into **five value heads** (farming, KDA, damage, pushing, win/lose), which measurably raised Elo.

### Cited Findings
- **OpenAI Five Table 6 (shaped weights)**:

  | Event | Weight | Note |
  |---|---|---|
  | Win | 5 (team) | |
  | Hero death | −1 | |
  | Courier death | −2 (team) | |
  | XP | 0.002 | per XP |
  | Gold gained | 0.006 | per gold, not lost on spend |
  | Gold spent | 0.0006 | |
  | Health changed | 2 | fraction of max, quartic |
  | Mana changed | 0.75 | |
  | Killed hero | −0.6 | offsets high gold/XP |
  | Last hit | −0.16 | net about 0.4 total |
  | Deny | 0.15 | |
  | Gained Aegis | 5 (team) | |
  | Ancient HP change | 5 (team) | |
  | Megas | 4 (team) | |
  | T1 tower | 2.25 | |
  | T3 tower | 3 | |
  | T4 tower | 4.5 | |
  | Shrine / Barracks | 2.25 each | |
  | Lane assign | −0.15 | per second in wrong lane |

  For buildings, 2/3 of the reward is paid linearly with HP lost and 1/3 on death. — [OpenAI Five paper, App. G](https://arxiv.org/abs/1912.06680)
- **Zero-sum**: from each hero's reward, "subtracting from each hero's reward the average of the enemies' rewards". **Time weighting**: all non-win rewards are multiplied by 0.6^(T/10 min), so the late game does not dominate learning. — [OpenAI Five paper](https://arxiv.org/abs/1912.06680)
- "We constructed the reward function once at the start of the project"; when game versions changed, the initial choice "worked fairly" well. — [OpenAI Five paper](https://arxiv.org/abs/1912.06680)
- **Sparse-reward ablation** (partial rewards disabled): it "learned to play well enough to beat a hand-coded scripted agent consistently", with a large sample-efficiency penalty. It was weaker early in the game but coordinated fights later. — [OpenAI Five paper, App. G](https://arxiv.org/abs/1912.06680)
- **Team-spirit schedule**: Rerun went 0.3 to 0.8, and the planned final value was 1.0. Early ablation: τ = 0 best at the very start, 0.3–0.5 best soon after. — [OpenAI Five paper](https://arxiv.org/abs/1912.06680)
- **Quirk (Q.2)**: a leftover team-spirit embedding was set to zero, which gave about 55% win rate vs before, "although the win rate was higher, the shaped reward... was approximately the same". This illustrates that shaped reward and win rate can diverge. — [OpenAI Five paper](https://arxiv.org/abs/1912.06680)
- **JueWu multi-head value**:
  - Five heads: (1) farming (gold, XP, mana, monster, no-op); (2) KDA (kill, death, assist, tyrant/overlord buffs, exposing invisible enemies, last hit); (3) damage (HP, hurt to hero); (4) pushing (turret and base damage); (5) win/lose.
  - The total value is a weighted sum of the heads.
  - The ablation shows that adding opponent info to the value input and adding MHV "can both increase the Elo score effectively" over OpenAI Five's baseline value.
  - Discount 0.998, GAE λ 0.95.
  - — [JueWu NeurIPS 2020](https://arxiv.org/abs/2011.12692)
- Solo's reward design was "inspired by OpenAI Five's Dota reward" (hp point, tower hp, gold, exp, death, kill, last hit). — [Ye et al. AAAI 2020](https://arxiv.org/abs/1912.09729)

### Inferences
- For a CAMBC rule bot, the reward table is most useful as a **scoring function for evaluating rollouts or states**. Example: score a state by zero-sum (us − them) team gems + banked gems + HP (quartic) + kills, with values decaying over time. Use it for offline lookahead labelling, or as the objective in knob search when full games are too noisy.
- The Q.2 quirk and the memory note that "self-play doesn't predict ladder" point the same way. Validate any shaped proxy against actual win rate, because proxies drift.
- MHV corresponds to *separate per-component value estimates*. In table form, keep separate fitted terms (farm/gems, fight, objective) and combine them by phase-dependent weights, rather than fitting one opaque number.

### Gaps
- There is no published ablation of the individual OpenAI Five reward terms beyond "partial rewards off". Per-head weights for JueWu MHV are not given.

## 6. Self-play and league training: opponent pools, past-self sampling, curriculum, surgery

### Takeaway
OpenAI Five played 80% of games against the latest self and 20% against past versions. Past versions were sampled by a softmax over learned quality scores that are pushed down whenever the current agent beats them. Surgery let it keep training across about 20 environment and architecture changes over 10 months, but a clean "Rerun" got there with about 20% of the compute. JueWu's key addition was **curriculum self-play learning (CSPL)**: train small fixed-lineup teachers, distil them into one student, then continue on random lineups. That made 40-hero training converge where the baseline did not.

### Cited Findings
- **Opponent sampling**: 80% latest, 20% past. Each past opponent has a quality score q_i and is sampled with p_i ∝ e^{q_i}. Every 10 iterations the current agent is added with q equal to the max existing q. When the current agent beats past opponent i, q_i ← q_i − η/(N·p_i) with η = 0.01; there is no update when the past agent wins. The aim is avoiding "strategy collapse". — [OpenAI Five paper, App. N](https://arxiv.org/abs/1912.06680)
- **Surgery**: over 20 successful surgeries in 10 months, plus failed attempts. These covered observation and action changes, and growing the LSTM from 2048 to 4096 units. Rerun, without surgery, took 2 months and 150±5 PFlops/s·days (about 20% of OpenAI Five) and reached >98% win rate vs OpenAI Five. — [OpenAI Five paper](https://arxiv.org/abs/1912.06680)
- **Environment randomisation**:
  - Starting stats perturbed.
  - Roshan HP randomised from 0 to full, so the agent learns to try killing it.
  - Random lineups.
  - Randomised items.
  - Lane assignments (found unnecessary).
  - — [OpenAI Five paper, App. O](https://arxiv.org/abs/1912.06680)
- **Hero pool**: training with 80 heroes was about 20% slower than with 17 in early training (speedup ≈ 0.8). — [OpenAI Five paper, App. P](https://arxiv.org/abs/1912.06680). JueWu notes OpenAI's attempt to grow to 25 heroes was "unacceptably slow" with degraded performance — [JueWu](https://arxiv.org/abs/2011.12692)
- **Training system ablations** (OpenAI Five, small scale):
  - Batch 983k gave about 2.5× speedup over 123k.
  - Staleness of about 8 versions caused significant slowdown, so the target staleness was 0–1.
  - Sample reuse above 1 hurt badly, and reuse of 0.5 was slightly best.
  - Entropy 0.01 was best.
  - TrueSkill difference of 8.3 ≈ 80% win rate.
  - — [OpenAI Five paper](https://arxiv.org/abs/1912.06680)
- **JueWu CSPL**:
  - Phase 1 trains fixed-lineup teachers: four 10-hero groups, balanced to about 50% using human win-rate data, with smaller models (9M params, LSTM 512).
  - Phase 2 does multi-teacher, student-driven policy distillation (cross-entropy on policy plus MSE on each value head). It converged in under 2 days at an Elo "marginally below the teacher".
  - Phase 3 does random-pick training from the distilled init (17M params, LSTM 1024).
  - Phases advance on Elo convergence.
  - 20 heroes: baseline 192 h vs CSPL 144 h.
  - 40 heroes: baseline >480 h and still about 400 Elo below the upper limit, vs CSPL 336 h converged.
  - — [JueWu NeurIPS 2020](https://arxiv.org/abs/2011.12692)
- **Dual-clip PPO**: adds a lower bound c·Â (c = 3) when Â < 0, to stabilise off-policy updates. The ablation shows an Elo gain. — [JueWu](https://arxiv.org/abs/2011.12692); [Solo](https://arxiv.org/abs/1912.09729)
- JueWu-SL suggests a supervised model can initialise RL; HMS says the same ("can be further used as an initial policy for reinforcement learning"). — [HMS](https://arxiv.org/abs/1812.07887)

### Inferences
- The OpenAI Five opponent manager is a direct recipe for CAMBC's offline tuning pool. Keep past bot versions with quality scores, sample them by softmax, and lower a version's score when the candidate beats it. This auto-focuses evaluation on versions that still challenge the candidate. It complements the memory's "weighted farm/calm/v34c/sparexp pool predicts ladder".
- The "Roshan HP randomisation" idea is cheap in a local simulator: make rare objectives easy during tuning so knobs governing them get non-zero gradient or signal.
- CSPL's lesson for tables and knobs is to **fit per-lineup-size or per-map specialists first, then merge**. For example, fit 3v3, 4v4, 5v5 and 6v6 knob sets separately, then share where they agree. This matches memory notes that per-size values matter.

### Gaps
- Neither paper gives the realised benefit of the 20% past-opponent games (no ablation of the 80/20 split).

## 7. Compute required, and whether any distillation into small models was done

### Takeaway
The RL systems used industrial compute (hundreds of PFlops/s·days, or tens of thousands of CPUs plus hundreds of GPUs for weeks). The supervised systems were cheap: HMS was 8 GPUs × 12 h, and JueWu-SL was 16 GPUs × 36 h per hero. JueWu's distillation merged *teachers into a single student*, not into a smaller deployable model. None of these papers distil into a tiny or rule-based policy.

### Cited Findings
- **OpenAI Five**: 770±50 PFlops/s·days over 10 months (turned off 22 April 2019). About 159M params, mostly one 4096-unit LSTM. Batches of 1–3M timesteps in 16-step LSTM windows. About 16,000 observation values. Reaction time about 217 ms. — [OpenAI Five paper](https://arxiv.org/abs/1912.06680)
- **JueWu**: one "resource unit" is 320 GPUs + 35,000 CPUs, mini-batch 8,192 per GPU, with 6–7 experiments in parallel. Features: 9,227 scalar features plus 6×17×17 spatial channels. Teachers are 9M params and the final model 17M. 40-hero CSPL total 336 h. Online response time 193 ms; APM about 80, comparable to top humans. — [JueWu](https://arxiv.org/abs/2011.12692)
- **Solo**: 600,000 CPU cores and 1,064 GPUs in total; per hero 48 P40 GPUs + 18,000 CPU cores. — [Solo](https://arxiv.org/abs/1912.09729)
- **JueWu-SL**: per hero, 100M samples from about 0.12M top-1% games, 16 P40 GPUs, about 36 h. — [JueWu-SL](https://arxiv.org/abs/2011.12582). **HMS**: 8 GPUs, about 12 h — [HMS](https://arxiv.org/abs/1812.07887)
- **JueWu drafting**: the predictor and value nets are small 3-layer MLPs, and the MCTS budget is about 1 s per pick. — [JueWu](https://arxiv.org/abs/2011.12692); [JueWu-Draft](https://arxiv.org/abs/2012.10171)
- **Valve Dota bots**: Lua mode scripts, each with `GetDesire()` returning roughly 0 to 1.4. The highest desire wins, and its `Think()` runs each frame. — [r/dota2AI thread, Jan 2017 (mirror)](https://redlib.belloworld.it/r/dota2AI/comments/5mdi7r/calling_different_modes). Community suites (e.g. Open Hyper AI) reimplement mode_*_generic.lua for farm/push/defend/roam — [GitHub OpenHyperAI](https://github.com/forest0xia/dota2bot-OpenHyperAI)

### Inferences
- CAMBC's simulator runs at 0.3 s per game, so 1M games is about 83 CPU-hours. The 30M-game lineup dataset JueWu used for draft prediction would be about 2,500 CPU-hours, which is feasible only on a modest cluster. Lineup tables should therefore use low-parameter models (additive per-champion plus a few pair terms) fitted on 10^5–10^6 games.
- The supervised route (HMS/JueWu-SL) is the compute regime that fits CAMBC. Its "deployment" step is replacing the CNN with a lookup table over coarse regions and phases, which costs much less than 100k instructions.
- "Distillation" in CAMBC terms means running expensive offline lookahead or search in the simulator to label states with the best action or region, then fitting a small table or decision tree to those labels. No paper does this for MOBA, so this is an extrapolation.

### Gaps
- I found no published distillation of a MOBA RL policy into a small CPU-bound or rule-based model. Tencent's online AI ran a GPU or server model at 193 ms.

## 8. What could realistically transfer to a tiny-compute rule/table bot with offline training? (ranked by expected impact)

### Takeaway
The two highest-expected-value transfers both target *positioning*, which the memory notes identify as the remaining gap:
- (1) HMS/JueWu-SL **next-objective-region prediction**, fitted from top-team replays and conditioned on phase and camp timers.
- (2) HMS **imitated communication** done analytically: each champion simulates allies' destination choices with the shared deterministic function.

After that come a lineup-value table with exact minimax at draft (OpenAI Five), an OpenAI-Five-style quality-scored opponent pool for offline tuning, and smaller items (scripted builds, action-mask "never" rules, quartic HP valuation, exploit guards).

### Cited Findings
- Macro-region prediction: +75/25 vs no-macro, +65/35 vs no-phase (HMS); without macro-intent aux, JueWu-SL drops to 31% vs full. — [HMS](https://arxiv.org/abs/1812.07887); [JueWu-SL](https://arxiv.org/abs/2011.12582)
- Ally-intent features: 62.5/37.5; reasonable openings 22% to 83%. — [HMS](https://arxiv.org/abs/1812.07887)
- Shared-policy replicas over shared observation coordinated a superhuman team with no messaging. — [OpenAI Five paper](https://arxiv.org/abs/1912.06680)
- Draft search over a predictor: 0.68 vs greedy highest-win-rate, 0.86 vs random (predicted). The OpenAI Five drafter was exact minimax/DP over a precomputed table. — [JueWu](https://arxiv.org/abs/2011.12692); [OpenAI Five paper](https://arxiv.org/abs/1912.06680)
- Scripted items and abilities were sufficient for superhuman play. — [OpenAI Five paper](https://arxiv.org/abs/1912.06680)
- Action mask sped convergence 80 h → 65 h. — [Solo](https://arxiv.org/abs/1912.09729)
- The exploits that beat OpenAI Five were avoiding fair fights, split-pushing, and attacking undefended base or objectives. — [ONE Esports](https://www.oneesports.gg/dota2/openais-bots-trounced-humans-7215-to-42-in-dota-2/); [Vice](https://vice.com/en/article/we-will-win-openais-dota-2-team-is-crushing-humans-online-but-players-are-not-giving-up)

### Inferences
Ranked transfer list for CAMBC. Expected impact is my judgement from the cited ablations, not a measured number.

1. **Destination/objective table from replays (HMS attention + phase; JueWu-SL global intent).**
   - Label = coarse region (or camp/altar ID) of the champion's next scoring event.
   - Condition on a phase bucket (time, camp-respawn state), role/champion, gems carried, and HP bucket.
   - Fit from top-team replays in the existing replay DB. Deploy as argmax(table score + current utility) as the movement target.
   - Add a "be there at respawn" timing term (HMS baron-timing effect).
   - The evidence is the largest ablation effects in the literature: 65–75% head-to-head.
2. **Analytic imitated communication.**
   - Every champion evaluates the same destination function for each visible ally, applying deterministic tie-breaks by champion ID, and takes the best *unassigned* target.
   - Reserve the 8 shared bytes for non-recomputable facts (claims, last-seen enemies).
   - This mirrors HMS's +62.5% and OpenAI Five's replicated-policy coordination.
   - Caveat: duplicate-suppression rules have already lost points in CAMBC's pool, so apply it to *spread across objectives*, not to suppress joint fights.
3. **Draft: precomputed lineup-value table + exact minimax/DP on the 10M-instruction first turn.**
   - Fit from simulator self-play with per-size champion values plus sparse pair terms (counters were found to be noise).
   - Gains over greedy "best win rate" picking are plausible but are an upper bound, because the evidence is only predicted win rate.
4. **Offline tuning infrastructure.**
   - OpenAI Five opponent manager: 80/20 latest vs past, with softmax quality scores.
   - Environment randomisation: perturb opponent builds and drafts; make rare objectives easier during tuning.
   - CSPL-style "specialists then merge" for per-size or per-map knob sets.
   - Validate proxies against real win rate (OpenAI Five Q.2).
5. **Fight evaluator details.**
   - Quartic HP valuation x + 1 − (1−x)^4/2 inside engagement scoring, rather than hard flee thresholds.
   - Target scoring by damage/effective-HP to avoid the LDHH bias.
   - Zero-sum (us − them) state scoring with phase-decayed weights.
6. **Anti-exploit guards.** Explicit triggers for "the enemy is avoiding fights and farming elsewhere" and for "altar/banked gems under threat" (OpenAI Five Arena losses).
7. **Items/emblems.** Fixed per-champion build orders tuned offline. Research shows learned item choice was not needed for superhuman play, so expect small gains here.
8. **Action-mask "never" rules.** Prune obviously bad moves. Mostly saves tuning games rather than adding strength (Solo: same strength, faster convergence).

Not worth transferring to CAMBC: end-to-end deep RL (compute is 3–6 orders of magnitude too high), surgery (CAMBC can just retune from scratch cheaply), and MCTS drafting over neural nets (the pool is small enough for exact search).

### Gaps
- None of the papers measure "macro tables without a neural micro layer". The HMS and JueWu-SL gains were measured with a learned micro model underneath, so the gains may not transfer one-to-one to a rule-based micro layer.
- I could not retrieve the Valve wiki directly: it sits behind an Anubis bot-protection page, so I relied on search summaries and community threads. I also could not retrieve the internals of Riot's 2023 behaviour-tree rework or any Heroes of the Storm AI technical write-up; I found no reliable published source for HotS bot internals.
- Not covered for lack of time or tool budget: Honor of Kings Arena benchmark papers (2022), Tencent human-agent collaboration work (MCC), and academic LoL RL papers.
