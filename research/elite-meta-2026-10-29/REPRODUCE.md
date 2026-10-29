# Reproduction and arbitrary-round inspection

Run from this repository root. Python 3.12 and Node 24 were used; the shared engine loader supports the pinned official visualiser assets. CLI/SDK 4.0.0 and engine 2.0.0 are different version numbers. Do not use the loader's historical 1.0.3 default.

Charts require Matplotlib 3.11.2. It was installed only into the ignored temporary directory, with `PYTHONPATH=artifacts/tmp/elite-meta-plotlibs` and `MPLCONFIGDIR=artifacts/tmp/elite-meta-matplotlib`; no global Python installation was changed. An ordinary environment with Matplotlib installed can run charts.py directly. Run finalize.py after report/chart generation to check links, polish prose spacing and package the outputs.

## Preserve the sample

MANIFEST.json and MANIFEST.sha 256 freeze 30 match IDs and official metadata. SELECTION_PROTOCOL.md was written before examining new trajectories. MANIFEST_INITIAL.json and SELECTION_AUDIT.md disclose a metadata-classification precedence correction made before decoding. The full catalog had 325 eligible matches; six unavailable weaker-opponent slots were filled from elite games under the registered fallback. Never rerun catalog against a new live ladder and describe it as the same frozen sample.

The existing metadata catalog and public responses are local-only under `artifacts/local-only/elite-meta-2026-10-29/public` and `catalog.json`. LADDER.json contains the selection-time ranks, developer status and wider 50-game pick summaries; those wider summaries are not primary replay evidence. Opponent submission versions are hidden. MATCH_INDEX.csv supplies a source URL and ID for every primary match.

## Acquire the frozen games

Use an already authenticated official CLI. Agents did not log in or handle credentials. These scripts only read metadata/downloads; they cannot create matches, submit or activate bots.

```powershell
$env:PYTHONUTF8='1'
$env:NFS_REPLAY_ENGINE='2.0.0'
python research/elite-meta-2026-10-29/acquire.py download
python research/elite-meta-2026-10-29/acquire.py summaries
```

All bundles and raw summaries stay ignored under `artifacts/local-only/elite-meta-2026-10-29`. Download/summary retries handle transient server failures. Six surplus files were downloaded from the initial metadata selection; they were excluded from every primary analysis. The secondary integrity decoder happened to validate those six too, so its 36-file count must not be presented as 36 investigated matches.

## Recreate the complete extraction

```powershell
node research/elite-meta-2026-10-29/mechanics.mjs
node research/elite-meta-2026-10-29/extract.mjs
python research/elite-meta-2026-10-29/analyse.py
python research/elite-meta-2026-10-29/enrich.py
python research/elite-meta-2026-10-29/activity.py
python research/elite-meta-2026-10-29/deep_cases.py
python research/elite-meta-2026-10-29/write_reports.py
python research/elite-meta-2026-10-29/charts.py
```

`extract.mjs` verifies the frozen manifest, pins engine assets, reads every timeline event, records every post-draft round and every champion's personal turn-start view, and checks gold/gems/earnedGold at every boundary against independent native RLE timelines. It additionally checks final cursor, scores, result, duration, drafts and physical bodies. A synthetic initial recordR 0 corresponds to the post-draft start of engine round 1; R1 onward are round-end states, with a partial terminal round retained. R0 is clearly labelled and is not counted as an actual played round.

`enrich.py` recovers static camp membership from the rich initial PC.F snapshot, because the compact timeline PC.I snapshot omits group/maxHealth fields. It changes derived grouping metadata, not the complete state/action/view ledgers. `activity.py` counts movement independently of channel presence, preventing productive recall/cancel controllers from being mislabelled idle. `deep_cases.py` saves the extended gate sequence beyond the generic±5 windows. These are disclosed analysis corrections, not engine migrations.

The scripts resume existing immutable extraction records where appropriate. To recompute derived metrics from scratch, use a new local-only output copy or move only this study's derived metrics aside; do not alter submitted bots, synced sources or older research partitions. `write_reports.py` combines machine evidence with authored `analyst_notes.json`; automation does not invent those causal interpretations.

## Independently verify the decoder

```powershell
$taskManifest = Get-Content research/elite-meta-2026-10-29/MANIFEST.json -Raw | ConvertFrom-Json
$taskReplayPaths = @($taskManifest.rows | ForEach-Object { 'artifacts/local-only/elite-meta-2026-10-29/replays/' + $_.id + '.repl26a' })
node tools/replay/decode_replays.mjs --workers 4 --out artifacts/local-only/elite-meta-2026-10-29/independent-decoder.jsonl @taskReplayPaths
python research/elite-meta-2026-10-29/audit.py
```

The standard decoder has historical action labels, including its obsolete event 23 label; it is used here only for numeric/final-state reconciliation, not mobility interpretation. The new transition ledger uses the official current engine label “Movement blocked”. All 30 primary pairs pass the standard decoder's eight independent-summary checks. VALIDATION.json also validates gzip CRC/readability, line counts, SHA hashes, all expected round IDs, terminal cursor/score, current extraction code hash, native conservation and protected tracked paths.

## Inspect any round without rerunning a replay

```powershell
python research/elite-meta-2026-10-29/inspect_round.py 3b30c86a-59c6-4ba9-985b-e771210c3f51 538 2
```

This reads the already extracted compressed ledgers for R536–540: rich omniscient round states, ordered transitions and each actor's own fog-limited turn-start context. It does not initialise an engine or replay other matches. Use the input/substep cursor to order actions within a round. The complete replay and native summary remain available for an independent re-extraction.

## Source comparison

USER_BOT_IDENTITY.json proves 33 byte-identical files between the newly supplied `bot (9).zip` and frozen `bots/live-69`. CURRENT_SOURCE.json records the live-v71 metadata and conditional comparison with the existing V81 archive. The latter archive matched filename/size, but a fresh server download failed; no server hash was invented. Raw source archives stay local-only. `source_intake.py` is a read-only identity/extraction utility, not a build command.

## Limits and experimental status

No new controlled match or counterfactual policy simulation was run. Item paybacks and channel-duration comparisons are arithmetic under stated conditions. POLICY_DIAGNOSTIC.json is a retrospective earlier/later diagnostic, not a clean prospective holdout. Existing historical exact reproductions are explicitly attributed to v69/v70. No spent reserved trajectory, release holdout or new map was used to tune a bot.

The report archive contains reports, derived CSVs, charts and research scripts; it deliberately excludes raw replays, source archives and the 256MB local ledger. Keep the local evidence directory with this checkout, or reacquire the frozen IDs to reconstruct it elsewhere.
