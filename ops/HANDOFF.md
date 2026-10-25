# Handoff: v52 work (read this first)

Last updated by Claude Code on 2026-10-25. The repository is the only shared channel. This machine (the training box) runs every build, match and training run. You (on another laptop) direct it by pushing job scripts. See "Job runner" below.

## Goal and approvals

The user's goal is an "unbeatable" bot. The measurable target is ladder top 25; team **DOOMSDAY** is currently rank 87. Approved by the user (2026-10-25):
- queue unranked match groups against top teams;
- multi-hour CPU/GPU training runs on this machine;
- **submit v52 once it passes the gate** (below).

Never log in or enter credentials. The `cambc` CLI on this machine already has a session.

## What is live

- **v51** (`bots/v51`, submitted 2026-10-25 ~11:29 UTC as platform version 51) = v50 plus the moated-island fix (`bots/v51/CHANGES.md`).
- The ladder tracker writes `artifacts/claude_ops/logs/v51_ladder.log` on this machine. The job runner copies its tail into `ops/STATUS.md`.
- Baseline before v51 (800 ranked games): 51% overall; big_world 0/26; islands 3/25.

## Key findings (do not relearn these)

1. **The bot lineage** (v48, v50, v51 and `artifacts/baselines/heuristic-v1`) is a single hand-written heuristic codebase. Neural parts:
   - draft net (`A2_MLDRAFT`);
   - v50's camp net (`A2_CAMPNET`; 321 parameters; 3 hours of PPO in `work/neural-gameplay`; the extra 2 hours showed no reliable gain);
   - v48's danger net (`UB_DANGER`).

   On 56-game local A/B tests none had a measurable effect. Policy-v2 (behaviour cloning from 7.3M top-team decisions, `tools/policy_bc.py`) learned nothing that helps in games: 0 gems, 0-12 against heuristic-v1. Do not revive it.
2. **The bot is fuel-limited, and that dominates evaluation.** A behaviour-identical change that added a few instructions in hot code (`open_call_by_lower` and the group-scoring loop) scored **70-98 (41.7%, -85 gem margin) over 168 games** against v51. The same no-op in a cold path played identical games, because the engine is deterministic.
   - Hot-path additions must be near-free. Gate code with a flag that is checked once per turn, never inside per-group or per-camp loops.
   - Making hot paths cheaper is likely the single strongest lever (an expected +5-10 win-rate points).
3. **Ladder losses are map-specific** (`tools/replay/ladder_report.py`). Over the last 800 games: stampede 0/28, big_world 0/26 (fixed in v51), boss_battle 1/16, islands 3/25 (fixed in v51), concentrated_wealth 3/21, elkring 7/24, swirl 6/19, monolith 6/18, fracture 5/13, yellow_brick_road 9/23. Most other maps are at 50-86%.
4. **stampede**: one camp (group 10, 20 monsters, 16,080 HP, 160 gems) holds all of the map's gems. Winners farm gold camps until about round 1,100, then the whole team clears it repeatedly and banks after each clear. We never attack it, because big-job joining is broken: `open_call_by_lower` ignores the team-size cap (the soak model says 7), and joiners count as initiators. A hot-path fix (v51b/v51c) won stampede but lost head-to-head because of the fuel cost (finding 2). Redo it with a once-per-turn flag, for example at the top of `score_groups`: return the sole gem group for healthy champions after round R, and let `fight_camps` staging gather the team.
5. **boss_battle**: gems are collected but never banked, because the altars are gated behind monolith camps (see `A2_ALTARFIX`, `no_bank`). Not yet diagnosed further.

## How to measure

- Builds: `engine.official_build(<dir with src/>, <out.wasm>)` (python `nfs.engine`), or `cambc build`.
- `tools/bot_match.py --a <dir|wasm> [--b <wasm>] --maps ... --out artifacts/evaluations/<fresh>`. Default B is heuristic-v1.
- `artifacts/claude_ops/bench28.sh <a.wasm> <b.wasm|""> <out>`: 28 development maps × 2 sides, 4 shards.
- **`artifacts/claude_ops/bench2.sh <cand dir> <opp dir> <out> [seeds]`**: bench v2, 168 games with `NOVA_SEED` 1-3 for both bots. Use it against `bots/v51`.
  - **Gate:** win rate ≥ 0.58 and margin ≥ +60 against v51, plus both sides won on the target maps.
  - Check against heuristic-v1 too.
  - The 12 `final` maps in `evaluation/schedules/map_partitions.json` are a holdout. Run them once, at release.
