# Evaluation protocol (Agent H, `nfs-eval-v1`)

## Recorded amendment — 2026-10-24

Current protocol SHA256: `70b872f3cd4ddabb95a152d0af93579c0d9f80f25ba4408014f5c80b2c17adc1`.
The original hash below and the intermediate amendment hash remain in `protocol.lock.json` history. This amendment
was recorded after the initial framework/bisection results and before Wave2 engine results; it does not claim to
precede every candidate result. Partitions, cells and promotion thresholds are unchanged.

The smoke, fuel and equivalence schedules now explicitly require a `neutral_real` overhead-control arm paired with
`dev_untrained` on identical cells. It shares architecture, features and scoring work in shadow mode; it is not proof
of byte-identical overhead. Zero weights and experimental fuel credit do not establish action neutrality.
The old neutral_credit and per-head-credit equality rules in the original table below are superseded by **measured
divergence and fuel reporting**. `teacher_exact` remains the strict byte/action-equivalence requirement. Historical
result receipts retain their original protocol hash; do not relabel them as new runs.

Current release profiles preserve `NN_STRIP_LAB=0`; the original document's references to a stripped release describe
the earlier proposed configuration, not the checked-in profile. Removing lab host controls changed decisions in
previous official tests. A stripped release would need separate variant evaluation. No post-Wave2 package is accepted.

The rest of this document preserves the original protocol rationale; the current frozen JSON controls execution.

Frozen machine-readable form: `evaluation/protocol.json`, sha256
`af278d4f088e4bd391c44729fa713c474c2a99dc51a3b2b7401bd91daaff4bd3`, frozen 2026-10-23T23:29:54Z
(`evaluation/protocol.lock.json`, which also pins the sha256 of every `evaluation/schedules/*.json`). It was written
before any candidate result existed; only reference-vs-reference matches had been run. Every tool calls
`nfs.evaluate.protocol.load(verify=True)` and refuses a protocol or schedule whose bytes differ from the lock.
`tests/python/test_eval_protocol.py` additionally fails if the code would now generate a different protocol.
Changing it requires `python tools/eval_protocol.py freeze --supersede-reason "..."`; the old hash stays in the lock
history and must be reported.

This document explains the frozen JSON. If the two disagree, the JSON is what the tools apply.

## 1. Ground rules

- Only the official CLI (`cambc 3.0.5`, engine `1.0.3` as reported in summaries), `cambc run --release`, default fuel.
  The fuel-override flag is forbidden. `verify_release` scans `tools/`, `python/` and `configs/` for any use of it.
- At most 4 concurrent engine matches (`nfs.evaluate.schedule.MAX_WORKERS`).
- **Determinism.** A match is a fixed function of (wasm A, wasm B, map). The engine seed is per map. Re-running a cell
  or "changing a seed" does not create an independent sample. Match folders are content-addressed
  (`<map>__<sha(A)[:12]>__<sha(B)[:12]>`), so the same match is never run or counted twice. Original vs original
  side A and side B are one match.
- **Uncertainty.** The resampling unit is the map. Side and opponent cells on one map are not independent, so all
  opponents are resampled jointly with the same bootstrap map indices. Wilson intervals over games are shown only as
  a secondary, naive view.
- **Reused benchmarks.** Previous experiments used all 40 local maps, so every map is labelled `reused_benchmark`.
  Local results are deterministic benchmark evidence. They are not ladder strength and not a fresh holdout.

## 2. Map partitions (`evaluation/schedules/map_partitions.json`)

Maps are ranked once by sha256(`nfs-eval-v1|partition|<map>`) inside each series (`00`: 25 maps, `01`: 15), then
split proportionally. The salt was fixed in advance and never tuned.

