# Strategy ML review (2026-11-01): three user papers + search, mapped to DZ

Sources read: the user's three papers (two only through abstracts/datasets, since ResearchGate and the publisher
blocked full text) and a search for ML approaches to strategy development and in-game strategy switching.

## 1. The three papers

| Paper | What it does | What transfers to DZ |
|---|---|---|
| Akhmedov & Phan, *ML models for Dota 2 outcome prediction* (arXiv 2106.01782, IEEE ToG) | Live game state (160 GSI features; 10 most gold-correlated kept) → predict a target d steps ahead from a window of L past steps. LR / MLP / LSTM; LSTM best (0.99 at d=2,L=5 → 0.94 at d=25,L=20); accuracy falls with horizon. | A **multi-horizon value model** over time series of our own state. Short horizons are near-deterministic; the useful signal is how fast predictability decays, which marks decisive moments. |
| Lee, *Comeback victories with the bounty mechanism in MOBA* (2025; dataset IEEE DataPort 10.21227/aes9-0c53) | Label = comeback win (1/0) in bounty-active matches. 24 predictors: objective kills by type, champion kills/assists, wards placed / control wards / wards killed, damage-type ratio, tank count, jungle-invade rate, champion-mastery mean / CV / top-10 rate, team similarity. Related: Hojaji et al. 2025 (154k LoL games) rank turrets lost first, then bounty level. | Our engine has **no bounty or comeback mechanic** (fixed kill/assist gold), so a trailing DZ must create its own comeback. Feature families to measure for DZ: objective control/denial, vision, composition, *how well DZ plays each champion*, and pressure on the enemy half. |
| Shaipullah & Habib Sultan, *ML in MOBA esports: systematic review* (Pertanika JST 33(2), 2025) | PRISMA review of 35 studies, mostly Dota 2 / LoL; categories: outcome prediction, draft/hero recommendation, behaviour; gaps in data access and real deployments. | Confirms that most MOBA ML is outcome prediction and draft recommendation; few studies turn predictions into decisions, which is the step DZ needs. |

## 2. Own search: ML for strategy development and dynamic strategies

| Approach | Source | Mechanism | DZ fit |
|---|---|---|---|
| Phase → attention macro strategy | HMS, Tencent (AAAI 2019) | A phase layer recognises the game stage; an attention layer predicts which map region heroes should go to; phase is an auxiliary task. 48% vs top-1% humans. | Phase-aware job choice: region weights that change with a recognised phase, not a fixed round. |
| Bandit strategist over command tuples | Leenders et al. (arXiv 2610.11663, MicroRTS) | Thompson sampling picks strategy commands (economy, army, posture) from an **in-game estimate of the opponent's strategy**, not its identity. A constrained PPO policy executes them. Against held-out opponents: 0.55 → 0.97 and 0.01 → 0.34. | Our team plans are the "commands"; DZ's executor already exists. Fits A2 without deep RL. |
| Strategy pool + opponent modelling | Silva et al. (IEEE ToG 2019, μRTS) | Generate a pool from designed strategies; choose among them during play with an opponent model. | DZ's flag configs are the pool; choose per game, not only per map. |
| Detecting strategy switches | R-max# (Hernandez-Leal et al.); two-sample-test opponent models | Detect when the opponent changes strategy, then reset or relearn the counter. | Re-plan when opponent behaviour changes mid-game. |
| Early strategy recognition | Weber & Mateas (build orders; kNN best early); Synnaeve & Bessière (Bayesian, unlabelled replays); NTNU thesis (recognise + counter) | Classify the opponent's strategy from partial early observations; prediction improves with time. | Classify opponent style by ~R100–150 from what DZ sees; map style → counter plan. Our three style bots give labelled data. |
| Comeback / snowball composites | Kamal et al. (Applied Soft Computing 2025, MLBB) | Expert-weighted snowball and comeback scores in interpretable logistic models. | A cheap in-bot "are we snowballing or behind" score to trigger plan switches. |

## 3. What this adds to the plan (new tasks, each behind a flag with an exit test)

