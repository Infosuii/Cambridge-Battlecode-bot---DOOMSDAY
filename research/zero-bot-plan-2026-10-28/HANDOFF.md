# HANDOFF: DOOMSDAY Zero clean-slate plan (2026-10-28)

**Status: planning complete, awaiting user approval. Do not implement before approval.**

This package **supersedes** `research/master-plan-2026-10-28/` (the redesign on v76) at the user's instruction:
"a fresh bot not relying on previous bot version code at all". Older packages are kept as history.

## Read in this order

1. `EXECUTIVE_RECOMMENDATION.md`
2. `GAME_MECHANICS_AND_WIN_CONDITIONS.md`: the complete reference, with verification status
3. `SDK_AND_ENGINE_INTERFACE.md`
4. `ENGINE_CONFORMANCE_SUITE.md`
5. `VARIABLE_COVERAGE_MATRIX.md`
6. `MASTER_ARCHITECTURE.md`
7. `ALGORITHM_SPECIFICATIONS.md`
8. `DATA_STRUCTURES_AND_INTERFACES.md`
9. `FUEL_AND_PERFORMANCE.md`
10. `IMPLEMENTATION_PLAN.md`
11. `VALIDATION_PLAN.md`
12. `FINALS_ROADMAP.md`
13. `OPEN_QUESTIONS_AND_RISKS.md`
14. Background, carried forward with notes:
    - `TOP_TEAM_REVERSE_ENGINEERING.md`
    - `STRATEGY_PORTFOLIO.md`
    - `ARCHITECTURE_COMPARISON.md` (rewritten for the clean slate)
    - `SCENARIOS_AND_FAILURE_MODES.md`
    - `EXTERNAL_RESEARCH.md`
    - `RESEARCH_BIBLIOGRAPHY.md`
    - `LESSONS_FROM_PREVIOUS_BOTS.md`

## Facts established in this planning session (no games run)

| Fact | Method |
|---|---|
| Fuel budgets: draft turn 1 = 10,000,000; later draft turns 100k; first play turn 200k; then 100k | Budget words of saved `.fuel` traces |
| Treasure +10% on all gold, kills included; Vesper +33%; Vesper + Treasure +43% | `earnedGold` step sizes in SA-P-base (proxy buys Treasure): `research/strategic-audit-2026-10-28/scripts/engine_facts_check.py` → `data/engine_facts_check.txt` |
| Capture emblem gives capture time 3 | Last-kill-to-reward delay: mode 6–7 → 4–5 rounds, 6,000+ captures (same script) |
| Damaged camps don't regenerate while unattended | 1,846 round-pairs from 6 decoded replays, 0 increases: `scripts/camp_regen_check.mjs` |
| Prospector gives +25% gem-cluster gems | `scripts/prospector_check.py` |
| SDK inventory: 154 imports; visibility, error codes, prediction APIs (`damage_amount(target)`), engine pathing (`move_towards`, distance fields, BFS, shadowcast) | `sdk/cpp/cambc.h`, `imports.h` |
| Execution model: persistent `main()` per instance; a fuel-out resumes mid-code; `debug_block` is free only in debug builds | SDK header and tests |
| cambc release cadence of 3–5 days; source private | PyPI; GitHub 404 |
| Deep-analysis study complete; its 165-game reserved set is spent | branch @ 19109c4 |

## Environment

- **Checkout:** `work/neural-full-stack`, branch `checkpoint/research-v85-2026-10-28`.
  - The user's `config/paths.json` and untracked artefacts are untouched.
  - Untracked research folders:
    - `research/zero-bot-plan-2026-10-28/`
    - `research/master-plan-2026-10-28/`
    - `research/algorithmic-plan-2026-10-28/`
    - `research/strategic-audit-2026-10-28/`
- **Deep-analysis worktree:** `work/deep-analysis-wt`, detached at 19109c4, read-only. Remove it after use with
  `git worktree remove ../deep-analysis-wt`.
- **Replay decoding:** set `NFS_REPLAY_ENGINE=2.0.0`, and extract `replay.repl26a` from the bundle zip before
  decoding.
- **Python:** `../neural-gameplay/.venv/Scripts/python.exe`. `pdftotext` is available.

## First steps after approval (Day 1)

1. **Ask the user Q1–Q5** (OPEN_QUESTIONS_AND_RISKS §A).
2. **Before any experiment,** write `research/dz/HOLDOUT.md` (seeds 121–124, once-only) and
   `research/dz/SEED_LEDGER.md`.
3. **Z0:** build the conformance diagnostics under `artifacts/tmp/dz-conformance/` and run CT-1..27. Record the
   results in `research/dz/CONFORMANCE.md`.
4. **Z1:** the DZ kernel in `bots/dz/src`. No code may be copied from `bots/*` or `references/*`.
5. **Parallel offline work:** ObjModel replay extraction (V-M1), the EE contact dataset (V-M2), the λ_gold
   regression.

## Rules

- **No previous-bot code in DZ.** Evaluation tools may be used.
- **One mechanism per experiment.** The gate order is offline, then idle, then contested, then holdout, then ladder.
- **A failed gate stops a module.** No constant-tuning rescues.
- **No logging in release builds.**
- **Never** submit, activate or run ladder duels (`ladder_duel.py run` activates) without explicit user approval.
- **Never** edit frozen bots or historical results.
- Commit only with approval; never push or merge without approval.
