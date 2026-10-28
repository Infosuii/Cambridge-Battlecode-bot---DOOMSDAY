# Tools

## Deep-analysis preflight

`replay/deep_preflight.py` hashes supplied ZIPs, compares their exact Git blob
hashes with every pinned bot tree, and saves a public ladder/group snapshot.
It has no credential, upload, activation or match-creation operation.

```bash
python tools/replay/deep_preflight.py --work artifacts/local-only/deep-2026-10-28 --out research/deep-2026-10-28 --inputs /path/to/source-zips
```

The default repository ref is the analysis parent `294500b8c4da4af19a81f2cdb262305ea54d27f9`.
Use `--repository-ref` and `--repository-branch` for a different study. A full
Git checkout can generate its own tree manifest; a connector-backed checkout
can supply `repository-tree.json` under the local work directory. Raw HTTP
responses remain local-only. Snapshot metadata does not prove live identity.
Session status and remaining validation: `research/deep-2026-10-28/STATE.md`.

Run everything from the repository root. The first line of each script says what it does. Scripts stay in this one
folder because their paths are part of commands in the prompts and records.

## Website replay intake and reconciliation

Use the signed-in official match-group page's Download 5 games and each game's
Summary / Download JSON controls. Keep the frozen IDs in CANDIDATE_MANIFEST.json;
do not queue replacement games or read held-out trajectories while retrieving files.

`replay/deep_download_ingest.py --downloads <download-directory>` reads only named
study files, validates both ZIP CRC layers and the exact five registered match IDs,
preserves immutable raw evidence under artifacts/local-only and writes DOWNLOADS.json.

```bash
python tools/replay/deep_download_ingest.py --downloads /path/to/Downloads
NFS_REPLAY_ENGINE=2.0.0 node --no-warnings tools/replay/decode_replays.mjs --workers 4 --out artifacts/local-only/deep-2026-10-28/decoded.jsonl artifacts/local-only/deep-2026-10-28/replays/calibration-excluded artifacts/local-only/deep-2026-10-28/replays/examined artifacts/local-only/deep-2026-10-28/replays/hands-off
python tools/replay/deep_reconcile.py artifacts/local-only/deep-2026-10-28/decoded.jsonl
```

On PowerShell set `$env:NFS_REPLAY_ENGINE='2.0.0'` before invoking Node. The shared
loader finds installed official assets or accepts NFS_REPLAY_ASSETS.
Validate the five calibration pairs before bulk decoding. `deep_reconcile.py`
audits native accounting, replay final states, drafts, dynamic rosters and available
frozen metadata, reporting booleans rather than held-out decisions or detector rates.

For an already verified prefix from the same pinned decoder, avoid duplicate decoding:
`python tools/replay/deep_decode_missing.py --node <node-executable> --prior <prior-local.jsonl>`.
It retains prior passing rows, decodes only missing files, combines local JSONL and
reconciles the complete result. Raw JSONL, native summaries and ZIPs are never committed.

## Registered replay detectors

Read research/deep-2026-10-28/DETECTOR_SPEC.json first. Definitions were committed
before examined processing. The extractor accepts only calibration-excluded or
examined; it refuses hands-off before creating output. It uses the pinned engine-2
loader, actual channel/capture state and native events. Flags are associations;
read the registered limits for mode, gate, island and vision proxies.

```bash
NFS_REPLAY_ENGINE=2.0.0 node tools/replay/test_detectors.mjs
NFS_REPLAY_ENGINE=2.0.0 node --no-warnings tools/replay/detectors.mjs --partition calibration-excluded --validate --workers 3 --out artifacts/local-only/deep-2026-10-28/detector-calibration-NEW
NFS_REPLAY_ENGINE=2.0.0 node --no-warnings tools/replay/detectors.mjs --partition examined --validate --workers 4 --out artifacts/local-only/deep-2026-10-28/detector-examined-NEW
python tools/replay/test_deep_detector_report.py
python tools/replay/deep_detector_report.py --run artifacts/local-only/deep-2026-10-28/detector-examined-NEW
```

Use new run names. Current-source/spec hashes and five passing calibration games
are required before examined processing. Per-game local JSON contains per-champion
events, ranges, first-flag rounds, contexts, rates and denominators. The report
produces P2_DETECTORS.md and DETECTOR_DATA.json, with Wilson intervals and map/
opponent bootstrap sensitivity. This does not calibrate win probability or prove
causal mistakes. PowerShell: set `$env:NFS_REPLAY_ENGINE='2.0.0'` before Node.

`deep_metadata_restore.py` reads only frozen public group endpoints, paced and
cached. It creates no match and uses no login. It validates all selected identities,
maps, sides, outcomes and native scores/rounds; raw responses remain local-only.

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

## Deep analysis: 28 October 2026 Session 1

