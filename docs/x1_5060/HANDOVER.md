# Handover to the 5060 PC (1 Nov 2026, 23:55)

## State of play

- **x1** (`bots/x1`, hash 1746f2bb7fa3) = v81hl + exact fuel fix + camp watch; live on the ladder as v73.
- **Benchmark v88** (`bots/x2` a9f1bbc43ef7, seed build `bots/x2-s2`) = teammate's v86h + x1's two changes.
  x1 vs v88: ladder 68/140, ladder-style generated maps 55/100: even. On Agent 2's maze-style maps v88 wins.
- Small one-off features are exhausted (all within ±4 games). The plan now: 3-4 hardcoded team strategies, a branch
  farm that finds which strategy wins each lost game, a small selector, then a joint search over everything.
- Every past rejection is back in the queue (research/x1/RETRY_QUEUE.md) with the retries it still owes.

Read: research/x1/PLAN_TWO_MACHINES.md (schedule, cycle), RETRY_QUEUE.md, STRATEGY_SYNTHESIS.md (game facts, results).

## Your jobs (posted in comms/x1 `pc/jobs/`)

| Job | What | Priority |
|---|---|---|
| J001 | setup, hashes, reproduce x1 vs x2 ladder 68/140 game for game, games/minute | 1 |
| J004 | maze-style map set into maps/x1-maze | 1 |
| J002 | take over sweep 1d | 2 |
| J003 | retry round 1 (X1_SECURE variants, X1_ALONE) | 3 |
| next | branch farm on the plan hook (2 Nov afternoon), gates for every PC candidate, retry round 2, joint search (4 Nov), table refit and league (5 Nov) | as posted |

When idle with no job: post that in g5060/STATUS.md and run the next unfinished retry-queue gate (lowest #).

## Prompt for the Claude Code session on this PC

> You are the run machine for the x1 Battlecode bot. Read docs/x1_5060/README.md and HANDOVER.md on branch
> build/z-plan, then set up the comms folder with `SIDE=g5060 bash tools/x1_comms.sh init` and read PROTOCOL.md
> and pc/ there. Work through pc/jobs in priority order. Post results to g5060/ only, push code only to
> build/z-plan-5060, never edit bots/x1, never touch other branches. Poll comms every 10 minutes while jobs are open
> and keep g5060/STATUS.md current (what runs, ETA). Decide and continue on your own; ask the PC through g5060/msgs
> only when blocked. Use all but 2 CPU threads, one run at a time, and report every fuel-out.
