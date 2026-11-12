# Handoff: the "mimic" bot (a new-architecture local stand-in for the top teams)

## Continuation completed, 2026-10-27: read this first

The text below is the original v6 handoff. Current source/weights are **v9**. See `README.md`, `MODEL.json`,
`TRAINING.md`, `PARITY.json`, `LOCAL_RESULTS.json`, `ECONOMY.json`, `STYLE.md`, and `VALIDATION.md` here.

The important new discovery is a recall-cancellation freeze: the bot cancelled after observing and retained false
move/attack/cast permission bits. The extractor also dropped those teams' action rows. Both now use the
post-cancel state. Also fixed partial-clear dead navigation roots, respawn availability, and single capturer
ownership; added crew/camp-damage features and strict actual-shared-snapshot parity.

Final checks: 39,288 observations/memories and 37,867 complete-field decisions match exactly, including NEETCoders;
WASI/SIMD and native core regressions pass. v9 vs v65: **0/240 wins, -912.6 gems** (v6 -967.8). Opening capture gold
at R250: 407.5 vs 235.4 before cancellation correction; spawn idling falls from 35.7% to 9.6%. Still far too weak.
Six arms, two seeds each: 14/15 existing ladder pairs agree, rank correlation +0.94 (self-play 9/15, +0.43), but
all six arms beat mimic 240/240, team difficulty r is only +0.18 and per-game r -0.13. Do not treat this as a gate.

**What to do next now:** reduce fuel suspensions (83/game), diagnose low reward yield despite corrected clearing
time, then improve retreat/action ordering against top-team situation rows. Use fresh validation arms/opponents;
the current six-arm comparison is retrospective. Keep the cancellation regression and all original standing rules.

---

You are continuing work started by Claude Code. Read this whole file before acting. The workspace is
`C:\projects\cambridge battlecode\work\neural-full-stack` (git branch `claude/compare-fix-replay-decoder`). Python is
`../neural-gameplay/.venv/Scripts/python.exe` (torch + CUDA available). The CAMBC CLI is `tools/vendor/cambc.exe`.

## What the user asked for

1. Earlier: "a local test opponent that fights like a top team, built from their games the crawler now collects …
   make no mistakes". That produced `bots/proxy` (v65 code + top-team drafts/items/recall trick), committed as 76d2337.
   Result: v65 beats it by +250; it did not predict the ladder better than self-play (`research/proxy/README.md`).
2. Then: "Under all of that it is still v65's code, and it's weak. if this is the problem then change that and rewrite
   a new architecture instead of building off something". That is the current task: `bots/mimic`, written from
   scratch (no v65 code), with decisions imitation-learned from top-team replays.

Standing rules from the user: never log in or enter credentials; don't commit other agents' work; leave
`config/paths.json` (locally modified) uncommitted; the untracked `bots/v66x_*`, `bots/v66y_*`, `compile_commands.json`
files and `data/ladder/v57_games_20261026.json` are not ours. Submitting/activating bots or queueing unranked ladder
games was allowed earlier ("you can spam unrateds"), but nothing for mimic has been submitted. Commit/push only when
the work is in a good state; end commit messages with the attribution lines the user's tooling asks for.

**Nothing of the mimic work is committed yet.** All files below are new/untracked.

## Architecture (all new code)

- `bots/mimic/src/core.h`, `core.cpp`: the SDK-free **shared core**. Map/static data, per-champion memory, candidate
  generation and features for six decisions, scoring, parity hashes. Compiled into the bot AND (via
  `tools/mimic/kernel.cpp`, built to `artifacts/tmp/mimic/kernel.wasm` by `tools/mimic/build_kernel.py`, same wasi-sdk
  clang, -O3 -msimd128) into the offline extractor, so training features are byte-identical to runtime features.
  Decisions (feature counts in core.h `NF_*`):
  - objective (conditional logit over: the 20 nearest camp groups = farm, bank, home, each visible enemy = fight), 58 f.
  - move (stay, 8 walks, dash ring tiles), 32 f; target (none + attackable units), 19 f; cast (none + each ready
    non-dash ability on each legal target), 24 f; recall (logistic), 10 f; tribute (logistic), 6 f.
- `bots/mimic/src/bot.cpp/.h`: runtime. Reads the game with the same SDK host calls the extractor mirrors
  (`sdk_champion`, `sdk_camp`, `sdk_camp_group_state`, …), builds distance fields with `bc::distance_field` (lazily,
  fuel-budgeted, verified identical to the kernel BFS), shares coarse ally positions in the 8-byte shared memory
  (10-bit slot per ally; allies are NOT visible outside own vision via the API), shops from `team_tables.h`
  (copied proxy tables: per-team per-map drafts and item milestones), executes decisions. `main.cpp` keeps the Mimic
  object static (it is ~100 KB; on the wasm stack it crashed everything).
- `bots/mimic/src/common.h`: `MIMIC_TEAM` (index into weights.h kTeamNames, -1 pooled), `MIMIC_PARITY`, `MIMIC_FUEL`
  (fuel probe), `MIMIC_TRACE` (decision trace), `MIMIC_STICKY`, `NOVA_SEED` (tie-break noise; local_duel varies it).
- `bots/mimic/src/weights.h`: generated by `tools/mimic/train.py` (row 0 pooled, then 13 teams; move/target/cast per
  hero). Current file = `artifacts/tmp/mimic/weights_v6.h`.
