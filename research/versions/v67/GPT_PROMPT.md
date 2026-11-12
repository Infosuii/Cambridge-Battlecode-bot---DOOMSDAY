# Task: build bot v67 that beats v65 in at least 220 of 240 local games

Work in `C:\projects\cambridge battlecode\work\neural-full-stack`, git branch `claude/compare-fix-replay-decoder`.
Python: `..\neural-gameplay\.venv\Scripts\python.exe` (torch with CUDA). CLI: `tools\vendor\cambc.exe` (engine 2.0.0).
Work autonomously until the goal is met or you have clear evidence that it can't be met. Don't stop at a plan.

## The goal and how it is measured (do not change the test)

- Create `bots/v67` (new directory). Any architecture is allowed: fork v65, rewrite from scratch, or mix in learned
  models. Use every mechanic the game offers.
- Pass condition: **v67 wins at least 220 of 240 games against v65** (`bots/v65`, unmodified), win = more tributed
  gems. The 240 games are the 120 (map, side) slots of `research/v59/duel_top1.json` times seeds 1 and 2:
  ```
  python tools/proxy/local_duel.py --plan research/v59/duel_top1.json --bot bots/v67 --name v67 --proxy bots/v65 --seeds 1 2 --workers 16 --out artifacts/evaluations/v67/<run>
  ```
  This takes a few minutes. Win count and mean margin are printed; `games.json` has every game.
  `local_duel.build` rewrites the line `#define NOVA_SEED 1` in `src/common.h`. It must exist exactly once in v67.
- Guards before you claim success:
  - Seeds 3 and 4 as a holdout. The two bots are deterministic per seed, so don't tune on 3/4.
  - No collapse against v61, v58 and v66b (run the same command with `--proxy bots/v61` etc.; v67 should win the
    majority).
  - 0 bot faults, fuel-outs comparable to v65's.
  - Report all of these honestly. Never claim 220/240 without the full run's output.
- Don't submit to the ladder or queue ladder games without asking the user.

## What we already know (read these first, they are the result of weeks of analysis)

- **`research/v67/PROBLEMS.md` first.** It is the measured summary of why our lineage loses:
  - no teammate positions in shared memory;
  - passive-emblem items (3% Bruiser against the top teams' 63%);
  - economy lost in the mid game through deaths;
  - deaths alone and outnumbered in our own half;
  - why earlier fixes failed.

- `research/v62/BIG_STRATEGIES.md`: the top teams' measured rulebook:
  - engage healthy, with numbers, at vision range;
  - hit the closest enemy;
  - open with the reach spell; double-hit with attack resets;
  - short chases; leave while healthy;
  - fight in their own half;
  - stack one stat per carry.
- `research/top-losses-20261026/README.md` (+ FAILURE_LEDGER.md): why our lineage loses. Same-match medians:

  | Measure | Us | Them |
  |---|---:|---:|
  | Gold | 3.7k | 7.2k |
  | Deaths | 13.5 | 3.7 |
  | Kills | 2.9 | 11.7 |
  | Gems lost to champions | 132 | 30 |

  Also: no Bruiser before R300; carries starved (Vesper/Marcella gold 0.9k vs 2.5k); lone 2v1s not avoided; idle
  champions (stationary 80+ rounds); gated-altar maps never banked; single-objective maps 0/8 to 0/23.
- `research/proxy/README.md`: top teams against v65 in the same 120 duel games, compared with v65's own figures:

  | Measure | Top teams | v65 |
  |---|---:|---:|
  | Deaths | 6.6 | 14.3 |
  | Back-off in contact | 0.26 | 0.39 |
  | Walk-in | 0.38 | 0.30 |
  | Focus | 0.32 | 0.25 |
  | Alone in contact | 0.18 | 0.23 |
  | Gems collected | 1,110 | 785 |
  | Gems banked | 911 | 525 |
  | Gold | 6.8k | 4.3k |

  v65 is the best ladder version (24/120 against the top 12, margin −386). v66a/b were better locally (+52) and worse
  on the ladder.
- `research/v58/V58_CLAUDUS_FINDINGS.md`: Claudus' economy. Vesper+Heart+Vendetta, Treasure at R88, 4.0 elk-size
  groups by R250 starting at R21.
- `research/mimic/` (README, HANDOFF, ECONOMY.json, STYLE.*) and `bots/mimic`: a from-scratch imitation bot. Weak
  (0/120 against v65), but its tooling is reusable:
  - a shared SDK-free core;
  - the replay extractor `tools/mimic/extract.mjs`, which rebuilds each top-team champion's own-perspective
    observation with `Game_API_*`;
  - `tools/mimic/parity.py`;
  - trained models on 9.7M top-team champion turns (`artifacts/local-only/mimic/rows-v6`).

  Bugs found there that any new bot must respect:
  - allies are invisible outside your own vision, so share positions in the 8-byte shared memory;
  - query every camp group's state (the engine reports some respawning groups out of vision);
  - camps inside bushes are hidden until you stand in the same bush cluster;
  - **standing on a camp's spawn tile blocks that group's respawn** (a denial weapon against the enemy, and a trap
    for yourself);
  - `Game_GetNumCamps` undercounts, so list camps through the map group API;
  - big objects (>~60 KB) must be static, not on the wasm stack;
  - linear argmax decoding freezes when "stay" is the single likeliest option;
  - fuel is 100k per turn (2x on the first turn): measure it.
- Data on this machine:
  - 1,177 engine-2 replays in `artifacts/local-only/proxy/replays` (index.json): about 1,050 top-vs-top games plus
    120 top-12 games against v65;
  - top-team per-map drafts and item milestones in `bots/proxy/src/proxy_tables.h` (13 teams);
  - meta crawl summaries in `artifacts/local-only/meta/20261027`;
  - tools: `tools/proxy/fight_style.mjs` + `style_report.py` (fight fingerprints), `tools/replay/*` (decoders,
    audits), `python/nfs/engine.py` (`run_match`, `team_stdout`, `replay_bundle`).
- The rules are in `C:\projects\cambridge battlecode\game rules\GameRules.md` and the API in `BotAPICpp.md`. The SDK
  header is `sdk/cpp/cambc.h`.

## Opportunities to exploit (check each with experiments)

1. **Fight with numbers.** v65 champions are often alone in contact.
   - Group into packs or a deathball that hunts isolated v65 champions with local superiority: a fight estimate from
     HP, damage, ready spells and stuns.
   - Coordinate through shared memory: team focus target, rally point.
   - Open with burst spells and stuns, double-hit with resets, kite as ranged.
   - A kill pays 100 gold plus the victim's carried gems, and sends it out for 60 rounds.
2. **Survive.** Leave at about 50-80% HP when not winning; walk away instead of recalling within reach (damage
   cancels a recall); never stand alone against two.
3. **Economy.**
   - Farm group sizes the team can clear fast.
   - Treasure on the gold carry (Vesper +33%).
   - Stack one stat per carry, with Bruiser/Power early.
   - Capture with exactly one champion (rewards split).
   - Bank before risky trips.
   - Copy the best top teams' per-map drafts and item orders: Intercontinental Fish beats v65 by about 730.
4. **Denial.**
   - Contest or steal v65's camps.
   - Stand on enemy camp spawn tiles when their respawn is due.
   - Place altar locks (10 gold) on altars v65 is tributing at; kill its gem carriers.
   - Race the 1,000-gem win.
5. **Map play.** Gated altars and single-objective maps (`00stampede`, `00dunes`, `02famine`, `00elkring`,
   `02arena`) where our lineage fails; bushes for ambush and hiding; wards; teleport crystals.
6. **Draft.** Per-map counters to v65's draft (v65's draft is deterministic; see `bots/v65/src/draft.cpp`).

