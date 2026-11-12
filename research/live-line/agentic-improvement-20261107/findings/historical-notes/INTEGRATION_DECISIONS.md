# Building on the full session's work

Local work only. No official upload, publication or activation is authorized.
Original v111/x1, prior candidates and teammate checkouts remain frozen.

## How progress is retained

The substantial target (8 percentage points and 60% direct score, repeated)
does not decide whether a smaller improvement or verified correction is kept.
We keep a working incumbent, a corrected model for retuning, and the frozen
original for comparison. A verified incremental champion requires repeatable
match evidence; it need not satisfy the substantial target.

The full index is `INTEGRATION_AUDIT.md` and
`autonomy/data/integration-audit/inventory.json`. It includes all durable
experiment records and every local candidate metadata file. An indexed item
has been retained and assigned an integration action; indexing alone does not
mean its combined implementation has passed detailed checks.

## Current corrected working model

`auto_corrected_es12_actions_r4` keeps the g12 learned weights, the verified
one-spell budget, spent root spell/cooldown state, ranged spell plus basic,
Heart passive/striking dash, and adjacent dash priority. The integration audit
then found and repaired additional dependencies:

* After a real ranged move, the engine blocks an ordinary basic attack while
  the previous model predicted 45 damage. The new initial-root permissions
  prevent that attack and ordinary extra movement; restrictions clear for
  future owner turns.
* Willow reset is an important exception. Actual SDK move -> reset -> attack
  succeeds for 55 damage and still leaves ordinary movement spent. The first
  repair's contrary assumption was disproved, preserved, and corrected.
* Actual fresh Willow basic -> reset -> basic deals 110 damage. The old ranged
  model omitted the reset follow-up; the new model includes the existing real
  executor's sequence. Proactively resetting after an already-spent move is
  still a separately documented executor opportunity, not an assumed policy.
* Lethal Ren retaliation could be followed by a simulated posthumous reset,
  attack or step. Primitive guards now stop those actions. Paired Wasm cases
  reduce invented damage from 60 to the legitimate first 30.
* Actual stationary Heart dash is rejected (error32). The old enabled model
  still awarded 120 damage/stun when both attempted steps were blocked. It now
  preserves cooldown and applies no landing effect. A legal positive-distance
  dash still allows a normal move afterward, as verified in the real engine.

Evidence is in `autonomy/data/experiments/corrected-model-dependency-audit-20261106`.
The 12-case permission/reset/retaliation matrix and 14-case dash extension pass;
the latter preserves every earlier control and its legal-dash control. Original
ranged, cast-budget, Heart-priority and actual root-cooldown contracts also pass
on the final R4 source. All fixtures require the same actual engine round and
zero faults/fuel suspensions. All 34 existing autonomy checks pass.

These are model-contract improvements, not a claim of greater game strength
yet. Remaining model approximations include incomplete visibility/actors,
team-order reconstruction, longer dash geometry, shield layers and the
already-moved reset executor opportunity. Do not silently turn an approximation
into a proved rule or retune against a known implementation error.

## Earlier small changes and teammate work

| Family | What is retained / current action |
|---|---|
| Native target learning | g12's separate60-map result +2.1875pp, 63/120 direct, zero faults; its weights are retained in the corrected base. Smaller-scale failed means and all checkpoints remain reproducible. |
| Earlier PPO/native/team-win actors | Retain training lessons, deployment/parity fixes and checkpoints. Weight files are alternatives, not additive patches. Initial-checkpoint retention is not a learned improvement. |
| Lean reset / Vendetta kill refresh | Reconsider the earlier +0.625pp/33of64 result; exact lean source patches are now tested on the corrected base, independently and with logging/cache changes. |
| Release-only old camp logging | Reconsider removing unused diagnostic writes while keeping active lab knobs, map profiles and models. Test independently and with lean reset; do not disable the entire legacy stack. |
| Ishan bush interval codec | Exact codec/adapter correctness evidence retained. Both64/128tile admission versions are ported byte-for-byte into unchanged main/world files and tested with every reset/log combination. No blind replacement of the corrected combat files. |
| Ishan Varg geometry/capability | Correctness prerequisites and180-game negative first strength panel retained; latest shared hashes are not a winning upgrade. Parked as a revisitable model/role dependency, not rejected solely for that gate. Retrieve exact kernel/dependency evidence before a new port. |
| Max gx / John nnfinal | Frozen current-engine whole bots retained as references and opponents in the integration study. Do not splice incompatible whole policies or neural weights together. |
| Claude / Agent2 findings | Retain deployment and selection lessons, including failed nomarcfun confirmation and optimistic map-selector overfit. Five tracked heads rechecked this turn; none changed. |
| Route depth / retention | First +10.7pp signal and later diverse/published regressions retained. This is a strategy/conditional configuration to retune, not an engine-correctness rule. |
| Gold timing / equipped capital / Marcella value & banking | Preserve component evidence and passive gold checks; evaluate banking, equipment and value together rather than globally lowering all gold value. Available retuning dimensions cover those tradeoffs; alternate formulas remain separate arms. |
| Neural crew / staging / Ryth roles / major objectives | Retain admission, safe spell and crew evidence. Requires matching draft, claims, execution and reward timing; do not add a crew flag without its dependent execution. |
| Bush reveal commitment | Retain the observed backtracking repair and conditional Cassi benefit; global60-map result was negative. Needs terrain/route/execution scope, not unconditional activation. |
| Retreat/rejoin guards | Retain10-turn/2-turn and native-policy factorial results and failed replay evidence. Existing strategy sensitivity is not proof that every rejoin is an error. |
| NN avoid/unreachable filtering | Retain topology and activation evidence. An avoid label is a preference, not an engine-invalid action; static reachability and dynamic obstruction must remain distinct. |
| Actual fuel / bank search / C1 preparation / farm order | Retain controlled savings and all focused repairs. Preparation warms caches and reserves farming work; fuel saved can activate other expensive branches. Stable target order changes ties as well as truncation. Both need corrected-base resource/strategy retuning. |
| Replay decoding / accounting / evidence guards | Teammate methods have already been adapted and integrated: official engine3 decoder, native score/roster/bag parity, failure investigation, bounded evidence, exact build/schedule and both-team fault checks. These infrastructure improvements remain active regardless of bot win thresholds. |

