# v58 round2: capture discipline, economy and survival

The user resumed research after the failed coordinated-economy round, asking what top teams do differently and
whether we can implement it. They identified sustained contested-camp throughput, economy scaling and survival
against stronger opponents as the priorities. The later request explicitly changes the evaluation unit to combined
packages; round3 is recorded separately in V58_R3_PLAN.json. Round2 has not been submitted.

## Evidence and hypotheses

The recorded historical item and pressure audits use34 v55-versus-Claudus games from the registered development
partition. The full historical corpus and earlier analyses already contain original-map exposure; this is not a
pristine holdout source. Initial inventory inspection also viewed the existing broad aggregate. The saved new
ladder analyses filter to development maps. No new original/fresh holdout benchmark or match group was run.
The previous SDK/CLI3.0.5 and engine1.0.3 were kept; Sprint3 patch notes were ignored as requested.

On gold-bearing groups byR500, historical DOOMSDAY had3.06 occupation interruptions near enemies per game,
Claudus1.24. Claudus captured19 such groups versus15.62. These are descriptive/confounded: stronger
gear, draft and pressure all matter. Their base capture gold1873.5 versus1083.8 shows a much larger gap than
captures of groups with only enemy basic attackers (24.1 versus11.2 gold). Most of the income deficit is not simply
reward theft. The new counter therefore protects our completed work while retaining normal nearby fighting.

The pressure audit infers capture from gold gains and interruption from lost uncontested occupation; it is not an
engine progress counter. Gold-free groups are deliberately excluded from these counters so completed gem-only
captures are not mislabeled as interruptions. Simultaneous kills/purchases can obscure recognition, and spell-only
clearers are absent from the basic-attack attribution. The same decoder is used for both teams. R500 means a
window, not whole-life throughput. Do not mistake base camp gold for actual income including champion/item bonuses.

## Implemented strategies

* M1: Marcella opens Jungle strength and Durability health, then stacks attack. This was an attack-oriented
  hypothesis, not a faithful full top-team build: later inspection shows focus, health, then strength emblems.
  R3 corrects that hybrid support progression as KIT_MARCELLA=2; it has no separate individual R2 result.
* T1: Tavi uses Treasure strength, Durability health and Monster strength before attack stacking.
* H1: Heart adds Durability health before its long stat stack.
* C1: retain an already occupied cleared reward region when a conservative visible-enemy burst estimate says it
  is safe; stationary attacks/casts remain available. Do not chase off the reward just because an enemy is visible.
* N1: healthy, light-bag champions may enter an adjacent enemy capture region immediately, only with nearby allied
  support and a visible power advantage. No remote chase. The final disabled code also respects winning bags.
* F1: defer a healthy gold-only shopping reset for at most10 rounds to finish an already engaged nearly dead camp
  or collect a nearby pending reward. Health retreats and winning-bag banking retain priority. One deadline per target.
* P1: finish an almost-dead engaged camp while every visible enemy is outside immediate reach, instead of chasing.
  It reuses existing camp staffing, tank rotation, targeting and movement; it does not introduce a new global plan.
* C2: C1 with winning-bag, imminent enemy tribute, end-of-game guards and a more conservative burst allowance
  (possible extra basic reset and both damage abilities). It received the fixed12-seed test directly.
* C3b: elect one visible safe anchor (Vesper first, then actor id) so other bodies keep their existing combat logic.
  The first C3 preflight used the wrong gem accessor; it exited1 with0games, was preserved as invalid, and was
  corrected to champion::gem_count() in a distinct immutable C3b snapshot before any strength games.
* C4/C4b: a sole capturer on an unsafe tile may step to a safer adjacent tile within the same capture region.
  It never overrides a safe attack, and still falls back to normal flight when no safe interior tile exists. C4b
  adds the explicit bounds guard required before the raw bitmap helper. Both screens produced identical game
  outcomes and0faults; C4 is not suitable for release without that guard. No12-seed footwork claim is made.

Every mechanism remains behind a disabled default in the production research tree. V57 and all earlier bots,
SDK, benchmark wrappers and machine configuration were preserved. Raw replays/caches/builds remain local-only.

## Results and interpretation

C1 was the first new component to pass incomplete-loop non-inferiority. Its fixed12-seed result was354/672,
+42.6 raw gems; Bayes+58.2/P=.883, cluster95%[-21.4,+111.4], fuel1.930/game. Its R500 pressure interruptions
fell1.74 versus2.58, about one third; base capture gold1431.6 versus1384.8. This does not prove top-team strength.

C2:361/672,+40.9; Bayes+59.2/P=.905, cluster[-15.5,+103.9], fuel1.954/game. Pressure interruptions1.76 versus2.60.
C3b:368/672 (54.8%),+57.1; Bayes+85.5/P=.964 (Bayesian ACCEPT), cluster[-4.9,+126.2], fuel1347/672=2.00446.
Do not round that fuel result down to a pass. C3b is promising but still fails the strict clustered/fuel conditions.
Its incremental result versus C2 was+16.1, cluster[-15.5,+50.8]; the anchor change is not independently proven.
R500 pressure interruptions1.84 versus2.66; base capture gold1432.8 versus1373.0; captures17.56 versus17.08.
The full income and survival deficits remain. Native death reductions are modest, not the30% target.

The role-build, shopping, distant-contact and denial screens were small/negative or inconclusive. Footwork gave
+59.7 over224games, P=.938, cluster[-8.1,+132.5], fuel2.058/game. None of these individual results establishes an
accepted improvement. More seeds on the same maps are not a substitute for a coherent package or independent
validation. No once-only holdout was opened to rescue them, and no upload occurred.

## Commands and reproducibility

All normal runs returned0. Each used bench3 with absolute snapshot, frozen v57 and new absolute output prefix,
then seeds1–4 or the fixed1–12. Screens repeated in confirmation are labeled; they are not independent data.
Validation: tools/check_bench_run.py <prefix> --seeds <list> --json <out>. Strength: tools/bench_bayes.py and
only tools/bench_compare.py for clustered candidate comparisons, including the paired C3b/C2 and footwork ablations.
Mechanisms: tools/bench_observables.py; tools/replay/v58_pressure_report.py <prefix> <out.json>, or --ladder
<raw replay directory> <out.json>; tools/replay/v58_top_builds.py <cached audit.json> <out.json>.

Every R2 source snapshot, including invalid C3, reconstructs hash-exactly using tools/reproduce_v58.py. Manifest:
V58_EXPERIMENTS.json. Per-seed source/build identities and complete result tables: V58_R2_RESULTS.json/.md.
No naive standard error was used to select a mechanism. The user has now requested testing the combined package,
so R3 will judge the package rather than requiring each component to pass individually.


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

Fuel is not rounded before applying theâ‰¤2 gate. Bayesian acceptance alone does not satisfy the clustered-interval rule.

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
