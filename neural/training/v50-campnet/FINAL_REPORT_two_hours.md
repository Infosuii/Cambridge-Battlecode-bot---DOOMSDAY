# Additional two-hour training result

Training: 43,632 new simulated games; 6,631,254 recorded decisions; 1818 PPO updates.

Selected iteration: 792 (0 retains the first-hour policy). Selection score: 45.0/60.

Against supplied v47 on 40 maps, both sides: 41.0/80 wins. This covers 40 deterministic map clusters, not 80 independent maps.

Eight reserved-map pooled results: selected bot 47.0/80; original bot 47.0/80; first-hour bot 52.0/80. Full opponent-specific rows and faults/fuel are in evaluation/. Earlier final maps have been reported already; these are reused benchmarks, not a fresh independent generalization test.

The source ZIP was checked against its files, then independently rebuilt with identical executable Wasm sections. Training tracing is disabled. No ladder submission was made.

No new historical draft was fitted; the first experiment's rejected historical network remains rejected. The four existing 21 October archives have 89,606 unsampled entries before eligibility filtering, so historical supply is not low. Local simulated games and historical matches are distinct.

Artifacts: release/bot_neural.zip and release/bot_neural.wasm. Full machine-readable report: report.json; verification: verification.json. The first-hour artifacts remain unchanged.

## Full opponent comparisons

| Opponent | All 40 maps, both sides | Eight reserved maps, both sides | Candidate faults | Fuel-exhaustion entries (all maps) |
|---|---:|---:|---:|---:|
| v47 | 41/80 wins | 9/16 wins | 0 | 73 |
| original | 36/80 wins | 8/16 wins | 0 | 74 |
| first-hour | 43/80 wins | 7/16 wins | 0 | 101 |

The new policy does not show a reliable general improvement. It narrowly beat v47 and the first-hour bot over all maps, but lost to the original. On the reused eight-map pooled benchmark it scored 47/80, matching the original 47/80 and below the first-hour bot's 52/80. The exploratory map-cluster 95% interval for its pooled win-rate difference from original is -15 to +15 percentage points. Fuel exhaustion is distinct from a crash; zero bot faults does not mean zero fuel exhaustion.

## Upload and activation

The exact verified source was uploaded successfully as **version 50** through the official CLI. CLI packaging was compared byte-for-byte by source member with the verified source archive before upload. See deployment.json and submission.log.

**Live activation is unverified and remains blocked.** The CLI provides no activation command, the existing CLI bearer login receives HTTP 401 from the submission-list API, and the official site interface asset receives HTTP 403. Server compilation status and active-version state could not be read. No desktop/browser control was taken, consistent with the user's restriction. Open https://2026a.battlecode.co.uk/game/submissions to check server compilation and activate version 50. This upload alone is not evidence that version 50 is live.
