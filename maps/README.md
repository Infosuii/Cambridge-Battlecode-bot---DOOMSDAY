# Maps

Map files (`.map26a`) for local games. Many hold only the authored half of a map, and the engine mirrors the rest by symmetry.

| Folder | Maps | Use |
|---|---:|---|
| `ladder-pool/` | 86 | The competition pool, from `cambc maps` |
| `local-benchmarks/` | 70 | The published maps used for development benches. 28 development and 12 held-out maps are registered in `neural/evaluation/schedules/map_partitions.json` |
| `generated/` | 50 | Template-anchored generated dev and holdout maps (see its README) |
| `x1-maze/`, `x1-maze-g5060-extra/` | 60+ | Maze maps for the x1 navigation work |
| `x1-unseen/` | 50 | Generated maps never used for tuning, used to check generalisation |

Rule we followed: held-out maps run once per frozen candidate and are never tuned on.
