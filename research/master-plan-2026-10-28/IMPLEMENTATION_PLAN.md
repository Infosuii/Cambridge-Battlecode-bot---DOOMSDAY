# Implementation plan (engineering tasks, dependencies, migration)

**Not authorised yet.** This plan starts only after the user approves it.

## 1. Choice of approach and rationale

The approach is **(2): replace strategic decision-making while keeping tested execution** (Architecture B on v76
infrastructure, ARCHITECTURE_COMPARISON.md).

Rationale:
- The measured gaps are decision-level: deaths and commitment, contest retention, opening and gear, banking.
- v76's execution layer is proven and costly to reproduce.
- Every past whole-controller rewrite lost, and every past layered addition lost. Replacement *behind flags with
  byte-identical controls* is the remaining path with a reliable fallback.

## 2. Project structure

```
bots/v86/src/            copy of bots/v76/src (frozen v76 never edited)
  occ_config.h           flags (all 0 = v76), default scalars, per-map rows, parameter sets
  occ_gov.h              M8 governor
  occ_ledger.{h,cpp}     M1 TeamLedger + EnemyBelief
  occ_proto.{h,cpp}      M5 shared-word codec (claims unchanged + typed beacon)
  occ_race.{h,cpp}       M10 race controller / TEAM_MODE
  occ_model.{h,cpp}      M2 ObjModel (pure functions)
  occ_tep.{h,cpp}        M3 Team Economy Planner
  occ_ee.{h,cpp}         M4 Engagement Evaluator (pure evaluate + glue)
  occ_gear.{h,cpp}       M6 gear planner
  occ_open.{h,cpp}       M9 opening schedule (draft side)
  occ_draft.{h,cpp}      M7 optional draft optimiser
  occ_micro.{h,cpp}      M11 optional micro scorer
  occ_trace.h            trace macros (OCC_TRACE only)
research/v86/
  RESULTS.md SEED_LEDGER.md HOLDOUT.md   results, seeds, once-only holdout record
  offline/                               Python ports and validation scripts (objmodel_check.py, ee_calibrate.py, lomo_knobs.py)
tests/v86/
  host/                                  native unit tests of pure cores (CMake, no engine)
  loss_cases/                            puppet warm-state cases (from deep analysis tests/loss_cases)
```

## 3. Hooks into v86 `bot.cpp`

Each hook is guarded by `#if OCC_*`, and its `#else` branch is the v76 line, unchanged.

| Hook | Location (v76 line numbers) | Purpose |
|---|---|---|
| H1 | `play_turn` start (≈6582) | `gov.start_turn()`, `ledger.sync()`, `race.update()` |
| H2 | Recall-cancel branch (≈7005) | M1 fix: cancel a winning-bag recall only if `!w.no_bank && round >= tribute_off_until` |
| H3 | Target worth (≈3236) | Robust targeting: the recalling bonus only if the channel age is ≥ 2 |
| H4 | `handle_enemies` entry (3162) | EE: stage 1 shadow, stage 2 verdict mapping, stage ≥3 owns the turn |
| H5 | `score_groups` entry (≈5420; pattern of `V58_DIRECTOR economy_assignment`) | Return TEP's assignment |
| H6 | `farm()` capture branch | Single-capturer leave rule from TEP roles |
| H7 | `tribute_if_needed` / `go_home_if_needed` | BANK hazard rule (OCC_TEP ≥ 3) |
| H8 | Shopping (`build_for` callers) | Gear planner (OCC_GEAR) |
| H9 | Claim and beacon writes (bot.cpp:545–640, 7190–7208) | Typed beacon codec (OCC_CREW) |
| H10 | `play_draft` (draft.cpp ≈805) | Opening schedule and optional optimiser |

## 4. Task list with dependencies

