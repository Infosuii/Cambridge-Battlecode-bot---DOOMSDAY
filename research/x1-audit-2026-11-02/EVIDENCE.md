# Evidence location and publication boundary

The GitHub publication contains the completed diagnosis, all35 readable timelines,16 loss case studies, source evidence excerpts,617 feature/threshold identifiers,171 interaction-pair classifications, match/cohort indexes and validation receipts. No bot source, bot binary or runnable patch is published by this commit.

The complete local evidence package is `C:/projects/cambridge battlecode/analysis/x1-audit-2026-11-01/x1-analysis-evidence.zip` (208,221,742 bytes; SHA256 `49e21e025191b3ea6fd56577ed750ca65a23b6612395637696bbf79b7ff74b9c`). It contains all35 full-round CSV and JSONL files,39,729 opening/completed/terminal round records, raw native replays, diagnostic scripts and source-preservation evidence. Uncompressed evidence is approximately2.62GB. These large artifacts are intentionally not placed in ordinary Git history.

Full per-round paths, relative to the local audit folder, are `decoded/<match UUID>.rounds.csv` and `.rounds.jsonl`. Original replay and native summary are in `matches/<match UUID>/`. Source inventory, effective macro preprocessing, compile commands and all experimental receipts remain there. Publication links pointing here identify a local-only artifact rather than a missing claimed GitHub upload.

Cutoff:2026-11-01T23:10:04.114Z.20 games reproduce byte-for-byte with attached x1 source;15 are context-only source mismatches. The10 newly collected games against EggsAfter11AM and dromedaries are included in the context cohort. No adaptive-opponent counterfactual victory benefit is claimed. The analysis-only scope excludes fix recommendations.

