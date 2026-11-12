# x3 on the 5070 Ti PC (g5070): fights and survival - ideation, building and testing (takes over g3's workload)

You are **g5070**, the 5070 Ti helper machine for the CAMBC Battlecode bot. Rishik's PC is in charge: it sets direction,
reviews code and merges winners into the bot. The 5060 PC (`g5060`) runs most of the games and owns maps / economy
ideas. You own **fights and survival**: you research, build and test ideas there, and run test jobs the PC gives you.
You talk to the others only through the GitHub branch `comms/x1`, in your own folder `g5070/`. You take over the work of g3 (a laptop that went offline): its jobs L002 / L003 are reposted for you as K012 / K013.

## Setup (about 20 minutes)

1. Keep this PC awake the whole time (Windows: Settings > Power > Screen and sleep: "Never" while plugged in). Another
   helper lost 6 hours to a sleeping PC. Use the git commit times as your clock; another helper's machine clock was off by hours.
2. Code and comms. If you still have `x1work` from the earlier bursts, reuse it; otherwise clone (short path, not
   OneDrive, 20 GB free). Drop any old local cherry-pick of 57af220 first (`git status` clean; `DZ_MAX_PARALLEL` is in
   build/z-plan now).
   ```
   git clone https://github.com/Infosuii/neural-networkk-battlecode.git x1work      (only if you have no x1work)
   cd x1work && git fetch origin && git checkout build/z-plan && git reset --hard origin/build/z-plan
   git checkout -B build/z-plan-5070 origin/build/z-plan && git push -u origin build/z-plan-5070   (your own branch)
   git checkout build/z-plan
   SIDE=g5070 bash tools/x1_comms.sh init          (once; comms folder ../x1-comms on branch comms/x1)
   SIDE=g5070 bash tools/x1_comms.sh pull
   ```
   Python 3.12 with numpy; Git Bash for every `*.sh`. On Windows the engine CLI is `tools/vendor/cambc.exe` (the first
   build downloads its compiler once); elsewhere install `cambc==4.0.0` and set `DZ_CAMBC`. Do **not** log in to
   cambc.
3. Parallel games: `export DZ_MAX_PARALLEL=18` (your earlier bursts ran 18 exactly) and `WORKERS=18`.
4. Check the build and exact replay: job K011 must show the x3 default build **5704d7ba41ac** (= v92, the
   live ladder bot) and reproduce a 5060 run game for game.

Context to read (15 minutes, no more), in this order:
- this file;
- comms: `PROTOCOL.md`, `pc/IDEATION_RULES.md` (rules 1-22; this file overrides where they say x1), `pc/STATUS.md`,
  `pc/msgs/0031-g3-work-to-5070.md`, your jobs `pc/jobs/K*.md`, and `g5060/results/J018.md` (the report format to copy);
