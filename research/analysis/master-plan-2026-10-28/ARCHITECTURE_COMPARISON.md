# Architecture comparison and recommendation

## The six complete candidates

| ID | Architecture | Essence |
|---|---|---|
| **A** | Lean deterministic specialist (clean slate) | A new compact controller: own world model, utility arbiter, executors. Only SDK wrappers are reused. |
| **B** | Hierarchical algorithmic planner on v76 infrastructure ("OCC") | Strategic (TEP, race), coordination (claims and typed beacon) and tactical (EE plus executors) layers with explicit ownership. v76's engine-facing code and executors are kept; flags make it byte-identical to v76 when off. |
| **C** | Search-assisted | B plus bounded rollout search (short playouts of stance portfolios) at high-impact moments: contested captures, big-bag fights. |
| **D** | Offline-optimised strategy engine | Offline optimisation produces tables: per-map lineups, opening schedules, knob profiles, item builds, stance thresholds. The runtime is v76 or B reading those tables. |
| **E** | Adaptive opponent-aware | B or v76 plus online style classification switching among parameter sets. |
| **F** | Incremental v76 ("A+") | v76 plus bug fixes (M1), a gear-planner patch, robust targeting and league re-selection. No new decision core. |

## Comparison

| Criterion | A clean slate | B OCC | C search-assisted | D offline tables | E adaptive | F incremental |
|---|---|---|---|---|---|---|
| Expected strength (prior) | High ceiling, low floor | **Medium-high** | B plus a small increment, with risk | Medium (proven, diminishing: v73→v74 +7..+13) | Small increment | Low-medium |
| Strategic coherence | High | **High** (one GE scale) | High | Unchanged core | Unchanged core | Low (stacked overrides) |
| Compute cost | Low–medium | Medium (≤48k mean) | **High**: playouts exceeded the budget before (16 fuel-outs per game) | Zero at runtime | Negligible | As v76 |
| Implementation complexity | Very high | High but modular | Very high | Low–medium (offline) | Low | Low |
| Two-week suitability | No (parity alone exceeds 14 days) | **Yes, with gates and fallback** | No (only after B) | Yes, as a process | Yes, as an add-on | Yes |
| Failure risk | Very high (mimic 0/120, GPT 0–32/240) | Medium (isolated by flags) | High (fuel, model accuracy [B12]) | Low (overfitting controlled by held-outs) | Medium (misclassification) | Low |
| Generalisation to unseen maps | Good if models are good | Good (rule-derived models) | Good | **Poor** (E6: per-map tables don't generalise) | Neutral | Poor |
| Interpretability | Good | Good (logged stance and rate values) | Medium | Medium | Medium | Poor |
| Extensibility | Good | Good | Medium | Good | Good | Poor |
| Fit with proven infrastructure | Poor | **Excellent** | Good | Excellent | Excellent | Excellent |
| Operation under the fuel limit | Good | Good (governor tiers) | Poor | Excellent | Excellent | As v76 |
| Supporting evidence | Little; base rates negative | Mechanism and gap evidence (E9–E15, opponents' profiles); literature [B10–B18] | Literature with an accurate model only; tsearch evidence negative | E21 transfer | Low | M1 trace; item package +136 |

## Recommendation: B as the runtime, D as the tuning process, E only as a gated add-on

How the components interact. There is one overarching decision system, the B hierarchy in MASTER_ARCHITECTURE.md.
D and E never act at runtime as separate deciders:

1. **B owns every runtime decision.**
   - TEP: objectives, crews, roles, BANK, SHOP.
   - EE: every turn with a threat present.
   - Race controller: TEAM_MODE.
   - Executors: actions.
2. **D supplies B's constants**, selected offline with the league protocol:
   - λ calibrations
   - EE scalars (π, m_commit, hidden weight, …)
   - TEP scalars (γ, hysteresis, contract length)
   - per-map lineup table, opening priors, gear-planner priors

   B reads them from compiled tables. On unseen maps it uses general defaults, or a kNN profile only if held-out
   validation is positive.
3. **E (style detection) selects one of at most three D-provided parameter sets at R100.**
   - Off by default. Enabled only if it passes its own gate.
   - It never introduces new decision code paths.
4. **C (rollout search) is rejected for the runtime.** Its useful idea, evaluating a *portfolio of scripted stances*
   [B12], is kept in EE with an analytic evaluator instead of playouts (the speed argument of [B11]).
5. **F's items are folded into B's Day 1–2 track** (M1 fix, robust targeting, gear-planner patch). With all OCC flags
   off they form the fallback candidate "v76s".

## Why not A (clean slate)

- **The opponent gap is at the decision level, not the infrastructure level.** v76's executors, world update and
  pathing are proven. Rewriting them costs parity time with no evidence of gain.
- **Base rates:** every whole-controller replacement has failed (mimic 0/120, GPT controllers 0–32/240), and every
  partial replacement v81–v85 lost.
- B provides the same coherence benefits where they matter.

## Why not F only

- F does not change the decision structure that produces the deaths, retention and opening gaps against top teams
  (CURRENT_BOT_AUDIT §5).
- Its expected gain is small, and v73→v74 per-map gains were already diminishing (+7..+13).
- It is the right **fallback**, not the strategy.

## Strongest alternative and when to switch

**F + D ("v76s plus re-selected tables").**

Switch at decision point D7 (FINALS_ROADMAP.md) if either holds:
- neither TEP nor EE passes its mechanism and scenario gates by 2026-11-04; or
- ladder duels are not approved and B's gains are only in combat (unverifiable locally).

In that case ship F + D. It is low-risk, uses the only demonstrated transfer mechanism, and includes the confirmed
bug fix.
