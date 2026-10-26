# Setting up a fresh device (the next agent's laptop)

Everything needed to build, test, analyse and submit is in this repository. Only the large training data stays on the training box (`docs/handoff.md` §7), and none of the next steps need it.

## 1. Prerequisites

- Windows x64. Other platforms need their own official `cambc` 4.0.0 binary.
- Git Bash: every `*.sh` here is bash.
- Python 3.12 with `numpy`, and `torch` for training (`pip install -r requirements-dev.txt`). A CUDA torch build is only needed for GPU training.
- Node.js ≥ 20, for `tools/replay/*.mjs`.
- Optional: MSYS2 UCRT64 `g++`, only for the native policy tools (`tools/check_teacher_exact.py`, `policy_ops.py compare`). The bot builds do not need it.

## 2. Official CLI and login

The unmodified official CLI is vendored: `tools/vendor/cambc.exe` (4.0.0 / engine2.0.0, SHA-256 in `tools/vendor/manifest.json`).
- **The user must log in on this device:** `tools/vendor/cambc.exe login`. Agents never enter credentials. Without a login, everything local still works; only `ladder`, `matches`, `match-groups` and `submit` need it.
- The first `cambc build` downloads the wasi-sdk into `%LOCALAPPDATA%/cambc/wasi-sdk-33`.
- Replay decoding (`tools/replay/decode_replays.mjs`) loads the engine wasm from the CLI's visualiser assets, `%LOCALAPPDATA%/cambc/assets/<hash>/visualiser/assets` (pinned by SHA-256 in the script). Run `tools/vendor/cambc.exe view <any replay>` once to install them, or pass `--assets <dir>`.

## 3. Configure the clone

```bash
python tools/configure_dev.py --cli tools/vendor/cambc.exe       # rewrites config/paths.json for this machine
```

`configure_dev.py` stops if it cannot find a native `g++`. Install MSYS2 UCRT64, or pass `--native-cxx <path>`; any existing file works if you will not use the native policy tools.

Check the `cli`, `python` and `maps` entries in `config/paths.json`. `maps` should be `maps/local-benchmarks`: all70 published maps are vendored there, and `nfs.engine` falls back to it when the configured map folder is missing.

Environment for every command (bash):

```bash
export PYTHONPATH="$PWD/python" PYTHONDONTWRITEBYTECODE=1 TMP="$PWD/artifacts/tmp" TEMP="$PWD/artifacts/tmp"
export PY=python   # or the full path to your interpreter; the bench scripts read config/paths.json otherwise
```

## 4. Smoke test (about 5 minutes)

```bash
python -c "from pathlib import Path; from nfs import engine; engine.official_build(Path('bots/v52'), Path('artifacts/tmp/v52.wasm'))"
python tools/bot_match.py --a artifacts/tmp/v52.wasm --maps 00rows --out artifacts/evaluations/smoke   # v52 against heuristic-v1
MAPS_OVERRIDE="00rows" bash tools/bench3.sh "$PWD/bots/v54" "$PWD/bots/v53" "$PWD/artifacts/evaluations/smoke-b3" 1
```

Pass **absolute** paths to `bench3.sh`, because they `cd` to the repo root. The default run is 168 games (28 maps, both sides, three seeds); twelve seeds give 672. A non-zero exit, any faults, or fewer than twice the map count times the seed count makes the run invalid. Compare candidates with `tools/bench_compare.py` and use its map-clustered 95% interval for decisions.

## 5. Where things are

| What | Where |
|---|---|
| State, findings, gate, next steps | `docs/handoff.md` |
| Plan | `research/v52/V52_PLAN.md` |
| Bot versions | `bots/v48`, `v50`, `v51`, `v52` (live), `v53` (work base) |
| Bench and match tools | `tools/bench3.sh`, `tools/bench_compare.py`, `tools/bot_match.py`, `tools/match_stats.py`, `tools/bench_summary.py` |
| Ladder tools | `tools/replay/ladder_report.py`, `track_submission.py`, `decode_replays.mjs`, `team_ratings.py` |
| Ladder data snapshots | `data/ladder/` |
| Benchmark results so far | `research/<version>/results/` |
| v50 camp-net PPO training code | `training/v50-campnet/` (paths inside are the training box's; adjust ROOT and CLI) |
| Policy-v2 neural framework (abandoned) | `python/nfs/policy`, `tools/policy_bc.py`, `bot/src/nn_policy_*` |
| Frozen baseline | `artifacts/baselines/heuristic-v1` (do not modify) |

Sprint3: the active workspace uses official SDK/CLI4.0.0 and engine2.0.0. bench3 fingerprints CLI, SDK, CMake and toolchain inputs, so legacy Wasm caches cannot be reused after migration. Native faults on either team invalidate the run. Compare only matching environments. Historical training records and replay analysis default to1.0.3; explicitly set NFS_REPLAY_ENGINE=2.0.0 for new replays. Do not mix old/new gameplay labels. Fresh-map final checks use HOLDOUT=1 MAP_DIR=<directory> with bench3, without opening those pools during development.