| ID | Task | Method | Data / cost | Exit test |
|---|---|---|---|---|
| **F1** | Multi-horizon value model | Offline: from saved timelines (gold, banked, carried, kills, deaths, camp clears, items, wards, locks, both teams) predict final margin and P(win) at d = 50/100/250 rounds from windows of L checkpoints; logistic → GBM → small LSTM; map-grouped CV. | ~40k stored games already | Brier/MAE beats the banked-difference baseline; then used as the reward for F2/F4 |
| **F2** | Comeback / risk policy | Using F1 and the A2 branches: when F1 says we are behind, are higher-variance plans (fight, lock-heavy, enemy-half pressure) better than when ahead? If so, add "trailing → switch" rows. | A2 runs + new branches | Positive CV policy gain conditioned on trailing (A2's exit test) |
| **F3** | Phase-aware attention | Phase from rounds, gold, banked and visible enemy positions; per-phase region weights (own half, centre, enemy half, altars) in job value; weights fitted from where the *winning* side's bodies were per phase in replays. | Replays (positions in summaries/replays) | G5 screen |
| **F4** | In-game bandit strategist | Every K rounds, Thompson-sample a team plan from posteriors keyed by an opponent-style estimate; reward = income-rate or F1-value change over the window; state in Memory (no shared memory needed, each body can run it deterministically on shared observations or slot 0 can publish one plan code). Fuel: a few counters per round. | Offline posteriors from the branch screens, online update in-game | G5 screen vs fixed best plan |
| **F5** | Early opponent-style recognition | Features by R100–150: enemy sightings in our half, first contact round, enemy altar locks seen, enemy camp clears seen, ward density; kNN / logistic on labelled games vs rusher/turtle/farmer and v65/v74/v76/v81hl; counter plan per class. | Our style bots + league runs | CV accuracy, then counter-plan screen |
| **F6** | Objective control and denial | Altar locks (built, screening), pre-emptive locks on altars an enemy carrier approaches, breaking enemy locks faster; teleport crystals for shortcuts. The equivalents of turrets and objective bounties. | Replays: v76 uses 4.5 locks / 8.5 crystals a game | G5 |
| **F7** | Vision quality | DZ places 324 wards a game (v76: 82). Measure ward value (enemy sightings per ward, deaths avoided), use control wards (SDK has control-ward radii; DZ never uses them), deny enemy wards. | Replays | Deaths down, G5 |
| **F8** | Champion "mastery" for DZ | Per-champion DZ performance (deaths, gold, kills per champion type across the league) → draft toward champions DZ executes well; damage-type and tank balance as draft features. | Existing capsules | Draft screen (Z14 draft variants as baseline) |

## 4. Order (merged into COMBINED_PLAN section 8)

1. F6 altar locks (running) and lock extensions; F8 champion mastery (analysis only, cheap).
2. F1 value model (offline, needed by F2/F4).
3. F5 early style recognition + F4 bandit strategist: the "dynamic strategy" core.
4. F2 trailing-risk policy, F3 phase attention, F7 vision quality.

Sources: arxiv.org/abs/2106.01782; ar5iv.labs.arxiv.org/html/2106.01782; ieee-dataport.org/node/14834;
ir.unimas.my/id/eprint/47788; arxiv.org/abs/1812.07887; papers.cool/arxiv/2610.11663;
webdocs.cs.ualberta.ca/~santanad/papers/2019/silvaMLG19.pdf; ir.cwi.nl/pub/24750/AAMS2869.pdf;
gamedeveloper.com/programming/reproducible-research-starcraft-data-mining; arxiv.org/pdf/1111.3735;
ntnuopen.ntnu.no/ntnu-xmlui/handle/11250/252930; doi 10.1016/j.chbr.2025.100718; doi 10.1016/j.asoc.2025.114301.

## 5. Full texts supplied by the user (update, same day)

**Lee & Kim, Electronics 14:1445 (2025), comeback victories with the bounty mechanism.** Comeback = the team whose
objective bounty is active (the trailing team) wins. Features in four groups: resource (gold, XP, turrets,
inhibitors, minions), combat (kills, assists, jungle-invade pressure, damage-type ratio, tank count, champion
mastery), objective (dragons by type, Herald, Baron) and vision (wards placed, control wards, wards killed).
Models: SVM, RF, XGBoost, CatBoost, LightGBM, MLP. Best F1 0.937 (MLP 64-32); a soft-voting ensemble of SVM,
XGBoost and MLP is used for stability (classes are imbalanced, so F1 rather than accuracy). Importance (XGBoost
gain/weight): champion kills top by gain; inhibitor destruction second; **assists high on both** (teamwork);
team champion mastery and mastery similarity used in many splits; a movement-speed dragon is the most informative
dragon; minion counts frequent but low gain; **vision below average, not decisive**. Bounties mostly activate in the
first 15 minutes and many games end within 10 minutes of activation (trailing players give up). SHAP per-game
explanations are used to say why a comeback did or didn't happen.

**Arik, Acta Infologica 7(1) (2023), LoL winner prediction.** 96 player-level features; LightGBM 0.97 accuracy,
LR 0.96, SVM/GBC 0.95 (10-fold CV). Most important: **earned gold per minute**, then gold shared, gold spent,
assists, deaths.

**Kamal, Mansor et al., Pertanika JST 33(2) (2025), systematic review (35 studies, PRISMA).** Predictors used
across studies: GPM, XPM, KDA, hero picks/bans, tower damage, ward placement, team composition. Methods: mostly
supervised (LR, SVM, RF, GBoost, XGBoost, NN); RL in Honor of Kings studies (PPO, DQN). Gaps the review lists:
real-time use of predictions, team dynamics, meta shifts, human intervention, data access.

### What changes in the DZ plan

- **Gold rate is the dominant indicator** in every paper (GPM first in Arik; resource group in Lee & Kim). DZ earns
  141 vs v76's 327 gold by R100: economy-first work (fast boot, v76-style camp cycle, consumables) stays first.
- **Assists / joint kills matter** (Lee & Kim): measure DZ kill participation; B3 focus fire and co-ordinated
  engagements are justified, unlike the pair/whole-team *crews for camps* that failed.
- **Vision is not decisive**, and DZ places 4x v76's wards: F7 becomes *ward economy* (test fewer, better-placed
  wards; each ward costs an action and fuel), not more vision.
- **Mastery matters** (team mastery and similarity): F8 confirmed; weight DZ's draft toward champions DZ plays
  well, measured per champion across the league.
- **Early game decides** (bounties fire early; games end soon after): F1/F5 should focus on R100-R300.
- **Explain losses with SHAP** on the F1 value model, per map, to target fixes (the review's "real-time use" gap).
- Model choice for F1/F5: gradient-boosted trees + logistic baseline, F1-score for imbalanced events, soft-voting
  ensemble; LSTM only if trees plateau.
