# Combined package results on the previous rules

Each package completed672 games:28 development maps, both sides, seeds1-12. Every wrapper exited0, coverage was exact and both teams had zero native faults. Packages are evaluated as a whole under the user's revised instruction. These are development results, not ladder forecasts.

| Package | Wins | Raw margin | Bayes mean / P(gain) | Map-cluster95% | Fuel/game |
|---|---:|---:|---:|---:|---:|
| bundle | 333/672 | +26.0 | +18.9 / 0.628 | [-50.9,+111.9] | 2.159 |
| team | 292/672 | -40.8 | -69.6 / 0.143 | [-134.2,+76.8] | 2.152 |
| core | 363/672 | +75.4 | +101.1 / 0.976 | [-1.0,+153.0] | 2.299 |
| localmeta | 315/672 | +6.1 | -10.7 / 0.421 | [-87.6,+97.7] | 2.396 |

Core was strongest, but its clustered interval crossed zero and fuel exceeded2/game. None passed the strict final release gate. No holdouts, match groups or submission were run. Core becomes a development starting point for the explicitly requested patch update, not an accepted release. All exact source snapshots and reconstruction patches are in V58_EXPERIMENTS.json.

The full team director and forced carry draft lost strength. Removing the broad vision/lock additions improved the combined package; the tested core retains objective anchoring/footwork, nearby denial, finish-before-reset, distant-contact camp work, hybrid Marcella/Tavi/Heart builds and post-walk/post-dash action reuse.
