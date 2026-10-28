# Next bot brief — DOOMSDAY

Research frozen2026-10-28; study platform69 source, engine2.0.0. Read [REPORT](../research/deep-2026-10-28/REPORT.md), [MISTAKES](../research/deep-2026-10-28/MISTAKES.md) and [P6 deep track](../research/deep-2026-10-28/P6_DEEP_TRACK.md). These are recommendations. No production candidate is implemented or approved for release by this analysis.

## First concrete patch: M1 recall/bank eligibility

At frozen bot.cpp `play_turn` around7005, permit the winning-bag-only recall cancellation **only when** `!w.no_bank && round >= tribute_off_until`. Keep the existing dangerous-channel cancellation/escape branch intact. `tribute_if_needed` around4535 already uses this eligibility rule; around4639 sets the80-round disable after twenty non-progress bank turns. Match those semantics so recall is not cancelled for a bank the bot refuses.

Run the condition once per champion turn at the existing recall-cancel branch. Do not add map/camp scans or logging in hot loops. Expected tested effect: remove the cancel/restart inconsistency while retaining safe recall, not736 recovered gems or a proven match win. Exact evidence: C004 actor1, guardians, R1669 takeover; unchanged source fails with4 restart pairs, diagnostic passes with0 and recall completesR1673. Observed breadth: exact source mechanism confirmed in1 examined loss; winning-bag proxy1/191 examined losses, reserved2/83 losses. Generic loops also occur in wins. Planning score0.00489 uses generous associated-window coverage and is not expected gain.

Mandatory regression: tests/loss_cases/M1-recall-disabled-bank.json using the documented warm replay fixture. Preserve accepted inputs and every-round state beforeR1669, enemy accepted script through assertion end, full assertion coverage and default fuel. Original must fail, candidate must pass. Compare at most ten rounds; stop sooner on script rejection. A candidate that changes the opening cannot be evaluated as this same-state case without a warm takeover build.

## Broader research queue

| ID | Coverage proxy | Fixability* | Transfer* | Effort h* | Planning score |
|---|---:|---:|---:|---:|---:|
| M3 | 70.5% | 0.25 | 0.50 | 12 | 0.00734 |
| M1 | 3.6% | 0.90 | 0.30 | 2 | 0.00489 |
| M4 | 17.1% | 0.30 | 0.40 | 8 | 0.00256 |
| M5 | 70.5% | 0.15 | 0.15 | 12 | 0.00132 |
| M2 | 1.9% | 0.30 | 0.30 | 6 | 0.00028 |

*Judgments fixed from examined evidence. The score ranks research work; M1 is the first implementation-ready patch. Other entries need a concrete diagnosis before a production change. Coverage is an overlapping surrogate label, not a causal gain ceiling; no defensible gem equivalent is identified.

- **M3 economy/opening:** paired R100 inventory deficit−91.8 in83 Climb losses, later income gap−382.0. Locate the first map-specific allocation or purchase difference before changing policy. Keep draft fixed and compare one camp-route assignment or existing item milestone per experiment. No new universal carry/shop/aggression value is supported. Place new bookkeeping once per turn or in initialization, not per-group scoring. Require preserved source/knob identities, an exact opening comparison and a separate useful-equipment measure. No confirmed bug case exists yet for this broad category.
- **M4 bags:** C034 carrier343 was banking before an interrupt, then fleeing; banking “earlier” is not an established fix. Start with M1, then test one bank-route eligibility/interruption decision in C034 or C011 with warm state and original danger guards. Do not disable flee-attacks globally. Carry65/shop138 are observed effective values, not recommended new thresholds.
- **M5 capture handoff:** Climb flags52/83 losses and52/119 wins, with opponent-cluster interval crossing0. Reproduce a specific original camp-group reward handoff before writing an ownership/abandonment rule. C048/C026 are starting contexts, not executable confirmed failures. Avoid new per-camp scans.
- **M2 repeated death:** strongest normalized association, but card coverage is only2/90 windows and a generic watchdog already lost−126, strict engage rule−262, softer leave−18 in prior local tests (research/v66/RESULTS.md). Diagnose victim7 in C082 and actor6 in C070; preserve their own vision, current local numbers and TTK/TTD. Do not revive those global switches merely because D3 replicated. V58_SURVIVE is currently0; enabling it is a new unvalidated intervention.

No numerical threshold or exact patch is claimed for M2–M5. These require a concrete measurable decision defect and a baseline-failing regression before implementation. Missing causal evidence must not be filled with a plausible-looking heuristic.

## Candidate test and release gate

1. Copy frozen source into a new diagnostic/development directory; never edit bots/live-69/src or another frozen bot. Record source/toolchain/engine/Wasm hashes and effective V71/A2 settings. Baseline source should reproduce the selected12 cases exactly before judging a new mechanism.
2. Run the M1 baseline-fail/candidate-pass warm regression. Add cases only for confirmed failures. Retain the non-profile packs control and the vault masking context; keep existing dangerous-channel behaviour.
3. Run `bash tools/bench3.sh <absolute candidate dir> <absolute live-base dir> <absolute output prefix> 1 2 3` on the28 development maps/both sides. Use `MAPS_OVERRIDE="02guardians"` for the target-map screen. Capture complete expected game counts and zero native faults on **both** sides; fuel-sensitive logging stays out of production builds.
4. Compare paired candidate/base runs against the same opponent using `python tools/bench_compare.py <candidate-prefix> <base-prefix>` and `python tools/bench_bayes.py <candidate-prefix> <base-prefix>`. Retain a mechanism only if its map-clustered95% interval is above0 and the Bayesian verdict supports it. Preserve the repository target-map and overall non-regression gates in docs/handoff.md; a local same-lineage win does not prove transfer to strong teams.
5. Freeze the entire candidate before `HOLDOUT=1 MAPS_OVERRIDE="<untouched final maps>" bash tools/bench3.sh ...`. Run the release holdout once per frozen candidate, with all-count/fault checks. The165 games opened for this research confirmation are already spent and cannot serve as a fresh candidate holdout.
6. If a small strong-opponent probe is needed, verify current platform identity and obtain direct authorization for its shared quota; pin opponent/version/map/side and write the hypothesis before queuing. Wave2 remains unused. This brief does not authorize upload, activation or a new ranked request.

## Avoid the measurement traps

The win model is a conditional surrogate. Purchases cause abrupt drops partly because unspent gold is omitted; do not turn81.8% purchase coverage into a purchase-policy gain ceiling. Camp receipt, own death, enemy bank and lost bag labels overlap. Costed inventory is not fighting power; stationary time is not always idle; per-champion vision is not team omniscience. Use the exact source-trace cutoff and physical victim ID. No causal gem equivalent or expected rank gain is identified.
