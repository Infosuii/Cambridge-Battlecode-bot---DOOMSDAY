# v58 development screens — not submitted

28 development maps × both sides × seeds1–4 =224 games per screen;20 screens =4480 games.
Every completed screen has exact coverage and zero native faults on both teams. D2 failed to build and is excluded.
Eight diagnostic games are excluded. All results use SDK3.0.5 / engine1.0.3; Sprint3 changes were not applied.

| Variant | Wins/224 | Raw gems | Bayes mean | P(>0) | Map-cluster95% | Fuel/game |
|---|---:|---:|---:|---:|---|---:|
| d1 | 98 | -38.8 | -40.2 | 0.256 | [-116.5, +60.4] | 1.728 |
| d2b | 103 | -31.3 | -25.8 | 0.349 | [-135.4, +69.9] | 1.679 |
| d3 | 90 | -58.8 | -95.1 | 0.054 | [-152.8, +41.7] | 2.500 |
| d4 | 86 | -42.9 | -70.6 | 0.154 | [-160.2, +94.7] | 2.268 |
| d5 | 99 | -4.0 | -22.0 | 0.375 | [-111.7, +119.1] | 2.036 |
| d6 | 100 | +0.0 | -22.1 | 0.383 | [-115.2, +131.2] | 2.094 |
| d7 | 93 | -26.8 | -63.0 | 0.178 | [-132.2, +101.1] | 2.205 |
| a1 | 106 | -32.7 | -42.4 | 0.203 | [-104.9, +35.1] | 2.290 |
| d8 | 89 | -95.6 | -113.0 | 0.041 | [-192.9, +15.9] | 2.304 |
| a2 | 111 | +7.2 | +9.7 | 0.569 | [-39.0, +49.8] | 1.942 |
| d9 | 96 | -46.7 | -61.5 | 0.185 | [-161.8, +79.1] | 2.478 |
| s1 | 79 | -200.6 | -250.7 | 0.000 | [-302.2, -104.2] | 1.906 |
| d10 | 59 | -270.2 | -315.1 | 0.000 | [-378.7, -157.0] | 1.897 |
| a3 | 113 | -6.4 | -7.9 | 0.443 | [-21.9, +6.3] | 1.741 |
| d11 | 101 | -6.7 | -27.2 | 0.352 | [-120.6, +125.3] | 2.094 |
| d12 | 97 | -31.5 | -53.6 | 0.209 | [-140.5, +90.3] | 3.031 |
| v1 | 93 | -63.4 | -88.3 | 0.049 | [-133.2, +7.4] | 1.741 |
| l1 | 113 | +4.4 | +6.6 | 0.548 | [-55.6, +52.2] | 1.781 |
| d13 | 100 | -4.7 | -13.5 | 0.429 | [-119.8, +132.8] | 2.487 |
| d14 | 107 | +5.3 | +12.1 | 0.564 | [-136.7, +163.5] | 1.790 |

No screen reaches mechanism acceptance (Bayes mean≥25, P(>0)≥.95); none has a positive clustered lower bound.
No screen passes incomplete-loop non-inferiority. No12-seed confirmation or once-only holdout was justified.

## Incremental comparisons

These compare each revision with the prototype it modifies, using paired map/side/seed observations.

| Change vs base | Raw gain | Bayes mean | P(>0) | Map-cluster95% |
|---|---:|---:|---:|---|
| d2b vs d1 | +7.5 | -5.9 | 0.464 | [-102.4, +107.3] |
| d3 vs d2b | -27.6 | -30.0 | 0.326 | [-161.3, +111.0] |
| d4 vs d3 | +15.9 | -3.9 | 0.469 | [-100.8, +135.9] |
| d5 vs d4 | +38.9 | +30.8 | 0.721 | [-74.1, +159.2] |
| d6 vs d5 | +4.1 | +7.4 | 0.573 | [-69.7, +89.9] |
| d7 vs d6 | -26.9 | -13.8 | 0.328 | [-99.3, +37.9] |
| d8 vs d6 | -95.6 | -106.1 | 0.029 | [-189.5, -9.3] |
| d9 vs d6 | -46.8 | -40.5 | 0.161 | [-142.6, +48.9] |
| d10 vs d6 | -270.2 | -235.1 | 0.000 | [-370.2, -178.5] |
| d11 vs d6 | -6.7 | -0.4 | 0.415 | [-17.2, +0.0] |
| d12 vs d6 | -31.6 | -23.4 | 0.182 | [-88.5, +25.8] |
| d13 vs d12 | +26.9 | +0.9 | 0.565 | [-2.3, +61.1] |
| d14 vs d13 | +10.0 | +31.3 | 0.755 | [-91.8, +112.1] |

An incremental improvement inside a losing loop does not make the complete loop acceptable.

## Reproduction

Use `python tools/reproduce_v58.py <variant> <new repo-local directory>`; it verifies every source-file hash.
Then run `bash artifacts/claude_ops/bench3.sh "$PWD/<directory>" "$PWD/bots/v57" "$PWD/artifacts/evaluations/<new-prefix>" 1 2 3 4`.
Use the same pinned SDK/engine. Every normal run returned0; `check_bench_run.py` verifies exact224-game coverage and both fault counts.
Run `bench_bayes.py <prefix> --json <out>` and `bench_compare.py <prefix> [base-prefix] --json <out>`.
Use the optional replay-report tools listed in V58_BUILD_LOG.md for mechanism audits. Raw replays remain local-only.