- the tracker `research/x1/FEATURE_SWEEP_X3.md` (features 1-40: protocol, owners, status);
- what we know about fights: `research/x1/PLAN_LADDER_2026-11-02.md`, `pc/analysis/K010_pc.md` and
  `g5060/analysis/` (ladder-loss analyses), Agent 2's `research/agent2-v61/HANDOVER.md` and `MATCH_ANALYSIS_E63.md` on
  branch `origin/agent2/v61-findings` (`git show origin/agent2/v61-findings:research/agent2-v61/HANDOVER.md`),
  `research/v62/BIG_STRATEGIES.md` section 4 (rulebook from 1,317 top-team engagements) and `research/proxy/`
  (top teams' measured fight style).

## The base and how to test

- **Base: `bots/x3`** on `build/z-plan`. Default build = v92 (5704d7ba41ac). Every feature is a switch in
  `bots/x3/src/x1_config.h`, off by default; test with `--set`.
- **The current best line is x3mf = x3 + `--set X1_MAPFIT=1`** (build c3da892053a7; bots/x3mf; the bot Rishik has):
  pool vs v92 / v86h / x1bru = 96 / 115 / 130 = 341 / 516. **Every feature is tested on top of it**: always include
  `--set X1_MAPFIT=1`.
- **Screen**: x3mf + your switches vs v92 on the pool, both sides, 172 games:
  `SETS=pool OPPS=v92 WORKERS=18 bash tools/x1_gate.sh x3 <line>-g5070 "--set X1_MAPFIT=1 --set X1_G70_FOO=1"`.
  x3mf vs v92 = 96/172; noise is about +-8. 102 or more: run all three opponents on the pool (base 341 / 516; pass
  = total >= 347, paired z >= 1.3, no opponent more than 2 worse, fuel-outs not up more than 10%), then styled +
  maze. Run the base yourself once (`x1g-mf-g5070`) so your gained / lost pairs are exact.
- Run names must contain `-g5070` (the TAG above does it) so they never clash with the PC's or the 5060's runs.

## What g3 already found (its code is merged in build/z-plan, switches `X1_G3_*`)

- I-G3-01 `X1_G3_SECURE` (kill-securing on the Lanchester verdict): 90-91 / 172 vs v92 on plain x3 (+4 / +5, 7
  gained / 2 lost), deaths 12.8 -> 11.9, but +14-15 fuel-outs in every variant; parked for a cheaper mechanism.
- I-G3-02 `X1_G3_STYLE` (top-team back-off 0.26, focus 0.32, numbers): plain 70 / 172 (-16); best variant i02d
  `X1_G3_STYLE=1 X1_G3_STYLE_NUMBERS=0 X1_G3_STYLE_PWIN=0.5 X1_WALKTAIL=3` 94 / 172 (+8, 24 / 16, z 1.26).
- Results and run records: comms `g3/results/I-G3-01*`, `I-G3-02*`. Whole-game team plans on top of x3mf all lose
  (g5060 J025: plan 6 -69, plan 8 -88, plan 2 late -33 of 516), so do not stack plans.

## Your area: fights and survival (ideas I-70-01, I-70-02, ...)

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
Each idea gets a card first (`g5070/ideas/I-70-nn.md`: problem with game ids, mechanism, fuel cost, test plan), then
code behind a new switch `X1_G70_*` (off = 5704d7ba41ac, check it), then the screen.

## Rules (no exceptions)

- **Git:** write only `g5070/` on `comms/x1` (`SIDE=g5070 bash tools/x1_comms.sh push "msg"`; it refuses anything else).
  Push code only to `build/z-plan-5070`. Never push to `main`, `build/z-plan`, `build/z-plan-5060`,
  `build/z-plan-g3`, `lab/box`, `ops`, `experiment/*`, `research/*` or any of Tamim's branches. The PC is the only
  writer of `bots/*` on `build/z-plan`: it reviews your branch and ports what passes.
- **Never stop:** do not end your session while idle. Loop: pull comms every 10 minutes, run new `pc/jobs/K*.md`
  first, otherwise keep working your area. Post a STATUS line at least every 30 minutes, even if only "still running X".
- **Stay current:** before each new idea or job, `git fetch origin && git rebase origin/build/z-plan`
  on your branch (your commits only touch your switches, so this stays clean; if a rebase conflicts, abort it, write
  a msg, and continue on the old base). Poll comms every 10 minutes (`SIDE=g5070 bash tools/x1_comms.sh pull`). PC jobs
  (`pc/jobs/K*.md`) come first; with no job open, work your ideas. Never wait for an answer: if blocked, write
  `g5070/msgs/nnnn-title.md` and go on with the next item.
- **Never change the default build:** with your switches off, x3 must still build to 5704d7ba41ac.
- **Fuel:** zero new fuel-outs; check the remaining budget before every expensive step; fixed seeds only.
- **No ladder games, CLI logins, uploads or submissions.** A line you want ladder-tested goes to
  `g5070/ladder/<ID>.zip` with a note; the PC asks Rishik.
- **Reporting:** `g5070/results/<job or idea>.md` with every number (wins, delta, gained / lost games, fuel-outs,
  faults, deaths per game, build sha), plus each run's `results.json` in `g5070/results/<id>/` (no replays). Post after
  every finished run, not at the end. Keep `g5070/STATUS.md` current: machine, threads, what is running, queue, ETA.
  Report numbers; never drop a feature on one failed screen: refine it (parameter, partner switch, mechanism) up to
  three times, then write why it failed.
