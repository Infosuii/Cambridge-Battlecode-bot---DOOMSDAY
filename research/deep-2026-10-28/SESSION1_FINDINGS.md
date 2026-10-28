# Session 1 findings: detector screen, not the final mistake catalogue

Updated 2026-10-28T17:34:21.775493+00:00. **Association only; no causal fix has been established.**

The frozen examined set contains 360 DOOMSDAY games (191 losses,169 wins) and
25 top-v-top games. Five calibration games are separate. All 385 study games pass
every registered native/replay event and perspective-state check. Thirteen semantic
edge cases and six statistical edge cases pass. No detector has run on the 165
hands-off games. All 111 groups' public metadata now agree with native scores/rounds.

## Strongest next-review candidate: repeated deaths

The registered D3 flag is another death of the same physical champion within
250 rounds, either within 6 tiles of an earlier death or to the same enemy champion.
It occurs in 129/191 losses (67.5%) versus
74/169 wins (43.8%). The game-occurrence
difference remains positive under map- and opponent-cluster bootstraps.

This is not just more chances to flag in games with more deaths: repeated deaths
are 722/2337 native deaths in losses
(30.9%) versus 188/1028
in wins (18.3%). Difference 12.6 percentage
points; map-cluster 95% [7.2,
18.3] points; opponent-cluster 95%
[3.8,
16.9] points.

It also appears against Climb opponents: 50/83 losses versus
50/119 wins; per-death difference 9.4 points,
positive under both cluster choices. This cohort covers only six observed opponents,
so transfer beyond this sample is unresolved. It does not establish that a death
watchdog, an earlier retreat or a draft change will help; related fixes have failed
in prior versions. Matched visible-state cards and code traces come next.

## Findings that need more caution

- Capture rewards taken by the enemy after our native last-clear are more common
  in Climb losses, but opponent-cluster uncertainty spans both directions.
- The turn-sampled unseen-killer flag is more common per lost game, but its per-eligible
  death difference is not robust; the Climb rate difference is slightly negative.
  Do not turn this into a blanket warding or hidden-information bug claim.
- High-bag episodes and high-bag deaths are review candidates, with weak/heterogeneous
  opponent support. Do not select new banking thresholds from these associations.
- D1 stationary flags are common in wins and losses; their pooled time fraction is
  higher in wins. Generic inactivity is not supported as the leading loss explanation.
- Bank interruption is more common per winning game, and much of the gap shrinks
  after dividing by bank attempts. High-gold flags also occur more in wins. Neither
  is automatically an error merely because its detector fired.
- D4 movement oscillation is nearly universal and cannot identify hidden mode
  flip-flops. D9 ground-island and D11 visibility conditions retain their registered
  proxy limits. Native faults across the examined set: 0.

## Deliverables and next phase

P2_DETECTORS.md has occurrence intervals, exposure rates, subtype contrasts and
example game/round links. DETECTOR_DATA.json holds the rows needed for its tables.
DETECTOR_SPEC.json is immutable registration; DETECTOR_VALIDATION.json and
DETECTOR_SCREEN.json record the calibrated/current-code checks. Output flags are
per physical champion and game, with rounds, context and denominators, local-only.

This is deliberately not FAST_FINDINGS.md. Session 2 still needs paired timelines,
income/conversion/denial/time decomposition, openings, a game-separated calibrated
win-probability model, and about 100 varied moments with prediction-first cards and
ceilings. Review at least 60 examined losses plus control wins. Only then write
FAST_FINDINGS and reserve wave-2 hypothesis probes. Keep all hands-off trajectories
and detector outputs unopened until final frequency confirmation.
