# Release logging collector proof (JOHNDOE #69 / #74)

All runs: cambc 4.0.0, engine 2.0.0 (engineBuildHash 85aa7167...), release, 100k fuel, opponent bots/v92 release
`5704d7ba41acca8f...`. Logging build = bots/claude-native-1104 at c3ceaa4b with `CLNA_EPS 0.02` + `CLNA_RLOG 1`
prepended to common.h, release WASM `9f8cf58b454074a683a66ba965912ff1066f85b02f4bb16d6bd0626006ae76e8`.

| file | what |
|---|---|
| capture_vs_discard.json | same WASM, 00corners side A: `--log-limit 64MiB` vs `--log-limit 0`. Statistics JSON byte-identical (sha256 equal): 1006-927, 1271 rounds, 69 fuel-out entries, seed 14185859257870086076 |
| nat-rel-01.shard.json | collector proof on 00corners/00oasis x A/B (DEVELOPMENT maps: proof only, never trained on): 4/4 eligible, 9725 decisions, logp replay 4.8e-7 |
| rlog-vs-nolog.report.json | logging vs non-logging release eps build (nolog WASM `1a81c3d9...`), dev maps ambush/contest/corners/crater x A/B: 0/8 cells identical; own fuel-outs 655 vs 360; score 5/8 vs 3/8; paired +0.25 [0.0, 0.5], 4 families. Logging changes play, so the logging build is the evaluated/deployed artifact |
| nat-rel-train-01.shard.json | release batch on the first 8 TRAINING maps x A/B: 16/16 eligible, 35144 decisions, 7W 9L |
| gate-update-02.report.json / .clna_gate.h | one bounded update (4 epochs, lr 0.05, clip 0.2) on nat-rel-train-01 with --map-manifest; alpha 0.02 -> [0.0162, 0.0238], mean 0.0193; max approx-KL 2.3e-4; mechanism step, NOT a strength claim |

The map manifest used is JOHNDOE's PROVISIONAL `jd-eval-map-candidate-v1` (sha256 a1fcb51e...).
