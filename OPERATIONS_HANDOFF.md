# Training operations handover

Codex owns architecture, schemas, candidate/execution rules, budgets, losses, rewards and trainer logic. The separate Freebuff/DeepSeek coding agent operates the approved CLI workflow: launch bounded collection/training, inspect actions/metrics, recover checkpoints, compare versions and report results. Do not rewrite those designs, relax masks/fuel gates, change the baseline or activate a model without returning to Codex/the user.

The framework is untrained. Your first approved experiment is **role only**, with encoder and other heads frozen, up to12 collection games,5minutes of fitting and4epochs. Role recording now preserves valid intervals through safe held turns. The latest two smoke games yielded193 eligible role starts, with zero faults/exhaustions/invalid records; this is plumbing evidence, not learned strength.

GPU functional validation passed on the RTX5070Ti Laptop GPU with torch2.11.0+cu128. Tiny synthetic CPU/CUDA runs reproduced uninterrupted actor, critic, both optimizers and RNG exactly after epoch recovery. No match-data optimization ran. `evaluation/results/operations_verified.json` contains the evidence.

## Environment

Run from the repository root on the original laptop. Training data/checkpoints remain local. Read the existing CUDA environment; do not install into or modify it. A fresh development clone uses DEVELOPMENT_SETUP.md; its CPU environment is sufficient for tests but not GPU training.

```powershell
$py = (Get-Content config/paths.json | ConvertFrom-Json).python
$env:PYTHONPATH = "$PWD/python"
$env:TMP = "$PWD/artifacts/tmp"
$env:TEMP = $env:TMP
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PATH = 'C:/msys64/ucrt64/bin;' + $env:PATH
& $py -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Require CUDA availability for fitting; `--device cuda` fails instead of silently training on CPU. Official builds/matches use cambc release/default fuel. Never submit, log in, override engine fuel, mutate references, or use final-partition maps in collection. All available local maps are reused benchmarks.

## First bounded cycle — NOT RUN during development

Start from the committed seeded export. Every output directory must be fresh. Freeze code/Git revision while collecting and comparing. The two seeds below produce12games total; do not launch an unbounded loop.

```powershell
$base = 'models/policy_v2_untrained'
$r1 = & $py tools/check_policy_v2.py --profile direct_sample_record --record-head role --model-dir $base --seed 20261025 --maps 00rows --sides A B --opponents original v47 first-hour | ConvertFrom-Json
$r2 = & $py tools/check_policy_v2.py --profile direct_sample_record --record-head role --model-dir $base --seed 20261026 --maps 00rows --sides A B --opponents original v47 first-hour | ConvertFrom-Json
& $py tools/policy_train.py prepare --receipts $r1.receipt $r2.receipt --out artifacts/datasets/role-first
& $py tools/policy_train.py preflight --model-dir $base --train artifacts/datasets/role-first/train.npz --validation artifacts/datasets/role-first/validation.npz --head role --mode ppo
& $py tools/policy_train.py fit --model-dir $base --train artifacts/datasets/role-first/train.npz --validation artifacts/datasets/role-first/validation.npz --head role --mode ppo --device cuda --out artifacts/runs/role-first --minutes 5 --epochs 4 --evaluation-config configs/evaluation/policy_v2_regular.json --i-authorize-training
```

The user has requested that the later operations agent begin this bounded training workflow after handover. Codex did not execute these commands on match data. Before fitting, require at least16 eligible training rows and4 validation rows for the chosen head, no group overlap and exact pinned behavior logits/logp. Do not duplicate rows or weaken eligibility. Current direct records have no teacher annotations: imitation mode must refuse until Codex supplies an explicit teacher-annotation collection adapter.

`prepare` validates summary/receipt identity, engine1.0.3, masks/acks/options and grouped splits. Targets are discounted terminal win plus0.25 submitted-margin/1000. The critic is separate; shared encoder/other heads stay frozen. Selection/final data never enters preparation. Old engine1.0.2 archives remain draft-only;1.0.1 is excluded.

## Monitor and inspect

Every collection, comparison and training directory has `metrics.jsonl`. Training emits start/update/checkpoint/evaluation/stop events with loss, critic loss, KL, entropy, gradient norm, learning rates, samples/s, CUDA allocated/peak bytes and timestamps. Collection/comparison emits build/game start/completion. Action records are inspectable when the official CLI finishes a replay; this is not a privileged live per-turn stream.

```powershell
& $py tools/policy_ops.py status --run artifacts/runs/role-first
Get-Content artifacts/runs/role-first/metrics.jsonl -Tail 10
& $py tools/policy_ops.py list-checkpoints --run artifacts/runs/role-first
& $py tools/policy_ops.py list-versions --root artifacts/runs
# Use the actual game folder printed in collection receipt/metrics:
& $py tools/policy_ops.py inspect-game --folder "GAME_FOLDER_FROM_RECEIPT" --side A --tail 20
# Collection also supports status using the directory containing its receipt.json:
& $py tools/policy_ops.py status --run "COLLECTION_DIRECTORY_FROM_RECEIPT"
```

Operations commands emit JSON `ok/result`; errors use nonzero exit codes. Never treat a failed command as success. Status checks the atomic checkpoint index/hash and shows the latest events; retry a transient in-progress write rather than resuming a mismatched hash. Do not poll faster than a few seconds. Report faults, invalid records, budget refusals, sparse data, fuel tails and actual actions rather than only pooled win rate.

## Recovery and model versions

Checkpoint version3 includes actor/critic, both optimizers, NumPy/Torch/CUDA RNG, config, data hashes, epoch/update count and original deadline. `checkpoint.pt` plus atomic `checkpoint.json` points at the latest state; `checkpoints/epoch-NNNN.pt` retains epoch versions. Recovery rolls back at most the unfinished epoch and does not extend the deadline.

```powershell
# If interrupted and the original deadline remains open:
& $py tools/policy_train.py fit --model-dir artifacts/runs/role-first/behavior --train artifacts/datasets/role-first/train.npz --validation artifacts/datasets/role-first/validation.npz --head role --mode ppo --device cuda --out artifacts/runs/role-first-recovered --epochs 4 --resume-checkpoint artifacts/runs/role-first/checkpoint.pt --evaluation-config configs/evaluation/policy_v2_regular.json --i-authorize-training

