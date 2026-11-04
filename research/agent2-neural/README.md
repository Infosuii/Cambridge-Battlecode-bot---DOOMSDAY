# Agent 2 findings — neural bot and large-gains experiments (updated 4 Nov 2026)

These are Agent 2's results on the CAMBC (Cambridge Battlecode 2026) bot, engine 2.0.0 (cambc 4.0.0). Unless a test says otherwise, every number comes from real-engine `run-batch` games played against v92, the best hand-written bot.

**To run it yourself:** see `rl_workspace/README_RL.md`. It has everything needed, including the full experiment log.

## Where things stand (4 Nov, about 01:20)

- **Best bot you can submit: still v92.** No network bot fits the real fuel limit yet, and nothing has been submitted.
- **The network is stronger than v92 only with fuel off** (20M per turn for both bots). It gains about 9–12 points on new maps. On the official maps it's about level to slightly ahead, and that part is less certain (see below).
- **Making it fit real fuel is the blocker.** The cost is down to about 109k per decision, against roughly 30–45k free per turn. Spreading a decision over several turns works mechanically, but holding decisions costs over 30 points. Fixes for that are being tested now.

### Network results with fuel off (20M per turn, both bots)

| Bot | Official maps vs v92 (140) | Pool-test (300) | Fresh pool-like (498) | Unseen (500) |
|---|---|---|---|---|
| RL 2 best (`agent2/nn_rl2/best.pt`) | 69 (49.3%) | 185 (61.7%) | 308 (61.8%) | 295 (59.0%) |
| Same, all v92 per-map tables off | 66 (47.1%) | 184 (61.3%) | – | – |
| Macro RL iteration 2 (`agent2/nn_rl3/best.pt`) | 77 (55.0%) | 180 (60.0%) | 306 (61.4%) | – |
| Student of iteration 2, deciding every turn | 62 (44.3%) | 183 (61.0%) | 284 (57.0%) | – |

- **Treat the 77/140 with care.** That checkpoint was picked as the best on these same 140 deterministic games, and it trains on those maps. The 10.7-point drop to the student isn't all luck, though (next bullet).
- **Partial held-out check on the official maps** (`results/e120_held_partial.tsv`, job stopped early, 140 games each): against b5_c3, the teacher 71.4%, v92 67.1%, the student 60.7%. Against v61_c3, the teacher 66.4% (v92 not measured). b5_c3 is 10% of the RL opponents, so v61_c3 is the cleaner of the two.
- **v92's per-map tables are worth only about 2 points** against v92 (E118), so the network doesn't need them.
- **Why official maps are harder:** the network wins official maps 41–60 wide 59%, but only 38% at 40 wide or less and 41% above 60 (47.1% version, E119). The same split on pool-test maps is 58 / 69 / 53%. It wins from both sides on 26% of official maps and loses from both on 31%, against 41% and 17% on fresh pool-like maps. Earlier RL trained on official maps only 7.6% of the time; `nn_rl3.py` now uses 70%.
- **Student copy quality:** the same choice as the teacher on 93.9% of targets and 91.0% of bank decisions on held-out maps. In play it's 0–4 points weaker on pool-like maps, but 10.7 points weaker on official maps, against both v92 and b5_c3. The fast code path looks responsible rather than the small network, because the teacher on the fast path also fell to 58/140. **Cause not found yet.** The fast path changes how the distance fields get built, so that's the first thing to check.

### Team candidate x3mf2 (`candidates_20261103.zip`)

| Matchup | Fuel | Pool-like (250) | Unseen (250) |
|---|---|---|---|
| Macro RL iteration 2 vs x3mf2 | 20M | 145 (58.0%) | 149 (59.6%) |
| v92 vs x3mf2 | real | 125 (50.0%) | 125 (50.0%) |

Off the official maps x3mf2 plays exactly like v92: 247 of those 250 maps gave gem-for-gem identical games with the sides swapped. Its differences are its per-map settings and counter tables, so its value is only on the official maps, which this test did not cover. At 20M fuel its fight search also runs deeper than it could on the ladder.

### Real fuel: what the engine actually gives

Decoded from each replay's `team-a.fuel` / `team-b.fuel`: a 13-byte header, then 64-bit little-endian values. The first 8 are settings; the rest are fuel used per unit turn.