All raw inputs stay in `artifacts/local-only/deep-2026-10-28/`; public/derived ledgers
and reports are in `research/deep-2026-10-28/`. No tool here submits or activates a bot.

| Tool | Usage and boundary |
|---|---|
| `replay/deep_ingest_source.py` | `python tools/replay/deep_ingest_source.py bot.zip --platform-version 69 --submission-id <id>`; compare pinned repository blobs and freeze exact bytes; refuses differing existing source. Requires the pinned repository-tree export. |
| `replay/deep_catalog.py` | `--ui <version-filtered-UI-export.json>`; join authenticated v69 group IDs to paced, cached public metadata. No timestamp-only attribution. |
| `replay/deep_plan.py` | Freeze official ladder cohorts and existing ranked-map loss metadata; no match creation. Do not refresh a frozen cohort after starting its wave. |
| `replay/deep_ledger.py` | `plan`, `reserve --number N`, `confirm --number N --group UUID --state finished`, `status`; local budget ledger only. Reserve before the separate authorized UI request. Never retry a reserved/uncertain write. |
| `replay/deep_native_audit.py` | `--downloads <JSON [{match_id,path}]>`; internal official-summary identities plus metadata checks; explicitly does not reconcile replay trajectories. |
| `replay/deep_top_catalog.py` | Bounded public current-engine top-five-versus-top-five catalog, metadata only. |
| `replay/deep_wave_results.py` | `--ui <verified-group-UI-receipts.json>`; check every requested map, ordered side, opponent and unranked type; no private downloads or new requests. |
| `replay/deep_checkpoint.py` | Build the metadata candidate manifest, freeze seed20261028 cohort/map split, and regenerate Session-1 reports. Refuses to change existing candidate assignments. Requires study inputs and the saved proof screenshot. |

`decode_replays.mjs` now uses the shared engine loader/pins. Select current games with
`NFS_REPLAY_ENGINE=2.0.0 node tools/replay/decode_replays.mjs --workers 4 --perspective --out <local-only.jsonl> <replays>`.
`NFS_REPLAY_ASSETS` or `--assets` selects an installed asset directory; Linux cache
and Windows AppData are supported. Syntax/pin/instantiation checks pass. All555 current replay/native pairs now reconcile; five-game calibration passed
before accepted bulk decoding. See research/deep-2026-10-28/STATE.md for later checks.


## Session 2 timelines, model and prediction-first cards

All commands run at the repository root. Set NFS_REPLAY_ENGINE=2.0.0 (PowerShell:
$env:NFS_REPLAY_ENGINE='2.0.0'). Raw trajectories stay ignored. The tools reject
hands-off analysis. Use new output directories; preserve prior calibration receipts.

| Tool | Purpose / usage |
|---|---|
| replay/timeline.mjs | --partition calibration-excluded --workers3 --out artifacts/local-only/deep-2026-10-28/timeline-calibration-NEW, then --partition examined with a new output. Requires5 current-code calibration passes. End-of-round/native ledger validation, exact gold credit phases, union vision, first camp targets and accepted action/blocked-step log. |
| replay/deep_timeline_report.py | --run <examined-run>; creates P3_TIMELINES/TIMELINE_DATA/TIMELINE_SCREEN from360 own games. Actual native draft picks are separate from physical rosters. |
| replay/deep_model_split.py | Creates immutable MODEL_SPLIT.json,231/77/77 stratified game partitions. Never resplit after fitting. |
| replay/winprob.py | --run <examined-run>; fixed-scale symmetric L2 logistic plus calibration-set temperature, game weights, frozen test evaluation. Needs NumPy; no sklearn/scipy. Do not tune on test results. |
| replay/test_winprob.py | Four scientific checks: neutral calibration bins, symmetry, no future income, per-game weighting. |
| replay/deep_model_report.py | Renders P3_WINPROB from the saved model without refitting. |
| replay/deep_moments.py | --run <examined-run>; up to5 disjoint ~10-round drops/loss, immutable105-card MOMENT_SAMPLE. |
| replay/moment_contexts.mjs | before <examined-run> freezes exact focus-actor own observations and conditional expectations; commit them before after <examined-run> exposes subsequent action windows. CARD_PREDICTIONS must remain unchanged. |
| replay/deep_card_report.py | --run <examined-run> [--detectors <corrected-detector-run>]; cards<=25 lines, error_analysis.csv, event-label surrogate ceilings and nearest-state winner controls. Descriptive, not confirmed bugs. |
| replay/deep_correction_audit.py | Uses preserved timeline-examined-v2/v3 and detector-examined-v2/v3 to prove feature/native-event equivalence after the blocked-movement correction. Fixed historical directory names are intentional. |
| replay/deep_session2_checkpoint.py | Refreshes the measured checkpoint, small resource-only calibration sample and handoff pointers; does not implement bots, queue games or fabricate traces. |
| replay/audit_session2_delivery.py | Checks105 cards,65 losses,15 control wins, line limits, frozen predictions/splits, source integrity and no hands-off leakage. |

