# Neural bot and RL: a runnable workspace (Agent 2, 3 Nov 2026)

This is everything needed to rebuild, test and keep training Agent 2's neural network bot for CAMBC (engine 2.0.0, cambc 4.0.0). It also covers its reinforcement learning (RL).

- **Bot base:** v92, Agent 2's best hand-written bot.
- **The network's job:** it makes chosen decisions inside v92; v92's own code still does the rest (pathfinding, fights, shopping).
- **Further context:** the full experiment log is `agent2/EXPERIMENTS.md` (E101–E119), and the design is in `agent2/plans/neural_bot_2026-11-03.md`.

## Results so far

All results are real-engine games against v92, with fuel effectively off for both sides (`--fuel-quantum 20000000`).

| Bot | Official ladder maps (70 × 2) | Fresh pool-like maps (249 × 2) | Unseen maps (500) |
|---|---|---|---|
| Best RL network (`agent2/nn_rl2/best.pt`), network picks camp targets + bank timing | 49.3% | **61.8%** | **59.0%** |
| Same, with every v92 per-map table switched off | 47.1% | 61.3% (pool-test) | – |

- **v92's per-map tables** (`ladfit`, `LADDER_TABLES`) are worth only about 2 points (E118). The network does not need them.
- **Why the ladder result is lower:**
  - by map width, the network wins medium official maps (41–60) 59%, but loses small (≤ 40) 38% and large (> 60) 41%;
  - v92 was developed on these 70 maps, while earlier RL trained on them only 7.6% of the time;
  - `nn_rl3.py` now trains on them 70% of the time.
- **v81 and x1 are inflated yardsticks on ladder maps:** v92's per-map fits were tuned against exactly them, and the engine is deterministic, so they are memorised games (E119). Use b5_c3 and v61_c3 as held-out opponents.

## How it works (short)

**Network inputs.** The network reads entities from the champion's view. There are two feature layouts:

| Layout | Features | Contents |
|---|---|---|
| Layout 2 (current) | 500 | self + history, 5 allies, 8 enemies, 10 camp groups, 4 altars |
| Layout 3 | 828 | 24 camp groups, allies' claimed targets from shared memory, ladder map id |

**Architecture.**

| | Teacher | Student |
|---|---|---|
| Encoder | 2 × 64 | 1 × 16 |
| Trunk | 2 × 128 | 2 × 64 |