| ID | Task | Depends on | Effort | Parallel? |
|---|---|---|---|---|
| T0 | Create `bots/v86`, flag scaffold, prove byte identity (G0) | — | 0.5 d | — |
| T1 | M1 recall fix (H2) and robust targeting (H3); puppet case M1 (baseline fail, candidate pass) | T0 | 0.5 d | with T2–T4 |
| T2 | Offline: ObjModel Python port, extraction of clear/arrival/damage from SA-IDLE-v76, V-M1 report | — | 1 d | yes |
| T3 | Offline: EE Python port and contact dataset (local + examined ladder), V-M2 calibration | — | 1.5 d | yes |
| T4 | Offline: V-S9 knob LOMO, V-S5/S12 death analyses, λ_gold regression | — | 0.5 d | yes |
| T5 | Governor (M8) and trace plumbing | T0 | 0.5 d | |
| T6 | Ledger (M1) and protocol codec (M5, claims-compatible) with host unit tests | T0 | 1 d | |
| T7 | ObjModel C++ (pure) matching the Python port to within 1e-3 on fixtures | T2 | 0.5 d | |
| T8 | TEP shadow (OCC_TEP=1): assignments computed and logged, behaviour v76 | T6, T7 | 1 d | |
| T9 | TEP owns farming (OCC_TEP=2), plus CLUSTER_RUN and single capturer | T8 | 1 d | |
| T10 | BANK hazard rule, altar choice, locks (OCC_TEP=3) and race controller (M10) | T9 | 1 d | |
| T11 | EE C++ pure evaluate matching the Python port; shadow (OCC_EE=1) | T3, T6 | 1 d | with T8–T9 |
| T12 | EE stage 2: verdict mapping | T11 | 0.5 d | |
| T13 | EE stage 3: stances, HOLD/AMBUSH, free-action rule | T12 | 1 d | |
| T14 | Crew stance (OCC_EE=4, OCC_CREW=1) | T13, T6 | 1 d | |
| T15 | Gear planner (OCC_GEAR) | T7, T9 | 1 d | with T13 |
| T16 | Opening schedule (OCC_OPEN), optional | T9 | 1 d | |
| T17 | 2–3 scripted style opponents for evaluation (rusher, perma-recall turtle, cluster farmer) as v76 flag variants under `artifacts/tmp` (evaluation-only bots) | T0 | 1 d | yes |
| T18 | League re-tune (V-T1) of OCC scalars and lineup re-selection | final module set | 1.5 d | |
| T19 | Release hardening: fuel gates, fault checks, release record, fallback package v76s | all | 1 d | |

**Shortest path to a functional algorithmic prototype:**
T0 → T5 → T6 → (T2 → T7) → T8 → T9, plus (T3 → T11 → T12).

The result is "OCC-min" = TEP stage 2 + EE stage 2 + M1 fix, about Day 6.

**Can be deferred without undermining the core:** T14 crew, T15 gear, T16 opening, T17 style opponents (but needed
for confidence), M11 micro, M7 draft optimiser, style adaptation.

## 5. Initialisation and turn order

See MASTER_ARCHITECTURE.md §3: draft turns, then the first play turn (metadata, draft memory, fields, ledger init),
then every turn (governor → world → ledger → race → channel guard → EE/TEP → executors → gear → publish).

## 6. Error handling and configuration

- Exceptions are caught at every OCC entry, which falls back to the v76 path for that turn. A module disables itself
  after 3 errors.
- Configuration is compile-time only (`occ_config.h`): default scalars, per-map rows, 3 parameter sets.

## 7. Offline precomputation (implementation phase)

- ObjModel κ per camp type; λ_gold coefficient `a`; EE scalars (≤8); TEP scalars (γ, hysteresis, contract length,
  M).
- Lineup table re-selection; optional kNN profile table for unseen maps (only if LOMO > 0).
- All fitted on training maps and seeds only (VALIDATION_PLAN.md §2).

## 8. Build integration

- Official CLI only: `cambc build --release` through `python/nfs/engine.py`, `research/v81/run_experiment.py`.
- Flag variants via `tools/v67/c_variant.py --set FLAG=VAL`.
- Each candidate records its source tree hash, flags, Wasm SHA-256, CLI, SDK and engine identity (`run_experiment.py`
  provenance).

## 9. Migration and rollback

- Every stage is a flag value. Rolling back means setting the flag to 0. The frozen v76 and the v76s fallback stay
  untouched.
- No change to `bots/v76`, earlier bots, historical results, or the live platform version without the user's
  approval.
