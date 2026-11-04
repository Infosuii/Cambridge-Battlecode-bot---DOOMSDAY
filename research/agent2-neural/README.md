# Agent 2 findings — neural bot and large-gains experiments (3-4 Nov 2026)

These are Agent 2's results on the CAMBC (Cambridge Battlecode 2026) bot, engine 2.0.0 (cambc 4.0.0). Unless a test says otherwise, every number comes from real-engine `run-batch` games played against v92, the best hand-written bot.

## Latest status (4 Nov 2026)

All results vs v92 (or v92 with +-0.5% noise on its camp scores, `mk_v92j.py`, which gives new games on the same maps). Full log: `docs/EXPERIMENTS.md` (E120-E124).

**Best bot at the real fuel limit: `nnq4`, the blend in 16-bit with the distance-field fix** (student `models/student_i2m.pt`, flags in `code/e125_fields.sh`). Against v92 and noisy copies only, half the games with noise on its own scores: official 54.6% +- 1.3 (1,440 games), fresh 53.5% +- 1.6 (996), unseen 57.8% +- 2.0 (600). Key fix: v92 kept a 30-35k margin before building a distance field, so on big maps most fields were missing for 100+ rounds; official maps over 60 wide went from 37% to about 58%. More fuel per turn no longer helps it. Not trained with RL yet.

**RL checkpoint 4 is not an improvement.** `nnc4` (RL checkpoint 4, `models/nn_rl5_student_4.pt`) looked like it was, but the gain does not survive tiny noise on its own scores:

| Official maps, real fuel | Without own-score noise | With own-score noise |
|---|---|---|
| `nnc4` (checkpoint 4) | 56.3% (380 games it was not picked on) | 44.5% (560 games) |
| `nnc0` (its starting point) | 48.6% (280 games) | 49.3% (560 games) |

So RL most likely learned specific lines of play against a deterministic v92 on these maps, not a stronger policy. Do not treat `nnc4` as an improvement. A retest on 600 games no earlier test played (no own-score noise), `nnc4` against its start: official 52.3% against 49.7% (paired +2.7 +- 3.9), unseen 49.3% against 54.3% (paired -5.0 +- 3.7). Fresh 53.6% against 53.4%.

How it plays:
- v92 chooses a target as usual. The network overrides only if another camp scores more than 2 logits higher (`A2_NN_ENS=2`).
- Camps are scored inside `farm()`, after v92's choice, on the fuel left (`A2_NN_LAZY`). The network's slow part is refreshed in stages on spare fuel. v92 banks.
- Two new inputs start at zero weight for RL: an exact enemy and ally respawn countdown, and the draft turn's analysis (7.5M of the 10M draft fuel) (`A2_NN_XF`).

**Best result without the fuel limit: the same blend with everything fresh every turn, at 20M fuel: official about 59%, fresh about 56%.** Deterministic games make each build one draw: the first runs showed 63.3%, and tiny noise on the bot's own scores (`A2_NN_LJIT`) brought it to about 59%. It needs more fuel than the 100k limit, so it cannot run on the platform yet.

Other findings:
- **Bug fixed:** the fast path's log table used the nearest step for values >= 4096, and the error was multiplied by 1 / sd on the way in: logits off by up to 6.8. Weight headers exported before this must be re-exported.
- **Larger networks do not help:** 24x96 and 32x128 show no steady gain at 20M, and 24x96 is no better at real fuel.
- **How fresh the summary is matters more than size:** official maps at 20M, every turn 63.3%, every 2 turns 55.0%, every 4 turns 47.6%. Self + camps fresh gets 58.1%, with global + enemies too 63.8%.
- **What the blend's overrides are:** 94% keep the current target when v92 wants to switch (official maps: walking distance 8 vs 22, gems 29 vs 125). A fixed "stay" rule in plain v92 does not reproduce it (official 46-52%, fresh 45-50%): the network chooses when to stay.
- **The scoring moment does not matter:** start of the turn and inside `farm()` both reach about 59% once own-score noise gives independent lines of play. An apparent 8-point gap was noise.
- **Lost turns:** v92 forced to lose 0.3% / 1% of its turns shows no measurable cost at these rates (`results/e124_sk*.tsv`).
- **Testing:** with deterministic games a single build is one draw, even against noisy opponents. Compare bots with own-score noise too.

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