Latest valid runs: detector-calibration-v7/examined-v3 and
timeline-calibration-v5/examined-v3. Official PanelChrome.L distinguishes22 teleport
completion,23 movement blocked,25 sell and9 priority. DECODER_CORRECTION.md records
the post-registration implementation fix; thresholds were not changed.

## Session 3–4 exact replay research and final confirmation

Run from repository root with NFS_REPLAY_ENGINE=2.0.0 and the pinned official CLI4.0.0/default fuel. Build/run require the installed compiler cache. Raw replay/scripts/logs/Wasm stay under ignored artifacts/. These tools never upload, activate or queue games.

| Tool | Usage / boundary |
|---|---|
| replay/deep_repro_prepare.py, deep_repro_plan.py | Copy all33 frozen source files byte-for-byte into ignored artifacts and freeze the12-case reproduction plan. |
| replay/puppet/replay_format.py, parse_inputs.py | Exact engine2 accepted-input format; `parse_inputs.py --partition calibration-excluded` or `examined --ids <selected UUIDs>`. Rejects unknown records and bulk examined parsing without selected IDs. |
| replay/puppet/validate_inputs.mjs | `<script.json> ...`; API reapplication, exact saved raw bytes and every-round state hash. Five calibration games first. |
| replay/puppet/gen_puppet.py | `--help`; generate exact per-team C++ script including drafts, accepted targets/orders and fuel-pause continuation. No opponent source involved. |
| replay/puppet/run_reproductions.py | `--workers 2`; official local both-scripted and frozen-source-vs-enemy-puppet suite. Reuses hash-checked builds; preserve original run directories. |
| replay/puppet/compare_replays.mjs, audit_reproductions.py | `node compare_replays.mjs <match-id> <actual raw> <local output.json>`; `python audit_reproductions.py --node <node.exe>`. Full round-state hashes, first divergence incl draft. Originals calibration/examined only. |
| replay/puppet/make_trace*.py, trace_format.py, run_traces.py | `run_traces.py --format numeric|tail|bank-tail --suite artifacts/tmp/deep-repro/<NEW> --cards <IDs> --node <node.exe>`. Generator formats verbose/channel retain failed attempts. Trust only lines whose logical and emission rounds precede first accepted-input divergence; sparse tail lacks mid-guard data. Never replace a successful receipt with an incompatible format. |
| replay/puppet/label_inputs.mjs | `<local script.json>`; label accepted raw inputs and bounded actor states. Calibration/examined references only. |
| replay/puppet/run_recall_takeover.py | `--node <node.exe>`; predeclared C004 warm diagnostic with bank-eligibility cancellation condition. Ten-round cap; ignore match outcome; reads TAKEOVER_PLAN. Diagnostic source only. |
| tests/loss_cases/run_case.py | See tests/loss_cases/README.md; requires exact warm inputs/states and unchanged accepted enemy script. Rejects incomplete/short candidates. |
| replay/puppet/run_masking.py | `--node <node.exe>`; two MASKING_PLAN contexts, restore baked A2 vector at warm takeover to remove V71 override; no outcome claims. |
| replay/puppet/screen_recall_loops.py | `--run artifacts/local-only/deep-2026-10-28/timeline-examined-v3`; fixed exploratory M1 observable proxy, not exact private timer mechanism. |
| replay/profile_contacts.mjs | `calibration-excluded|examined <new-local-output>`; official geometry/native-damage/basic-focus extract. Current five-game calibration required for bulk. No reserved profile mode. |
| replay/deep_profiles.py | Build eight profiles/78 size-band strata from current profile-examined-v1 and TIMELINE_DATA. Includes real sample denominators and map-cluster uncertainty. |
| replay/deep_puppet_audit.py | Assert17 real parser fixtures unchanged and independent basic-attack focus counts equal ten calibration team outputs. |
| replay/final_actions.mjs | `<partition> <local-output>`; minimal fixed D3/M1 support extraction. Reserved mode requires FINAL_VALIDATION current hashes; no full detector/model/card work. |
| replay/deep_final_confirmation.py | `validate` compares all385 examined M1/D3 outputs and360 native accounting rows; `confirm` consumes the165 final fixed extracts. The plan was committed before first access. Do not reuse the reserved games for tuning. |
| replay/deep_final_report.py | Rebuild REPORT/DATA/mistakes/NEXT_BOT_BRIEF and state from committed fixed result receipts. Append-once knowledge/tool/handoff updates; no fitting or external writes. |
| replay/audit_final_delivery.py | Check complete report/case/provenance/split boundaries, exact reproduction, final validation and frozen source. |

Canonical paths and measured limitations are in research/deep-2026-10-28/STATE.md. Historical Session2 tools/receipts are retained as earlier checkpoints; final state supersedes their “still unfinished” notes.
