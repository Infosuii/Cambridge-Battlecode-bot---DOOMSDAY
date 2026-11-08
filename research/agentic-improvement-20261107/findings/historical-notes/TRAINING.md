# Local GPU training

Open PowerShell and run these commands from this folder:

```powershell
cd 'C:\projects\cambridge battlecode\work\agentic-improvement'
powershell -NoProfile -ExecutionPolicy Bypass -File .\train.ps1 -Action status
```

Start or resume (do not start a second copy):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\train.ps1 -Action start
```

Stop:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\train.ps1 -Action stop
```

Watch the live log (Ctrl+C only stops watching it):

```powershell
Get-Content .\training\training.log -Tail 20 -Wait
```

The default bounded job first validates CUDA and a byte-identical v111 checkpoint
export, builds opponents once, then runs a pilot: 24 simulated games, one GPU
update and a small development evaluation. Only if that succeeds does it start
10 iterations of 96 games each, with development evaluation every two iterations.
This is a first continuation experiment, not a proof of strength or promotion.
Maps and opponents are frozen in training/splits.json and the trainer source.
Pilot and main run have separate evidence directories. CPU generates engine
games; GPU trains the small network. GPU use will be low during simulations.

No AI model, API or subscription is called by the training process. It consumes
local electricity, CPU/GPU time and disk space. The computer needs power and
cooling. The supervisor prevents idle sleep while running; closing the lid or
shutting down can still interrupt it. It runs in a hidden window and survives
closing this chat, but does not install a service or scheduled task.

Files:

- Status: training/supervisor.json; progress: training/training.log.
- Runner errors: training/supervisor-errors.log, individual *.runner.log files.
- Pilot checkpoints: training/runs/pilot.
- Main actor, critic, optimizer/RNG checkpoints: training/runs/v111-continuation.
- Games, summaries, and selection reports: training/v4/bench_out.
- Frozen original files: reference/nn-rl6-original (not modified).
- Installed packages: training/requirements.lock.txt.

Stopping during an iteration preserves its evidence and the last completed
checkpoint. Restart reruns the interrupted iteration. New completed checkpoints
also persist optimizer/RNG state; exact nondeterministic GPU replay is not
guaranteed. The original v111 archive did not contain optimizer state, so this
job begins a fresh optimizer at the recovered actor and critic weights.

The evaluation maps are disjoint from this run's training map bytes, but they
have historical usage; they are development selection maps, not untouched final
holdouts. The score is reported separately for v111, nnm4 and v92. In particular,
a pooled gain cannot prove the candidate beats v111.

Training samples target choices; release uses its existing deterministic choice
and fuel system. The original Q16 actor and floating training reconstruction have
small numerical differences. Batch logs retain measured probability differences;
the run aborts for large discrepancies, missing training data, wrong engine,
failed games, invalid actions, non-finite losses, low RAM or explicit STOP.
Raw evidence remains for diagnosis. An error is Retry required, not a rejected
strategy. A later candidate needs paired confirmation and normal-fuel/runtime
checks. This training job never uploads, activates or queues ladder games.