## Current interaction study and retuning decision

`corrected-history-integration-20261106` freezes twelve corrected variants:
lean reset on/off, release logging removal on/off, and teammate cache off/64/128.
Original v111 and previous g12 are controls. There are24 development maps,
seven opponent conditions (including the corrected core, Max and John), both
sides:4,704 normal-fuel games. Every variant retains the corrected combat source
and learned weights. Current engine build, exact source/wasm/maps and both-team
faults/codes are audited before comparison. Failed replays are decoded.

This panel informs which arms to retune; it is not a new threshold for rejecting
verified mechanics. Long retuning has not started. Before it starts, freeze the
chosen corrected source, verify zero-offset identity and once-only offsets after
map overrides, and preserve original/g12/untuned-corrected controls. Compare
retuned versions against both their corrected parent and those controls, then
use untouched maps/styles for incremental and substantial strength claims.

## Update: retuning and expanded compute actually running, 6 November21:34UTC

The integration factorial completed all4704games, current build/both-team0faults
and diagnostic codes, with decoded failed replays for all12variants. Corrected
core + lean reset + release-log removal gained4.861pp versus original in that
24map development panel (26/48 direct original,29/48 corrected-core), with fewer
fuel exhaustions (5218 versus5803 original and5526 corrected-core across336games).
That is promising development evidence, not demonstrated independent strength.
Cache64 with both had mixed styles (-2.083pp reference,30/48 original but22/48
corrected-core). Retained as a separate retuning arm, not rejected from this gate.
Original NNweights on the same corrected+reset/log source gained2.431pp,28/48
original. This dependency comparison justified keeping original and g12 weights
as separate arms rather than assuming one correct weight choice.

Previous g12 learned-targeting independent published repeat was only+.426pp,
43/88direct. Pooled104maps: +1.442pp,90%CI[-.180,+3.125]pp,106/208direct. It is
retained as learned source and comparison; repeatable upgrade is unestablished.
No existing local incumbent has been replaced on that evidence.

Frozen three-arm corrected-strategy retuning started20:53. Verified zero builds,
once-only strategy offsets AFTER recognized-map overrides on all three anchors.
Three first rounds complete: learned full-step mean accepted on second training
batch (.5625->.625); cache full mean failed, focused half-step repair accepted
(.618056->.659722); original-weight proposals failed fresh comparison and its
parent remains. All measured source checkpoints and failed proposals preserved.
Second training batches are not final strength evidence. Mechanics stay fixed
while surrounding aggression, retreat, banking, farming and tactical preferences
are retuned. Initial development and final controls retain original/g12/R4 and
untuned parents. Reserved new60final +44published replication remain untouched.

User explicitly requested using plentiful local compute. Main8workers + extra
low-priority8workers now run concurrently; measured96.1%CPU,14.27GBavailableRAM,
602.17GBfree disk. Extra5040-game league freezes first accepted learned mean,
original and corrected parent across120maps/7styles/both sides. Published60 ARE
part of the primary training pool (60published+600generated); older synthetic60
were used previously. Results are DEVELOPMENT, not independent final evidence.
Its successor queue waits for completion, then tests each newly accepted training
checkpoint on the same120map league (1680newgames/checkpoint), reusing3360frozen
control cells. Exact current build, source, Wasm, maps, both teams and schedule
remain audited; failed replays decoded. No post-hoc current-final selection or
promotion through this development queue. All work is local; no AI calls per
game and no official actions. Primary source pins and other checkouts unchanged.

Infrastructure checks now36passing, including controller deferral under native
training ownership. Collector stays read-only during the native run. Queue and
primary preserve sleep inhibition and stop/failure handling. Live status details
are recorded in CURRENT_WORK.md and the respective runtime JSON files.
