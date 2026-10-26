# Current training operations workflow

OPERATIONS_HANDOFF.md supersedes the first-experiment recipe below: use ROLE, explicit --device cuda, version3 checkpoints, streaming metrics, and the approved regular evaluation configuration. Synthetic CPU/GPU optimization/resume has now passed. No match-data training ran. The user requested that the later Freebuff/DeepSeek agent begin the bounded cycle after handover; use DEEPSEEK_TRAINING_PROMPT.md.

---

Historical recipe/details:

# Later training: executable workflow, not jobs already run

No training has run. Every command in this document is **NOT RUN** and is for a later user-authorized session on the original laptop. The direct framework is integrated; the new heads remain untrained/off in release. This is not a trained competition bot.

## Setup and bounded first experiment

Use a workspace environment with PyTorch/NumPy; the verified CPU development interpreter is `artifacts/tmp/cpu_dev_venv/Scripts/python.exe`. For GPU fitting on this laptop, the existing CUDA interpreter in `config/paths.json` may be read without changing that environment. All outputs must stay inside workspace `artifacts/`; training data/checkpoints remain local and ignored by Git. `DEVELOPMENT_SETUP.md` covers fresh development clones.

The first experiment changes **move only**, freezing the shared encoder and all other heads. Use at most12 newly collected games,5minutes of fitting and4epochs. Terminal Monte Carlo targets are discounted terminal win plus0.25 submitted-gem margin/1000. A separate critic supplies the baseline. This is not the legacy residual PPO/GAE path and does not mix its NFS1 data.

```powershell
# NOT RUN — environment for the later session.
$py = './artifacts/tmp/cpu_dev_venv/Scripts/python.exe'
$env:PYTHONPATH = "$PWD/python"
$env:TMP = "$PWD/artifacts/tmp"
$env:TEMP = $env:TMP
$base = 'models/policy_v2_untrained'

# NOT RUN — two bounded6-game collection/check batches, twelve games total.
# Both sides, all three frozen references, reused training-partition map.
$r1 = & $py tools/check_policy_v2.py --profile direct_sample_record --record-head move --model-dir $base --seed 20261025 --maps 00rows --sides A B --opponents original v47 first-hour | ConvertFrom-Json
$r2 = & $py tools/check_policy_v2.py --profile direct_sample_record --record-head move --model-dir $base --seed 20261026 --maps 00rows --sides A B --opponents original v47 first-hour | ConvertFrom-Json

# NOT RUN — read completed records/summaries, validate identities, group both sides together,
# and write checksummed train/validation arrays. No parameter update here.
& $py tools/policy_train.py prepare --receipts $r1.receipt $r2.receipt --out artifacts/datasets/v2-first

# NOT RUN — exact pinned behavior logits/logp, schema, mask and disjoint-group check.
& $py tools/policy_train.py preflight --model-dir $base --train artifacts/datasets/v2-first/train.npz --validation artifacts/datasets/v2-first/validation.npz --head move --mode ppo

# NOT RUN — only after the user authorizes learning and the preflight/data gates pass.
& $py tools/policy_train.py fit --model-dir $base --train artifacts/datasets/v2-first/train.npz --validation artifacts/datasets/v2-first/validation.npz --head move --mode ppo --out artifacts/runs/v2-first --minutes 5 --epochs 4 --i-authorize-training
```

The current diagnostic records are not enough: the final movement-only four-game check yielded only five actor-eligible rows. Fitting requires at least16 eligible training rows and4 validation rows **for the chosen head**. If the bounded collection remains underfilled, stop, inspect admission/record counts, and plan another bounded batch or a fuel fix. Never duplicate rows, weaken masks or label refusals as actions to reach a minimum.

## Stop criteria and validation

Stop before fitting on any bot fault, malformed record, schema mismatch, train/validation group overlap or behavior mismatch. Only engine1.0.3 gameplay is admitted. Selection/final-partition maps are rejected. Grouping uses map and unordered Wasm pair, including both sides; row count is not independent match count.

During fitting, stop on deadline,4epochs, nonfinite loss/gradient, approximate KL above0.015 or entropy below0.05. Gradients clip at0.5; actor LR is1e-4 and critic LR3e-4. CPU preflight compares the exact exported behavior; float32 fitting uses the highest matmul precision. Missing acks/context, unsampled decisions, overrides and censored/interrupted macros cannot enter the actor loss.

No optimizer step, real fitting or CUDA training was executed during implementation. Synthetic tests cover batch round-trip, parity, grouping, authorization and safe installation; existing synthetic tests cover direct loss/gradient math. The first authorized trial must verify optimizer/checkpoint recovery in practice. Validation data currently gates parity and data independence; it is not a held-out strength-selection result.

## Checkpoint recovery and export

The run saves an atomic checkpoint initially and after every completed epoch, including actor, critic, both optimizers, RNG, schema/config, data identities, progress and original absolute deadline. A copy of the behavior export stays in the run directory. Recovery may roll back the unfinished epoch and never extends the deadline. An expired/completed experiment cannot be resumed as though it were a fresh budget.

```powershell
# NOT RUN — recover a genuinely interrupted experiment while its original deadline remains open.
& $py tools/policy_train.py fit --model-dir artifacts/runs/v2-first/behavior --train artifacts/datasets/v2-first/train.npz --validation artifacts/datasets/v2-first/validation.npz --head move --mode ppo --out artifacts/runs/v2-first-recovered --epochs 4 --resume-checkpoint artifacts/runs/v2-first/checkpoint.pt --i-authorize-training

# NOT RUN — development check of a later trained export, never release activation.
& $py tools/check_policy_v2.py --profile direct_record --model-dir artifacts/runs/v2-first/export --maps 00rows --sides A B --opponents original v47 first-hour
```

A completed fit exports f32 weights/header/manifest under `export/`, with the actually trained head named in provenance. Other heads remain untrained or retain their prior state. Do not call every head trained because one head changed. No script automatically promotes, changes the registry/release selection, submits or activates this export. Strength selection must use the frozen evaluation protocol with per-opponent/side anti-regression checks, then a separately authorized promotion/release change.

## Imitation and later expansion

`policy_train.py ... --mode imitation` implements the direct masked supervised path, but requires explicit teacher annotations actually executed in NFS2. Current direct-policy checks deliberately leave teacher labels absent, so they cannot supply imitation labels. Instrumented teacher annotation/collection is a separate follow-up; do not fabricate labels or reinterpret legacy residual candidates/archives. Historical engine1.0.2 data remains observational draft-only and1.0.1 stays excluded.

For later heads, record one chosen head with `--record-head`, obtain enough valid starts/closed commitments, and run its own bounded experiment. Architecture changes require new matching engine calibration, budget generation and parity. Large-map budget refusals and conservative dash/combat coverage remain improvement work. Learned fog, carry-risk and search-leaf auxiliaries are deferred until they have useful targets, training paths and measured benefit.
