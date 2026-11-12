# Research bibliography and evidence map

## External sources

Accessed 2026-10-28.

| # | Source | URL | Date | Lesson used (document) |
|---|---|---|---|---|
| B1 | Cambridge Battlecode official site (redirect chain) | https://battlecode.cam → https://battlecode.co.uk → https://2026a.battlecode.co.uk/ | — | JS app; no public text reachable by fetch. Limitation recorded (EXTERNAL §1) |
| B2 | Cambridge Battlecode finals event page | https://luma.com/a1jsj4wq | past event | 16-team double elimination at Cambridge Union: consistency over peak (EXTERNAL §1) |
| B3 | Participant profile post mentioning Cambridge Battlecode | https://ch.linkedin.com/in/emilvinu | — | Earlier edition was Python-based; not this game (EXTERNAL §1) |
| B4 | Web searches for public cambc bots | (no relevant hits) | — | No public top-team source (EXTERNAL §1, TOP_TEAM) |
| B5 | "Cout for Clout" MIT Battlecode 2024 postmortem | https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf | 2024 | XSquare-style per-direction scored micro; aggression; execution matters (EXTERNAL §2; ALGO §6) |
| B6 | "4 Musketeers" Battlecode 2023 Strategy Guide | https://battlecode.org/assets/files/postmortem-2023-4-musketeers.pdf | Feb 2023 | Sector encoding, staleness resets, buffer-pool writes, carriers bank or flee, CI testing (EXTERNAL §2; DATA §4) |
| B7 | Berner et al. (OpenAI), "Dota 2 with Large Scale Deep RL" | https://arxiv.org/abs/1912.06680 | Dec 2019 | Scripted items and abilities; team spirit; time-decayed reward (EXTERNAL §3; ALGO §2) |
| B8 | Wu et al., "Hierarchical Macro Strategy Model for MOBA Game AI", AAAI 2019 | https://arxiv.org/abs/1812.07887 | 2018/2019 | Phase plus attention (where to go) macro decomposition (EXTERNAL §3; MASTER §2) |
| B9 | Ye et al., "Towards Playing Full MOBA Games with Deep RL", NeurIPS 2020 | https://arxiv.org/abs/2011.12692 | Nov 2020 | Draft as search with a value; compute infeasible for us (EXTERNAL §3) |
| B10 | Stanescu, Barriga, Buro, "Using Lanchester Attrition Laws for Combat Prediction in StarCraft", AIIDE 2015 | https://ojs.aaai.org/index.php/AIIDE/article/view/12780 | 2015 | Lanchester predictor beat a simulation-based bot for attack/retreat (EXTERNAL §4; ALGO §5) |
| B11 | Uriarte and Ontañón, "Combat Models for RTS Games" | https://arxiv.org/abs/1605.05305 | May 2016 | TS-Lanchester²: accurate, 19–145× faster than simulation; static DPF best (EXTERNAL §4; ALGO §5) |
| B12 | Churchill and Buro, "Portfolio Greedy Search and Simulation for Large-Scale Combat in StarCraft", IEEE CIG 2013 | https://www.cs.mun.ca/~dchurchill/publications/pdf/combat13.pdf | 2013 | Search over a portfolio of scripts; model accuracy is critical (EXTERNAL §4; ALGO §5) |
| B13 | Lanchester square law references (NPS lecture notes) | https://faculty.nps.edu/mpatkins/docs/lanchester.pdf | — | Concentration of force; focus fire (EXTERNAL §4) |
| B14 | DeepMind, "AlphaStar: Grandmaster level in StarCraft II using multi-agent RL" (Nature 575, 2019) | https://deepmind.google/discover/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/ | Oct 2019 | League with exploiters: evaluation diversity (EXTERNAL §4; VALIDATION §3) |
| B15 | Vansteenwegen and Gunawan, *Orienteering Problems* (Springer) | https://link.springer.com/book/10.1007/978-3-030-29746-6 | 2019 | TOPTW model of farming (EXTERNAL §5; ALGO §3) |
| B16 | Survey of the orienteering problem | https://arxiv.org/abs/2512.16865 | 2025 | Variants and heuristics (EXTERNAL §5) |
| B17 | Bertsekas, auction algorithm (encyclopedia entry) | https://www.mit.edu/~dimitrib/Auction_Encycl.pdf | — | ε-CS auctions; equivalence to min-cost flow (EXTERNAL §5) |
| B18 | Choi, Brunet, How, "Consensus-Based Decentralized Auctions for Robust Task Allocation", IEEE T-RO 2009 | https://dspace.mit.edu/handle/1721.1/52330 | 2009 | Decentralised auction robust to inconsistent awareness (EXTERNAL §5; ALGO §3) |
| B19 | Optimal stopping (overview) | https://en.wikipedia.org/wiki/Optimal_stopping | — | Stopping-rule framing for banking (ALGO §4) |
| B20 | "The Monotone Case Approach…" (burglar problem treatment) | https://arxiv.org/abs/1705.01763 | 2017 | Burglar problem: loot lost on capture; cutoff rules (ALGO §4) |
| B21 | Dave Mark, Infinite Axis Utility System | https://gameai.com/iaus.php | — | Utility architectures; data-driven considerations (EXTERNAL §6) |
| B22 | Dave Mark, "Modular Tactical Influence Maps" (Game AI Pro 2, ch. 30) | https://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter30_Modular_Tactical_Influence_Maps.pdf | 2015 | Local influence windows (EXTERNAL §6; FUEL §3) |
| B23 | Bošanský, Lisý, Lanctot, Čermák, Winands, "Algorithms for computing strategies in two-player simultaneous move games", AIJ 237 | https://dke.maastrichtuniversity.nl/m.winands/documents/sm-journal.pdf | 2016 | Simultaneous-move search: offline sanity checks only (EXTERNAL §6) |