| Per unit turn | Budget | v92 used (one logged game, 6,684 turns) |
|---|---|---|
| Draft turn | 10M | 25k |
| First champion turn | 200k | about 140k |
| Every later turn | 100k | median 56k, 10th–90th percentile 25–71k |

- Unused fuel does **not** carry over (`GameRules.md`).
- A bot out of fuel is suspended and finishes on the next round's fuel, which costs it that turn. The engine does not report this as a bot fault (`diagnostics.botFaults` stays 0), so a bot can silently lose every other turn.

### Fuel fit so far (`code/fuel_probe.py`, E120)

| Fuel per decision | Network | Features | Total |
|---|---|---|---|
| Teacher, fast path | 1.09M | 40k | about 1.13M |
| Student, fast path | 158k | 40k | about 198k |
| Student + speed-ups | **83k** | **25k** | **about 109k** |

- **Speed-ups, none of which change the maths:** the dense layers walk the inputs instead of the outputs and skip zero inputs, pooling uses SIMD, and the transposed weights are exported ahead of time. Per-group constants such as camp-group centres are cached once. The new code scored 284/498, the same as the old.
- **Largest remaining costs:** trunk about 26k, camp encoder about 29k, camp features about 16k.
- **Pipeline (`A2_NN_PIPE`):** the network is cut into 6 stages plus features. They run after v92's turn, only while the fuel left covers the next stage plus a 5k reserve. In a 10-game log, 9 games had 0 overruns and 1 had a single overrun, with 84–495 decisions per champion per game.

### What holding decisions costs (20M fuel, fresh features, vs v92)

| Decision cadence | Score | Every-turn student on the same games |
|---|---|---|
| Every turn | 284/498 (57.0%) | – |
| Every 4 turns, applied 3 late | 58/247 (23.5%, partial) | 57.1% |
| Every 8 turns, applied 6 late | 76/498 (15.3%) | 57.0% |

My best explanation, not yet proven: the network has only ever played with fresh decisions, so a held target at a finished camp, or a held bank decision, puts it in situations it never trained on.

**Invalid numbers, kept only so nobody reuses them:** the first real-fuel pipeline runs (`results/e120_pipe_*.tsv`, bots `nnp1` and `nnp2`, 19–36%) had a bug. The feature buffer wasn't cleared between decisions, so absent enemies and allies stayed in the input. The control `nnp0`, which never acts, is unaffected: 59/140 on official maps and 245/498 (49.2%) on fresh ones.

### Running now, not in this update

Five variants on the same 498 fresh games against v92:

- dropping finished targets for the network's next choice;
- leaving banking to v92;
- both of those together;
- the pipeline at 20M with the bug fixed;
- the pipeline at real fuel with both fixes.

The macro RL run is paused at iteration 2. To resume, run only the `python` line in `rl_workspace/README_RL.md`.

## Summary

| Line of work | Result |
|---|---|
| Hand-tuned macro changes (E101–E113: imitation layer, economy core, schedule optimiser, contest model, item builds, self-play draft, endgame / intel / wards, top-team structure + ES) | Level with v92 or behind it, against v92's own family of bots |
| Opponent-specific counters (E114) | Top teams' openings are repeatable and team-specific up to round ~100. The draft identifies the opponent only 46% of the time. Building this needs current-engine replays (platform login) |
| Rules diff 1.0.3 → 2.0.0 (E115) | Balance changes only: Vesper, Marcella, Heart of Ruin and Ryth nerfed; Varg, Issac, Cassi, Ren, Tavi, Willow, Stellar and Prism buffed |
| **Neural bot (E116–E120, this folder)** | Imitation + DAgger reaches about v92's level. RL gains 9–12 points on new maps with fuel off. It does not yet fit real fuel |

## Neural bot

### Architecture

The user's design (`docs/neural_bot_2026-11-03.md`):

- **Entities**, each type with its own encoder:
  - self (44 features, including memory of the past);
  - 5 allies;
  - 8 enemies (visible, plus remembered sightings);
  - the 10 nearest camp groups (22 features each, including first-turn map analysis: walking distance, side margin, altar / spawn distance, allies that reach the group first, current-target flag);
  - 4 altars;
  - global features.
  500 int16 features in all.
