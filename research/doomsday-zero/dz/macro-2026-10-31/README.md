# Common macro itineraries and quoted equipment visits — 2026-10-31

Implemented inside `DZ_ECONOMY_V2=0`; development only, not promoted. Selected
release defaults are unchanged. No new experiment flag, holdout, ladder or submission.

## Source changes

`macro_value.h` compares complete farm, bank and shop itineraries in a common
finite horizon, then assumes the same productive continuation rate. Each alternative
counts the existing bag once, includes travel and tribute delay, and gives no
terminal gems or imaginary continuation income when delivery is unknown. Gold
from a completed capture can have development value even when its gems cannot
arrive before the deadline. Explicit equipment benefits and risk costs are GE
estimates, not fitted probabilities. One productive round prices a job switch.

`economy.cpp` refreshes retained-job work from current member HP and crew views,
rather than subtracting elapsed time while blocked. Unpriced/incomplete crew work
keeps the productive contract instead of inventing a zero-time alternative.
Certain-win and deadline deposits can interrupt equipment trips. A committed
shopping visit persists to Home with a finite deadline; its claim/crew is released.
The fixed 150-gold Home rule and bag-threshold interruptions are removed from this
new economy path. The proven legacy fallback remains separate and still has its
old rules. Emergency combat, low-health recovery and active siege still pre-empt
this partial macro layer; this is not completion of the full Z8 action enumerator.

`gear.cpp` shares project selection between the distant visit quote and the live
shop. It executes the quoted shard project, checks inventory identity, bounds the
quote age, retains unfinished-project hysteresis, and reprices additional purchases
using current stats. The quote includes affordable purchases only and values their
benefit after the trip. It uses the earlier explicit marginal gear model, whose
income/passive estimates remain uncalibrated. Static member-to-altar endpoint
travel and pressure discounts are estimates, not native access/survival proofs.

## Validation and failure

Host checks independently account for existing bags, delivered/undeliverable
rewards, time spent, finite horizon, switching cost, equipment payoff, risk,
unknown access, invalid inputs and numeric overflow. All host suites, 28 measurement
checks and six audit/parser checks pass. The merged default Mac Wasm remains
SHA256 `437f91c3a6abb160ea151be081c4d410e9e3161d4ef8042c73df2db4063581f0`.
The combined `DZ_ECONOMY_V2=1`, `DZ_PLAN_TABLE=1`, `DZ_SIEGE=1` configuration
also compiles (SHA256 `52e50541fb9387ca1befa50ecf20f4fb759adcc4d83dae319e4eec0be9a7e207`);
this compile check is not additional native/competitive evidence.

Native production-bot fixtures 11/12 exercise the new path and planned purchases.
Final-source `dz-macro-final-fixtures-14` completes four cells on `recovery-shop`
and `siege-two-layer`, all banking positively, with zero native faults/fuel-outs;
p99 fuel 73,344. Trace emits quoted projects and actual planned buys. Traces can
be dropped under budget: they do not prove every purchase or every visit completes.
These maps establish functional integration, not strength or a general ObjModel.

Preliminary `dz-macro-income-dev-13` on four development cells vs v65 banks 169.25,
versus selected-source control 294.5 (prior broad economy candidate 173.0).
Zero faults/fuel-outs, p99 fuel 84,566. This is a decisive failed preliminary gate:
no larger screen or second-opponent confirmation. Later correctness/fuel fixes
were checked on fixtures only; no strength claim is made for the final source.
Frozen capsules and source hashes are in RESULTS.json.

## Continue engineering

1. Move gate investment into this same comparison: resource income and equipment
   progression must be able to precede an expensive gate. Current active-siege
   priority remains a structural limitation, not something to tune with thresholds.
2. Make actual tank/rear positions and common crew focus executable. The present
   quote requires every crew member to survive tanking; current committed-ally
   protection lasts only one round. Neither is a real tank rotation.
3. Compare combat exchange, retreat, ward and capture choices with the same task
   opportunity cost, retaining conformance-safe fallbacks. Reaudit the inherited
   EE2 calibration scope before claiming the complete planned V-M2 gate.
