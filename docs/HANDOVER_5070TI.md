# Handover: the RTX 5070 Ti box (run-only)

You are a Claude Code session on the team's RTX 5070 Ti machine. **Your whole job is to set the machine up once and
start a job runner. After that, do nothing: the runner works on its own.** Another session (the coordinator) pushes
job scripts; the runner runs them and pushes small results back. Spend as few tokens as possible: no exploring, no
reading code, no reports.

## Steps (in Git Bash)

```bash
git clone https://github.com/Infosuii/neural-networkk-battlecode.git nnbc && cd nnbc
git checkout lab/box
bash ops/box_setup.sh                # one line per step; ends with "done"
nohup bash ops/box_runner.sh > artifacts/tmp/box_runner.log 2>&1 &
```

Then reply with only: `setup done, runner started` (or the failing setup line), and stop.

## Rules

- **Do not** read, review or summarise repository files, logs or results. Do not run anything besides the four commands
  above unless a step fails.
- If a setup step fails: read only the last 30 lines of its output, fix that one problem (for example a missing
  winget package or a network retry), and re-run `bash ops/box_setup.sh`. If it still fails, reply with the failing
  line and stop.
- Never log in to anything, never enter credentials, never submit bots, never queue platform matches.
- Never push to any branch other than `lab/box` (the runner does the pushing). Never edit files in `bots/`.
- If the person at this machine asks you to stop the runner: `touch ops/box/STOP && git add ops/box/STOP &&
  git commit -m "box: stop" && git push origin HEAD:lab/box`.
- Keep the machine awake and plugged in. Jobs can run for many hours; the runner restarts nothing by itself, so if the
  machine reboots, only the last command (`nohup bash ops/box_runner.sh ...`) needs to be run again.

## What the runner does (no action needed)

Every 5 minutes it pulls `lab/box`, runs `ops/box/pending/*.sh` in name order, moves finished jobs to `ops/box/done/`,
writes `ops/box/logs/<job>.log` and small results to `ops/box/results/`, and pushes. Large outputs stay on this machine
under `artifacts/` (git-ignored). A pushed `ops/box/STOP` ends it.
