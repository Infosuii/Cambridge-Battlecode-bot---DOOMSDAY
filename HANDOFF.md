# HANDOFF — neural full-stack Battlecode bot (paused 2026-10-24 02:00)

**Start here.** Then read `CONTRACTS.md` (binding interfaces and file ownership) and `agents/USER_REQUEST.md` (the
user's full specification, sections 1–11; it is the acceptance definition).

- ROOT = `C:\projects\cambridge battlecode\work\neural-full-stack`
- Local git repo, HEAD `9598703`, working tree clean. Commit with
  `git -c user.name=lead -c user.email=lead@local commit`. `core.autocrlf=false`.

## 1. Hard rules (from the user; never relax)
- **No training**, no fine-tuning, no long self-play. Only synthetic shape/gradient/parity/round-trip tests, and
  anything synthetic is labelled synthetic.
- **No submission/upload/activation** and no `cambc submit`/login. No browser or desktop control.
- Write only inside ROOT. The previous experiment (`work/neural-gameplay`), the archives and the CLI/SDK/maps are
  read-only. Never overwrite `references/**`.
- Official CLI only: `--release` at default fuel, never `--fuel`.
- Never present untrained heads as trained or as evidence of strength. All 40 local maps are *reused benchmarks*.
- Historical data: only 21 Oct 2026 onward. Engine 1.0.1 is excluded. 1.0.2 is draft-observational only.

## 2. Environment (verified)
| Item | Value |
|---|---|
| Paths | `config/paths.json` |
| CLI | cambc 3.0.5, engine 1.0.3, WASI clang 22.1 |
| Python | `$py = "C:\projects\cambridge battlecode\work\neural-gameplay\.venv\Scripts\python.exe"` (torch 2.11+cu128, numpy). **No pytest**: use unittest. Set `$env:PYTHONPATH="$PWD\python"` |
| Native C++ | g++ 16.2. Put `C:\msys64\ucrt64\bin` on PATH, or the obs-parity tests skip |
| Machine | RTX 5070 Ti Laptop 12 GB, 20 logical CPUs, 31 GB RAM |
| Build | `cambc build bot --release` from ROOT (has `cambc.toml`, `cmake/`, `sdk/`). Recursive `src/*.cpp` glob at -O3. **Keep sources flat in `bot/src/`** |
| References | `references/{original,v47,first-hour,v50}-src`, plus wasm and hashes in `references/builds/manifest.json` (original `eb0ea88f…`). Builds are byte-reproducible (`tools/build_references.py`) |
| Fuel | ≈100k per turn; first champion turn ≈182k; first draft turn 10x. Matches are deterministic per (wasmA, wasmB, map) |

PowerShell mangles inline Python/C++ that contains quotes. Use the file-edit tool or script files.

## 3. Verification commands (all pass at HEAD)
```
$py -m unittest discover -s tests/python -p "test_*.py"   # 186 tests OK
$py tools/run_cpp_tests.py                                # 11 targets, 451/451 checks
$py -m unittest tests.python.test_obs_parity -v           # C++ vs Python obs encode bit-exact
$py tools/lead_profile_check.py --profiles teacher_exact dev_untrained neutral_credit training --maps 2
$py tools/audit_equivalence.py compare --candidate X.wasm --label L --opponents original --maps 6 --out R.json
```

## 4. Task status
| # | Task | Status |
|---|---|---|
| 1 | Workspace, contracts, references, probes | done |
| 2 | Wave 1 agents A, B, C, G, H | done (reports in `agents/*/REPORT.md`; the lead wrote B's and C's after their sessions were cut off) |
| 3 | Integrate wave 1, teacher/neutral equivalence | done (section 5) |
| 4 | Wave 2: D strategy/draft/objective/role/value, E move/combat/engage/ward/ts_leaf, F bank/shop | **not started (NEXT)** |
| 5 | Integrate wave-2 hooks, build all profiles, parity tests | not started |
| 6 | Engine checks: plumbing, fuel profiling, smoke vs original/v47/first-hour | not started (only small smokes so far) |
| 7 | Wave 3 independent review (`agents/H/REVIEW_CHECKLIST.md`) | not started |
| 8 | Docs: ARCHITECTURE, DIAGNOSIS_AND_DESIGN, TRAINING_LATER, STATUS, agent record (EVALUATION_PROTOCOL exists) | not started |
| 9 | Package release ZIP+wasm, checksums, independent rebuild (`tools/package_release.py`, `tools/verify_release.py`) | not started |

## 5. What exists now
**C++ bot (`bot/src`)**
- The original sources, plus A's patches:
  - fuel routing: 38 decision fuel reads go through `nnb::teacher_left()`;
  - lab-strip, gated by `NN_STRIP_LAB`, off;
  - teacher captures: compile-time gated, `[[gnu::noinline]]`, wrapped in `nnb::CreditScope`.
- `main.cpp` hooks under `#if NN_ANY_HEAD`:
  - draft turn: `begin_turn`, `play_draft`, then `nnh::warmup`;
  - gameplay turn: `begin_turn`, `{CreditScope; turn_start}`, `play_turn`, `nnh::idle` (flushes NFS1 records from leftover fuel only).
- Runtime:
  - `nn_rt.h`: kernels and PRNG;
  - `nn_model.h`: model descriptor and checksums;
  - `nn_head.{h,cpp}`: `decide`, `value`, `leaf` and the fallback reasons;
  - `nn_budget.h`: admission, Meter, CreditScope, NFT1 telemetry;
  - `nn_log.h`: NFS1 records;
  - `nn_obs*.{h,cpp}` and `nn_schema.h`: the observation (kObsDim 563, hash 0xD341B69C);
  - `nn_teacher.{h,cpp}`: teacher capture access;
  - generated `nn_config.h`, `nn_registry.h`, `nn_weights_*.h`.
- The checked-in `nn_config.h` is profile **teacher_exact**, and the build is **byte-identical to the original wasm**.
- **No gameplay `nnh::decide()` call sites exist yet.** Only captures of the teacher's choices exist.

**Profiles and models**
- Profiles: `configs/profiles/{release,teacher_exact,neutral_credit,neutral_real,dev_untrained,training,selftest}.json`.
  Switch with `$py tools/install_models.py --profile P --src <scratch>/src`; that command is the single model-install switch.
- Every profile builds, and smoke games vs the original had 0 faults and 0 bot errors
  (`evaluation/results/lead_profile_check*.json`).
- The training profile emits about 75–80 NFS1 records per game.
- Models in `models/registry.json`, all synthetic and untrained:
  - `fs_v1_untrained`: zero residual;
  - `fs_v1_dev`: non-zero residual, plumbing only;
  - `draft_net_original`: the inherited trained draft network, used by the teacher and not re-exported.
  - Regenerate them with `$py -m nfs.models.untrained`.

**Python (`python/nfs`)**
- `engine.py`: official build/run, summary parsing, replay stdout, wasm sections.
- `models/`, `export.py`, `registry.py`, `records.py` (B).
- `obs.py`, `transforms.py`, `schema_gen.py` (C).
- `data/`, `train/` (rewards, imitation, value, PPO, league, checkpoint, collect) and `cli.py` / `tools/nfs.py` (G).
  Parameter-updating commands refuse to run without `--i-authorize-training` and a time limit.
- `evaluate/`: stats, gate, ledger, schedule, fuel, equivalence, wasm, release (H).

**Evaluation (H)**
- `EVALUATION_PROTOCOL.md` and `evaluation/protocol.json`, frozen with `protocol.lock.json` at 2026-10-23T23:29Z.
- Schedules in `evaluation/schedules/`, an empty hash-chained `evaluation/ledger.jsonl`, and reference baselines in
  `evaluation/results/reference/`.
- The gate is per-opponent with map-cluster bootstrap. A test reproduces the phase-2 "pooled up, original down → FAIL" case.

**Audit (A)**
- `agents/A/decision_inventory.json`: 59 decision points with exact hook points, teacher variables and fuel gating.
- `agents/A/sdk_facts.json`: SDK facts with line references.
- `agents/A/INVARIANTS.md`.
- Equivalence comparator `tools/audit_equivalence.py`; fixtures in `tests/fixtures/teacher/`.

## 6. Key findings (carry into DIAGNOSIS_AND_DESIGN.md)
1. **A neural-enabled build cannot be byte-equivalent to the original.** The original's decisions are chaotically
   sensitive to a few dozen fuel units spent before or while it decides. Spend after its decisions is harmless.
   Evidence: `evaluation/evidence/neutral_equivalence_bisect.json`.

   | Build | Identical cells |
   |---|---|
   | Original + ~40 fuel at turn start | 10/12 |
   | Original + 13.5k fuel at turn end (H) | 24/24 |
   | neutral_credit | 4/12 |
   | Runtime linked, idle, no credit | 11/12 |
   | The same plus only the credit arithmetic | 6/12 |

   Consequences:
   - teacher_exact is the only exact-equivalence claim;
   - every evaluation needs an **overhead-matched control arm** (neutral_real: the same binary, heads shadow/zero-residual), not just the original;
   - `kFuelCredit` is experimental and is not a neutrality proof;
   - neural work before teacher decisions must stay minimal, and logging runs after `play_turn`.
2. A debug (CAMBC_DEBUG) build diverges from release on 2/4 maps (`evaluation/evidence/debug-build-fuel-probe.json`), so
   `debug_block` cannot carry training logging at parity.
3. `A2_LAB=1` is not inert: tuned `A2_KNOBS` feed gameplay. Stripping the lab host code changed 20/24 cells (A's
   evidence), so `NN_STRIP_LAB` stays 0 in every profile.
4. Archived summaries contain no per-turn actions (G's `agents/G/DATA_AUDIT.md`). Only draft and coarse value labels come
   from archives; the other heads need instrumented teacher rollouts (NFS1).

## 7. Open problems (fix during steps 4–6)
1. `models/budget.json` is **provisional (coefficient model, not engine-measured)**. The lead raised turn_allowance to
   55000, because one K=16 decision plus the encoder is estimated at ≈30k of a ≈100k turn (encoder ≈12.9k, ≈919 per
   candidate). Write an engine fuel probe and probably shrink the default model in `configs/model/fs_v1.json`.
2. Add the neutral_real arm to H's schedules as a **recorded protocol amendment** (the protocol is frozen; use
   `tools/eval_protocol.py`).
3. NFT1 telemetry prints numeric head ids; map them to names. No NFT1 lines appear yet, because there are no decide() hooks.
4. `agents/{A,G,H}/CONTRACT_ISSUES.md` contain issues nobody has resolved.
5. No per-head schemas yet (`schemas/heads/*.json`), so every head uses the provisional F=24.
6. C still owes `agents/C/VISIBILITY.md` (per-feature legality audit), real RawTurn fixtures in `tests/fixtures/obs/`,
   and a team-intent encoding proposal within `shared_memory_bytes` (the existing 8-byte claim/sighting protocol must
   stay unchanged).

## 8. Next steps (in order)
1. **Fuel probe and budget.** Measure encoder, per-candidate and record costs in the engine. Rewrite `models/budget.json`
   and resize the default model if needed. Re-run `tools/run_cpp_tests.py` (the tests depend on the budget numbers).
2. **Wave 2 (D/E/F).** For each head in `schemas/heads.json`:
   - write a candidate builder in `bot/src/nn_{strategy,tactics,economy}.{h,cpp}` that fills `nnh::Decision`;
     candidate 0 is the teacher choice and always legal, legality stays deterministic, and features come after
     candidate narrowing;
   - add a schema in `schemas/heads/<name>.json` and a Python twin in `python/nfs/heads/`;
   - add a parity test;
   - add an `if constexpr`-gated hook at A's inventory hook point, next to the existing `cap_*` call. The draft goes at
     `cap_draft_pick(best)` in draft.cpp.

   Each new file must keep teacher_exact byte-identical. Agents can be launched with the `subagent` tool. Last session,
   the configured model claude-opus-5.5 was used for all workers.
3. Rebuild every profile and run `lead_profile_check.py`. Run H's plumbing, fuel and smoke schedules
   (`tools/eval_check.py`) for dev_untrained and neutral_real vs original, v47 and first-hour on both sides, labelled
   *untrained framework check*. Require 0 faults, 0 invalid actions and 0 NaN.
4. Wave 3: review against `agents/H/REVIEW_CHECKLIST.md`, then fix what it finds.
5. Docs:
   - `ARCHITECTURE.md`, with a coverage matrix: decision, observed state, candidates, head output, call site,
     fallback, fuel cost, model status, future labels;
   - `DIAGNOSIS_AND_DESIGN.md`: map the user's nine failure points to confirmed/suspected/ruled out and how each is
     addressed;
   - `TRAINING_LATER.md`: G's CLI commands labelled *not run*, a bounded first experiment and its stop criteria;
   - `STATUS.md`;
   - an agent assignment record.
6. Package with the release profile (untrained heads off): `tools/package_release.py`, then `tools/verify_release.py`
   with an independent rebuild. **Do not submit.**

## 9. Tool index (lead-written)
| Tool | Purpose |
|---|---|
| `tools/build_references.py` | Rebuild and verify the reference wasms |
| `tools/probe_debug_fuel.py` | Debug-vs-release probe |
| `tools/lead_profile_check.py` | Build profiles in `artifacts/tmp/profiles/<p>` and run smokes |
| `tools/lead_neutral_bisect.py` | Neutral bisection variants |
| `tools/lead_wrap_captures.py` | Idempotent noinline+CreditScope wrapper for `cap_*` |

Scratch work goes in `artifacts/tmp/` (gitignored). Engine stdout in bundles is NUL-padded; use `engine.team_stdout()`.