- **Pooling:** mean + max per type, then a shared trunk.
- **Heads:** behaviour, target group (a pointer over camps), step, attack target (pointer), cast slot, cast target (pointer), cast timing, utility, shop.
- **Sizes:** teacher encoder 2 × 64, trunk 2 × 128 (186k parameters). Student encoder 1 × 16, trunk 2 × 64 (28.6k parameters).
- **Training:** PyTorch 2.11 with CUDA on an RTX 5060, with the whole dataset resident on the GPU.

### Data path

- The real engine keeps each team's stdout inside the replay bundle (`team-a.stdout`). The recorder bot (v92 + `nnrec.cpp`) prints its features and every SDK action it takes, using wrapped imports in a bot-local copy of `cambc.h`.
- Recording therefore runs at engine speed, about 200–300 games a minute.
- Training features are byte-identical to what the bot computes in play. The C++ forward pass matches PyTorch to within 0.01 on the logits.

### Results

All results against v92 with fuel ignored. "Ladder" is the 70 ladder map-sides × 2 = 140 games; "pool-like" is the first 150 maps of `maps_pooltest` × 2 = 300 games.

| Bot | Network controls | Ladder | Pool-like |
|---|---|---|---|
| nn1b | banking (428 features) | 50.7% | (old unseen set) 47.0% |
| nn1t | target group, no memory | 25.0% | — |
| nn2t | target, with memory features | 9.3% | — |
| nn3t1 | target, DAgger iteration 1 | 27.9% | — |
| nn3t2 | target, DAgger iteration 2 | 35.0% | — |
| nn3t3 | target, DAgger iteration 3 | **45.0%** | **52.3%** |
| nn3 | target + banking, DAgger 3 student | 43.6% | **54.7%** |

- **What went wrong first:** offline imitation accuracy (96% on targets) collapsed in play to 10–60% agreement with v92 because errors compound. The network committed to wrong targets and ended up in states v92 never visits.
- **The fix:** DAgger. The network acts, and every state it reaches is labelled with v92's own choice, which v92 computes each turn just before the network overrides it. After three iterations the bot plays at about v92's level.
- **Fuel:** in-bot inference over-runs the real fuel budget, so rollouts use `--fuel-quantum 20000000`. See the fuel sections above for the current state.

### Pool-like maps

`maps/pool_stats.md`; generator `code/mapmake6.js`.

The old unseen suites were unlike the 70 pool maps: 70–110 tiles wide, scattered bushes in 250+ clusters, no holes, 6–12 altars, open layouts. `mapmake6.js` draws every property from the pool's own distributions:

- size and shape;
- symmetry type;
- walls as structures;
- hole lakes and bands;
- a few large bush patches;
- altar and camp-group counts;
- walk / straight-line distance ratio matched bucket by bucket.

It produced two suites:

- `maps_pooltest` (300 maps): the new held-out test suite;
- `maps_pooltrain` (600 maps): training data.

### Reinforcement learning

- **RL 2 (`code/nn_rl.py`):** started from the DAgger-3 teacher, trains the target head. Each iteration plays real-engine games with the bot sampling its target choices, followed by a PPO step on the GPU. Checkpoints are tested deterministically against v92 (`results/rl2.log`).
- **Macro RL (`rl_workspace/agent2/lab/nn_rl3.py`, `results/rl3_macro.log`):** adds an option head that starts at "none", so its first check matched its starting network exactly (69/140, 185/300). Rewards come from the match statistics timelines, and the critic sees the full game state during training only. It trains 70% on official maps against six opponents. Options barely explore in this run (about 0.4% of decisions), so its gains so far come from the target head.

## Layout

- `rl_workspace/`: everything needed to run it, with `README_RL.md` as the guide.
- `docs/`: experiment log (E101–E120), plans (large gains v3, neural bot, game analysis).
- `code/`: recorder, labels, model, training, export, C++ inference, DAgger and pipeline scripts, RL, fuel probe, map tools, B1 opponent-repeatability analysis.
- `models/`: DAgger-3 teacher and student (`.pt`) and the exported student C++ header. The RL networks are in `rl_workspace/agent2/`.
- `results/`: per-game result tables (bot, opponent, map, side, win, gems) and RL logs.

No credentials, platform data or replay dumps are included.