## Step 1, before any bot code: a per-map meta study

Our past versions mostly tuned one generic build. Top teams play each map differently, and our losses concentrate
on particular maps: `00stampede` 0/8, `00dunes` 0/23, `02famine` 0/17, `00elkring` 0/14, `02arena` 0/13.

- Build `research/v67/MAPS.md`, with a table per map for all 70 pool maps (`maps/local-benchmarks`).
- Source: the 1,177 replays and the meta crawl. Weight the winners' games.
- For each map, record:
  - the winning drafts and their win rates;
  - the opening route: which camp groups each slot takes in the first 150 rounds, in which order, and with how
    many champions;
  - where and when the first fights happen;
  - banking cadence (bag size, which altar, when);
  - denial patterns: contested groups, respawn blocking, altar locks;
  - item order per hero;
  - how games are won there (gem race, kills, or the gold tiebreak);
  - v65's own record and failure there (play v65 against itself, and against the best top-team approach).
- Then encode a per-map plan into v67: draft, opening route, roles and carry, fight zones, bank and denial
  rules. Use the 1,024-byte draft memory, or a compiled per-map table keyed like `draft.cpp proxy_map_key`.
- Evaluate per map. A map is not done until v67 wins it on both sides.

## Suggested way of working

- Fastest path is probably to fork v65 into `bots/v67` (robust pathing, fuel, farming) and add a team-level strategy
  layer (packs, hunting, focus, retreat, denial), plus Fish-style draft and items. Rewrite anything that gets in the
  way.
- Run one change at a time on the 240-game benchmark and keep a results log in `research/v67/RESULTS.md`: change,
  wins/240, mean margin, deaths, kills, gold.
- Use replays of your own games to see why games are lost: `fight_style.mjs`, and bot printf output read through
  `engine.team_stdout(folder, 'a')`.
- Watch per-map results. A few maps usually carry most of the losses.

## Rules and environment gotchas

- Never log in or enter credentials.
- Don't commit others' work: `config/paths.json` (leave modified), `bots/v66x_*`, `bots/v66y_*`,
  `data/ladder/v57_games_20261026.json`, `compile_commands.json`, `.cambc/`.
- Don't modify `bots/v65` or `bots/mimic`.
- Bot sources copied from v65 are CRLF. Keep line endings consistent; write new text files with LF.
- In this Git-Bash environment, backslashes inside heredocs get mangled (`\n` turns into a newline). Write edit
  scripts to files instead.
- When done: write `research/v67/README.md`. Cover the method, the final 240-game result plus the seed 3/4 holdout,
  results against v61/v58/v66b, per-map weak spots, and what worked and what didn't. Add v67 to `bots/README.md`.
  Commit only your files and push.
