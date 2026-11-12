# Open questions, competing hypotheses and risks

E-numbers refer to FINAL_DEEP_ANALYSIS.md. Each question names the experiment that answers it (VALIDATION_PLAN.md),
or who must answer it.

## A. Questions only the user can answer

| # | Question | Why it matters |
|---|---|---|
| Q1 | **Are the finals played on the current 70-map pool, or on new maps?** | On the pool, the per-map tables (V70 draft, V71 knobs) are worth ~100–200 gems in-sample (E4) and transferred to the ladder (E21), which favours A+. On unseen maps they do not generalise from coarse features (E6), which favours B's rule-based models and makes S8/S9 matter. |
| Q2 | **Will ladder duels be approved during development?** They activate arms (`ladder_duel.py run`). | Without them, B's combat changes cannot be judged on the target population (E16). The roadmap then ships OCC only on economic and league evidence, or ships A+. |
| Q3 | Which version is live now, and should the finals candidate be compared against it or against v76? | Deep analysis: platform 69 = v75, activation not re-verified. v81 RESEARCH: platform 68 = v74 live at that time. Baseline arms must be same-day. |
| Q4 | What risk appetite is acceptable for the final submission (A+ vs OCC at equal local evidence)? | Decides the Day-12 freeze when results are ambiguous. |

## B. Unresolved technical assumptions

| # | Assumption | Status | Resolved by |
|---|---|---|---|
| T1 | Contest retention, not uncontested farming, is the main lever. | Supported by same-map comparisons (E10, E13); confounded by draft and loss-conditioning | V-E2 retention metric; ladder duel |
| T2 | An analytic 4-round exchange model predicts deaths better than v76's stacked verdict. | Untested | V-M2 (offline, no games) |
| T3 | ObjModel's travel and clear predictions are accurate enough for team assignment. | Untested; v82 failed here | V-M1 |
| T4 | Team assignment via sequential claims (no leader broadcast) is good enough given unshared vision. | Hypothesis | V-E1 disagreement logs; V-E2 |
| T5 | λ_gold (gold → gem-equivalents) is about v76's effective gold weight. | Assumed for parity; real value is unknown | V-T1 re-tune |
| T6 | λ_tempo ≈ 1 (a death costs 60 rounds of the unit's farming rate). | Assumed | V-M2 fit, V-T1 |
| T7 | The puppet horizon (≤10 rounds) is long enough to see the immediate effect of stance changes. | Plausible; enemies are non-reactive | V-C1 caveats |
| T8 | Crew stance via the beacon is fresh enough (the leader acts first via `set_priority`). | Rule says priority changes apply next round | V-C3 unit test of turn order |
| T9 | `tactical_decide` contributes positively in v76. | Unmeasured (it is active) | V-C0 |
| T10 | Gains measured against our lineage will hold against top teams for **economic** changes, as per-map work did (E21). | Partly supported | Ladder duel |

## C. Competing hypotheses

1. **"We lose fights" vs "we lose economy, and fights follow."**
   - Ladder losses show the snowball both ways: kill gold, equipment and dead time all reverse in wins (E11–E12).
   - Discriminator: the R100–R250 window. If our deficit at R100 is gold without deaths (E8: 283 vs 381 at R100),
     the economy leads. If deaths come before the gold gap, fights lead.
   - **Partly answered offline in this session (E28).** At R100 in losses, 36% trail in capture gold with no extra
     dead time (wins 20%), and 34% have extra dead time (wins 19%). Both channels diverge by R100 at similar rates.
     Neither hypothesis is sufficient alone, which is why the design keeps both TEP and EE.
   - Still open: within-game ordering at finer resolution (R25 steps), which needs the per-round native traces rather
     than the 4-point curves.
2. **"Top teams' opening is better" vs "top teams contest us earlier."**
   - Their contested R100 381 exceeds our uncontested 329 (E8, E24).
   - Discriminator: their R100 income in top-v-top games (25 reference games in the examined set) vs in games against
     us.
3. **Campnet's value comes from commitment, not learning.**
   - If so, TEP's hysteresis replaces it.
   - Discriminator: a v76 build with campnet replaced by "commit to the base pick for 40 rounds". A one-flag
     experiment, cheap, but it adds work to v76: optional.
4. **Perma-recall (E19) is an exploit of opponents' heuristics** (e.g. "recalling" enemies are discounted or ignored)
   rather than noise.
   - v76 gives recalling enemies worth +0.5.
   - Discriminator: in ladder replays, do champions that keep recalling get chased less, or do they bait?
   - Relevant to EE's target valuation.

## D. Risks before finals

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| OCC modules fail gates and time runs out | Medium-high (base rate E17) | Medium | D7 decision point; v76s fallback ready on Day 2 |
| Local gains don't transfer to the ladder | Medium (E16) | High | Prefer economic metrics; puppets; ask for a duel early (Day 11) |
| Fuel regressions at the tail (p99) | Medium | High (fuel-outs are lethal) | Governor tiers, G2 on every build, fallbacks |
| Over-tuning new scalars to the pool | Medium | Medium | Held-out maps (G6), fresh seeds |
| Silent protocol bugs in the shared word | Medium | High | Round-trip tests; claim codes unchanged; beacon pre-emption tests |
| Scope creep into optional modules | High | Medium | Essential/optional split; last architecture change Day 8 |
| Mis-specified hands-off use | Low | High (study integrity) | Never use the 165 hands-off games for development |
| Accidental activation or submission | Low | Very high | No `ladder_duel.py run` or submission without written user approval |
