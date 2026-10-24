# Agent H report: evaluation, fuel/regression review, release verification (wave 1)

Model/runtime: this session ran as Kiro (claude-opus-5.5) in kiro-cli. No training, no submission, no model
selection, no git writes. Only H-owned files were edited.

## 1. What was delivered

| item | files |
|---|---|
| protocol (frozen) | `EVALUATION_PROTOCOL.md`, `evaluation/protocol.json` (sha256 `af278d4f…4bd3`), `evaluation/protocol.lock.json` (frozen 2026-10-23T23:29:54Z, before any candidate result), `evaluation/schedules/{map_partitions,repro,equivalence,smoke,fuel_profile,selection,final}.json`, `evaluation/ledger.jsonl` (empty, append-only, hash-chained) |
| library | `python/nfs/evaluate/{protocol,stats,gate,ledger,schedule,fuel,equivalence,wasm,release}.py` |
| tools | `tools/eval_protocol.py` (freeze/verify/show), `tools/eval_run.py`, `tools/eval_report.py` (tables, paired CIs, `--gate`), `tools/eval_check.py` (refs/repro/equivalence/plumbing/fuel/smoke/baseline), `tools/verify_release.py`, `tools/package_release.py` |
| tests | `tests/python/test_eval_{stats,gate,ledger,wasm,release,fuel,protocol}.py`: 75 tests, all pass |
| baselines | `evaluation/results/reference/{repro,equivalence,smoke,fuel_profile}/results.json` + checks, `evaluation/results/reference/baseline.json`, `evaluation/results/check-refs.json` |
| controls | `evaluation/results/controls/{fuelburn-probe,v47-as-candidate}` (comparator validation; not candidates), probe source `evaluation/controls/fuelburn_probe_main.cpp` |
| notes | `agents/H/{REVIEW_CHECKLIST,TELEMETRY_FORMAT,GATE_API,CONTRACT_ISSUES}.md` |

## 2. Protocol summary

- **Partitions:** maps were split by a fixed hash, stratified by series. Final 12, selection 10, training 18; all
  labelled `reused_benchmark`. Every framework schedule uses training maps only.
- **Framework checks:** see EVALUATION_PROTOCOL.md section 3 for exact rules.
  - reference preservation
  - reproducibility
  - teacher equivalence (`teacher_exact`: identical replay+summary on 24 cells)
  - neutral_credit equivalence (identical actions; fuel overhead reported)
  - neutral_real divergence (measured, never hidden)
  - per-head shadow
  - dev_untrained plumbing (0 faults, 0 invalid, counters present)
  - release audit
  - 5 fuel scenarios
  - smoke vs original, v47 and first-hour on both sides, labelled "untrained framework check"
- **Promotion gate:** paired against the teacher (the original in the candidate seat), plus the incumbent if one
  exists. Joint map-cluster bootstrap over the 4 references.
  - Original: point >= 0, one-sided 95% lower bound >= -0.10, margin lower bound >= -100.
  - Other references: point >= -0.05, lower bound >= -0.20, margin lower bound >= -150.
  - Benefit: pooled lower bound > 0.
  - Fuel: entries <= 1.25x + 4; games with exhaustion <= 1.25x + 2.
  - 0 faults, 0 diagnostics codes, engine 1.0.3.
  - In `final` mode, a ledger reservation is required. A second final evaluation of the same sha256 or family is
    refused unless a reason is recorded.
- **Power:** with 12 clusters, a candidate needs roughly +8-10 pp pooled improvement and no original regression. A
  true gain of a few points will usually fail. This is deliberate and documented.

## 3. Verified engine facts (each measured in this session)

1. **`cambc bundle` layout.** On `references/builds/original` it produces flat `src/<file>` members, sorted,
   DEFLATE, timestamp 1980-01-01, no directory entries. Two runs give the same bytes (sha `ab3b2a6d…`). A probe bot
   showed that `bundle` also packs nested `src/sub/*.cpp` and non-source files (`src/notes.txt`, `.hpp`), but ignores
   files outside `src/`. The verifier therefore enforces flat cpp/h itself.
2. **Names do not leak into match outputs.** A renamed copy of original.wasm vs original produced byte-identical
   `replay.repl26a` and `summary.json`.
3. **Fuel-insensitive replay.** I built the original plus an end-of-turn fuel burn of about 13.5k (only when more than
   40k fuel remains). On all 24 equivalence cells, replay and summary stayed byte-identical. All 24 `.fuel` members
   differed: mean overhead 9,534 per turn, p99 13,523. So actions can be compared by replay bytes and fuel by the
   `.fuel` member.
