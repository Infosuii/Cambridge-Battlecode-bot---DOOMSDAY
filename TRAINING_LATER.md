# Later training workflow — instructions, not jobs already run

**Plan superseded:** these commands describe legacy v1 residual tooling. The user now wants direct policy control;
follow [POLICY_FIRST_PLAN.md](POLICY_FIRST_PLAN.md) and implement versioned direct-logit records/collection/parity
before using a future v2 training workflow. No training is authorized by this change of plan.

**Do not run learning yet.** This build did not authorize training. Current acceptance is incomplete: official fuel,
integration, real-record parity and release checks remain pending, and carry-risk/belief/search-leaf label/loss paths
are incomplete. Candidate-policy imitation/PPO and win/margin value fitting are implemented, with synthetic tests.
The commands below are **NOT RUN** instructions for a later, explicitly authorized session after those blockers close.

## Environment and read-only inputs

From this workspace in PowerShell:

```powershell
# NOT RUN instructions; use this setup for later commands.
$py = 'C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe'
$env:PYTHONPATH = "$PWD/python"
$env:TMP = "$PWD/artifacts/tmp"
$env:TEMP = $env:TMP
$env:PATH = 'C:/msys64/ucrt64/bin;' + $env:PATH
```

The previous handoff verified an RTX5070Ti Laptop12GB,20 logical CPUs and31GB RAM. Recheck available GPU memory before
later training. Torch `device:auto` uses CUDA when available; engine games run on CPU. Worker counts are configured
in `configs/train/*.json`; the current engine helper clamps actual engine concurrency to4. Do not assume an8-worker
configuration currently launches8 games at once. GPU tensor work must never enter the Wasm bot.

## Inspect and collect defensible data

```powershell
# NOT RUN — reads current accounting; does not fit a model.
& $py tools/nfs.py inspect-data
# NOT RUN — optional new bounded index; do not overwrite frozen experiment receipts.
& $py tools/nfs.py index-archives --sample-per-part 190 --consistency-checks 10 --workers 4 --out data/manifests/archive_index_next.json
# NOT RUN — bounded instrumented teacher collection after integrated-profile validation.
& $py tools/nfs.py collect --config configs/train/collect_teacher.json --profile teacher_record --run-dir artifacts/runs/teacher-next --max-games 96 --time-limit-minutes 30 --workers 4 --i-authorize-collection
```

Only21Oct2026 onward is eligible. Engine1.0.1 stays excluded;1.0.2 is observational draft-only. Existing local archives
supplied no compatible1.0.3 gameplay labels in the bounded audit. They do not contain low-level movement/combat
actions. Use instrumented1.0.3 teacher episodes for those labels. Teacher recording has overhead and must be compared
with teacher_exact on the same cells; it is not an unchanged-teacher execution claim.

`teacher_record` runs all heads shadow with records, never sampling. Candidate0 is the teacher option. Summaries
supply targets only; inputs come from the acting side's NFS1 RawTurns. Canonical record/observation adapters now
connect, but a post-hook real engine conversion/parity test is still required. Missing/corrupt/incompatible records
are not silently treated as valid observations. Match caches verify both Wasm hashes, map hash and logging settings.

Build a **new local match split manifest**, grouped by match/series/team and deterministic Wasm-pair/map identity.
The archive split manifest does not assign IDs to newly collected local episodes. The dataset CLI's `--splits`
expects `grouped.assignment` keyed by local match IDs. Check map/opponent generalisation separately and label every
local map a reused benchmark. No unassigned rows should enter fitting.

```powershell
# NOT RUN — local-splits.json must first be generated/reviewed from the collected local match identities.
& $py tools/nfs.py build-dataset --games artifacts/runs/teacher-next/games --out artifacts/datasets/teacher-next --name teacher_next --splits artifacts/datasets/local-splits.json
```

## Fit, resume and export later

