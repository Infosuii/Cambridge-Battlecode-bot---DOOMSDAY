# Strategy synthesis: game, bots, methods, and where the research ideas need different solutions (2026-11-01)

Everything we know from the engine, our ~60k local games, the replays, the lab history and the papers, condensed;
then each idea is checked against this game, with a refinement or an alternative where the idea doesn't fit.

## 1. The game, from the engine's own settings (research/dz/ENGINE_FINGERPRINT.json, SDK)

| Fact | Value | What it implies |
|---|---|---|
| Win condition | first to **1000 banked gems**, else most at round 2000 | A race. Strong bots finish ~R900; the loser's last ~300 rounds are often wasted. Finishing time is the real score. |
| Kill gold | **100** (assist 0, passive 0) | One kill = 70% of DZ's R100 gold, 30% of v81hl's. Kills are the only gold besides camps. Early kills snowball (lab: one free R100 kill 53.5% → 71% wins). |
| Respawn | **60 rounds** | A death costs 60 rounds of production (~15 gems for v81hl-level farming), the carried bag, and a kill's 100 gold to the enemy. |
| Banking | adjacent to an altar (range 1); channel 0.1 × gems rounds (min 1) | A 100-gem bank takes 10 rounds and can be interrupted (stun, death, lock). Big bags = long exposed channels. |
| Altar lock | 10 gold, 5 hits to clear, blocks the opposing team | A denial tool whose value is (enemy channel or approach blocked) × (gems at stake), minus the 5 hits it costs them. |
| Capture | 5 rounds standing on a cleared group's region | Rewards are claimed by presence: contestable. |
| Camps | sleep after 2 rounds without a champion in range; respawn | Clearing is a tempo cycle; groups regrow. |
| Recall | 5 rounds to spawn; spawn healing 1.0 | Cheap full heal: aggressive clearing is sustainable *if* you recall (v76 heals 4x DZ). |
| Teleport crystal | 3-round channel | Fast relocation; winners hop fixed 3-tile shortcuts. |
| Wards | 1 active per champion, cooldown 10, infinite life, vision 6 | A new ward replaces the old one: DZ's 324 placements a game are mostly relocation churn. |
| Comms | 8 bytes shared, 1024 bytes draft memory | Coordination must be compact; heavy precompute can be done once in the draft. |
| Fuel | first draft turn 10M, first champion turn 200k, then 100k | Draft-time analysis is nearly free; per-turn work must be budgeted; overruns lose rounds. |
| Determinism | same binaries + map + side → same game | Counterfactuals are exact; screens are paired; "noise" is chaos from any code/fuel change. |

## 2. Derived economics (rough exchange rates, gems-equivalent)

- Gold → gems: ~0.18 early, ~0.10 by R500 (A3 fit over 35k games). Early gold buys items that compound.
- A death: ≈ 60 rounds × production rate + bag + 100 gold to the enemy (~10–18 gem-equivalents) + tempo. A kill is
  the mirror image. With v81hl farming ~0.25 gems per champion-round, a death is worth ~25–40 gems all-in.
- A bank channel of g gems lasts 0.1g rounds: risk grows with bag size, so bank size is a risk/tempo trade.
- Finishing time: at ~1000 gems in ~900 rounds, each round saved is worth ~1.1 gems of margin late in a won game.

## 3. What the bots actually do (replays, 140-game samples)

| | DZ (release) | v76 | v81hl |
|---|---|---|---|
| Gold by R100 / R250 | 141 / 393 | 327 / 1044 | (higher; per-champion gold 1100–1800 per 1k rounds) |
| Camp clears by R100 | 3 | 5 | – |
| Monster damage taken by R100 | 1052 | 2364 | – |
| Healing received by R100 | 530 | 2129 | – |
| Consumables a game | 0 | 13 (8.5 crystals, 4.5 locks) | uses both |
| Wards a game | 324 | 82 | – |
| Deaths a game | ~19 | ~1 | ~0.3–0.9 per champion |
| Strongest champions (in its hands) | Ryth, Marcella | – | Vendetta (6 kills/game), Varg, Ren, Ryth |
| Weakest | Heart, Vendetta | – | Willow, Cassi & Issac |

v81hl (437 knobs, 91 switched-off features): ladder per-map lineups and strategy profiles, a "home" side plan,
early gold valued 4x until R250 (UB_GOLD_MULT), fog-of-war beliefs, rollouts, tactical search with learned models.

## 4. Methodology lessons (what proved true about *measuring*)

1. **Exact pairing beats statistics.** Same snapshot, same flags except one, same maps and sides. Any code or fuel
   change reshuffles chaotic games (±15 banked SE per 140 games), so only paired deltas are trustworthy.
2. **Code identity matters.** A table build must screen with the final table's code (Z14b exact screens), or the
   "best config per map" is partly build noise. Volatile non-zero initialisers keep branch binaries data-only.
3. **Opponent independence.** v74 ≈ v76 here (118/140 identical cells): confirmations against near-clones inflate.
   Use genuinely different bots (v81hl, v85) and generated maps.
4. **Selection overfits.** Best-of-K per map on deterministic games is optimistic; generalists (one global build)
   transferred better than tables (mastery +70 everywhere vs tables +7..+25 vs v81hl).
5. **Fuel is a correctness issue.** Turn-1 overruns, libm calls, whole-map fields and per-call simulators caused
   most fuel-outs; meter real costs, gate on them, never trust formulas.
6. **Silent flag bugs.** Headers that don't include the config see a flag as 0 (fight.h, clear_risk.h): always check
   that flag on/off changes the binary hash.

