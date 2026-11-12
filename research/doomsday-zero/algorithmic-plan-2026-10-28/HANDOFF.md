# HANDOFF: algorithmic DOOMSDAY plan (2026-10-28)

**Status: planning complete, awaiting user approval. No implementation is authorised.**

Nothing was coded, compiled, benchmarked, trained, submitted or activated in this planning session. No commit, push
or merge was made.

## 1. Where everything is

| File | Purpose |
|---|---|
| `FINAL_DEEP_ANALYSIS.md` | Evidence register E1–E28; combat authority trace; economy lifecycle; coordination; history of failures |
| `NEURAL_VS_ALGORITHMIC.md` | A (net) vs B (fallback) vs C (designed algorithm) for each learned or tuned component; verdicts |
| `STRATEGY_PORTFOLIO.md` | 12 ranked concepts (S1–S12) with 11 fields each, plus 2 rejected |
| `ARCHITECTURE_COMPARISON.md` | A simplify / B redesign / C clean slate; recommendation B; strongest alternative A+ |
| `ALGORITHMIC_BOT_BLUEPRINT.md` | The OCC architecture: control flow, ownership, state, interfaces, flags, hooks, failure countermeasures |
| `DRAFT_AND_ECONOMY_DESIGN.md` | TeamLedger, ObjModel, TEP, banking, shopping, opening schedule, deterministic draft |
| `COMBAT_AND_COORDINATION_DESIGN.md` | Engagement Evaluator, survival rules, crew protocol and shared-word layout |
| `COMPUTATIONAL_DESIGN.md` | Fuel budgets, governor tiers, complexity, memory, fallbacks |
| `VALIDATION_PLAN.md` | Methodology audit, gates G0–G7, experiments V-* |
| `14_DAY_ROADMAP.md` | Day-by-day plan to 2026-11-11; D7 decision point; freeze on Day 12 |
| `OPEN_QUESTIONS.md` | User decisions Q1–Q4, assumptions T1–T10, competing hypotheses, risks |

**Supporting research (kept):** `research/strategic-audit-2026-10-28/`
- `HANDOFF.md`: the earlier paused audit, with a pointer added
- `scripts/`: curves, headroom, concentration, fuel, init_carry, carry_compare, lomo_draft (new), early_divergence (new)
- `data/`: includes the new `lomo_draft.json`, `contest_proxy_base.json`, `early_divergence.txt`
- The superseded deliverable list of the first audit mission (EXECUTIVE_SUMMARY.md etc.) is replaced by this plan
  set. Its findings are folded into FINAL_DEEP_ANALYSIS.md.

**Runs used (already on disk; none launched in this planning session):**
- `artifacts/evaluations/v67/SA-*` (seed 71)
- v70 league runs: `g01-v69`, `f0*-d*`, `L-*`

## 2. Environment

- Checkout: `work/neural-full-stack`, branch `checkpoint/research-v85-2026-10-28` @ 8a62987.
  - The pre-existing modified `config/paths.json` and the untracked build logs, wasm and `compile_commands.json` are
    the user's. Do not touch, commit or delete them.
  - New untracked files from this work:
    - `research/algorithmic-plan-2026-10-28/`
    - `research/strategic-audit-2026-10-28/` (scripts, data, HANDOFF)
- Read-only worktree `work/deep-analysis-wt`, detached at `origin/analysis/deep-2026-10-28` 19da05a (moved from
  a68aa9f this session; the newer commit adds the puppet reproduction tools). It stays because the implementation
  phase needs its puppet tools and examined timelines.
  - Remove it after use: `git worktree remove ../deep-analysis-wt` from `work/neural-full-stack`.
  - Never read the 165 hands-off games for development.
- Python: `../neural-gameplay/.venv/Scripts/python.exe`. Run environment as in the audit HANDOFF.
- **Never call `ladder_duel.py run`** (it activates arms), and never submit, without the user's explicit, specific
  approval.

## 3. Recommendation in brief

- **Architecture B (OCC) as a strangler on v76**, in a new `bots/v86`.
  - Every OCC flag at 0 gives a byte-identical v76.
  - Core modules:
    - TeamLedger + ObjModel + TEP (contest-aware team economy)
    - EE (single, objective-aware combat authority)
    - crew protocol
  - Built model-first, with gates.
- **Fallback: v76s** = v76 + S7 recall-restart guard, ready by Day 2.
- **D7 (2026-11-04) decides:** continue B, keep one module, or ship A+.
- Last major architecture change on Day 8 (11-05); freeze on Day 12 (11-09).

## 4. First implementation milestone (after approval)

**M-1 (Day 1–2): scaffold and fallback.**
1. Create `bots/v86` as a copy of `bots/v76/src` with empty `occ_*` modules and flags (all 0). Prove Wasm SHA-256
   equality with v76 (G0).
2. Implement `OCC_FIX_RECALL` (S7). Run the frozen deep-analysis takeover diagnostic (TAKEOVER_PLAN.json, C004) under
   its own decision rule. Then run the 5-opponent league non-inferiority check on seeds 101–102. This yields **v76s**.
3. Start the offline analyses: V-S9 knob LOMO, V-S5 / V-S12 death analyses, V-M1 data extraction; and the V-C0
   ablation (APEX_TS_DECIDE=0).

Done when G0 passes, v76s is packaged (not submitted) with a release record, and the offline analyses have results
files.

## 5. Rules the implementation agent must follow

- Frozen bots (`bots/v76`, earlier) and historical records are never edited. New work goes in `bots/v86`,
  `research/v86/`.
- Seed ledger: development 101–110, validation 111–120, final 121–124. Seeds 3 and 4 are reserved; do not reuse
  1–22, 24, 41, 42 or 71.
- Hold out every 5th map of the sorted 70-map pool for new-module tuning.
- A module that fails its offline model gate or its idle gate stops. Do not tune constants to rescue it (the v82
  rule).
- No logging in release builds. Trace builds never support strength or fuel-out claims.
- Report every result, including failures, in `research/v86/RESULTS.md`.
- Commits only on an authorised working branch and only with the user's approval. Never push, merge or force
  anything.

## 6. Biggest open items

- **Q1** (pool vs new maps at finals) and **Q2** (ladder duel approval) change the plan materially. Ask the user
  first.
- **T2 / T3**: whether the analytic combat model and ObjModel are accurate enough. Answered offline in the first 3–4
  days.

## Superseded (later on 2026-10-28)

This plan set is superseded by `research/master-plan-2026-10-28/` (start with its `HANDOFF.md`). The evidence register
E1–E28 here remains valid and is cited there. Corrections in the new package:
- the opening gap against the strongest teams is larger than "contest only"
- the deep analysis's 165-game holdout is spent
- the gear planner and cluster circuits are core
