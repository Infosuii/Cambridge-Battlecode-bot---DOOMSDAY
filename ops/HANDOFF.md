# Handoff: bot development from v52 onward (read this first)

Written by Claude Code on 2026-10-25, when development was paused at v53. The next agent (GPT/Codex) works on **another device** and should set it up with `ops/SETUP.md`. Everything needed to build, test, analyse and submit is in this repository. Only bulk training data stays on the original laptop, the "training box" (§7), and none of the next steps need it.

## 1. Goal and standing approvals

- **Goal:** the user wants an "unbeatable" bot. The measurable target is ladder top 25; team **DOOMSDAY** (team id `fcf5f666-ea55-4da0-b8d4-97c64bb37236`) is currently rank 87, rating 1834.
- **Approved by the user (2026-10-25):**
  - queueing unranked match groups against top teams;
  - multi-hour CPU/GPU training runs;
  - submitting a new version **once it passes the gate** (§4).
- **Credentials:** never log in or enter them. The user logs the CLI in on each device (`ops/SETUP.md` §2).

## 2. Versions

Sources are in `bots/`; `src/` is exactly what `cambc submit` uploads. Each version's `CHANGES.md` has its measurements.

| Version | Platform | Content |
|---|---|---|
| v48 | - | heuristic lineage; draft net and danger net on |
| v50 | version 50 | v48 lineage plus a camp net (321 parameters, about 3 hours of PPO; `training/v50-campnet/`); danger net off |
| v51 | version 51, submitted 2026-10-25 11:29 UTC | v50 plus the moated-island fix (champions froze at camps behind two-tile hole moats: big_world, islands) |
| **v52** | **version 52, submitted 12:02 UTC, live** | v51 plus the sole-gem-camp rule (stampede) |
| v53 | not submitted | v52 plus the boss_battle gate rule, **switched off** (`A2_GATE_JOB 0`; rejected 0-6/1-5/1-5). Use it as the work base. |

`artifacts/baselines/heuristic-v1` is the frozen local baseline from the same lineage; do not modify it.

## 3. Findings (do not relearn)

1. **One heuristic codebase.** v48, v50, v51, v52 and heuristic-v1 differ by only a few hundred lines. Neural parts:
   - draft net (`A2_MLDRAFT`);
   - camp net (`A2_CAMPNET`; its extra 2 hours of training gave no reliable gain);
   - danger net (v48, `UB_DANGER`).

   In 56-game local A/B tests none had a measurable effect. The policy-v2 network, trained by behaviour cloning on 7.3M top-team decisions (`tools/policy_bc.py`, `artifacts/claude_ops/NIGHT_REPORT.md`), learned nothing useful in games: 0 gems, 0-12 against heuristic-v1. Do not revive it.
2. **The bot runs at its fuel limit, and that dominates evaluation.** The engine is deterministic.
   - A behaviour-identical change that added a few instructions in hot code (`open_call_by_lower` and the group-scoring loop) lost **70-98 with a -85 gem margin over 168 games**.
   - The same no-op in a cold path played identical games.
   - Fuel is also charged for memory fills (1 per byte, per a comment in `bot.cpp`).

   Rules that follow:
   - Put new logic behind a check that runs once per call or once per turn, never inside per-group or per-camp loops.
   - Making hot paths cheaper is probably the strongest untried lever.
3. **Ladder losses are map-specific.** These are the 800 ranked games before v51 (`data/ladder/doomsday_ranked_800_20261025.json`, analysed with `tools/replay/ladder_report.py`); overall 51%.

   | Map | Record | Status |
   |---|---|---|
   | stampede | 0/28 | v52 fix |
   | big_world | 0/26 | v51 fix |
   | boss_battle | 1/16 | open |
   | islands | 3/25 | v51 fix |
   | concentrated_wealth | 3/21 | open |
   | elkring | 7/24 | open |
   | swirl | 6/19 | open |
   | monolith (holdout) | 6/18 | open |
   | fracture (holdout) | 5/13 | open |
   | yellow_brick_road | 9/23 | open |

   Most other maps are at 50-86%. Early ladder after v51: 14/20 (70%), with none yet on the target maps.
