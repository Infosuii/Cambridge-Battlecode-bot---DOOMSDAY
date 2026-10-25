# Setting up a fresh device (the next agent's laptop)

Everything needed to build, test, analyse and submit is in this repository. Only the large training data stays on the training box (`ops/HANDOFF.md` §7), and none of the next steps need it.

## 1. Prerequisites

- Windows x64. Other platforms need their own official `cambc` 3.0.5 binary.
- Git Bash: every `*.sh` here is bash.
- Python 3.12 with `numpy`, and `torch` for training (`pip install -r requirements-dev.txt`). A CUDA torch build is only needed for GPU training.
- Node.js ≥ 20, for `tools/replay/*.mjs`.
- Optional: MSYS2 UCRT64 `g++`, only for the native policy tools (`tools/check_teacher_exact.py`, `policy_ops.py compare`). The bot builds do not need it.

## 2. Official CLI and login

The unmodified official CLI is vendored: `tools/vendor/cambc.exe` (3.0.5, SHA-256 in `tools/vendor/manifest.json`).
- **The user must log in on this device:** `tools/vendor/cambc.exe login`. Agents never enter credentials. Without a login, everything local still works; only `ladder`, `matches`, `match-groups` and `submit` need it.
- The first `cambc build` downloads the wasi-sdk into `%LOCALAPPDATA%/cambc/wasi-sdk-33`.
- Replay decoding (`tools/replay/decode_replays.mjs`) loads the engine wasm from the CLI's visualiser assets, `%LOCALAPPDATA%/cambc/assets/<hash>/visualiser/assets` (pinned by SHA-256 in the script). Run `tools/vendor/cambc.exe view <any replay>` once to install them, or pass `--assets <dir>`.

## 3. Configure the clone

```bash
python tools/configure_dev.py --cli tools/vendor/cambc.exe       # rewrites config/paths.json for this machine
```

`configure_dev.py` stops if it cannot find a native `g++`. Install MSYS2 UCRT64, or pass `--native-cxx <path>`; any existing file works if you will not use the native policy tools.

Check the `cli`, `python` and `maps` entries in `config/paths.json`. `maps` should be `maps/local-benchmarks`: all 40 ladder maps are vendored there, and `nfs.engine` falls back to it when the configured map folder is missing.

Environment for every command (bash):

```bash
export PYTHONPATH="$PWD/python" PYTHONDONTWRITEBYTECODE=1 TMP="$PWD/artifacts/tmp" TEMP="$PWD/artifacts/tmp"
export PY=python   # or the full path to your interpreter; the bench scripts read config/paths.json otherwise
```

## 4. Smoke test (about 5 minutes)

```bash
python -c "from pathlib import Path; from nfs import engine; engine.official_build(Path('bots/v52'), Path('artifacts/tmp/v52.wasm'))"
python tools/bot_match.py --a artifacts/tmp/v52.wasm --maps 00rows --out artifacts/evaluations/smoke   # v52 against heuristic-v1
MAPS_OVERRIDE=00stampede bash artifacts/claude_ops/bench2.sh "$PWD/bots/v52" "$PWD/bots/v51" "$PWD/artifacts/evaluations/smoke-b2"
```

Pass **absolute** paths to `bench2.sh`/`bench28.sh`, because they `cd` to the repo root. A full bench2 run is 168 games; with 20 CPU threads it takes about 25 minutes, so it scales with your core count.

## 5. Where things are

| What | Where |
|---|---|
| State, findings, gate, next steps | `ops/HANDOFF.md` |
| Plan | `artifacts/claude_ops/V52_PLAN.md` |
| Bot versions | `bots/v48`, `v50`, `v51`, `v52` (live), `v53` (work base) |
| Bench and match tools | `artifacts/claude_ops/bench2.sh`, `bench28.sh`, `tools/bot_match.py`, `tools/match_stats.py`, `tools/bench_summary.py` |
| Ladder tools | `tools/replay/ladder_report.py`, `track_submission.py`, `decode_replays.mjs`, `team_ratings.py` |
| Ladder data snapshots | `data/ladder/` |
| Benchmark results so far | `artifacts/claude_ops/results/` |
| v50 camp-net PPO training code | `training/v50-campnet/` (paths inside are the training box's; adjust ROOT and CLI) |
| Policy-v2 neural framework (abandoned) | `python/nfs/policy`, `tools/policy_bc.py`, `bot/src/nn_policy_*` |
| Frozen baseline | `artifacts/baselines/heuristic-v1` (do not modify) |
