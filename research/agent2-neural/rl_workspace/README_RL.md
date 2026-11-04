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
| Macro RL iteration 2 (`agent2/nn_rl3/best.pt`), picked on these ladder games, so treat its 55.0% with care | 55.0% | 61.4% | – |
| Student of iteration 2 (`agent2/student_i2.pt`), deciding every turn | 44.3% | 57.0% | – |

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
agent2/nn_rl2/best.pt          RL 2 best network (layout 2, teacher) - the macro run starts from this
agent2/nn_rl3/best.pt          macro RL iteration 2 (layout 2, teacher)
agent2/student_i2.pt           student distilled from macro RL iteration 2
agent2/nn_out_dag3/*.pt        DAgger-3 imitation teacher / student (layout 2)
agent2/nn_out_v3/*.pt          layout-3 teacher / student (behaviour cloning; fails in play without DAgger, see E118)
v4/bots/<bot>/src              v92 (base for every build) + league opponents x1 x3ctr p65 p65pack b5_c3 v61_c3 v81
v4/maps                        the 70 official ladder maps
v4/maps_pooltrain|pooltest|poolfresh   pool-calibrated generated maps (600 train / 300 test / 249 fresh)
v4/sdk/cpp, v4/cambc.toml, v4/mkvar.py
tools/viz/mapmake4|5|6.js + v2_0_0.wasm + eng.js   map generators (mapmake6 = pool-calibrated)
```

Six larger suites (about 1.7 GB) are not in the repo: `maps_real250`, `maps_real200b`, `maps_mazetest`, `maps_test4`, `maps_new4`, `maps_maze`.
- `bash agent2/lab/regen_maps.sh` rebuilds them from fixed seeds, identical to Agent 2's (the first maps of every suite were checked byte for byte).
- `final_check.sh` needs `maps_mazetest` and `maps_real200b`. `nn_rl3.py` trains on `maps_real250` 10% of the time; without it, the other suites' weights renormalise. The imitation / DAgger pipelines use `maps_test4`, `maps_new4` and `maps_maze`.
- More pool-like maps: `node tools/viz/mapmake6.js v4/maps_X 300 SEED`.

## Setup

1. Copy `cambc.exe` (the cambc 4.0.0 CLI; check with `v4/cambc.exe --version`) into `v4/`. The scripts call `v4/cambc.exe run-batch` and `v4/cambc.exe build`.
2. Install Python 3.12 with numpy and PyTorch with CUDA: `pip install torch --index-url https://download.pytorch.org/whl/cu128`. An NVIDIA GPU is required: `nn_rl.py`, `nn_rl3.py` and `nn_distill.py` run the network on `cuda`.
3. Install Node 20+ (for the map tools).
4. Use Windows with Git Bash, which is how this was run. The RAM watchdog calls `powershell`; on other systems it reads "99 GB free", so watch RAM yourself.
5. Run every command from the workspace root with `python -P`.
6. Build the league bots once (the scripts build only the network bots and the candidates):
   `cd v4 && for b in v92 x1 x3ctr p65 p65pack b5_c3 v61_c3 v81; do ./cambc.exe build bots/$b --release; done; cd ..`
7. Rebuild the map suites that are not in the repo: `bash agent2/lab/regen_maps.sh` (see Layout).

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

**Macro-policy RL, the current main run.** Each iteration is 800 games, about 12 minutes on Agent 2's PC; a held-out check runs every 2 iterations.

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

**Fuel-fit bots and the fuel probe.** Build flags go after the weights header. All of these need `A2_NN=11 A2_NN_MACRO=1 A2_NN_FAST=1`.

```bash
python -P agent2/lab/nn_export.py agent2/student_i2.pt student agent2/student_i2_w.h
python -P agent2/lab/nn_mkbot.py nnp agent2/student_i2_w.h A2_NN=11 A2_NN_MACRO=1 A2_NN_FAST=1 A2_NN_PIPE=1 A2_NN_RESERVE=5000 A2_NN_VALID=1 A2_NN_BEH=0 A2_NN_TTL=30 A2_FUELLOG=1
python -P agent2/lab/fuel_probe.py nnp v92 maps:0:5
```

Leaving out `--fuel` uses the real per-turn fuel. With `A2_FUELLOG=1` the replay's `team-X.stdout` holds `fuellog` lines (overruns) and `nnpipe` lines (decisions, stage cost estimates). Bots built with `A2_NN_FUEL=1` also print `NNFUEL` lines (fuel per decision), which `fuel_probe.py` summarises; `A2_NN_PROF=1` adds the per-stage profile lines `NNPROF` and `NNFPROF`.

**The whole pipeline from scratch** (records data with the real engine; see the script headers).
- `nn_pipeline.sh TAG`: recorder (v92 + `nnrec.cpp`), record, label, train, export.
- `nn_dagger.sh I WEIGHTS.h LABELS.npz:frac ...`: one DAgger iteration for the target head.
- `nn_rl.py`: the earlier target-only PPO (RL 2).
- `nn_v3.sh`: layout 3 (set `NN_LAYOUT=3`).

## Key settings and gotchas

- **Fuel.** Every result above is with fuel effectively off (20M) for both sides. The real budget is 10M on the draft turn, 200k on a champion's first turn, then 100k per turn, and unused fuel doesn't carry over. v92 uses a median of 56k per turn.
  - Cost per decision: teacher about 1.13M; student about 109k with the fast path (network 83k, features 25k).
  - A bot out of fuel is suspended and finishes on the next round's fuel, which loses that turn. The engine doesn't report it as a fault, so check `A2_FUELLOG` overruns.
  - `A2_NN_PIPE=1` spreads a decision over several turns, using only the fuel left after v92's turn minus `A2_NN_RESERVE`. Holding decisions is the open problem: every 4 turns applied 3 late scored 23.5% against 57.0% for deciding every turn.
  - Don't use the SDK's `fuel_pause` / `fuel_resume`. Free compute through them would be exploiting the platform.
- **Determinism.** A map + side + pair of bots is always the same game. More games need more maps, and a per-map fit against one opponent is memorisation (see x3ctr, v92 vs v81 / x1).
- **Design lessons.** Forcing the network's fight / flee verdict cost 18 points, and replacing v92's routines with network options cost 6–10. Always start the network as a residual on v92: the option head ships as "none".
- **Layout 3** (24 groups, ally claims, map id) is wired end to end and C++ matches PyTorch to 0.009, but behaviour cloning failed in play (17.9%). It needs DAgger with the RL network as the expert running inside the same bot.
- **Build flags** (`nn_mkbot.py NAME WEIGHTS.h FLAGS`):
  - `A2_NN=3` target + bank; `A2_NN=11` + options; `A2_NN_MACRO=1`;
  - `A2_NN_RL=1 A2_NN_RL_T=0.4 A2_NN_OPT_T=1.0` for rollouts;
  - `A2_NN_LAYOUT=3`;
  - `TOP_LADDER_TABLES=0 TOP_A2_LADFIT=0` switch off v92's tables;
  - `BASE=nnrec A2_NNREC=4` makes a recorder (with `A2_NNREC_LAYOUT=3` it logs layout-3 features);
  - fuel fit: `A2_NN_FAST=1`, `A2_NN_PIPE=1`, `A2_NN_RESERVE=N`, `A2_NN_CHOLD=1` (keep the decision in force during contact);
  - held decisions: `A2_NN_EVERY=k A2_NN_LAG=l` (simulated at any fuel), `A2_NN_VALID=1` (drop targets that have finished, take the next choice), `A2_NN_BEH=0|1|2` (v92 banks / network may only force a bank / network's bank gate), `A2_NN_TTL=N` (expire a decision after N rounds).

## Status (4 Nov, about 01:20)

Full findings are in `../README.md` and in `agent2/EXPERIMENTS.md` (E120).

- **Macro RL:** paused at iteration 2 on Agent 2's PC. To resume, run only the `python` command above, which continues from `state.json`.
- **Running on Agent 2's PC:** fixes for held decisions, tested on 498 fresh games against v92, including the pipeline at real fuel.
- **Next, in order of expected gain:**
  1. a fuel-fit bot that keeps its gains at real fuel; if the fixes aren't enough, train on rollouts that include the decision delays;
  2. resume macro RL, with team candidates like x3mf2 added to the opponents;
  3. layout 3 with DAgger;
  4. fight learning.
- **Nothing has been submitted.** Submitting and ladder trials are the user's decision.