- `tools/mimic/extract.mjs`: replays → training rows. Pass 1 records turns/actions and hindsight labels (objective =
  next event within 60 rounds; bank/home "trips" relabelled; move = first walk/dash; target = first basic attack; cast
  = first non-dash cast; recall = real recall, not the perma-recall trick). Pass 2 rebuilds each top-team champion's
  observation through `Game_API_*` from its own perspective, simulates shared memory, writes rows. `--parity` mode
  writes kernel hashes instead. Run: `NFS_REPLAY_ENGINE=2.0.0 node --no-warnings tools/mimic/extract.mjs --index
  artifacts/local-only/proxy/replays/index.json --replays artifacts/local-only/proxy/replays --teams
  research/v59/duel_top1.json --out artifacts/local-only/mimic/rows-vN --workers 12` (~12 min, 1,177 replays).
- `tools/mimic/train.py --rows <dir> --out <weights.h> --report <md>`: L-BFGS conditional logit / logistic,
  hierarchical (pooled → hero → team), held-out report. ~10 min on GPU.
- `tools/mimic/parity.py --maps …`: builds a MIMIC_PARITY bot, plays it vs itself, compares every turn's
  observation/memory/feature hashes with the extractor on that replay. Last run (`artifacts/evaluations/
  mimic-parity/p9`): maps 10/10, distance fields 894/894, observations ~28,000 identical; 13 ally mismatches, all
  right after an ally's fuel-suspended turn (shared-memory write timing; parity builds run out of fuel often).
- `tools/proxy/local_duel.py` was extended: `--proxy bots/mimic --per-team` sets MIMIC_TEAM per opponent team.

Data: `artifacts/local-only/proxy/replays` (1,177 engine-2 replays: 120 v65 duel + ~1,050 top-vs-top),
rows `artifacts/local-only/mimic/rows-v6` (latest; older rows-v5 may still exist and can be deleted).

## Current results (v6 weights + two-stage decisions, uncommitted)

Held-out imitation accuracy (`artifacts/tmp/mimic/train_v6.md`): objective 0.596 (nearest-group rule 0.456), move
0.670 (greedy 0.453), target 0.944 (0.779), cast 0.910 (0.866), tribute 0.715, recall = base rate (it is sampled
with its probability at runtime, a per-turn hazard).

Local, 120-game duel schedule v65 vs mimic (`artifacts/evaluations/mimic-duel/v6b-v65`): **v65 wins 120/120,
margin +968**. Fingerprint, mimic vs top teams against v65 (`research/proxy/style_ladder.json` top@v65):
deaths 14.7 vs 6.6, gold 1,017 vs 6,773, back_off 0.097 vs 0.263, walk_in 0.157 vs 0.380, attack|in_range 0.615 vs
0.676. So it is far weaker than v65, mainly economy (farming throughput) and fights it loses.

Bugs found and fixed along the way (keep them fixed): signed vs unsigned hashes in JS (`>>> 0`); stale `exact`
flag on reused ally slots; groups must be queried all (engine reports some respawning groups out of vision);
Game_GetNumCamps undercounts — use the map API group listing; bush-hidden camps (bush clusters in core);
champions blocking their own respawns (feature `blocks_respawn`, memory keeps engine state in vision); fuel
(Obs reset was 17k fuel, objective features were O(groups²) — now capped at 20 nearest groups, histogram ranks;
re-decide objective every 3rd calm turn); argmax freeze (now `act_or_not`: act only if acting candidates hold >50%
probability, then take the best acting candidate); bot stack overflow (static Mimic).

## What to do next (suggested order)

1. Find why farming throughput is ~15% of the top teams'. Use the trace build (copy src, set `MIMIC_TRACE 1`, build,
   run, read `engine.team_stdout(folder, 'a')`, lines `TR` objective, `TM` move, `TA` attack). Seen so far: all five
   champions converge on the same small group; teammates wait 2-5 tiles away while one fights; solo fights with big
   camps. Ideas: a team-level assignment feature (allies' objectives in the 4 spare shared-memory bits, or "allies
   already at this group"), capture logic, earlier retreat from camps.
2. Fights: v65 kills it ~8 times a game. Compare per-situation behaviour with top teams (fight_style rows).
3. Every feature change needs: rebuild kernel → re-extract → retrain → copy weights → parity check → duel.
4. When it is meaningfully stronger, validate as in `research/proxy`: run `local_duel.py` for each ladder arm
   (v60, v61, v62c, v65, v66a, v66b) against `--proxy bots/mimic --per-team --seeds 1 2`, then
   `tools/proxy/compare.py --ladder research/proxy/ladder_arms.json --run mimic=<dirs> --run self-play=<dirs>`.
5. Write `research/mimic/README.md` (method, parity, training table, local results, ladder validation, limits,
   reproduce commands), update `bots/README.md`, commit (not config/paths.json or others' files), push.

## Gotchas

- In this Windows Git-Bash tool environment, heredoc'd Python lost backslashes (`\\n` became a newline, regex `\\`
  halved). Write edit scripts to files and run them, or use a real editor.
- Bot printf output is not in the runner log: read it with `python/nfs/engine.py` `team_stdout(folder, side)`;
  per-turn output is truncated by the engine (newlines can be lost).
- Repo files use LF except some bot sources; write with `newline='\n'`. Don't commit `.cambc/` or
  `compile_commands.json`.
- Local maps: `maps/local-benchmarks/<name with _ replaced by ->.map26a` (identical to the platform pool).
- Fuel: 100k per turn (2x first turn). Measure with the `MIMIC_FUEL` build; each probe mark itself costs ~2.3k.