4. **stampede (fixed in v52).** One group holds every gem (20 monsters, 16,080 HP, 160 gems). Big-job calls never filled, so the camp was never attacked.
   - Fix: `A2_SOLE_GEM` at the top of `score_groups`.
   - Result: stampede 6-0 locally at every tested start round, banking about 870 gems against v51's 100.
5. **boss_battle (open).**
   - The altars' only access tiles are monolith camp tiles: group 16 at (24,20), 2 members, 400 gems, 600 gold, strength 200, range 5, 20,000 HP. Banking opens only while that group is dead. See `A2_ALTARFIX`, `no_bank`, `altar_gated`, `gate_camps` and `World::update_altar_gates`.
   - Our carriers hold 170-570 gems each from round ~900 and never bank. Even v52 against v52 collects about 2,500 gems but banks only about 300. Top teams bank first at rounds 645-1,100.
   - Rushing the gate with the whole team (v53 `A2_GATE_JOB`) gets the team killed.

   Next ideas:
   - decode top teams' winning boss_battle replays to see when and how they kill group 16 (draft, items, timing);
   - take the gate only late, with full items, as a whole-team job;
   - change the boss_battle draft, which is fixed to types 3, 5, 9, 11 (`APEX_MAPDRAFT`, `draft.cpp`).
6. **Methodology for map bugs** (it found the v51 and v52 bugs in about an hour each). Reproduce the bug with a logging build (§5), look for champions whose position or mode never changes, find the code path, and fix it cheaply.

## 4. Measuring and the gate

- **bench v2:** `bash artifacts/claude_ops/bench2.sh <abs cand dir> <abs opp dir> <abs out prefix> [seeds]`.
  - It plays the 28 development maps × both sides × `NOVA_SEED` 1-3, rebuilding both bots per seed (the shipped bots use seed 1): 168 games.
  - Single maps: `MAPS_OVERRIDE="00stampede" bench2.sh ...`.
- **Gate** for a new version against the live one:
  - (a) Every target map is won on both sides across seeds, by a clear margin.
  - (b) Overall win rate ≥ 0.47 and margin ≥ -30. This is the noise floor: the behaviour-identical control scored 0.417 and -85.
  - (c) No regression on the 12 holdout maps (`HOLDOUT=1 MAPS_OVERRIDE="<the 12 final maps>" bench2.sh ...`). Run them once per release.
  - A map whose six games mirror the opponent's exactly (A-side margins = -B-side margins) is untouched by the change.
- **Other tools:**
  - `tools/bot_match.py`: any two bots; the default opponent is heuristic-v1.
  - `artifacts/claude_ops/bench28.sh`.
  - `tools/match_stats.py` and `tools/bench_summary.py`.
- **Results so far** are in `artifacts/claude_ops/results/*.txt`:
  - `b2-v52a-vs-v51`: 83-85, +6.7;
  - `b2-holdout-v52-vs-v51`: 36-36, +29.6;
  - `b2-noop-vs-v51`: the noise floor;
  - `bb-gate*`: the rejected gate rule;
  - `st-sole*`: the stampede sweeps.

## 5. Diagnosing a map (logging build)

1. Copy the bot and prepend `#define APEX_LOG 1` to `src/common.h`.
2. In `src/world.cpp`, change the per-turn GROUP dump's `if (APEX_LOG)` (near line 179) to `if (0)`. Leave it on and run 2 rounds when you want the camp-group list.
3. Build with `engine.official_build(dir, out.wasm)` (python `nfs.engine`) or `cambc build`.
4. Run `cambc run <a.wasm> <b.wasm> --map maps/local-benchmarks/<map>.map26a --rounds 600 --release --log-limit 16000000 --out-dir <dir>`.
5. The `.repl26a` output is a ZIP. Unzip it and run `strings` on `team-a.stdout` / `team-b.stdout`.