Some of these are secondary sources. B13, B16 and B19 are used for general background only.

## Internal evidence (reproducible repository research)

| ID | Item | Path |
|---|---|---|
| I1 | Engine settings, champions, camps and 84 items | `research/misc/SPRINT3_SDK_FACTS.json`; `sdk/cpp/cambc.h` |
| I2 | Deep analysis (examined set; reserved set spent by its own confirmation) | `origin/analysis/deep-2026-10-28` @ 19109c4: `REPORT.md`, `P5_OPPONENTS.md`, `PROFILE_DATA.json`, `TIMELINE_DATA.json`, `P6_DEEP_TRACK.md`, `docs/NEXT_BOT_BRIEF.md`, `tests/loss_cases/` |
| I3 | Strategic audit runs and scripts (seed 71) | `research/strategic-audit-2026-10-28/` (`scripts/*.py`, `data/*`); runs `artifacts/evaluations/v67/SA-*` |
| I4 | Earlier plan set (superseded by this package) | `research/algorithmic-plan-2026-10-28/` (evidence register E1–E28 in `FINAL_DEEP_ANALYSIS.md`) |
| I5 | v81–v85 failed families | `research/v81/RESEARCH.md` |
| I6 | v58 director, Claudus and Sprint 3 | `research/v58/*.md` |
| I7 | v75 fight and loss forensics, duels | `research/v75/*.md` |
| I8 | v70/v71 per-map league method | `research/v70/V70.md`, `research/v71/V71.md` |
| I9 | Proxy and top-team item tables | `research/proxy/README.md`, `TABLES.md` |
| I10 | Prospector inference (this session) | SA-IDLE-v76 `summary.json` gemCollection events (method in GAME_MECHANICS §6) |

## Claim categories used throughout this package

- **Verified engine fact:** I1, or an exact replay reproduction (I2 puppet harness).
- **Direct observation of competitors:** I2 profiles, I9 tables.
- **Reproducible internal research:** I3–I8, I10.
- **Externally supported technique:** B5–B23.
- **Reasoned architectural hypothesis:** marked [HYP], or stated as design.
- **Speculative:** marked L confidence in TOP_TEAM_REVERSE_ENGINEERING.md.