- Heads: behaviour, target pointer, step, attack pointer, cast, cast target, utility, shop, and the RL-only option head.
- The bot reads three of them:
  - target: which camp group to farm (replaces v92's choice in `farm()`);
  - behaviour: bank or not, at v92's tribute step;
  - option, macro RL only: none / hunt / home / regroup / bank-now. A fresh option head says "none" (bias 7), so the starting policy equals the best bot exactly.

**Training path.**
1. Imitation of v92 from bot-recorded data. The real engine keeps each team's stdout in the replay bundle, so the bot logs its own features and actions.
2. DAgger: three iterations to fix compounding errors.
3. PPO RL.

**RL details (`nn_rl3.py`).**
- **Returns:** taken from the match statistics JSON timelines, which give exact per-round values for gems carried and banked, gold earned, kills, assists and deaths.
- **Critic:** privileged; it sees the full state, training only.
- **Advantages:** GAE per champion.
- **League:** v92, x1, x3ctr, p65pack (groups early), b5_c3, and a snapshot of our own best network.
- **Checkpoints:** a deterministic held-out evaluation every 2 iterations.

## Layout (mirrors Agent 2's project folder, so every script runs unchanged)

```
agent2/lab/          scripts (below)
agent2/plans/        design + plan docs
agent2/EXPERIMENTS.md
agent2/nn_rl2/best.pt          best RL network (layout 2, teacher) - start RL from this
agent2/nn_out_dag3/*.pt        DAgger-3 imitation teacher / student (layout 2)
agent2/nn_out_v3/*.pt          layout-3 teacher / student (behaviour cloning; fails in play without DAgger, see E118)
v4/bots/<bot>/src              v92 (base for every build) + league opponents x1 x3ctr p65 p65pack b5_c3 v61_c3 v81
v4/maps                        the 70 official ladder maps
v4/maps_pooltrain|pooltest|poolfresh   pool-calibrated generated maps (600 train / 300 test / 249 fresh)
v4/sdk/cpp, v4/cambc.toml, v4/mkvar.py
tools/viz/mapmake6.js + v2_0_0.wasm + eng.js   pool-calibrated map generator
```

Large older map suites are not included: `maps_real250`, `maps_test4`, `maps_new4`, `maps_maze`, `maps_mazetest`, `maps_real200b`.
- The scripts skip missing suites.
- Generate more maps with `node tools/viz/mapmake6.js v4/maps_X 300 SEED`.

## Setup

1. Copy `cambc.exe` (the cambc 4.0.0 CLI) into `v4/`. The scripts call `v4/cambc.exe run-batch` and `v4/cambc.exe build`.
2. Install Python 3.12 with numpy and PyTorch. With an NVIDIA GPU: `pip install torch --index-url https://download.pytorch.org/whl/cu128`; CPU also works but is slower.
3. Install Node 20+ (only for the map tools).
4. Use Windows with Git Bash, which is how this was run. The RAM watchdog calls `powershell`; on other systems it reads "99 GB free", so watch RAM yourself.
5. Run every command from the workspace root with `python -P`.

House rules from the handover (16 GB PC):
- keep at least 3 GB RAM free;
- one heavy job at a time;
- never build while a long job runs;
- one build at a time.

## Commands

**Build and test the best RL network** (deterministic: target + bank).

```bash
python -P agent2/lab/nn_export.py agent2/nn_rl2/best.pt teacher agent2/nn_rl2/best_w.h
python -P agent2/lab/nn_mkbot.py nnbest agent2/nn_rl2/best_w.h A2_NN=3
python -P agent2/lab/held_run.py agent2/lab/check_ladder.tsv nnbest v92,b5_c3 ladder --fuel 20000000
python -P agent2/lab/held_run.py agent2/lab/check_pool.tsv nnbest v92 maps_pooltest:0:150 --fuel 20000000
```

**Macro-policy RL, the current main run.** Each iteration is 800 games, about 7–8 minutes; a held-out check runs every 2 iterations.

```bash
python -P agent2/lab/nn_rl3.py agent2/nn_rl3_run agent2/nn_rl2/best.pt 14 --games 800 --eval-every 2
```

**Reading `agent2/nn_rl3_run/rl.log`.**
- **`EVAL iter N`:** deterministic games vs v92, ladder (140) plus pool-test (300). Iteration 0 must reproduce 69/140 and 185/300 (57.7%); `best.pt` is kept.
- **`iter N` line:**
  - rollout wins per league opponent;
  - rows (important decisions plus 10% of keep turns);
  - option mix;
  - `corr(return, result)`: should be clearly above 0;
  - `critic EV`: should rise to about 0.2–0.4;
  - KL to the start network: small, around 0.01–0.04;
  - the option ratio is a display average that includes masked rows; ignore it.
- **Resume:** run the same command again; it continues from `state.json`.

**Final validation** (never used for selection).

```bash
bash agent2/lab/final_check.sh nnbest best
```

**Distil a teacher into the small student** (for the fuel fit).

```bash
python -P agent2/lab/nn_distill.py agent2/nn_rl3_run/best.pt LABELS.npz agent2/student_rl.pt --rows 3000000 --epochs 10
python -P agent2/lab/nn_export.py agent2/student_rl.pt student agent2/student_rl_w.h
```

`LABELS.npz` is any `nn_labels.py` output, for example one recorded below.

**The whole pipeline from scratch** (records data with the real engine; see the script headers).
- `nn_pipeline.sh TAG`: recorder (v92 + `nnrec.cpp`), record, label, train, export.
- `nn_dagger.sh I WEIGHTS.h LABELS.npz:frac ...`: one DAgger iteration for the target head.
- `nn_rl.py`: the earlier target-only PPO (RL 2).
- `nn_v3.sh`: layout 3 (set `NN_LAYOUT=3`).

## Key settings and gotchas

- **Fuel.** In the real game each turn has about 100k fuel; the teacher network needs about 2M. Every result above is with fuel effectively off (20M) for both sides.
  - Fuel-fit code exists but is not yet compiled or tested: `A2_NN_FAST` in `nnrec.cpp` and `nn_infer.h` (SIMD layers, log table, only the heads used, no network in contact, fuel-aware distance fields).
  - The student network plus `A2_NN_FAST` is the route to a submittable bot.
- **Determinism.** A map + side + pair of bots is always the same game. More games need more maps, and a per-map fit against one opponent is memorisation (see x3ctr, v92 vs v81 / x1).
- **Design lessons.** Forcing the network's fight / flee verdict cost 18 points, and replacing v92's routines with network options cost 6–10. Always start the network as a residual on v92: the option head ships as "none".
- **Layout 3** (24 groups, ally claims, map id) is wired end to end and C++ matches PyTorch to 0.009, but behaviour cloning failed in play (17.9%). It needs DAgger with the RL network as the expert running inside the same bot.
- **Build flags** (`nn_mkbot.py NAME WEIGHTS.h FLAGS`):
  - `A2_NN=3` target + bank; `A2_NN=11` + options; `A2_NN_MACRO=1`;
  - `A2_NN_RL=1 A2_NN_RL_T=0.4 A2_NN_OPT_T=1.0` for rollouts;
  - `A2_NN_LAYOUT=3`;
  - `TOP_LADDER_TABLES=0 TOP_A2_LADFIT=0` switch off v92's tables;
  - `BASE=nnrec A2_NNREC=4` makes a recorder (with `A2_NNREC_LAYOUT=3` it logs layout-3 features).

## Status (3 Nov, 21:50)

- **Running on Agent 2's PC:** macro RL from `best.pt`, 14 iterations, 70% ladder maps.
- **Next, in order of expected gain:**
  1. confirm the best macro checkpoint on fresh maps and against b5 / v61;
  2. fuel fit: distil, compile `A2_NN_FAST`, measure at real fuel;
  3. layout 3 with DAgger;
  4. fight learning.
- **Nothing has been submitted.** Submitting and ladder trials are the user's decision.