Champion lines look like `R<round> <type> p(x,y) hp g<gems> $<gold> <mode> G<group>`. There are also `BIG`, `DUO` and `MODES`/`DIAG` lines every 50 rounds.

## 6. Ladder and platform (needs the user's CLI login on your device)

- **Recent games:**
  - `cambc matches list --team me --kind ranked --json` (paginate with `--cursor`);
  - `tools/replay/ladder_report.py --matches <json> --ladder <ladder json>`;
  - `tools/replay/track_submission.py --since 2026-10-25T12:05:00Z --maps 00stampede 01big_world 01islands` for results since v52.
- **Replays:** `cambc matches download <match id> -o <file>` gives a ZIP with the replay and our team's logs. Decode it with `node tools/replay/decode_replays.mjs --out <x.jsonl> <replay.repl26a>`. Local replays are also ZIPs; extract `replay.repl26a` first.
- **Standings:** `cambc ladder --json --limit 100 --page N` (snapshot: `data/ladder/ladder_top400_20261025.json`).
- **Match groups** were queued 2026-10-25 around 12:15 UTC with v52 on stampede, big_world, islands, concentrated_wealth and elkring, against Hidden Altar Keepers (#80) and meow (#25). Their ids are in `data/ladder/match_groups_20261025.json`. Read them with `cambc match-groups show <group id> --json` or `cambc match-groups download <group id>`. New groups: `cambc match-groups create <team uuid> --maps a,b,c,d,e --sides a,b,a,b,a`. Match groups play our **currently submitted** bot.
- **Submit:** `cambc submit bots/vNN --note "..."`, only after the gate passes.

## 7. Data

- **In the repo** (`data/ladder/`, see its README):
  - top-400 ladder snapshot;
  - our last 800 ranked games, and our games since v51;
  - compact Bradley-Terry ratings (743 teams, 244,981 matches);
  - 46 decoded bad-map losses (gz) with metadata, and 30 user-supplied decoded losses (gz);
  - the queued match groups.

  The 40 maps are in `maps/local-benchmarks`.
- **On the training box only** (too large, gitignored):
  - `artifacts/local-only/replays-20261023`: the decoded 23 Oct archive, 244,981 matches, with per-replay team ids in `team_ratings.json`;
  - `artifacts/local-only/bc-top12k`: the behaviour-cloning dataset;
  - downloaded match ZIPs;
  - the original archive ZIPs in `C:\projects\cambridge battlecode\match summaries 23102026`.

  You can rebuild the archive analysis from fresh downloads with `tools/replay/decode_archive.py` and `team_ratings.py`. For a draft model, new ladder downloads (`cambc matches list/download`) are enough.

## 8. Training box (original laptop) reference

- Repo: `C:\projects\cambridge battlecode\work\neural-full-stack`.
- Python (CUDA torch 2.11): `C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe`.
- Hardware: 20 CPU threads, RTX 5070 Ti laptop GPU (12 GB).
- Optional remote control: `ops/runner.sh` on branch `ops`, with its clone at `work/ops-runner`. The user must start it there (`nohup bash ops/runner.sh > runner.log 2>&1 &`, or add `--status-only`). It then runs scripts you push to `ops/jobs/pending/` and pushes their logs; see `ops/jobs/README.md`. It is not running now.

## 9. Suggested next steps (in order)

1. Read the match-group results and the ladder since v52 (§6). Confirm the stampede, big_world and islands fixes on the ladder.
2. Fix boss_battle (finding 5), then concentrated_wealth, elkring, swirl and yellow_brick_road. Use the §5 method, one fix per version, and gate each one.
3. Fuel: profile the hot paths with the `PROF`/`PROF_CHECK` instrumentation in `bot.cpp` and make them cheaper without changing behaviour. Because of finding 2, measure every change.
4. Neural, only with A/B evidence: a draft win-probability model (map plus both drafts → winner) from ladder downloads. Our win rate ranges from 39% to 58% depending on our picks (`ladder_report.py`).
5. Release loop: gate → submit → track → match groups → repeat.