4. **Fuel member format.** `team-?.fuel` (inferred, `agents/H/TELEMETRY_FORMAT.md`) holds per-turn fuel used.
   Cap-hit turns equal the `fuelExhausted` entries for both teams on 82/82 recorded matches; the layout is consistent
   on 82/82.
5. **Release builds keep debug custom sections** (`.debug_*`, `name`). The original exports 12 `lab_*` functions,
   and imports `env` (SDK) and `wasi_snapshot_preview1`.
6. **Snapshot of the WIP integrated bot.** `bot/src` at 00:39 (teacher_exact stub config, heads off) built to the
   original's exact wasm sha256 `eb0ea88f…`. `verify_release` on its bundle passed everything except
   `config_profile_release` (expected: the profile was teacher_exact). This includes an identical-sha256 independent
   rebuild and B's untrained-model checksums, which I recomputed independently. This is a snapshot only; the lead
   integrates further.
7. **`package_release.py` end to end.** I copied that WIP `bot/src` into `artifacts/tmp/H/pkgbot` and rendered the
   `release` profile there with B's `tools/gen_config.py`; nothing in `bot/src` was edited.
   - Results: bundle, build, SHA256SUMS, a manifest with `submitted: false`, and verification.
   - The verifier correctly **FAILED** `wasm_no_lab_exports`. The release profile selects NN_STRIP_LAB=1, but the
     WIP sources do not yet implement the strip (Agent A's patch 02 has not been applied). The wasm was still the
     original's (`eb0ea88f…`) with all 12 `lab_*` exports.
   - Every other check passed, including an identical-sha256 independent rebuild
     (`artifacts/tmp/H/pkg/probe-release.verification.json`).

## 4. Baseline measurements (reference-only: the original in the candidate seat; no candidate exists)

Matches run by H: 85 in total, within the limit of 120.
- 3 pre-protocol probes on 00ambush (orig-orig, renamed copy, fuel burn). 00ambush later fell into the final
  partition. These were reference/probe matches, and orig-orig is symmetric by construction, but I disclose them.
- 52 reference matches.
- 30 control matches.

**(i) Reproducibility.** On 01starvation, 01big-world, 00swirl and 01islands, original vs original was run twice in
separate folders. All 7 bundle members and summary.json were byte-identical on 4/4 maps
(`reference/repro/check-repro.json`: PASS).

**(ii) Reference cells for equivalence.** `reference/equivalence` has 24 cells / 18 matches on 01starvation,
01big-world, 00swirl, 01islands, 00rows and 00rushbait-v2:
- original vs original: 6/12, margin 0.0
- original vs v47: 3/12, margin -176.7

`tools/eval_check.py equivalence --reference reference/equivalence` compares any later build against these folders.

**Comparator controls:**
- fuel-burn probe: actions identical 24/24, fuel identical 0/24, so a strict `teacher_exact` rule would PASS on
  actions. This shows the comparator separates action changes from fuel changes.
- v47 as candidate: 0/24 identical, 12 outcome flips, first divergent round min 3 / median 15. The comparator
  detects real divergence.

**(iii) Fuel baseline of the original on the smoke schedule.** 48 cells, 40 matches, 8 training maps, both sides.

| opponent | games | original wins | fuelExhausted entries | per game | games with exhaustion | max turn p99 | turns >= 95% |
|---|---:|---:|---:|---:|---:|---:|---:|
| original | 16 | 8 | 24 | 1.50 | 5 | 98,880 | 656 |
| v47 | 16 | 5 | 17 | 1.06 | 3 | 98,931 | 332 |
| first-hour | 16 | 10 | 26 | 1.62 | 5 | 96,070 | 244 |

Exhaustion is concentrated on 01islands (7-9 entries per game) and 01big-world. 0 faults in all games. These win
counts describe the references only: local reused-benchmark numbers, not a candidate result.

**Fuel-profile scenarios (original vs original, 18 cells / 9 matches):**

| scenario | maps | entries | games with exhaustion | max p99 | max turn | turns >= 95% |
|---|---|---:|---:|---:|---:|---:|
| low_fuel | 01yellow-brick-road, 01islands | 57 | 4 | 86,694 | 100,000 | 80 |
| many_entities | 01big-world, 01yellow-brick-road | 42 | 3 | 98,880 | 100,000 | 692 |
| crowded_combat | 00swirl, 01starfish | 3 | 2 | 77,826 | 100,000 | 4 |
| late_game | 00stampede, 01starvation | 1 | 1 | 75,026 | 100,000 | 8 |
| typical | 00rows, 00great-wall | 0 | 0 | 69,751 | 83,298 | 0 |

First champion turns reach up to 186,470 of the 200k budget.

**Reference preservation:** all 4 reference wasm sha256 and code-section hashes equal the manifest and the protocol
(`evaluation/results/check-refs.json`).

## 5. Commands used

```powershell
$py='C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe'; $mc='evaluation/results/reference/matches'
& $py tools/eval_protocol.py freeze; & $py tools/eval_protocol.py verify
foreach ($s in 'repro','equivalence','smoke','fuel_profile') { & $py tools/eval_run.py --schedule $s --label reference/$s --reference original --match-cache $mc }
& $py tools/eval_run.py --schedule equivalence --label controls/fuelburn-probe --wasm artifacts/tmp/H/fuelprobe.wasm --profile control:original+end-of-turn-fuel-burn
& $py tools/eval_run.py --schedule equivalence --label controls/v47-as-candidate --reference v47 --match-cache $mc
& $py tools/eval_check.py refs; & $py tools/eval_check.py repro --results reference/repro
& $py tools/eval_check.py equivalence --results controls/fuelburn-probe --reference reference/equivalence --profile teacher_exact
& $py tools/eval_check.py equivalence --results controls/v47-as-candidate --reference reference/equivalence --profile neutral_real
& $py tools/eval_check.py fuel --results reference/fuel_profile; & $py tools/eval_check.py smoke --results reference/smoke; & $py tools/eval_check.py baseline
& $py tools/verify_release.py --zip artifacts/tmp/H/original-bundle.zip --wasm references/builds/original.wasm --src references/original-src
$env:PYTHONPATH="$PWD/python"; & $py -m unittest discover -s tests/python -p "test_eval_*.py"   # Ran 75 tests ... OK
```

## 6. Test results

75 unittest cases, all OK (about 0.8 s). They cover:
- **Bootstrap known answers:** degenerate clusters, the exact 2-cluster distribution, Monte Carlo vs an exact
  multinomial enumeration, standard error, cross-opponent dependence preserved by joint resampling.
- **Wilson intervals.**
- **Gate:** the phase-2 case (pooled 40/60 -> 45/60 while the original fell 10/12 -> 6/12, which gives FAIL with and
  without an incumbent), a clear-improvement PASS, a failure on benefit only, faults, fuel, one-reference collapse
  despite a pooled gain, missing opponent, wrong schedule, unpaired cells, and the end-to-end `evaluate_files` path on
  the real final schedule with a temporary ledger.
- **Ledger:** repeated same sha256 or same family refused, short reason refused, long reason recorded, tampering and
  deletion detected.
- **Wasm parser:** on the real original.wasm (sections agree with `engine.wasm_sections`, 12 lab exports,
  env+wasi imports, data strings, no NFS1/NFT1) and on synthetic modules.
- **verify_release:** good synthetic ZIP; bad ones (traversal, nested, foreign, absolute, content mismatch, missing,
  duplicate); config flags; NFT1 string; lab exports with strip; registry lifecycle in B's layout; independent
  FNV-1a-64 checksum; fuel-flag use vs prose.
- **Fuel/NFT1 parsers.**
- **Equivalence comparator:** on synthetic folders.
- **Protocol integrity:** lock, code reproduces the frozen bytes, partitions, labels.

## 7. Open issues

1. **NFT1 telemetry format (Agent B).** Expected keys are documented and the parser is tolerant, but no real NFT1
   output existed yet. `dev_untrained_plumbing` cannot run until B's telemetry build lands.
2. **The release profile strips lab code.** Agent A measured that this changes gameplay. The release build must be
   judged as a variant and measured with `--profile release`, not assumed teacher-equivalent
   (`CONTRACT_ISSUES.md` #5). In the current WIP sources the strip is not implemented at all: a release-profile
   build still exports all 12 `lab_*` functions, and `verify_release` fails it (section 3, item 7).
3. **`.fuel` member format is inferred.** It is cross-checked on 82/82 matches, but gates use only the official
   `fuelExhausted` events; the tail is report-only.
4. **Gate power is limited** by 12 final map clusters. Re-running cells cannot add samples (deterministic engine).
   Only new maps would tighten the intervals, and all local maps are already reused.
5. **Framework checks on the integrated bot were not run.** That is for the later review wave, once the lead has
   built the profiles (teacher_exact / neutral_credit / neutral_real / dev_untrained / release).
6. **Proposals for the lead** (`CONTRACT_ISSUES.md`): concurrency cap in `engine.run_jobs`, and a cache identity check
   in `engine.run_match`.
7. **Provenance of the fuel-burn probe.** `controls/fuelburn-probe` points to `artifacts/tmp/H/fuelprobe.wasm`, which
   lives in a gitignored temp directory. Its source is preserved in `evaluation/controls/fuelburn_probe_main.cpp`
   (one inserted line before `bc::end_turn()`).
