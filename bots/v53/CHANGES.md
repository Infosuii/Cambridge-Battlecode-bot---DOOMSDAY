# v53 — cache open-job status once per scoring call

General fuel optimization against live v52. No map-specific behavior fix or draft change is shipped. A2_GATE_JOB remains off; sole-gem timing remains round 500.

## Change

`score_groups` previously asked `open_call_by_lower()` repeatedly while evaluating candidate camp groups. That scans earlier allies and may recalculate a job's staffing/soak requirements. Claims, health and the observed camp state do not change during the scoring call, so its answer is invariant. Compute it once before the candidate loop, with the existing eligibility checks, then reuse the boolean. This adds no per-group/camp logic. The source matches the recorded development candidate byte for byte.

## Measured against v52 (bench2, both sides, seeds 1–3)

| Test | Result | Mean gem margin | Faults |
|---|---:|---:|---:|
| 28 development maps / 168 games | 87–81, 51.8% | −2.1 | 0 |
| 12 release holdout maps / 72 games | 39–33, 54.2% | +5.3 | 0 |

Development fuel-exhausted turns: 235 for candidate versus 274 for the opponent; holdout: 23 versus 17. Fuel savings do not translate uniformly across maps because thresholds alter subsequent decisions. These results pass the documented aggregate floor (>=47% wins, >=−30 margin) and the aggregate no-regression holdout check, following the v52 release's suite-level interpretation. Criterion (a) applies to declared map fixes; this release is a general optimization with no map-specific target claim.

Per-map tradeoffs remain: holdout monolith 5/6, interlock 4/6 and expanse 4/6; ambush, elk_arena and hooks each 2/6. This is a small measured candidate, not evidence of a broad ladder win-rate increase. Results: `artifacts/claude_ops/results/v53-fuel-call-vs-v52.txt` and `v53-call-holdout.txt`.

## Research retained, experiments rejected

- Read setup/full handoff and the user-supplied game/API rules; verified official CLI checksum, setup smoke, and a deterministic unchanged-source control (84–84, zero margin).
- Pulled 20 ranked games (8 wins) and 55 unranked games (27 wins) since v52 went live. Downloaded and decoded all 40 losses plus seven top-team wins, 47/47 successful. See `V53_LOSS_REPORT.md` and `V53_PLAN.md`.
- Delaying stampede's team objective to R1100 won 6/6, +343.2 and halved deaths; in one seed's R900 snapshot it earned 4,644 gold versus 2,352. However the global threshold harmed elk_arena and scoped implementations also failed the holdout. None is retained. The failed implementation variants each had a release check; those repeated checks are disclosed and are not an untouched statistical holdout for later versions.
- A regularized model trained on 243,904 ladder games improves held-out prediction (log loss 0.6004 → 0.5925) but loses its local gameplay screen, 8/30. No new model is enabled.
- Fixed boss drafts, smaller concentrated-wealth banking, no-action caster micro fallback, duplicate mask-clear removal and observation-buffer reuse failed their applicable gates. Buffer reuse approximately halved profiled observation cost but lost −55.3 mean gems overall, illustrating why fuel optimizations still need game tests.

Submission status and source hashes are recorded in `artifacts/claude_ops/V53_RELEASE.json` and `ops/HANDOFF.md`.