| partition | n | maps | use |
|---|---:|---|---|
| final | 12 | 00ambush 00corners 00expanse 00interlock 00lanes 00monolith 00packs 00pilgrimage 01elk-arena 01fracture 01hooks 01the-farm | promotion gate, once per candidate (ledger) |
| selection | 10 | 00collision 00contest 00elkring 00fragment 00lost-world 00quadrants 01boss-battle 01concentrated-wealth 01corridors 01gold-rush | checkpoint selection during training (repeated use allowed) |
| training | 18 | 00eight 00gem-fields 00gemfight 00great-wall 00reverse-spiral 00road-of-riches 00rows 00rushbait-v2 00split 00stampede 00swirl 01big-world 01broken-curve 01islands 01shortcut 01starfish 01starvation 01yellow-brick-road | training/self-play; all build-time framework schedules |

Training (Agent G) uses only `training` maps. Selection uses only `selection` maps. Final maps are never used for
training or selection. Build-time framework schedules also stay on `training` maps, so the untrained build never
produces results on selection or final maps.

## 3. Build-time framework checks (untrained build; not strength claims)

| id | schedule | build/profile | pass rule |
|---|---|---|---|
| reference_preservation | - | references/builds/*.wasm | sha256 = manifest = protocol (and code-section sha) |
| reproducibility | `repro`: 4 maps, original vs original, side A, run twice in separate folders | any | every bundle member (replay, both `.fuel`, stdout, debug) and summary.json byte-identical |
| teacher_equivalence | `equivalence`: 6 maps x A/B x {original, v47} | `teacher_exact` | replay.repl26a and summary.json byte-identical to the recorded original cells on all 24 cells; `.fuel` reported |
| neutral_credit_equivalence | `equivalence` | `neutral_credit` | identical replay+summary on all cells (identical actions); per-turn fuel overhead reported |
| neutral_real_divergence | `equivalence` | `neutral_real` | measurement: divergent cells, first divergent round, outcome flips, margin deltas, fuel overhead. Reported in full, never hidden |
| per_head_shadow | `equivalence` | one head shadow, rest off | 0 faults; with credit identical; without credit measured like neutral_real |
| dev_untrained_plumbing | `smoke` | `dev_untrained` | 0 bot faults, 0 engine diagnostics codes, 0 invalid/NaN in NFT1 telemetry, per-head call/fallback/budget counters present. Win rates not evaluated |
| release_config_audit | - | packaged release | every `tools/verify_release.py` check passes (section 6) |
| fuel_profile | `fuel_profile` (below) | release and dev telemetry builds | release: fuelExhausted entries <= 1.25 x original + 4 per scenario; per-turn p99/p99.9/max reported; dev: per-head fuel and refusals reported |
| smoke | `smoke`: 8 maps x A/B x {original, v47, first-hour} | release (heads off) and dev_untrained | all 48 cells complete, 0 faults. Labelled **untrained framework check**: no learning or strength evidence |

How identity is measured. These facts were verified on engine 1.0.3; see `archive/agents/H/REPORT.md`.
`replay.repl26a` and `summary.json` do not depend on bot file names. A control build of the original burned about
13.5k extra fuel per turn after its decisions. Its replay and summary stayed byte-identical on 24/24 cells, while the
team's `.fuel` member changed. So "identical actions" means identical replay bytes. Fuel overhead is read per turn
from the `.fuel` member. That format is inferred, and its cap-hit turns are cross-checked against `fuelExhausted`
events on every cell. Any build whose fuel use changes the teacher's fuel-dependent decisions is measured as a
divergence. The `release` profile (lab strip) is one such build. Run it with
`eval_check.py equivalence --profile release`: that is a measurement, not an equivalence claim.

Fuel scenarios (training maps, chosen by property from the original-equivalent `campnet-off` control of the previous
diagnosis):

| scenario | maps | rule |
|---|---|---|
| low_fuel | 01yellow-brick-road, 01islands | most fuelExhausted entries (fuel limit unchanged; low-fuel fallback also covered by native budget tests) |
| many_entities | 01big-world, 01yellow-brick-road | 12 champions, most camp clears |
| crowded_combat | 00swirl, 01starfish | highest deaths per 100 rounds |
| late_game | 00stampede, 01starvation | longest games; last 25% of rounds summarised separately |
| typical | 00rows, 00great-wall | 10 champions, zero exhaustion, closest to median rounds/deaths |

Reference cells for later comparisons are recorded in `evaluation/results/reference/{repro,equivalence,smoke,fuel_profile}`
(original in the candidate seat). The summary is in `evaluation/results/reference/baseline.json`.

## 4. Statistics (`python/nfs/evaluate/stats.py`)

- Pairing: candidate cell minus baseline cell with identical (opponent, map, side). Baselines are (a) the teacher:
  the original in the candidate's seat on the same schedule, and (b) the incumbent, if a promoted candidate exists.
  Against the original opponent, the teacher baseline is exactly 0.5 per map (original vs original is one symmetric
  match), so the comparison is win rate minus 0.5.
- Per opponent, per map: average over the two sides, giving one value per cluster. Joint bootstrap over maps:
  B = 20000, seed 20261024, numpy `inverted_cdf` quantiles (exact for discrete bootstrap distributions). Reported
  values are the point estimate, the two-sided 95% interval, and the one-sided lower bound at alpha = 0.05 (5th
  percentile).
- `__pooled__` is the equal-weight mean over opponents, computed inside each replicate.

## 5. Promotion gate for trained candidates (`python/nfs/evaluate/gate.py`)

A candidate is promoted only if every check passes. A pooled gain never offsets a failed per-opponent check.

### 5.1 Validity
- Results come from the gate schedule (`final`, 96 cells = 12 maps x 2 sides x {original, v47, first-hour, v50}),
  the cells are complete and identical to the teacher baseline cells, and the protocol sha256 is the same.
- The teacher baseline is the frozen original wasm. All reference sha256s equal the protocol values.
- Every summary reports engine `1.0.3`. Candidate bot faults = 0, engine diagnostics codes = 0, invalid actions in
  telemetry = 0. Release builds have no telemetry, so invalid actions are also covered by the dev plumbing check.

### 5.2 No unacceptable regression against the original (primary reference)
- Win-rate difference vs teacher: point >= 0 **and** one-sided 95% lower bound >= -0.10.
- Gem-margin difference vs teacher: one-sided 95% lower bound >= -100.
- If an incumbent exists, the same win rules apply to candidate minus incumbent on the original-opponent cells.

### 5.3 Other references (v47, first-hour, v50)
- Win-rate difference: point >= -0.05 and one-sided lower bound >= -0.20. Margin lower bound >= -150 (vs teacher).
  The same win rules apply vs the incumbent.

### 5.4 Established benefit
- Pooled (equal-weight over the 4 references) win-rate difference vs teacher: one-sided lower bound > 0.
  Without established benefit, the teacher stays.

### 5.5 Fuel
- Candidate fuelExhausted entries <= 1.25 x teacher + 4. Games with any exhaustion <= 1.25 x teacher + 2.
- The per-turn tail from `.fuel` (p99.9, max, cap-hit turns) is reported but does not gate, because the format is
  inferred.

### 5.6 Justification
- The phase-2 failure: on selection maps the original fell from 10/12 to 6/12 while the pooled score rose from 40/60
  to 45/60. With an incumbent, this fails 5.2 (point -0.333). Without one, it fails the teacher lower bound
  (point 0, lower bound -0.33). Both cases are unit tests (`tests/python/test_eval_gate.py`).
- v50 against the original on 40 maps (36/80, point -0.05) would fail 5.2.
- The phase-2 "deferred features" variant (116 vs about 70 fuelExhausted entries) would fail 5.5.
- Power, stated plainly: with 12 map clusters, the per-map win difference vs original takes values in
  {-0.5, 0, +0.5}, and its standard error is about 0.08-0.10. To clear 5.2 and 5.4 together, a candidate needs
  roughly +8-10 points pooled improvement with no original regression. A true gain of a few points will usually not
  pass. That is deliberate: the burden of proof is on the candidate, and the known-good teacher is the default.
- The original is the user's reference teacher. The other references are secondary but may not be traded away below
  a modest loss. Margins guard against wins that come with collapsed gem totals.

### 5.7 Selection vs final, and the ledger
- Checkpoint selection may call the gate in `selection` mode on the `selection` schedule as often as needed. Those
  maps become overfit by repeated use, which is why `final` exists.
- `final`: before any final match runs, `tools/eval_run.py --schedule final --family <run id>` appends a hash-chained
  `final_reserved` entry to `evaluation/ledger.jsonl`. It refuses a second final evaluation of the same wasm sha256,
  or of any candidate from a family that already had one (a re-selected checkpoint). The only exception is a recorded
  reason of >= 20 characters (`--final-reason`), which is stored as an override and reported in the gate output.
  After the run, the results sha256 is logged. The verdict from `tools/eval_report.py --gate final` is logged too.
- `Ledger.verify()` detects edited, deleted or reordered lines. The gate in `final` mode fails without a reservation.
- Reference runs, where the candidate sha256 is one of the frozen references (for example the teacher baseline), do
  not use the ledger.
- The gate judges one candidate. Choosing among several candidates using final results is forbidden; the ledger makes
  any attempt visible.

## 6. Release verification (`tools/verify_release.py`, `tools/package_release.py`)

`cambc bundle` (3.0.5) writes flat `src/<file>` DEFLATE members with a 1980 timestamp, no directory entries and no
comment. It is deterministic. It packs everything under `src/`, including nested folders and non-source files. The
verifier therefore enforces the project rule itself:

- ZIP: only flat `src/*.cpp|*.h`; no traversal, absolute, backslash, duplicate or symlink members; CRC ok; member set
  and bytes equal to the source tree; the tree itself contains only flat cpp/h files.
- Independent rebuild: extract (validated names only) into a fresh directory, run the official build `--release`,
  then compare sha256 (or all non-custom sections) with the release wasm.
- Config: the shipped `nn_config.h` has profile `release`, kTraining/kTelemetry/kSelfTest/kFuelCredit = false,
  NN_TRAINING/NN_TELEMETRY = 0, no shadow heads, and kAnyHead consistent with the head modes.
- Wasm: no `NFS1`/`NFT1` bytes in the data section or any executable section. If lab strip is selected, no `lab_*`
  exports.
- Models: no untrained/teacher_initialized model active or release-selected. Every active head has a validated
  model. Registry status equals manifest status. The weights FNV-1a-64 is recomputed independently and every model
  file's sha256 is recorded.
- Scripts: no fuel override. References: wasm sha256 unchanged.

`package_release.py` refuses unless `bot/src/nn_config.h` is a clean release profile, then bundles, builds, writes
`SHA256SUMS` and a manifest with `submitted: false`, and runs the verifier. It never submits.

## 7. Commands (PowerShell, from ROOT)

```powershell
$py = 'C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe'
& $py tools/eval_protocol.py verify
& $py tools/eval_check.py refs
# framework checks for a build (bot dir with generated nn_config.h)
& $py tools/eval_run.py --schedule equivalence --label teacher-exact --bot-dir <dir>
& $py tools/eval_check.py equivalence --results teacher-exact --reference reference/equivalence
& $py tools/eval_run.py --schedule smoke --label dev-untrained --bot-dir <dir>
& $py tools/eval_check.py plumbing --results dev-untrained
& $py tools/eval_run.py --schedule fuel_profile --label rel-fuel --bot-dir <dir>
& $py tools/eval_check.py fuel --results rel-fuel --baseline reference/fuel_profile
# future promotion (trained candidate)
& $py tools/eval_run.py --schedule final --label ref-original-final --reference original
& $py tools/eval_run.py --schedule final --label cand-X --wasm cand.wasm --family <training-run-id>
& $py tools/eval_report.py evaluation/results/cand-X/results.json --baseline evaluation/results/ref-original-final/results.json --gate final
# release
& $py tools/package_release.py --bot bot --out artifacts/release
& $py -m unittest discover -s tests/python -p "test_eval_*.py"
```
