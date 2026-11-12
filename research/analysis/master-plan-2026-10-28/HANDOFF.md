# HANDOFF: DOOMSDAY master architecture package (2026-10-28)

**Status: research and planning complete. Awaiting user approval. No implementation is authorised.**

This session did not code, compile, benchmark, train, submit, activate, commit, push or merge anything. The only
computation was offline analysis of saved data:
- paired comparisons of existing runs
- leave-one-map-out draft analysis on saved league runs
- timeline and profile tables from the deep analysis's examined set
- gem-receipt events from saved idle runs (Prospector inference)

## 1. Read in this order

1. `EXECUTIVE_RECOMMENDATION.md`: the decision, alternatives, risks, open user decisions Q1–Q4, design review
2. `MASTER_ARCHITECTURE.md`: the standalone system design
3. `ALGORITHM_SPECIFICATIONS.md`: formulas, pseudocode, defaults
4. `DATA_STRUCTURES_AND_INTERFACES.md`: modules, structs, contracts, shared-word protocol
5. `FUEL_AND_PERFORMANCE.md`: budgets, governor, caching
6. `IMPLEMENTATION_PLAN.md`: tasks T0–T19, hooks H1–H10, structure
7. `VALIDATION_PLAN.md`: gates G0–G8 and experiments V-*
8. `FINALS_ROADMAP.md`: milestones MS0–MS14 and decision point D7
9. Background:
   - `GAME_MECHANICS_AND_WIN_CONDITIONS.md`
   - `TOP_TEAM_REVERSE_ENGINEERING.md`
   - `CURRENT_BOT_AUDIT.md`
   - `STRATEGY_PORTFOLIO.md`
   - `ARCHITECTURE_COMPARISON.md`
   - `SCENARIOS_AND_FAILURE_MODES.md`
   - `EXTERNAL_RESEARCH.md`
   - `RESEARCH_BIBLIOGRAPHY.md`

**Superseded:** `research/algorithmic-plan-2026-10-28/`, the previous plan. Its evidence register E1–E28 is still
cited and still valid. Corrections:
- the opening gap against the strongest teams is larger than "contest only"
- the holdout is spent
- items are now core

**Supporting scripts and data:** `research/strategic-audit-2026-10-28/` (`scripts/` and `data/`), including
`lomo_draft.py` and `early_divergence.py`.

## 2. New facts established in this session

- **The deep analysis finished** (origin/analysis/deep-2026-10-28 @ 19109c4).
  - M1 recall fix confirmed by a warm puppet test, with the regression at `tests/loss_cases/M1-recall-disabled-bank.json`.
  - Its 165 reserved games are now **spent**. Use the once-only release holdout in VALIDATION_PLAN §2.
- **The engine differs from GameRules.md:**
  - Treasure gives +10% gold, Monster +15% camp damage.
  - Several champion stats differ (e.g. Vesper base strength 45, Willow focus 140, Tavi stun 1.6×F, Ren stun 1.1×F).
  - Seven more emblem families exist.
  - Always read engine metadata at runtime.
- **Prospector** gives +25% gems from gem clusters, floored, inferred from 9,196 SA-IDLE-v76 capture events. Wolf and
  elk receipts are unchanged.
- **The Capture emblem makes capture 3 rounds** (v76's assumption, confirm with ENG-3). v76 computes
  `prospector_bonus` and `tribute_bonus` but never uses them.
- **The opening gap against the strongest opponent is large.** Intercontinental Fish: R100 gold 483 vs our 278;
  R250 1444 vs 739; deaths 5.5 vs 14.9; conversion 88% vs 56%.
- **Perma-recall** (Mite, newer team, print dont int) shows up as about 4,300 channel rounds per game. Its purpose is
  unknown. v76 gives recalling enemies a +0.5 target-worth bonus, which may be exploitable.
- **The official Cambridge site** is JS-only to a fetcher, and there is no public top-team source.

## 3. Environment and housekeeping

- **Checkout:** `work/neural-full-stack`, branch `checkpoint/research-v85-2026-10-28` @ 8a62987.
  - The user's modified `config/paths.json` and untracked build artefacts are untouched.
  - Untracked research folders from this work:
    - `research/master-plan-2026-10-28/`
    - `research/algorithmic-plan-2026-10-28/`
    - `research/strategic-audit-2026-10-28/`
- **Read-only worktree** `work/deep-analysis-wt`, detached at 19109c4. It is needed for the puppet tools,
  `tests/loss_cases` and the examined timelines. Remove it after use with `git worktree remove ../deep-analysis-wt`.
- **Python:** `../neural-gameplay/.venv/Scripts/python.exe`. `pdftotext` (mingw) is available for papers.
- **Never** run `ladder_duel.py run`, submit, or change the live version without explicit, specific user approval.
- **Never** edit `bots/v76` or earlier bots, or historical results.

## 4. First steps after approval (Day 1, 2026-10-29)

1. **T0.** Create `bots/v86` = copy of `bots/v76/src`, with `occ_config.h` and all flags 0. Build, and compare the
   Wasm SHA-256 with v76 (G0).
2. **T1.** Implement `OCC_FIX_RECALL` (and `OCC_FIX_TARGET`). Port the deep analysis's M1 warm case. The baseline must
   fail and the candidate pass.
3. **Before any game,** write `research/v86/HOLDOUT.md` (seeds 121–124 × 70 maps × 2 sides × 5 opponents, run once,
   with the list hash) and `research/v86/SEED_LEDGER.md`.
4. **Parallel offline work:**
   - T2: ObjModel extraction and V-M1
   - T3: EE dataset and V-M2
   - T4: S9 knob LOMO, death analyses, λ_gold regression
5. **Ask the user** Q1 (finals maps) and Q2 (ladder duel approval) at the start: they change priorities.

## 5. Rules for the implementation agent

- Change one mechanism per experiment. Gates come before broad benchmarks: offline, then idle, then contested, then
  holdout, then ladder.
- **A module that fails its gate stops.** No constant-tuning rescues (the v82 rule).
- No logging in release builds. Trace builds never support strength or fuel claims.
- Seeds 101–124 only, as ledgered. Seeds 3 and 4 are reserved. 14 held-out maps.
- Report every result, including failures, in `research/v86/RESULTS.md`.
- Commits only on an authorised branch, with user approval. No push or merge without approval.

## Superseded (later on 2026-10-28)

At the user's instruction ("a fresh bot not relying on previous bot version code at all"), this on-v76 plan is
superseded by `research/zero-bot-plan-2026-10-28/` (DOOMSDAY Zero). Start with its `HANDOFF.md`. The research findings
here remain valid inputs.
