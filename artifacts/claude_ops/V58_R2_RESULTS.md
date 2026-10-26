# v58 round2 strategy results

Frozen v57 opponent,28 development maps, both sides. SDK/CLI3.0.5, engine1.0.3; no Sprint3 changes.
13 valid runs, 4256 played games; 3808 distinct configuration/map/side/seed slots.
C1 and C3b screen seeds recur in confirmation. Variants share development maps; these are not independent confirmations.
All completed runs exited0, had exact coverage and zero native faults on both teams. C3 preflight failed with0games.

| Run | Games | Wins | Raw gems | Bayes mean | P(>0) | Map-cluster95% | Fuel/game |
|---|---:|---:|---:|---:|---:|---|---:|
| r2-m1 | 224 | 107 | -17.1 | -22.2 | 0.339 | [-56.3, +22.3] | 1.8259 |
| r2-t1 | 224 | 112 | -9.4 | -5.0 | 0.467 | [-46.9, +18.5] | 2.0134 |
| r2-h1 | 224 | 114 | +12.4 | +10.2 | 0.576 | [-15.5, +48.4] | 1.8170 |
| r2-c1 | 224 | 113 | +32.3 | +43.7 | 0.781 | [-39.1, +107.9] | 1.9107 |
| r2-n1 | 224 | 109 | -11.9 | -23.9 | 0.332 | [-54.7, +28.7] | 2.1518 |
| r2-c1-confirm | 672 | 354 | +42.6 | +58.2 | 0.883 | [-21.4, +111.4] | 1.9301 |
| r2-f1 | 224 | 112 | -5.5 | -8.1 | 0.436 | [-24.3, +8.8] | 1.8616 |
| r2-p1 | 224 | 110 | +1.7 | -8.0 | 0.441 | [-46.1, +47.4] | 1.7009 |
| r2-c2 | 672 | 361 | +40.9 | +59.2 | 0.905 | [-15.5, +103.9] | 1.9539 |
| r2-c3b | 224 | 122 | +57.5 | +81.3 | 0.922 | [-15.8, +135.1] | 2.1205 |
| r2-c3b-confirm | 672 | 368 | +57.1 | +85.5 | 0.964 | [-4.9, +126.2] | 2.0045 |
| r2-c4 | 224 | 122 | +59.7 | +85.0 | 0.938 | [-8.1, +132.5] | 2.0580 |
| r2-c4b | 224 | 122 | +59.7 | +85.0 | 0.938 | [-8.1, +132.5] | 2.0580 |

Fuel is not rounded before applying the≤2 gate. Bayesian acceptance alone does not satisfy the clustered-interval rule.

## Configurations

* **r2-m1**: Marcella camp-resistance/attack build.
* **r2-t1**: Tavi attack-stat farming build.
* **r2-h1**: Heart early universal damage reduction.
* **r2-c1**: Hold safe cleared captures under contact.
* **r2-n1**: Immediate supported capture denial.
* **r2-f1**: Bounded finish before gold-only shopping.
* **r2-p1**: Finish an engaged camp before chasing distant contact.
* **r2-c2**: Capture holding with urgent-race and conservative burst guards.
* **r2-c3b**: One visible safe capture anchor; other bodies retain combat.
* **r2-c4**: Prototype sole-anchor movement inside the capture region.
* **r2-c4b**: Capture movement with explicit board-edge bounds.

## Reproduction

`python tools/reproduce_v58.py <configuration> <new repo-local directory>` reconstructs the exact frozen source.
Use `bench3.sh` with absolute candidate/opponent/output paths and the recorded seeds; compare with both
`bench_bayes.py` and `bench_compare.py`. `check_bench_run.py --seeds <list>` verifies coverage and native faults.
Built-source and candidate/opponent wasm hashes for every seed are in V58_R2_RESULTS.json. Raw data remain local-only.