## 5. Each idea checked against this game, with refinements and alternatives

| Idea (source) | Why it may not fit here | Refinement / alternative |
|---|---|---|
| Win-probability models from game state (Dota 2 LSTM; LoL GBM papers) | Built for humans and noisy data; our engine is deterministic and our models were weak early (R² 0.08 at R100). Correlational. | **Branch-derived values**: replay a game and change one decision; the margin difference is an exact, causal label. Use these to train *decision* values, not outcome predictors. |
| Comeback via bounty (Lee & Kim) | No bounty mechanic; nothing helps the trailing team. | **Manufactured comebacks**: when behind, target the enemy's biggest bag carrier (kills return 100 gold + deny gems), interrupt long bank channels, contest captures; seek variance only when the race is otherwise lost (finish-time model). |
| Champion mastery (human skill) | For bots, "mastery" is controller quality per champion, and it is map-dependent. | Per-(champion, map) mastery from our own games; and **fix weak controllers** (why does Willow/Cassi underperform in v81hl?) rather than only avoiding them. |
| Learned draft net (v81hl's) | Trained on other bots' play: it picked for them, lost 60 margin in DZ. | Draft value must be **conditional on our own controller**: retrain on x1's games, or an across-game contextual bandit over lineups per map class. |
| HMS phase/attention (deep supervised) | Needs big labelled human data; our maps are known and few. | **Influence maps**: cheap static region values (camp gems/gold, distance from spawns, altar access) plus decaying enemy-sighting heat; phase from rounds and score gap. |
| Bandit strategist (MicroRTS PPO executor) | One game gives few decision windows; noisy rewards; our executors are hand-coded. | **Offline-learned switch rules** from branches (exact) plus a small in-game prior; restrict to plans proven non-negative ("safe exploitation"); or across-game bandits per map class on the ladder. |
| Opponent-style recognition (StarCraft) | Fog and 8-byte comms; ladder opponents vary. | Cheap observable signals (first-contact round, enemy sightings in our half, locks seen, bank cadence); classify into the style bots we can play (rusher/turtle/farmer); precomputed counter plan. |
| Vision matters less (Lee & Kim) | True for outcomes, but bots *use* vision to decide. | Measure ward value (sightings per ward, deaths avoided); stop relocation churn; place one stable ward per champion on its route. |
| Learned fight rules (V-M2 death model; v81hl assess net) | Predicting death ≠ choosing well: both cut deaths (18 → 15) but lost 57 margin by leaving productive contacts. | Optimise the **decision objective**: label fight vs run by branch margin over a long horizon (≥50 rounds), and treat "keep working" as a third option. Thresholds tuned to margin, not death. |
| Gold value (A3 fit; v81hl UB_GOLD_MULT 4) | Flat multipliers failed in DZ; v81hl's works in v81hl's economy. | **Marginal item value**: gold is worth more just below an item threshold (next shard/emblem) and less right after a purchase; plan purchases, value gold by the plan. |
| Crews and market claims | Shared claims in 8 bytes are coarse; DZ crews and auctions lost. | **Static roles from the draft** (carrier, farmer, fighter, denier per slot), decided once with 10M draft fuel, plus a tiny claim protocol only for big groups. |
| Altar locks | Reactive locking rarely in range; pre-emptive locking cost our tempo. | **Endgame denial**: when the enemy is near 1000, station one denier on their likeliest altar route; lock on long channels (bag ≥ ~60 gems = 6+ rounds). |
| Hyperparameter search (CMA-ES etc.) | Lab: gains vanished on new maps. | Only within exact paired screens on many maps plus unseen opponents; prefer structural changes. |

## 6. What follows for x1 (priority order)

1. **Know x1's losses**: league baseline (running), loss maps, fuel profile, per-champion mastery in the mirror.
2. **Mastery-aware draft for x1**: bias v81hl's draft net and ladder lineups away from its weakest champions.
3. **Fuel**: port DZ's exact fast simulator / field meter; make v81hl's tactical search deeper with the headroom.
4. **Decision values from branches**: exact counterfactual labels for fight/run/work, recall/bank, plan switch;
   retrain v81hl's assess/act models on them (objective = final margin).
5. **Race model**: finishing-time estimate for both teams; endgame denial and safe banking from it; variance when
   losing the race.
6. **Static roles + influence maps** for macro; style recognition + safe switch rules for dynamic strategy.
7. **Self-play league** with exact screens; generalist first, per-map tables last (they overfit).

## 7. x1 results so far (2026-11-01 evening; 140 games per opponent, 70 maps x 2 sides)

| x1 build | v81hl | v85 | v76 | v65 | total wins |
|---|---|---|---|---|---|
| original v81hl | 69 | 81 | 81 | 84 | 315/560 (56.2%) |
| + X1_FAST_SIEGE (exact LOS precompute; fuel-outs 174->126 mirror, 407->115 vs v65) | 74 | 82 | 81 | 93 | 330 (58.9%) |
| **+ A2_CAMPWATCH (v81hl's switched-off camp watch) = new x1 default 1746f2bb7fa3** | **81** | **89** | **89** | 79 | **338 (60.4%)** |

Sweep of v81hl's 73 switched-off features (stage 1: 38 cells each; stage 2: 70 maps vs v81hl): campwatch 81,
flee-ally 80, snipe 79, pair 78; all nine finalists combined 61 and greedy combinations 71-76: they overlap. The
switch space is nearly exhausted; the structural work in section 6 is next. Parked on x1: role-aware mastery draft
(-25..-59 margin). Parked in DZ: v81hl's draft net (-60), fight-or-run net in all three threshold modes.