- Per-team statistics: `tools/match_stats.py <eval dir>`. Aggregate: `tools/bench_summary.py <dirs>`.
- **Diagnose a map**:
  1. Copy the bot and prepend `#define APEX_LOG 1` to `src/common.h`.
  2. Silence the per-turn GROUP dump in `src/world.cpp` (`if (APEX_LOG)` → `if (0)`, near line 179).
  3. `cambc run <a.wasm> <b.wasm> --map <path> --rounds 600 --release --log-limit 12000000 --out-dir <dir>`.
  4. The output `.repl26a` is a ZIP: unzip it and read `team-a.stdout` (`strings`).

  Champion lines look like `R<round> <type> p(x,y) hp g<gems> $<gold> <mode> G<group>`. Frozen positions or never-changing modes reveal bugs.
- Ladder:
  - `cambc matches list --team me --kind ranked --json` (paginate with `--cursor`);
  - `cambc matches download <id> -o <file>` (a ZIP holding the replay and our team's logs);
  - decode replays with `tools/replay/decode_replays.mjs`;
  - `tools/replay/track_submission.py --since <iso>`.
- Unranked match groups against a team: `cambc match-groups create <team uuid> --maps a,b,c,d,e`. They use our currently submitted bot. Team UUIDs come from `cambc ladder --json`.

## Environment on this machine

- Repo: `C:\projects\cambridge battlecode\work\neural-full-stack`.
- Python: `C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe`.
- Env: `PYTHONPATH=<repo>/python`, `TMP=TEMP=<repo>/artifacts/tmp`, `PYTHONDONTWRITEBYTECODE=1`, and `C:/msys64/ucrt64/bin` prefixed to `PATH`.
- CLI path: `config/paths.json` → `cli`.
- Data (local only):
  - `artifacts/local-only/replays-20261023` (244,981 decoded matches, `team_ratings.json`);
  - `artifacts/local-only/doomsday-losses` (our recent ranked list and downloaded losses);
  - `artifacts/local-only/bot-v48|v50|v51` (+ wasm).
- Hardware: 20 CPU threads, RTX 5070 Ti laptop GPU with 12 GB. One bench2 run uses 12 match processes and takes about 25 minutes.

## v52 plan (`artifacts/claude_ops/V52_PLAN.md`), status

- [x] A. bench v2 plus the noise-floor control (finding 2).
- [ ] B. Map fixes, in this order: stampede (finding 4), boss_battle, concentrated_wealth, elkring, swirl, yellow_brick_road; then a pass on deaths. One fix per candidate; gate each with bench2.
- [ ] C. Fuel profiling and hot-path optimisation (`PROF`/`PROF_CHECK` macros in `bot.cpp`). Probably the biggest gain.
- [ ] D. Neural:
  - a draft win-probability model from the 245k archive plus our ladder games (our win rate ranges 39-58% by pick);
  - camp-net PPO is low value (finding 1).
- [ ] E. Release: gate, holdout, `cambc submit bots/v52 --note ...`, then ladder tracking and match groups.

## Job runner (how to make this machine do work)

`ops/runner.sh` runs detached on this machine against a separate clone at `C:\projects\cambridge battlecode\work\ops-runner`, on branch **`ops`**. Every 10 minutes it:
1. `git pull`s the `ops` branch.
2. Runs each `ops/jobs/pending/*.sh` in name order. Each job runs with `bash`; `REPO` is set to the training checkout above, and the environment variables above are exported. Jobs run sequentially and synchronously, so start long training detached inside your job (`nohup ... &` or PowerShell `Start-Process`) and write its progress to a file your later jobs can `cat`.
3. Moves each finished job to `ops/jobs/done/` and its log (last 400 lines) to `ops/jobs/logs/<job>.log`.
4. Rewrites `ops/STATUS.md`, then commits and pushes.

Workflow from the other laptop:
1. `git checkout ops && git pull`.
2. Add `ops/jobs/pending/NN-name.sh`, commit, push.
3. Within about 10 minutes, `git pull` and read `ops/jobs/logs/NN-name.log`.

Bot code changes: push them to `main` (or a branch). A job then runs `git -C "$REPO" pull` or checks out your branch before building. Stop the runner by pushing the file `ops/STOP` to the `ops` branch.
