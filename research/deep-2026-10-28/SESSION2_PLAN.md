# Session 2 measurement and model plan

Registered before timeline features or model results are examined. The 165 hands-off
games remain outside this phase. The five calibration games validate the sampler;
the 385 examined games supply analysis and internal game-separated model splits.

- Use end-of-round engine states, plus the exact final partial round. Validate the
  resource clock against native RLE series on all five calibration games before
  extraction. Every row records its engine round/input/substep and sampling convention.
- Retain every round through 300, every fifth round afterward, exact native event
  rounds, and the final row. Timelines remain local-only; commit schema, tool, small
  calibration sample and generated aggregate data rather than raw trajectories.
- Native events provide exact deaths, gems, banks, purchases, wards, kills and clear/
  reward ownership. Unresolved gold-source credits remain explicit residuals until
  validated at event-level engine states; do not guess from a net round gold change.
- Use the repository's middle definition: compare minimum Chebyshev distance to the
  two teams' initial spawn positions; own/enemy if one is below 0.8 times the other,
  otherwise middle. Use official camp-group IDs, not a new flood-order numbering.
- Win race: banked = collected − lost − carried, per physical body and team. Report
  the exact additive final-margin identity separately from causal interpretation.
- Time categories and visibility describe their sampling points. State/action-based
  proxies are not true hidden policy modes, and unseen-between-samples is unmeasured.

## Model

- Predict Team A victory using team differences in banked gems, carried gems,
  inventory cost, alive count, summed health, last-50-round gem income, last-50-round
  middle gem income and vision coverage; include bank/equipment differences interacted
  with normalized round progress. The maximum round count comes from engine settings.
- Fix an internal 60/20/20 train/calibration/test split by game, seed 20261028,
  stratified by source cohort and Team A outcome. All snapshots from a game share a
  split. Neither the external 165 hands-off games nor future outcomes enter features.
- Fit an interpretable L2 logistic model with no intercept (team-exchange symmetry),
  fixed unit scales, and lambda in {0.01,0.1,1,10}, selected by calibration log-loss.
  If needed, fit a positive scalar temperature on that calibration set. Never use
  test games for feature, lambda or calibration selection.
- Weight snapshots so each game has equal total weight. Exclude terminal states.
  Report log-loss, Brier score and calibration bins on the untouched internal test
  games, plus early/late round slices. Compare with 0.5 and a simple bank-difference
  baseline. Poor calibration requires simplification and explicit limits.
- Event WPA uses approximately 10-round windows and is association. Overlapping
  windows do not become additive causal credit; sample disjoint drops for cards.

## Error analysis

Select about 100 moments from at least 60 distinct examined losses across Learn,
Climb and maps, plus control wins. Cards preserve own-perspective observations;
write expected rule-based behaviour before exposing the actual action window.
Categories and cost ceilings remain provisional until matched controls and traces.
Do not write FAST_FINDINGS or queue wave 2 before this stage supports hypotheses.
