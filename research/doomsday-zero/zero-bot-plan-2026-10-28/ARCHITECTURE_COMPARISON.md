# Architecture comparison for a clean-slate bot

The user directed a fresh bot with no previous-bot code. The question here is therefore **which clean-slate
architecture**, compared also against the status quo (keeping the live bot for the finals).

| ID | Architecture | Essence |
|---|---|---|
| Z-A | Lean deterministic specialist | SafeMode extended with hand-written rules per situation (flee, farm, bank thresholds). No planner, no evaluator |
| **Z-B** | **Hierarchical algorithmic planner (DZ)** | Kernel + knowledge + coordination + strategy (auction economy, bank rule, gear, race) + tactics (EE stance portfolio + action scorer), on one GE value scale |
| Z-C | Search-assisted | Z-B plus bounded rollout search (playouts of stance portfolios) at high-impact moments |
| Z-D | Offline-optimised tables | Runtime is a thin rule engine reading large league-optimised tables (per-map openings, thresholds, lineups) |
| Z-E | Adaptive opponent-aware | Z-B or Z-A plus online style classification selecting parameter sets |
| SQ | Status quo | Keep the current live bot (v74/v75 lineage) for the finals |

| Criterion | Z-A | Z-B | Z-C | Z-D | Z-E | SQ |
|---|---|---|---|---|---|---|
| Strength ceiling | Low–medium | **Medium–high** | Higher in theory | Medium on known maps, low on unseen maps | Small increment | Known: 21–30/120 vs top 12 |
| Two-week feasibility | High | **Medium** (staged, with gates) | Low | Medium (needs a working runtime first) | Add-on | Already done |
| Fuel risk | Low | Medium (governor tiers) | **High** (playouts; past search had 16 fuel-outs/game) | Low | Low | Known |
| Coherence | Low (rule interactions, as in v76's override stack) | **High** (single owners, one value) | High | Medium | — | Low |
| Generalisation | Poor | Good (rule-derived models) | Good if the model is accurate | **Poor** (per-map tables don't generalise: +17 vs an oracle +134) | Neutral | Poor |
| Debuggability | Medium | Good (logged stance and rate values) | Medium | Poor | Medium | Poor |
| Evidence for | — | Literature on Lanchester prediction, portfolio stances, auctions [B10–B18]; the measured gap structure | PGS beats alpha-beta and UCT when the model is accurate [B12] | v70/v71 tables transferred to the ladder | — | — |
| Evidence against | v76-style rule stacks failed to fix the gap | Clean slates lost historically (mimic, GPT controllers), though those were imitation or learned designs | tsearch −366; v81 −532 | Diminishing returns (v73→v74) | Little data | Gap persists |

## Recommendation

**Z-B (DOOMSDAY Zero) as the runtime, D as the tuning process, and E as a gated add-on**:
- Z-D's useful part, league-selected per-map rows and scalars, is applied to DZ's parameters on Day 10. It is not a
  separate runtime.
- Z-E's style switch selects among at most 3 parameter sets, behind `DZ_STYLE`, only if it passes its gate.
- Z-C is not adopted. Its useful idea, evaluating a portfolio of scripted stances, is kept with an analytic evaluator
  (19–145× faster than simulation [B11]).

**Why Z-B over Z-A.** Z-A is what v76 became: a growing stack of situational rules whose interactions produced the
measured failures. Z-B costs about 2 more days, and it is the only option that integrates economy and combat on one
value scale.

## The status quo remains the fallback

The plan's decision points (D7, D9) explicitly fall back to the live bot if DZ misses parity. This is the user's
safety net, and no DZ code depends on it.
