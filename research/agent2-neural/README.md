# Agent 2 findings — neural bot and large-gains experiments (3 Nov 2026)

These are Agent 2's results on the CAMBC (Cambridge Battlecode 2026) bot, engine 2.0.0 (cambc 4.0.0). Unless a test says otherwise, every number comes from real-engine `run-batch` games played against v92, the best hand-written bot.

## Summary

| Line of work | Result |
|---|---|
| Hand-tuned macro changes (E101–E113: imitation layer, economy core, schedule optimiser, contest model, item builds, self-play draft, endgame / intel / wards, top-team structure + ES) | Level with v92 or behind it, against v92's own family of bots |
| Opponent-specific counters (E114) | Top teams' openings are repeatable and team-specific up to round ~100. The draft identifies the opponent only 46% of the time. Building this needs current-engine replays (platform login) |
| Rules diff 1.0.3 → 2.0.0 (E115) | Balance changes only: Vesper, Marcella, Heart of Ruin and Ryth nerfed; Varg, Issac, Cassi, Ren, Tavi, Willow, Stellar and Prism buffed |
| **Neural bot (E116, this folder)** | Imitation + DAgger reaches about v92's level. Reinforcement learning (PPO) is running |

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
- **Fuel:** in-bot inference over-runs the real fuel budget. Fuel is ignored for now; this needs optimisation (quantised int8 with wasm SIMD) before any submission. The teacher needs about 2M fuel a turn, so rollouts use `--fuel-quantum 20000000`.

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

### In progress

Reinforcement learning (`code/nn_rl.py`), started from the DAgger-3 teacher:

- each iteration plays 400 real-engine games against v92, x1 and x3ctr, with the bot sampling its target choices;
- each update is a PPO step on the GPU, with a critic baseline, a KL penalty to the imitation policy and an entropy bonus;
- checkpoints are tested deterministically against v92 on ladder and pool-like maps.

## Layout

- `docs/`: experiment log (E101–E116), plans (large gains v3, neural bot, game analysis).
- `code/`: recorder, labels, model, training, export, C++ inference, DAgger and pipeline scripts, RL, map tools, B1 opponent-repeatability analysis.
- `models/`: DAgger-3 teacher and student (`.pt`) and the exported student C++ header.

No credentials, platform data or replay dumps are included.
