# Handover: lead role, team DOOMSDAY (CAMBC 2026), 3 Nov 2026

Objective information only: how the competition works, what the game and tools do, what exists, what was tried and
what it measured. No recommendations.

## 1. Objective

Owner: Rishik (rishik.siripurapu@gmail.com). Stated goals: a bot that wins the competition; climb the ladder; do not
lose to teams rated below 2000. Rules the owner set (still in force):
- A new bot counts as better only at **> 60% head-to-head vs the current best**; notify the owner (ntfy) at > 53%.
- Never cut an experiment's size to save compute.
- Machines should not sit idle without reason. The 5070 must not run past 02:00-03:00 UTC.
- The owner allowed the lead to queue platform match groups, download matches and switch the live version for
  testing (switch back to the best known bot afterwards).
- Do not edit or push over teammate Tamim's work (his branches). Do not push to `main`, `lab/box`, `ops`,
  `experiment/*`, `research/*`, `max/*`.
- ntfy topic for the owner: `https://ntfy.sh/bashcode` (bots ready to test, decisions).

## 2. The competition

- Platform: https://2026a.battlecode.co.uk (Cambridge Battlecode, "CAMBC"). Team: **DOOMSDAY**, team id
  `fcf5f666-ea55-4da0-b8d4-97c64bb37236`.
- Ladder on 3 Nov ~14:00 UTC: DOOMSDAY rank 68, rating 2016 (2,945 matches). Top: Mite 2599, Intercontinental Fish
  2568, Univardisty of Shingtonwash 2509. Rank 30 ~2173, rank 50 ~2069. Snapshot: `data/ladder/duel/ladder_20261103_p*.json`.
- Language: C++ compiled to wasm with the official CLI `cambc` 4.0.0 (`tools/vendor/cambc.exe`), engine 2.0.0.
- Submissions: `cambc submit bots/NAME --note ...`. A new upload cancels any other queued compile. With mode "follow
  newest ready version" a compiled upload goes live automatically; `cambc submissions activate N` pins a version.
- Match groups (unranked, 5 games): `cambc match-groups create <teamId> --maps m1,..,m5 --sides a,b,...`; they always
  play our **active** version. Quota: 50 groups per rolling hour, shared with the website.
- Other CLI: `cambc ladder --json --page N`, `cambc matches list --team me --kind ranked|unranked --json`
  (paginate with `--cursor`), `cambc matches summary --json -o F <id>` (rate-limited: two at a time),
  `cambc match-groups download <groupId> -o F.zip` (zip of 5 game zips, each with `replay.repl26a` and our logs),
  `cambc bundle bots/NAME --output F.zip`, `cambc build bots/NAME --release --output F.wasm`.
- Match listings do not say which of our versions played; `cambc submissions list --json` gives createdAt / statusAt.

## 3. The game (engine 2.0.0 facts used by the code)

- Draft of champions, then up to ~2000 rounds; a team wins at 1,000 banked ("submitted") gems, otherwise by score.
- Champions: Ryth, Vesper Vale, Vendetta, Cassi + Issac (one pick, two bodies sharing fate), Stellar, Prism, Marcella,
  Willow, Ren, Varg, Tavi, Heart of Ruin. Platform character ids in match listings differ from the SDK enum; mapping
  in `data/ladder/char_ids.json` (0 Ryth, 1 Vesper, 2 Vendetta, 3 Cassi+Issac, 5 Prism, 6 Marcella, 7 Willow, 8 Ren,
  9 Varg, 10 Tavi, 11 Heart of Ruin).
- Camps (wolf, elk, golem, monolith, harmless) in groups; clearing gives gold and gems; camps respawn. Gems are
  carried and banked at altars; **a killed champion's carried gems go to its killer** (`bots/x3/src/common.h` ~2032).
- Gold buys items: shards (30 gold, + growth of one stat) combine 5 -> emblem with a passive. Families: monster
  (+15% camp damage), power (counts as 6 shards), durability (-10% damage taken), treasure (+10% gold), jungle
  (-30% camp damage taken), home, bruiser (5 of the stat + 1 of each other), tribute, capture, prospector, hunter,
  skirmish, greed, collectors (SDK `sdk/cpp/cambc.h`). Consumables: teleport crystal, altar lock.
- Fuel: counted per wasm instruction; 10M draft, 200k first turn, 100k per turn. Host-side bitboard/BFS calls are
  cheap relative to wasm loops. Running out of fuel ends the turn ("fuel-out").