# After an expired/crashed run, recover a version for a NEW bounded cycle, without optimizing:
& $py tools/policy_ops.py export-checkpoint --checkpoint artifacts/runs/role-first/checkpoint.pt --out artifacts/exports/recovered-role-v1
```

A completed fit also writes `export/`. Provenance lists actually trained heads; other heads remain untrained/inherited. Never call the entire bot trained because one head changed. A new PPO cycle must collect fresh on-policy records from that exact export with new explicit seeds. Reusing old data with changed weights is rejected.

## Automated comparisons

Regular fitting evaluates every2epochs, at most twice, using the selection maps and bounds in `configs/evaluation/policy_v2_regular.json`. It compares the current export with the previous version and the frozen non-neural baseline. It records per-opponent results, never promotes automatically, and stops on implementation failure/time limit.

```powershell
& $py tools/policy_ops.py plan-comparison --candidate artifacts/runs/role-first/export --previous models/policy_v2_untrained --maps 00rows --max-games 4
& $py tools/policy_ops.py compare --candidate artifacts/runs/role-first/export --previous models/policy_v2_untrained --maps 00rows --max-games 4 --max-seconds 300 --out artifacts/evaluations/role-v1-vs-initial
```

For real selection use the frozen selection schedule/approved configuration, not training-map smoke scores. Final maps are refused by this lightweight comparison command; final evaluation uses the existing reserved/gated protocol. Small comparisons do not establish statistical superiority.

The genuinely non-neural baseline is frozen at `artifacts/baselines/heuristic-v1`, Wasm SHA256 `00c7d487990959cb4be7aac9955a4ad06f36d863b1936632f4c9cdfc93dca283`. It has audited neural switches0, including the inherited trained draft. `original` is a separate reference that still contains trained drafting. Baseline ZIP/Wasm hashes are verified every comparison. Do not rebuild or replace the frozen baseline; changes require Codex and a new version.

Stop fitting on deadline/4epochs, nonfinite loss/gradients, KL above0.015, entropy below0.05, incompatible data, implementation evaluation failure, or any user stop. Report the last checkpoint/export, data IDs, seed, per-opponent metrics and why it stopped. No auto-selection, registry edits, release activation or submission. Return architecture/training problems to Codex rather than experimenting with the design independently.
