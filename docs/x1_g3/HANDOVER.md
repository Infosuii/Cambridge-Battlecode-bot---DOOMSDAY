# x3 on the third helper (g3): ideation, building and testing for fights

You are **g3**, the third helper machine for the CAMBC Battlecode bot. Rishik's PC is in charge: it sets direction,
reviews code and merges winners into the bot. The 5060 PC (`g5060`) runs most of the games and owns maps / economy
ideas. You own **fights and survival**: you research, build and test ideas there, and run test jobs the PC gives you.
You talk to the others only through the GitHub branch `comms/x1`, in your own folder `g3/`.

## Setup (about 20 minutes)

1. Keep this PC awake the whole time (Windows: Settings > Power > Screen and sleep: "Never" while plugged in). Another
   helper lost 6 hours to a sleeping PC. Use the git commit times as your clock; another helper's machine clock was off by hours.
2. Clone and check out the code branch (short path, not OneDrive, 20 GB free):
   ```
   git clone https://github.com/Infosuii/neural-networkk-battlecode.git x1work
   cd x1work && git checkout build/z-plan && git pull
   git checkout -b build/z-plan-g3 && git push -u origin build/z-plan-g3      (your own branch, from build/z-plan)
   git checkout build/z-plan
   SIDE=g3 bash tools/x1_comms.sh init          (comms folder ../x1-comms on branch comms/x1)
   ```
   Python 3.12 with numpy; Git Bash for every `*.sh`. On Windows the engine CLI is `tools/vendor/cambc.exe` (the first
   build downloads its compiler once); elsewhere install `cambc==4.0.0` and set `DZ_CAMBC`. Do **not** log in to
   cambc.
3. Parallel games: `export DZ_MAX_PARALLEL=<threads - 2>` and pass `--workers` (or `WORKERS=`) with the same number.
4. Check the build and exact replay: job L001 (below) must show the x3 default build **5704d7ba41ac** (= v92, the
   live ladder bot) and reproduce a 5060 run game for game.

Context to read (15 minutes, no more), in this order:
- this file;
- comms: `PROTOCOL.md`, `pc/IDEATION_RULES.md` (rules 1-22; this file overrides where they say x1), `pc/STATUS.md`,
  `pc/msgs/0028-g3-joins.md`, your jobs `pc/jobs/L*.md`, and `g5060/results/J018.md` (the report format to copy);
- the tracker `research/x1/FEATURE_SWEEP_X3.md` (features 1-40: protocol, owners, status);
- what we know about fights: `research/x1/PLAN_LADDER_2026-11-02.md`, `pc/analysis/K010_pc.md` and
  `g5060/analysis/` (ladder-loss analyses), Agent 2's `research/agent2-v61/HANDOVER.md` and `MATCH_ANALYSIS_E63.md` on
  branch `origin/agent2/v61-findings` (`git show origin/agent2/v61-findings:research/agent2-v61/HANDOVER.md`),
  `research/v62/BIG_STRATEGIES.md` section 4 (rulebook from 1,317 top-team engagements) and `research/proxy/`
  (top teams' measured fight style).

## The base and how to test

- **Base: `bots/x3`** on `build/z-plan`. Default build = v92 (5704d7ba41ac). Every feature is a switch in
  `bots/x3/src/x1_config.h`, off by default; test with `--set`.
- **Screen**: x3 + your switches vs v92 on the competition pool, both sides, 172 games:
  `SETS=pool OPPS=v92 WORKERS=$N bash tools/x1_gate.sh x3 <line>-g3 "--set X1_G3_FOO=1"`.
  Plain x3 vs v92 = 86/172; noise is about +-8. 92 or more: run the **full gate** (OPPS="v92 v86h x1bru",
  SETS="pool styled maze") and report the paired sign test (gained / lost games, z). The protocol is in the tracker.
- Run names must contain `-g3` (the TAG above does it) so they never clash with the PC's or the 5060's runs.

## Your area: fights and survival (ideas I-G3-01, I-G3-02, ...)

The ladder evidence: we die 14.9 times a game against the top 12 vs their 5.1; kills 3.6 vs 13.6; deaths are mostly
alone or outnumbered, in our own half; we stay in fights we cannot win; conversion (bank the winning bag) is 47% of
losses. Start with these tracker rows (move to the next when one passes or is rethought three times):
1. Row 31, kill-securing coordinator: focus fire on the enemy v92's Lanchester model (A2_LANCH2) says we can kill;
   bring the nearest allies; stop when the verdict turns.
2. Row 38, top-team fight style: back off at 0.26 in contact (A3_BACKOFF / A3_BACK_EQ), enter contact with more
   friends (A3_NUMBERS), focus 0.32.
3. Row 32, Bruiser items with v92's fight model (V58_ITEM_PLAN=0 lost alone; make the fight model know the stats).
4. Rows 29 / 35, leash and fight-back as inputs to the Lanchester verdict rather than overrides (both raised deaths
   as overrides).
Each idea gets a card first (`g3/ideas/I-G3-nn.md`: problem with game ids, mechanism, fuel cost, test plan), then
code behind a new switch `X1_G3_*` (off = 5704d7ba41ac, check it), then the screen.

## Rules (no exceptions)

- **Git:** write only `g3/` on `comms/x1` (`SIDE=g3 bash tools/x1_comms.sh push "msg"`; it refuses anything else).
  Push code only to `build/z-plan-g3`. Never push to `main`, `build/z-plan`, `build/z-plan-5060`,
  `build/z-plan-5070`, `lab/box`, `ops`, `experiment/*`, `research/*` or any of Tamim's branches. The PC is the only
  writer of `bots/*` on `build/z-plan`: it reviews your branch and ports what passes.
- **Stay current, never stall:** before each new idea or job, `git fetch origin && git rebase origin/build/z-plan`
  on your branch (your commits only touch your switches, so this stays clean; if a rebase conflicts, abort it, write
  a msg, and continue on the old base). Poll comms every 10 minutes (`SIDE=g3 bash tools/x1_comms.sh pull`). PC jobs
  (`pc/jobs/L*.md`) come first; with no job open, work your ideas. Never wait for an answer: if blocked, write
  `g3/msgs/nnnn-title.md` and go on with the next item.
- **Never change the default build:** with your switches off, x3 must still build to 5704d7ba41ac.
- **Fuel:** zero new fuel-outs; check the remaining budget before every expensive step; fixed seeds only.
- **No ladder games, CLI logins, uploads or submissions.** A line you want ladder-tested goes to
  `g3/ladder/<ID>.zip` with a note; the PC asks Rishik.
- **Reporting:** `g3/results/<job or idea>.md` with every number (wins, delta, gained / lost games, fuel-outs,
  faults, deaths per game, build sha), plus each run's `results.json` in `g3/results/<id>/` (no replays). Post after
  every finished run, not at the end. Keep `g3/STATUS.md` current: machine, threads, what is running, queue, ETA.
  Report numbers; never drop a feature on one failed screen: refine it (parameter, partner switch, mechanism) up to
  three times, then write why it failed.
