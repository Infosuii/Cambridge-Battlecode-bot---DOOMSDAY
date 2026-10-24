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

## Known problems / findings (open)
1. **Neutral equivalence currently FAILS:** this is with no decision hooks wired (no `decide()` calls in gameplay yet).
   - neutral_credit and dev_untrained already change outcomes vs the original: 00ambush A gives 1047–745 vs the original's 1029–782.
   - Cause: overhead the fuel credit doesn't cover. That is the teacher captures (`nnt::kAny` turns on every capture when any head is on), `nnh::warmup()` in the draft, and `turn_start`.
   - Fix: wrap the captures, warmup and turn hooks in `nnb::Meter`/credit, or charge them via `nnb::credit()`. Then run H's equivalence schedule (`tools/eval_check.py`, `tools/audit_equivalence.py`) for neutral_credit and require identical replays. Report neutral_real divergence separately. This is exactly the diagnosis-phase-2 failure mode, so it must be solved before training.
2. Telemetry format mismatch: B prints `NNTEL ...` lines, while H's parser (`python/nfs/evaluate/fuel.py`, `agents/H/TELEMETRY_FORMAT.md`) expects `NFT1`. Unify them.
3. Each agent's `agents/*/CONTRACT_ISSUES.md` still lists issues nobody has resolved yet. Read them all.
4. Stripping lab code changes behaviour: only 4/24 cells were identical. Keep `NN_STRIP_LAB=0` in every profile unless a separate evaluation justifies it.
5. No per-head schemas exist yet (`schemas/heads/*.json`), so every head uses the provisional default F=24.

## Next steps (in order)
1. Fix finding 1 (fuel-credit coverage), then prove neutral_credit gives identical replays on H's equivalence schedule. Measure real fuel with a probe (B's deliverable 4) and rewrite `models/budget.json`.
2. **Wave 2: decision hooks (D/E/F work).** Use A's `agents/A/decision_inventory.json` (59 entries, exact hook points) and the captures already in place.
   - Write candidate builders in `nn_strategy/tactics/economy.{h,cpp}` that call `nnh::decide()`.
   - Candidate 0 must be the teacher and always legal. Hooks are `if constexpr` gated.
   - Add `schemas/heads/<name>.json` with features, and Python twins in `python/nfs/heads/`.
   - The draft hook goes at `cap_draft_pick(best)` in draft.cpp.
3. Re-run all tests and `lead_profile_check.py`. Run H's plumbing/fuel/smoke schedules for dev_untrained, labelled as an untrained framework check.
4. Wave 3 review against `agents/H/REVIEW_CHECKLIST.md`.
5. **Docs:** ARCHITECTURE.md (coverage matrix: decision → state → candidates → head → call site → fallback → fuel → status → labels), DIAGNOSIS_AND_DESIGN.md, TRAINING_LATER.md (G's CLI commands, labelled as not run), STATUS.md, and an agent record. EVALUATION_PROTOCOL.md already exists. The agents ran as Kiro CLI subagents with the configured model claude-opus-5.5. The wave-1 run was cancelled partway by the user, which is why B and C have no reports.
6. **Package:** `tools/package_release.py` with the release profile (all untrained heads off) produces ZIP, wasm and checksums. Then run `tools/verify_release.py` with an independent rebuild. **Do not submit.**

## Gotchas
- Engine stdout in replay bundles is NUL-padded. Use `engine.team_stdout()`.
- `A2_LAB=1` is not inert: `A2_KNOBS` tuned values feed gameplay through `lab::knobs`.
- A zeroed residual alone is not a neutral control, because overhead changes the teacher's fuel-gated search.
- PowerShell mangles inline Python/C++ with quotes. Use the file edit tools or script files.
- Scratch work goes in `artifacts/tmp/` (gitignored).