- Games are **deterministic** per (map, side, both binaries). Any change to compiled code can change fuel use and
  so later decisions ("fuel chaos"); a do-nothing code change (X1_NOOP) flipped 4-7 of 172 local games.
- Map pool: 86 maps (`maps/ladder-pool`, from `cambc maps`). Map files may hold only the authored half; runtime map
  fingerprints the bot computes are in `research/x3/counter_fp.json`.

## 4. Current bots

| Platform | File | Content | Build (default) |
|---|---|---|---|
| v75 / v80 | `v92_engine4.zip` (`bots/v92/src`) | **v92** (Agent 2, experiments E79-E89) | 5704d7ba41ac |
| v77 | x3ctr.zip | v92 + counter table fitted vs v92 | 96612d0a188b |
| v78 | x3mf.zip | v92 + per-map knob table (13 maps) | c3da892053a7 |
| v79 | x3ctr3.zip | x3mf + counter table fitted vs x3mf | 8464965b3817 |
| v82 | x3mf2 | v92 + per-map knob table (25 maps) | 711886abdda7 |
| v83-v86 | v92af / v92a3i / v92bru / v92own | v92 + one change each (see 6) | |

v92 was live at the time of writing (v80 = same zip as v75). The owner reports v92 wins against higher-rated teams
where other versions lost.

`bots/x3/src` is the development source. Its default build is byte-identical to v92 (5704d7ba41ac); every
experiment is a `#define` switch in `bots/x3/src/x1_config.h` or `common.h`, off by default. Note: some v92 values
are forced (unguarded) in `common.h` (e.g. `A3_FOCUS 0.0f`, `A3_NUMBERS 0`, `A3_ONE_OWNER 0`, `A3_ITEMS 0`); a
config define does not change them, the forced line must be edited. Bot folders for candidates are copies of
`bots/x3/src` with defines prepended to `x1_config.h`.

## 5. Measurement tools

- Local games: `python tools/dz.py smoke --name RUN --pool --map-dir maps/ladder-pool --opponent OPPBOT
  --candidate-bot BOT --workers N [--set FLAG=V ...]` -> `research/dz/runs/RUN/results.json` (per game outcome,
  banked, deaths, fuel; `evidence.zip` holds every game summary). Wrapper: `tools/x1_gate.sh BOT TAG "--set ..."`
  with env `SETS=pool OPPS="..." WORKERS=`. 172 games per opponent (86 maps x 2 sides). Local opponents are bot
  folders (v92, v86h, x1bru, v81hl, v86h-s2, x1, x3inv, proxy, dzs-*, public-*, mimic).
- Platform duel: `tools/replay/ladder_duel.py plan|run|report|restore` and `tools/replay/duel_pipeline.py`
  (uploads candidates one at a time, plays a baseline arm and each candidate on the same groups, restores the base).
  Plan in use: `research/x3/duel/duel_20261103.json` (12 opponents x 2 groups x 5 maps = 120 games per arm;
  opponents Claudus Maximus, QS2isLaw, MFF1, Jupiter, Nanyang Technological University, 剑桥夜爬者, HBH, Nameless,
  0xDEADBEEF, will think later, Shawarma 🐫, an iq too high). Logs `research/x3/duel/pipeline*.log`.
- Replay analysis (node, set `NFS_REPLAY_ENGINE=2.0.0`): `tools/replay/death_context.mjs`, `camp_clear.mjs`,
  `hurt_contact.mjs`, `fight_review.mjs` and others in `tools/replay/`. Summary analysis scripts:
  `research/x3/banking/*.py`, `research/x3/duel/arm_econ.py`, `death_compare.py`, `research/x3/local_pattern.py`.
- Search tools: `tools/x3_knob_es.py` / `tools/x3_mapfit.sh` (per-map knob evolution strategy),
  `tools/x3_mapfit_table.py` (writes `x1_mapfit.h`), `tools/x3_counter.py` (counter tables).

## 6. Development history (measured results)

Local results: 172 games per opponent on the 86-map pool, both sides. Duel results: 120 paired platform games vs the
12 opponents above, 3 Nov 13:00-15:00 UTC.

