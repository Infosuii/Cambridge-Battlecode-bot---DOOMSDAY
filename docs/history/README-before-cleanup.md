# DOOMSDAY Battlecode bot

**Latest paused botx3 work (3 November 2026):** see [HANDOFF.md](HANDOFF.md),
[fresh-machine setup](SETUP_FRESH_MACHINE.md), and [next-agent prompt](NEXT_AGENT_PROMPT.md).
Full release: `bots/botx3_11`; strongest broad measured: `bots/botx3_1`.
Official ladder submission/publication/activation is forbidden for this work.

**Active pure algorithm build:** branch `build/pure-algorithm-zero`, fresh C++ source
in [bots/dz](bots/dz/README.md). Start at [CONTINUE_HERE.md](CONTINUE_HERE.md) and
[the DZ handoff](research/dz/HANDOFF.md). The walking skeleton passed 292 release
games without faults/fuel-outs; strategy parity is not achieved. All research,
runtime restoration, calibration evidence and experiment capsules are on the branch.

**2026-10-28 portable research checkpoint:** start at [CONTINUE_HERE.md](CONTINUE_HERE.md) and
[the precise paused handoff](research/v81/HANDOFF.md). This supersedes the historical version/status claims below.
Repo v74 is live platform68; v76 is the local comparator; v80-85 are not proven upgrades. No submission or activation
is authorized. The split portable archive includes the research evidence and official Windows runtime.

Our bot for the Cambridge Battlecode (CAMBC) ladder, team **DOOMSDAY**. It plays as a heuristic C++ bot compiled to
WebAssembly. A few small neural networks run inside it: a draft network, a camp network and an item model.

**Latest submission:** repository `bots/v58`, uploaded as platform version 57 on 2026-10-26. Platform numbers trail
repository numbers by one because v56 was never submitted. It was measured against v57 at 430 wins of 672 games
(+153 gems per game). The workspace runs the Sprint 3 rules: official CLI and SDK 4.0.0, engine 2.0.0.

## Where things are

| Folder | What it holds |
|---|---|
| [`bots/`](bots/README.md) | Every ladder version, one folder each (`v48` to `v58`). `bots/vNN/src` is exactly what gets uploaded; `CHANGES.md` records what changed and how it measured. |
| [`research/`](research/README.md) | Reports, benchmark results, experiment diffs and rejected ideas, one folder per version (`research/v58/` …). |
| [`docs/`](docs/README.md) | The current handoff, setup guide and agent prompts, plus the archived neural-framework design docs. |
| [`tools/`](tools/README.md) | Benchmarking, statistics, replay analysis and release scripts. `tools/bench3.sh` is the standard head-to-head bench. |
| `maps/` | All 70 published maps. 40 are registered in `evaluation/schedules/map_partitions.json` (28 development, 12 held out). The other 30 are fresh holdout maps: the 15 pool maps from 25 October and the 15 `02*` maps. |
| `ops/` | `runner.sh` and the job queue for long unattended runs. |
| `data/` | Ladder snapshots and the decoded replay samples the analysis tools use. |
| `training/` | The v50 camp-network training run (reports and scripts). |
| `artifacts/` | Frozen builds (`baselines/heuristic-v1`, `release/`) and a small dataset. `artifacts/tmp`, `artifacts/evaluations` and `artifacts/local-only` are local scratch space and are not in git. |
| `archive/` | Finished work kept for its history: the old multi-agent workspaces and a pre-cleanup bundle. Nothing here is used. |

The **neural framework** is the earlier attempt at a fully neural bot. It still sits at the top level because the
Python package, tests and frozen evaluation records point at these paths:

| Folder | Role |
|---|---|
| `python/nfs/` | Python package. The bench uses it to build bots (`nfs.engine.official_build`). |
| `bot/` | The framework's bot source: the heuristic base plus the neural runtime. It is not a ladder version. |
| `tests/` | 288 Python tests and the C++ checks. |
| `schemas/`, `models/`, `configs/`, `config/` | Observation schemas, model files, model and training configs. `config/paths.json` holds machine paths. |
| `evaluation/`, `references/` | The locked evaluation protocol, its results, and the frozen reference bots it compares against. |
| `sdk/`, `cmake/` | The C++ SDK and build files. |

## Common commands

Run these from the repository root in Git Bash.

```bash
# head-to-head bench: candidate vs opponent, 28 development maps x 2 sides, seeds 1-4
bash tools/bench3.sh "$PWD/bots/v59" "$PWD/bots/v58" "$PWD/artifacts/evaluations/v59-vs-v58" 1 2 3 4
# is the candidate better? (Bayesian and map-clustered bootstrap)
python tools/bench_bayes.py artifacts/evaluations/v59-vs-v58
python tools/bench_compare.py artifacts/evaluations/v59-vs-v58
# the 15 fresh pool maps as a holdout (frozen candidates only, once each)
bash tools/bench3_fresh.sh "$PWD/bots/v59" "$PWD/bots/v58" "$PWD/artifacts/evaluations/v59-fresh" 1 2 3 4
# Python tests
PYTHONPATH=python python -m unittest discover -s tests/python
```

Submitting uses `tools/vendor/cambc.exe submit bots/vNN --note "..."`. Only submit when the user says so or a
prompt's release gate allows it. The gate is described in [docs/handoff.md](docs/handoff.md) §4, and each release is
recorded in `research/vNN/VNN_RELEASE.json`.

## Rules for working here

- Never edit a submitted or frozen bot (`bots/v48` to `bots/v58`, `artifacts/baselines/heuristic-v1`). Copy it to a
  new version folder instead.
- Held-out maps (the 12 `final` maps and the 30 fresh maps) run once per frozen candidate. Never tune on them.
- Never compare bench runs from different engines: results from engine 1.0.3 (before 2026-10-26) and engine 2.0.0
  are not comparable. `tools/bench_provenance.py` checks this.
- `config/paths.json` holds machine-specific paths. Never commit it.
- Raw replays and downloaded match data stay in `artifacts/local-only/`.
- New logic must stay out of per-group and per-camp hot loops: the bot runs at its per-turn compute (fuel) limit, and
  small slowdowns cost games.