```powershell
# NOT RUN — candidate imitation and optional win/margin loss, bounded20minutes.
& $py tools/nfs.py pretrain --config configs/train/pretrain_default.json --model-config configs/model/fs_v1.json --train artifacts/datasets/teacher-next/teacher_next-train.npz --validation artifacts/datasets/teacher-next/teacher_next-validation.npz --run-dir artifacts/runs/pretrain-next --i-authorize-training --time-limit-minutes 20
# NOT RUN — gameplay win/margin value fit; saves value.pt plus a report.
& $py tools/nfs.py train-value --config configs/train/value_default.json --model-config configs/model/fs_v1.json --train artifacts/datasets/teacher-next/teacher_next-train.npz --validation artifacts/datasets/teacher-next/teacher_next-validation.npz --run-dir artifacts/runs/value-next --i-authorize-training --time-limit-minutes 15
# NOT RUN — first bounded on-policy experiment, objective only.
& $py tools/nfs.py rl --config configs/train/first_experiment.json --model-config configs/model/fs_v1.json --run-dir artifacts/runs/first-exp --i-authorize-training --time-limit-minutes 30
# NOT RUN — resume the same run; persisted absolute deadline is not extended.
& $py tools/nfs.py rl --config configs/train/first_experiment.json --model-config configs/model/fs_v1.json --run-dir artifacts/runs/first-exp --i-authorize-training --time-limit-minutes 30
# NOT RUN — selected real checkpoint only; synthetic checkpoints are refused by this CLI.
& $py tools/nfs.py export --checkpoint artifacts/runs/pretrain-next/pretrain.pt --model-config configs/model/fs_v1.json --name candidate_next --out artifacts/exports/candidate_next
```

PPO starts from seeded features with zero residual output layers, not an all-zero hidden network. It logs the true
masked sampled probability, checks behavior logits/logp before updating, separates agent/head streams, and uses
SMDP timing for commitments. Checkpoints include actor, separate critic, both optimizers, RNG, league, game ledger,
schema hashes and absolute deadline. An actor-only selected checkpoint needs an explicit critic/optimizer reset;
otherwise stale pairing is refused. Imitation/value commands save final artifacts; full optimizer resume is provided
by the PPO path, not claimed for every offline fitting command.

The fixed value margin output is submitted-gem difference /1000. Reward shaping has its own scale. Carry-risk is
currently **not supervised**, and belief/leaf do not have complete real record/target/loss paths. Do not enable them
as trained policies merely because another head was fitted or the shared encoder changed. Observational archive
draft-outcome models are separate, confounded checkpoints and cannot export into the runtime without an adapter.

## First experiment and stop criteria

Use `first_experiment.json`: objective only,30minutes or480games, original at least50% of the pinned league, frozen
training partition only. Actual current engine concurrency is capped4; GPU uses the configured device. Start only
after byte identity, measured full-call fuel limits, real NFS1 parity and all-head smoke safety have passed.

Stop **before updating** for any bot fault, any invalid selected action, fallback rate>0.2, missing required observation
rate>0.2, incompatible schemas, absent ratio rows, or behavior-probability mismatch. KL early stop is1.5*target_kl;
entropy<0.05 is reported for investigation. Persisted deadline and game cap remain hard bounds. Current NFS1 records
do not log every admission refusal, so logged-row fallback rate is not a complete opportunity-level skip metric;
combine it with NFT1 telemetry in framework validation.

Report explained variance, critic error, entropy/KL/clipping, gradient norm, reward components, off-teacher/action
distribution, invalids, fallbacks, skips and team outcomes. Loss reduction is not gameplay improvement. Evaluate the
deployed argmax rule separately from sampled behavior. Per-opponent selection constraints cannot be replaced by a
pooled score. Deterministic duplicate games are not new independent samples.

## Later benchmark and promotion

```powershell
# NOT RUN — install a local export into an already prepared copy, then official-release build/evaluation.
& $py tools/install_models.py --profile dev_untrained --model artifacts/exports/candidate_next --src artifacts/tmp/candidate_bot/src --receipt artifacts/tmp/candidate_bot/install.json
& $py tools/eval_run.py --schedule selection --label candidate-next-selection --bot-dir artifacts/tmp/candidate_bot
& $py tools/eval_report.py evaluation/results/candidate-next-selection/results.json --baseline evaluation/results/teacher-next-selection/results.json --gate selection
```

Prepare the teacher baseline under the same amended protocol first. Reserve final evaluation once per candidate
family through `eval_run --schedule final --family ...`; never choose among candidates repeatedly on final results.
`nfs.py promote` evaluates the frozen per-opponent gate and writes a receipt. Only a passing, schema-compatible
model may be registered as validated and explicitly selected in `models/registry.json.release_selection`, then
installed with `install_models.py --profile release`. No promotion or training command above was run in this build.

No submit, upload, login or activation command belongs to this workflow.
