# Why the promising original-weight directions did not combine

These are selection/development results, not final validation. All comparisons
use the completed registered panels, frozen normal-fuel releases and unchanged
Wasm code within the neural arm. Raw native evidence and input hashes are in
`original-arm-interaction-review.json` and the snapshot.

| Change | TRAIN reference gain vs v111 | TRAIN direct score /96 | FRESH reference gain vs v111 | FRESH direct score /96 |
|---|---:|---:|---:|---:|
| Zero-table control | +0.91 pp | 47 | +2.60 pp | 46 |
| Higher required helper pool, k10 +0.5 | +3.78 pp | 54 | +3.65 pp | 41 |
| Lower waiting weight, k9 -0.5 | +3.39 pp | 55 | +1.56 pp | 44 |
| Full combination | +0.52 pp | 47 | -1.04 pp | 42 |
| Half-strength combination | +2.73 pp | 44 | +4.30 pp | 36 |
| Shorter staging timeout, k14 -0.5 | +2.21 pp | 54 | +3.39 pp | 47 |

The full combination's observed TRAIN interaction, `AB - A - B + control`, is
-5.73 reference percentage points and -15.63 direct-score points. Adding two
positive individual results is not a valid prediction of their combined effect.
The damped combination is a separate caution: optimizing reference performance
alone would prefer a result that scores only 36/96 directly against v111.

On FRESH `00collision`, side A, against `ref_p65pack`, the control and both
individual changes win while the full combination loses. At the common round
600 horizon, the control has collected 380 camp gems and banked 409; the combined
bot has collected 212 and banked 248. Both have three fuel-exhaustion events.
The combination also has one death and 20 lost gems versus zero for the control.
This selected counterexample supports investigating collection/coordination
timing; it does not support a simple explanation that extra fuel exhaustion
caused this regression. Event-level intent and causal timing remain unproved.

The shorter timeout was the only direction passing the registered TRAIN/FRESH
qualification and domain constraints. Its FRESH gain over the table control is
small, and its direct score is below 50%. It remains a finalist to validate,
not an established upgrade. The other candidates, their dependency-correct
implementations and all failed confirmations remain available for later work.
