# HANDOFF — neural full-stack bot build (paused 2026-10-24 ~01:40, usage limit)

Read this first, then `CONTRACTS.md` (binding interfaces + file ownership) and `agents/USER_REQUEST.md` (the user's
full specification, sections 1–11). ROOT = `C:\projects\cambridge battlecode\work\neural-full-stack` (git repo;
latest commit `ee74a6b`, working tree clean at handoff).

## Non-negotiables (from the user)
- **No training**, no fine-tuning, no long self-play. Only synthetic shape/parity/round-trip tests.
- **No submission/upload/activation**, no login, no browser/desktop control.
- Do not modify anything outside ROOT (previous experiment `work/neural-gameplay`, archives, CLI/SDK are read-only).
- Official CLI only, `--release`, default fuel (never `--fuel`). Untrained heads must be reported as untrained.
- Only data from 21 Oct 2026 on; engine 1.0.1 is excluded; 1.0.2 is draft-observational only.

## Environment (verified)
- Tools: `config/paths.json`. cambc 3.0.5, engine 1.0.3, WASI clang 22.1.
  - Python venv: `C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe` (torch 2.11+cu128). It has **no pytest**: use unittest.
  - Set `$env:PYTHONPATH="$PWD\python"`. Put `C:\msys64\ucrt64\bin` on PATH for the g++ tests, otherwise the obs parity tests are skipped.
  - Machine: RTX 5070 Ti Laptop 12 GB, 20 logical CPUs, 31 GB RAM.
- `cambc build bot --release` works from ROOT (`cambc.toml`, `cmake/`, `sdk/`). The official build globs `src/*.cpp` at -O3. Keep sources flat in `bot/src/`.
- Official builds are byte-reproducible. Reference wasm + hashes are in `references/builds/manifest.json` (original
  `eb0ea88f…`, v47, first-hour, v50). Rebuild with `tools/build_references.py`.
- Fuel ≈100k per turn (first champion turn ≈182k). Matches are deterministic per (wasmA, wasmB, map).
- A debug (CAMBC_DEBUG) build of the original diverges from release on 2/4 maps
  (`evaluation/evidence/debug-build-fuel-probe.json`). `debug_block` is therefore not a free-parity logging path.

## Test commands (all pass at handoff)
```
$py -m unittest discover -s tests/python -p "test_*.py"     # 186 tests OK (data, train, eval, obs)
$py tools/run_cpp_tests.py                                  # 11 targets, 451/451 checks (runtime kernels/head/records)
$py -m unittest tests.python.test_obs_parity -v             # C++ vs Python obs encode bit-exact (needs g++ on PATH)
$py tools/lead_profile_check.py --profiles teacher_exact dev_untrained neutral_credit training --maps 2
```

## What exists and is integrated
- **bot/src (lead-integrated):**
  - Original sources, plus A's patches `01_fuel_routing` (38 fuel reads go through `nnb::teacher_left()`), `02_strip_lab` (gated by `NN_STRIP_LAB`, off) and `03_teacher_capture` (compile-time-gated captures of teacher choices: objective, bank, fight, chain, shop, move steps, cast, ward, draft).
  - `main.cpp` turn hooks under `#if NN_ANY_HEAD`: `nnb::begin_turn()`, `nnh::turn_start()`, `play_turn()`, `nnh::idle()`. `nnh::warmup()` runs on draft turns.
  - Runtime: nn_rt/model/head/log/budget/registry (B), nn_obs/obs_glue/schema (C), nn_teacher (A).
  - The checked-in `nn_config.h` is profile `teacher_exact`. **This build is byte-identical to the original wasm** (re-checked after integration).
- **Profiles** (`configs/profiles/*.json`, applied by `tools/install_models.py --profile X --src <scratch>/src`):
  - teacher_exact, neutral_credit, neutral_real, dev_untrained, training, selftest and release all build with the official CLI.
  - Smoke runs vs the original had 0 faults and 0 bot errors (`evaluation/results/lead_profile_check*.json`).
  - The training profile emits NFS1 records (75–80 per game, flushed only from leftover fuel).
- **Models** (`models/registry.json`, every one labelled synthetic):
  - `fs_v1_untrained`: zero residual, teacher-neutral.
  - `fs_v1_dev`: non-zero residual, plumbing only.
  - `draft_net_original`: inherited original draft network, status trained, used by the teacher and not re-exported.
  - fs_v1 models were regenerated against C's real schema (hash 0xD341B69C, kObsDim 563) with `python -m nfs.models.untrained`.
