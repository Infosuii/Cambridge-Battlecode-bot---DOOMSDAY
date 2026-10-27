# Tools

Run everything from the repository root. The first line of each script says what it does. Scripts stay in this one
folder because their paths are part of commands in the prompts and records.

## Benchmarking a candidate (current workflow)

| Script | Purpose |
|---|---|
| `bench3.sh` | Standard bench: candidate vs opponent on the 28 development maps, both sides, chosen seeds; cached builds, retried shards. |
| `bench3_fresh.sh` | Shortcut for `bench3.sh` with `HOLDOUT=1` and `MAP_DIR` defaulting to the 15 fresh pool maps in `artifacts/local-only/pool-maps/new15`. Frozen candidates only. |
| `bot_match.py`, `fresh_match.py` | One head-to-head shard (used by the two bench scripts). |
| `check_bench_run.py` | Verifies exact game coverage and zero native faults for both teams. |
| `bench_bayes.py` | Hierarchical Bayesian margin: accept when posterior mean ≥ 25 gems and P(>0) ≥ 0.95. |
| `bench_compare.py` | Map-clustered bootstrap interval of the margin. |
| `bench_summary.py`, `bench_maps.py`, `bench_pool.py` | Overall record, per-map table, and pooling of disjoint runs. |
| `bench_environment.py`, `bench_provenance.py` | Fingerprint the build environment (CLI, SDK, CMake, toolchain); refuse comparisons across engines or SDKs. |
| `bench_observables.py`, `bench_deaths.py`, `match_stats.py`, `deathlog_report.py` | Mechanism counts, deaths and kills, per-team totals, the bot's own death logs. |

## Version records

| Script | Purpose |
|---|---|
| `preserve_v55_experiment.py`, `preserve_v58.py` | Store an experiment as a patch against the frozen base, with source hashes. |
| `reproduce_v55.py`, `reproduce_v58.py` | Rebuild a stored experiment byte-for-byte. |
| `report_v58.py`, `report_v58_r2.py`, `report_v58_sprint3.py` | Collect the v58 rounds into `research/v58/` (`report_v58_sprint3.py` rebuilds the release evidence). |
| `patch_text.py`, `eol_like.py` | Line-ending-safe edits and diffs of bot sources. |
| `vendor/cambc.exe` | The official CAMBC CLI 4.0.0, engine 2.0.0 (`submit`, `bundle`, `maps pull`, `match-groups`). |

## Map suite (`mapgen/`)

`mapgen/` reads maps through the engine's MapBuilder, generates new maps by structured resampling of the official
maps, profiles them with a same-bot mirror, and screens/selects them. The 120-map suite (70 official + 50 generated:
`maps/generated/dev` and `maps/generated/holdout`) and its validation are described in `mapgen/README.md`.
`bench3.sh` accepts `MAP_DIR=maps/generated/dev` without `HOLDOUT=1`; every other map directory still requires it.

## Replay analysis (`replay/`)

`replay/engine.mjs` decodes `.repl26a` replays exactly through the official visualiser engine. The other scripts in
`replay/` build on it: for example `sanity_audit.mjs` (per-champion behaviour), `capture_funnel.mjs` (who clears and
who captures camps), `respawn_delay.mjs`, `fuel_outs.mjs`, `death_context.mjs`, `ladder_report.py` and
`track_submission.py` (ladder snapshots). They are offline analysis only and never feed into a bot. Set
`NFS_REPLAY_ENGINE=2.0.0` for replays from the Sprint 3 engine.

## Neural framework (earlier work; see `docs/neural-framework/`)

- Model, schema and config generation: `gen_*.py`, `install_models.py`, `install_policy_v2.py`.
- Training and data: `nfs.py` (entry point for `python/nfs`), `policy_*.py`, `train_supervisor.py`,
  `smoke_policy_training.py`.
- Checks and evaluation: `run_cpp_tests.py`, `check_*.py`, `eval_*.py`, `package_release.py`, `verify_release.py`,
  `build_references.py`.
- One-off audits and probes from the multi-agent build: `audit_*.py`, `lead_*.py`, `probe_*.py`, `stage_wave2.py`,
  `v2_baseline_audit.py`, `v53_diagnose.py`.
- Machine setup and backup: `configure_dev.py`, `configure_recovery.py`, `recovery_*.py`, `publish_*.py`,
  `verify_remote_recovery.py`.