| Bot / change | Local result | Platform duel (wins / 120) |
|---|---|---|
| v92 | baseline (x3) | **52** |
| x3mf (13-map knob ES table) | +30 / 516 vs v92, v86h, x1bru; +14 / 516 vs v81hl, v86h-s2, x1 | ladder ~ equal to v92 |
| x3mf2 (25-map table) | +18 / 516 over x3mf; 55.2% head-to-head vs x3mf; held-out -9 | 50 (118 / 120 games identical) |
| v92af (X1_ANTIFEED 3, DIFF 4) | -13 vs v86h | 43 |
| v92a3i (A3_ITEMS 1) | not wired before | 42 |
| v92bru (V58_ITEM_PLAN 0: Treasure + Bruiser) | -11 vs x3inv | 44 |
| x3ctr (counter table vs v92) | 171 / 172 vs v92; below x3 vs v86h, x1bru | ladder within noise of v92 |
| Counter tables, 4 opponents (120 runs) | in sample +37 to +89; left-out opponent -20 to +3 | not played |
| Banking B1-B3 (X1_SAFEROUTE, BAGRISK2, RACEBANK) | -1 to -39 / 516 | not played |
| Feature sweep rows 1-26 (60 lines) | none above base | not played |

Queued in the duel pipeline at handover: v92own (A3_ONE_OWNER 1), v92gold (UB_GOLD_UNTIL 600), v92foc (A3_FOCUS 1),
v92num (A3_NUMBERS 1), v92esc (APEX_ESCAPE_SEARCH 1), v92safe (NOVA_EARLY_SAFE_UNTIL 200), v92fn (focus + numbers),
then a v92 re-run (`research/x3/duel/pipeline2.log`).

Measured facts from data:
- Ladder (234 games, 1-2 Nov): in losses the opponent clears ~2x the camps after round 900, takes 12.5 camps a game
  on our side (5.5 in wins), out-earns us 2367 vs 1530 gold by round 600 and buys ~130 Bruiser shards a game (us 4).
- Duel v92 (120 games): in losses, gold by round 150 is 440 vs 591 with no deaths yet; solo camp clears per game
  36 vs 47, 22 vs 18 rounds per clear. In wins, 50 vs 46 clears. Deaths 9.8 vs 9.1 per game; 46% of our deaths with
  no attack back (theirs 36%).
- Ladder v78 vs 剑桥夜爬者: 1:4, 24-40 deaths vs 1-7 kills per game, our gold flat after round 200.
- Agent 2 handover (`origin/agent2/v61-findings`, `research/agent2-v61/HANDOVER.md`): local self-play gains were flat
  or negative on the ladder; top-team rulebook (`research/v62/BIG_STRATEGIES.md` section 4): engage healthy with
  numbers, target closest, open with reach abilities, short chase, leave healthy, stack one stat per carry.
- Other research notes: `research/x3/ECONOMY_GAP.md`, `ANTI_OVERFIT.md`, `banking/BANKING_RESEARCH.md`,
  `research/x1/FEATURE_SWEEP_X3.md`, `research/v59/V59_LADDER_TESTS.md`, CAMBC Discord advice summarised in
  `ANTI_OVERFIT.md`.

## 7. GitHub and machines

- Repo: `https://github.com/Infosuii/neural-networkk-battlecode` (gh CLI logged in on the PC). Local clone:
  `C:\projects\cambridge battlecode\work\neural-full-stack`. Working branch: **`build/z-plan`**.
- Helper branches (helpers push only there): `build/z-plan-5060`, `build/z-plan-5070`, `build/z-plan-g3`.
  Separate agent "GX": branch `max/gigabot` (read only; its own bots `bots/gx*`, notes `research/gx/`).
- Comms: branch `comms/x1`, clone `C:\projects\cambridge battlecode\work\x1-comms`; folders `pc/` (jobs `pc/jobs/`,
  messages `pc/msgs/`, `STATUS.md`), `g5060/`, `g5070/`, `g3/`, `gmax/`. Helper scripts `tools/x1_comms.sh`,
  `tools/x1_watchdog.sh`. Job prefixes: J* (5060), K* (5070), L* (g3). Push conflicts: `git pull --rebase` and retry.
- Machines: PC (8 cores, 12 workers; C: drive was nearly full; old run folders in `artifacts/tmp/dz` are NTFS
  compressed; their results are in `research/dz/runs/*/evidence.zip`); 5060 (silent since ~02:30 UTC 3 Nov);
  5070 (owner's other machine, off overnight); g3 (laptop, 14 workers, silent since ~13:00 UTC 3 Nov). Only the PC
  is logged in to the platform CLI.
- Running on the PC at handover: the duel pipeline (above) and `tools/x3_mapfit.sh` on 29 maps
  (`research/x3/es/ORDER_ALL.txt`).