- **Agents' outputs:** A, G and H are complete, with REPORT.md in `agents/A`, `agents/G` and `agents/H`. B and C have no REPORT.md. Their code is now tested (see the commands above), but their engine fuel measurements were never done.
- **Evaluation (H):** the protocol is frozen (`evaluation/protocol.json` + lock), with schedules, `python/nfs/evaluate/*`, `tools/eval_*.py`, `verify_release.py`, `package_release.py`, and baselines in `evaluation/results/reference/`.
- **Data/training (G):** `python/nfs/{data,train,cli.py}` and `tools/nfs.py`. Parameter-updating commands refuse to run without `--i-authorize-training`.

## Lead fixes made this session (B's runtime was mid-refactor)
- `nn_head.cpp`: `nnlog::write_*` became `enqueue_*`. Added `nnh::idle()`, which flushes queued records only while leftover fuel exceeds a 4000 reserve. In training mode, `Result.net` is now always the deployed argmax rule.
- `tools/run_cpp_tests.py`: runtime unit tests now use stub-schema test models in `artifacts/tmp/B/cpp/stub_models`. The stub-model fix also covers the selftest/tamper paths, and training-record checks tolerate non-context heads.
- `tests/cpp/rt_head.cpp`: flushes through `nnh::idle()` and prints `[dbg]` mismatch diagnostics.
- `models/budget.json` is still **provisional, not engine-measured**:
  - turn_allowance went 30000 → 55000, because a K=16 decision plus the encoder costs ≈30k by the coefficient model.
  - log cost at admission is now the enqueue cost only.
  - **Must be replaced by real measurements.** The default model may be too expensive: encoder ≈12.9k and ≈919 per candidate.

## Step 3 result: neutral equivalence (done 2026-10-24, evidence `evaluation/evidence/neutral_equivalence_bisect.json`)
- **teacher_exact** (all heads compiled out) is byte-identical to the original wasm. This is the only exact-equivalence claim.
- **Fuel credit cannot make a neural-enabled build byte-identical to the original.** Results (6 maps x 2 sides vs original):

  | Build | Identical cells |
  |---|---|
  | neutral_credit | 4/12, also with an engine-calibrated overhead of 33 fuel per capture call |
  | Runtime linked, no captures, no hooks, no credit | 11/12 |
  | The same plus only the credit arithmetic in `teacher_left()` | 6/12 |
  | **Control:** unchanged original + ~40 fuel burned at turn start | 10/12 |
  | **Control (agent H):** original + 13.5k fuel burned at turn **end** | 24/24 |

  So the teacher is chaotically sensitive to fuel shifts of a few dozen units **before or during** its decisions, while spend **after** them is harmless. Diagnosis-phase-2 finding 1 is a general property of this teacher.
- **Decisions taken:**
  1. Every future evaluation uses an overhead-matched control arm (the same binary with heads in shadow or zero-residual, i.e. neutral_real) as well as the original. The original alone does not show "neural changed play".
  2. Captures are `[[gnu::noinline]]` and wrapped in `nnb::CreditScope` (calibration in `NN_SCOPE_OVERHEAD`). Records and telemetry are written only after `play_turn`, from leftover fuel.
  3. `kFuelCredit` is kept as an experimental flag and is **not** a neutrality proof.

  These should go into DIAGNOSIS_AND_DESIGN.md and H's protocol. H's gate compares against references, so add the neutral_real arm to the schedules (needs a recorded protocol amendment, because the protocol is frozen).
- Telemetry is unified: B's lines are now `NFT1 head round=.. head=<id> admitted= refused= fallback= neural= fuel=`, which H's parser form 3 accepts. Head is a numeric id; mapping it to a name is still to do. No lines appear yet, because no gameplay `decide()` hooks exist.
- Tools: `tools/lead_profile_check.py` (build profiles + smoke), `tools/lead_neutral_bisect.py`, `tools/lead_wrap_captures.py` (idempotent).

## Known problems / findings (open)
1. `models/budget.json` is provisional. The engine fuel probe has not been run.
2. Each agent's `agents/*/CONTRACT_ISSUES.md` lists issues nobody has resolved yet.
3. Stripping lab code changes behaviour. Keep `NN_STRIP_LAB=0` unless a separate evaluation justifies it.
4. No per-head schemas exist yet (`schemas/heads/*.json`), so every head uses the default F=24.
5. C still owes VISIBILITY.md and real obs fixtures. No team-intent shared-memory encoding exists yet.
## Gotchas
- Engine stdout in replay bundles is NUL-padded. Use `engine.team_stdout()`.
- `A2_LAB=1` is not inert: `A2_KNOBS` tuned values feed gameplay through `lab::knobs`.
- A zeroed residual alone is not a neutral control, because overhead changes the teacher's fuel-gated search.
- PowerShell mangles inline Python/C++ with quotes. Use the file edit tools or script files.
- Scratch work goes in `artifacts/tmp/` (gitignored).
