# x1 on the 5070 Ti PC: one 1.5-hour burst

You are a **burst run machine** for the x1 Battlecode bot, available for about 1.5 hours. Rishik's PC develops the
bot; a 5060 PC runs most games. You take two game-heavy jobs off the 5060's queue. You talk to the others only
through the GitHub branch `comms/x1`, in your own folder `g5070/`.

## Setup (15 minutes)

```
git clone https://github.com/Infosuii/neural-networkk-battlecode.git x1work     (short path, not OneDrive, 20 GB free)
cd x1work && git checkout build/z-plan
SIDE=g5070 bash tools/x1_comms.sh init       (comms folder ../x1-comms on branch comms/x1)
```
Python 3.12; on Windows the engine CLI is `tools/vendor/cambc.exe` (first build downloads its compiler once);
elsewhere install `cambc==4.0.0` and set `DZ_CAMBC`. Threads: use all but 2. Before running games, merge the
5060's runner speed-up into your local checkout only (do not push): `git fetch origin build/z-plan-5060 &&
git cherry-pick 57af220`, then set `DZ_MAX_PARALLEL=<threads-2>` (default cap is 4 games at a time).

Context to read (10 minutes, no more): this file; `research/x1/PLAN_TWO_MACHINES.md`; `research/x1/RETRY_QUEUE.md`;
in comms: `PROTOCOL.md`, `pc/STATUS.md`, `pc/jobs/J007-audit-fixes.md`, `pc/jobs/J002-sweep1d.md`, your `pc/jobs/K*`.

## Your jobs (comms `pc/jobs/K*.md`)

| Job | What | Time |
|---|---|---|
| K001 | build check + one exact reproduction | 10 min |
| K002 | = J007: full gates of the six x1-audit fixes (8 lines) | ~35 min |
| K003 | = J002 remainder: sweep 1d, live switches only | the rest |

Post results after **every** gate line (do not wait to the end): `g5060`'s format, in `g5070/results/K00n.md` plus
each run's `results.json` in `g5070/results/K00n/`. At **1 h 20 min** stop starting new runs, let the running one
finish, push, and write `g5070/STATUS.md` with exactly which lines/flags are done and which are not, so the 5060
picks up the rest.

## Rules (no exceptions)

- Write only `g5070/` on `comms/x1` (the helper refuses anything else). Push nothing to any code branch. If you
  must keep a tool change, push it to `build/z-plan-5070` only. Never touch `main`, `build/z-plan`,
  `build/z-plan-5060`, `lab/box`, `ops`, `experiment/*`, `research/*` or any branch of Tamim's.
- Never edit `bots/x1`; test with `--set`. No ladder, no logins, no uploads.
- Run names must end in `-g5070` (e.g. `x1g-teamwin-ladder-x2-g5070`) so they never clash with the PC's or the
  5060's runs. Use `tools/x1_gate.sh` with `TAG=<line>-g5070`, i.e. `bash tools/x1_gate.sh x1 teamwin-g5070 "--set X1_TEAMWIN=1"`.
- Report numbers and the gate verdict; never reject a feature. Report every fuel-out and fault.
- Decide and carry on; if blocked, write `g5070/msgs/0001-...md` and continue with the next item.
