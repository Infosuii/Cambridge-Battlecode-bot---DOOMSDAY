# HANDOFF — neural full-stack bot build (paused 2026-10-24 01:0x, usage limit)

Read this first, then `CONTRACTS.md` (binding interfaces + file ownership) and `agents/USER_REQUEST.md` (the user's
full specification, sections 1–11). ROOT = `C:\projects\cambridge battlecode\work\neural-full-stack`.

## Non-negotiables (from the user)
- **No training**, no fine-tuning, no long self-play. Only synthetic shape/parity/round-trip tests.
- **No submission/upload/activation**, no login, no browser/desktop control.
- Do not modify anything outside ROOT (previous experiment `work/neural-gameplay`, archives, CLI/SDK are read-only).
- Official CLI only, `--release`, default fuel (never `--fuel`). Untrained heads must be reported as untrained.
- Only data from 21 Oct 2026 on; engine 1.0.1 is excluded; 1.0.2 is draft-observational only.

## Verified state (lead checked these)
- Tools: `config/paths.json`. cambc 3.0.5, engine 1.0.3, WASI clang 22.1. Python venv
  `C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe` (torch 2.11+cu128, **no pytest**:
  use unittest, `$env:PYTHONPATH="$PWD\python"`). g++ 16.2 at `C:/msys64/ucrt64/bin/g++.exe`. Machine: RTX 5070 Ti
  Laptop 12 GB, 20 logical CPUs, 31 GB RAM.
- ROOT can build with `cambc build bot --release` (has `cambc.toml`, `cmake/`, `sdk/` copied from the arena). The
  official build globs `src/*.cpp` recursively at -O3. Keep sources flat in `bot/src/`.
- Official builds are byte-reproducible. Reference builds + hashes: `references/builds/manifest.json`
  (original `eb0ea88f…`, v47, first-hour, v50), built by `tools/build_references.py` from `references/*-src`.
- **Current `bot/src` (original + all wave-1 nn_* files, nn_config profile `teacher_exact`) builds to a wasm
  byte-identical to the original** (checked at handoff time).
- Fuel ≈100k/turn (first champion turn ≈182k). Matches deterministic per (wasmA, wasmB, map).
- A debug (CAMBC_DEBUG) build of the unchanged original diverges from release on 2/4 maps
  (`evaluation/evidence/debug-build-fuel-probe.json`). So `debug_block` logging is not a free-parity training path.
- The friend declarations `nn_*_access` in `bot.h` have been applied; they produce a byte-identical wasm.

## Wave 1 status (agents ran in this session's configured model, claude-opus-5.5 via Kiro CLI subagents; run was cancelled midway by the user)
| Agent | Status | Where |
|---|---|---|
| A audit/teacher | **Complete** (REPORT.md). 59-entry decision inventory, SDK facts, 3 patches: `01_fuel_routing.diff` (38 reads → `nnb::teacher_left()`, byte-identical), `02_strip_lab.diff` (off = identical; on = only 4/24 cells identical → stripping lab changes behaviour), `03_teacher_capture.diff` (off = identical), `nn_teacher.{h,cpp}`, `tools/audit_*.py`, `tests/fixtures/teacher/` | `agents/A/` |
| B runtime/export | **Partial, no REPORT.md**. Files exist: `nn_rt.h, nn_model.h, nn_head.{h,cpp}, nn_log.h, nn_registry.h, nn_budget.h (extended), nn_config.h (generated)`, `python/nfs/{models,export.py,registry.py,records.py}`, `configs/`, `models/`. Unverified: tests, `tools/run_cpp_tests.py`, `tools/gen_config.py`/`install_models.py` presence, `models/budget.json` fuel measurements | check `git status`, rerun tests |
| C observations | **Partial, no REPORT.md**. `schemas/observation.json`, `nn_schema.h`, `nn_obs.{h,cpp}`, `nn_obs_glue.cpp`, `python/nfs/{obs,schema_gen,transforms}.py`, `agents/C/evidence/build_checks.json`. Unverified: parity tests, VISIBILITY.md, engine fuel measurement | `agents/C/` |
| G data/training | **Complete** (REPORT.md, DATA_AUDIT.md). `python/nfs/{data,train,cli.py}`, `data/manifests` | `agents/G/` |
| H evaluation | **Complete** (REPORT.md). Frozen protocol (`evaluation/protocol.json` + lock, 2026-10-23T23:29Z), schedules, `python/nfs/evaluate/*`, `tools/eval_*.py`, `verify_release.py`, `package_release.py`, 75 tests passing, reference baselines in `evaluation/results/reference/` | `agents/H/` |

Each agent also wrote `agents/<X>/CONTRACT_ISSUES.md`. **Read those before integrating**, because they flag mismatches between agents.

## Next steps (original plan, tasks 2–9)
1. **Finish B and C**: run their tests (`tests/cpp`, `tests/python/test_rt_*`, `test_obs_*`). Fill gaps: C++/Python
   parity, fuel measurement → `models/budget.json`, REPORT.md for each. Resolve CONTRACT_ISSUES.
2. **Integrate wave 1** in lead-owned files: `git apply agents/A/patches/01_fuel_routing.diff`, then `03_teacher_capture.diff`.
   Apply 02 (lab strip) only behind `NN_STRIP_LAB` and keep it **off** in `teacher_exact`. Add `nnb::begin_turn()` at the top
   of `Bot::play_turn`. After each step, check that the code section still equals the original's
   (`engine.code_section_sha`) and run `tools/audit_equivalence.py`.
3. **Wave 2 (D strategy/draft/objective/role/value, E move/combat/engage/ward/ts_leaf, F bank/shop)**: write candidate
   builders in `nn_strategy/tactics/economy.{h,cpp}` against `nnh::decide()`, add per-head schemas `schemas/heads/*.json`,
   and supply hook patches at the points in A's `decision_inventory.json`. Candidate 0 must always be the teacher, and
   hooks must be compile-time gated. Keep `draft_net_original` as a separate inherited model.
4. **Engine checks** using H's tools: all-off == original (identical replays), neutral_credit equivalence,
   neutral_real divergence measured, and dev_untrained plumbing (no faults/invalid actions). Also fuel-profile scenarios
   and bounded smoke against original/v47/first-hour on both sides, labelled as an untrained framework check.
5. **Wave 3**: independent review using `agents/H/REVIEW_CHECKLIST.md`, then fixes.
6. **Docs**: ARCHITECTURE.md (with coverage matrix), DIAGNOSIS_AND_DESIGN.md, TRAINING_LATER.md, STATUS.md, and an agent
   assignment record. EVALUATION_PROTOCOL.md already exists.
7. **Package**: `tools/package_release.py` (release profile, all untrained heads off) → ZIP + wasm + checksums, then
   `tools/verify_release.py` with an independent rebuild. **Do not submit.**

## Gotchas
- Engine stdout in replay bundles is NUL-padded. Use `engine.team_stdout()`.
- `A2_LAB=1` in the original is not inert: `A2_KNOBS` tuned values flow into gameplay through `lab::knobs`. Stripping
  any lab code changes behaviour (A measured this).
- Zeroed residual weights are not a neutral control on their own: overhead fuel changes teacher search. Use `kFuelCredit`
  (neutral_credit) to prove action equivalence, and report neutral_real separately.
- Scratch work goes under `artifacts/tmp/` (gitignored). The lead commits and agents don't run git writes.
