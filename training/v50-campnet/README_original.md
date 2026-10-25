# Neural gameplay training

This workspace preserves `mld_fuel35_engine103.zip` in `baseline/src` and adds a
trained neural camp-selection policy in `candidate/src`. The original source
and existing work elsewhere in the project are unchanged.

## Current run

The user requested **one hour first**, superseding the earlier four-hour choice.
The main optimization clock starts at `training_started` in `progress.jsonl`.
Setup, compilation and the final independent evaluation are additional.

- `status.json`: current stage, progress and any error.
- `progress.jsonl`: complete chronological progress.
- `checkpoints/latest.pt`: resumable GPU model, critic and optimizer checkpoint.
- `checkpoints/best-trained.pt`: best trained policy on the selection maps.
- `draft-training.json`: recent-data draft fitting results.
- `protocol.json`: frozen training, selection and final-test map sets.
- `report.json`: final results, written only after the run completes.
- `release/bot_neural.zip`: final C++ source upload candidate.
- `release/bot_neural.wasm`: final locally tested compiled candidate.

## What learns

The gameplay policy is an **18-input, 16-hidden-unit neural network**. It adjusts
the original camp ranking using health, travel distance, rewards, camp type,
nearby enemies and allies, time, and carried gems. A bounded output and fuel
reserve keep the original strategy available when the network cannot be used.

Training uses clipped PPO on the RTX 5070 Ti, with 20 parallel CPU match workers.
Rewards come from real match-summary timelines: collected and banked gems,
earned gold, deaths and the final team outcome. Training-only sampled decisions
and compact observation records are excluded from the final inference artifact.
The submitted bot uses fixed learned weights; it does not backpropagate during
competition games.

The existing drafting network is also fitted against recent ranked outcomes.
Only games from the last 24 hours are admitted; the initial snapshot used
games played on 23 October 2026 between 16:00 and 19:00 UTC. Whole match groups
are split chronologically, and engine final-test maps are excluded from draft
fitting. The original draft weights are retained if fitting fails to improve
validation loss. Match outcomes also reflect team skill, so fitting a win
predictor alone does not establish a stronger draft policy.

The original bot and two explicitly labeled recent-meta local proxies provide
training opponents. Proxy champion orders are derived from current winning
drafts; their gameplay is our original bot. They are **not** the actual
executables of the leading teams.

## Historical archive extension

The user subsequently supplied the 21 October archive and authorized **21 October
onward only**. The four available summary parts contain 93,606 entries. The
first-hour experiment samples 1,000 matches per part in reproducible UUID-hash
order. Of those 4,000 samples, 3,070 post-patch matches were accepted; engine
1.0.1 games and unfinished/very short matches were excluded. Engine 1.0.2
outcomes are admitted only for separate draft pretraining, with today's examples
weighted more heavily. Gameplay PPO and final tests still use engine 1.0.3.
The other 18 archive parts can be added in a later run.

`historical-training/fit.json` records the separate historical fit.
`historical-extension-protocol.json` freezes its selection rule before final
testing. The historical draft is promoted only if it improves current-engine
selection results with the same gameplay model; it does not replace the running
trainer's draft weights. If promoted, its source is saved separately as
`release/bot_neural_history.zip` and verified by `tools/verify_release.py --history`.

Desktop control has stopped at the user's request. Archive processing reads
completed local files only. Progress updates are attached to this chat every
five minutes while the authorized experiment is running.

## Validation and packaging

Training uses 26 maps; six other maps select checkpoints. Eight maps are held
for the final comparison, run once for the selected candidate and the original
bot, with both sides and all three opponents. Tests use the official CLI in
release mode and default competition fuel. Source/binary hashes and all match
summaries are retained. A candidate is an experiment until the final report
shows its results; it is not automatically submitted to the ladder.

## Run again

From this directory:

```powershell
.\.venv\Scripts\python.exe tools\train.py --minutes 60 --workers 20
```

Use a separate copied experiment directory for a new run. Existing match
folders are immutable cached evidence, not additional independent games.
Do not repeatedly tune against the final holdout maps.

Dependencies are installed in the project-local `.venv`. The script records the
CLI and engine evidence; local runtime paths are near the top of `tools/train.py`.
The final source ZIP contains only the bot sources and its trained weights.
