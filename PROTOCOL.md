# comms/x1: how the two x1 machines talk

This branch is **only** for messages between Rishik's PC (`pc/`) and the 5060 PC (`g5060/`). It is an orphan branch:
it shares no history with any code branch, is never merged anywhere, and holds no code.

- Check it out with `SIDE=<you> bash tools/x1_comms.sh init` from a clone of the repo (code branch `build/z-plan`).
  It lands in a separate folder, `../x1-comms`, so comms commits can never touch a code checkout.
- **Write only your own folder.** PC: `pc/`. 5060: `g5060/`. `tools/x1_comms.sh push` refuses anything else. This
  root file was written once at creation and is read-only after that.
- Commit messages: `comms(pc): ...` / `comms(g5060): ...` (the helper adds the prefix).
- Poll every 10 minutes while you have open jobs: `bash tools/x1_comms.sh pull`.

## Files

| Path | Writer | What |
|---|---|---|
| `pc/STATUS.md` | PC | what the PC is doing, x1's current switches and hash, open jobs |
| `pc/jobs/Jnnn-name.md` | PC | a job for the 5060 (format below); never edited after posting except `state:` lines in STATUS |
| `g5060/STATUS.md` | 5060 | machine, threads, RAM, what is running, queue position, ETA |
| `g5060/results/Jnnn.md` | 5060 | the job's numbers, verdict by the gate rule, anything odd |
| `g5060/results/Jnnn/*.json` | 5060 | `results.json` of each run (no `evidence.zip`: replays stay on the machine that played them) |
| `g5060/msgs/nnnn-title.md`, `pc/msgs/...` | each | questions, problems, proposals (numbered, never edited) |

## Job format

```
id: J003
title: retry round 1
commit: <sha on build/z-plan, or on build/z-plan-5060 for 5060 tools>
bot: x1 (bots/x1 at that commit; base hash 1746f2bb7fa3)
run: gate | sweep | farm | search | league | other
switches: one run per line, e.g. "--set X1_SECURE=1 --set X1_SECURE_MULT=1.5"
opponents: x2 x2-s2
maps: ladder styled maze
priority: 1 (lower runs first)
done when: what to post
```

Gate rule (research/x1/RETRY_QUEUE.md, R1): total wins over all cells ≥ the base on the same cells, no map kind more
than 2 points below the base, and no new fuel-outs or faults. The 5060 states the verdict; the PC applies it.
