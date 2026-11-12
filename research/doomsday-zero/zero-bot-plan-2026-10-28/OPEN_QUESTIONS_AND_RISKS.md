# Open questions and risks (DOOMSDAY Zero)

## A. Decisions for the user

| ID | Question | Effect on the plan |
|---|---|---|
| Q1 | Are finals played on the 70-map pool, or on new maps? | New maps raise the value of rule-derived models and lower per-map rows |
| Q2 | Will ladder duels be approved (they activate arms), and when? | Only judge of top-team strength; Day 11 slot |
| Q3 | Which bot is the finals fallback (current live version)? | D7/D9 fallback target |
| Q4 | Accept the clean-slate risk (my estimate: 30–45% chance DZ beats v76 against top teams by Day 12)? | Go/no-go at D7 and D9 |
| Q5 | May the agent download fresh top-team replays (`cambc matches download`) for calibration? | Better EE and opening calibration. Needs explicit permission (downloads) |

## B. Engine unknowns

All have conformance tests (ENGINE_CONFORMANCE_SUITE.md):
- CT-1 host-call fuel costs (largest design-relevant unknown)
- CT-6 exact turn interleaving
- CT-8/9 visibility of enemy cooldowns, gems and liveness
- CT-11 camp hit cadence
- CT-12 Tribute emblem
- CT-14/15 Hunter, Skirmish and Collectors effects
- CT-19/21 C&I slots and team size
- CT-20 draft timing
- CT-25 kill credit

Until each is resolved, DZ uses the conservative defaults in ALGORITHM_SPECIFICATIONS §15.

## C. Model assumptions (validated before use)

ObjModel accuracy (V-M1), EE calibration (V-M2), λ_gold and λ_tempo calibration (V-T1), auction sufficiency under
unshared vision (V-E1).

## D. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| DZ misses parity by D7/D9 | **Medium-high** (clean slate in 14 days) | High | Parity gates; fallback to the live bot; SafeMode skeleton by Day 2 |
| Engine or balance update mid-development | High (3–5-day cadence) | Medium | Runtime-read values; conformance re-run; fingerprint |
| Host calls expensive (CT-1) | Medium | Medium | Scenario B budgets; lazy fields; caching |
| Fuel-out resumption bugs | Medium | High | Kernel stale-turn guard; tests in CT-2 |
| Uncaught exceptions | Low | Very high | Catch-all at the turn boundary; module disable after 3 errors |
| Protocol bugs | Medium | High | Host round-trip tests; freshness rules |
| Local gains don't transfer to top teams | Medium | High | Style opponents; ladder duel request (approval) |
| Over-tuning to the pool | Medium | Medium | Held-out maps; fresh seeds; once-only holdout |
| Scope creep | High | Medium | Essential/optional split; last architecture change Day 8 |
| Accidental submission or activation | Low | Very high | Never without explicit user approval |
