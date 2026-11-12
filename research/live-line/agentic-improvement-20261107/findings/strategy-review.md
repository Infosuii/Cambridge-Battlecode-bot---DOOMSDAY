# What changed in the improvement strategy

The initial strong local signals did not consistently generalize. One early
challenger gained 10.7 percentage points against reference opponents and reduced
fuel exhaustion, yet scored only 44/84 against v111. Later broad comparisons
confirmed that development strength could coexist with direct-match weakness.
Those early numbers are historical evidence, not the final bot's performance.

## Correctness before retuning

Real-engine fixtures identified and repaired model errors: one spell budget per
turn, spent root cooldowns and permissions, ranged spell/basic combinations,
Willow reset exceptions, posthumous simulated actions, and stationary Heart dash
effects. Legal positive-distance controls and reset sequences were retained.
Repairs were tested together with their dependencies before strategy tuning.

The ancestry study separated original/learned neural weights, old/corrected
mechanics and route depth. On 164 maps across nine opponent styles, corrected
original/deep-route scored 174/328 directly against v111, with +1.448 percentage
points against the other references. Corrected learned/deep-route scored 167/328
directly and +2.782 points against references. Short routing's development gain
did not reliably survive the broader distribution. These results motivated two
corrected, deeper-routing anchors; they did not establish the substantial target.

## A hidden experimental confound

Changing parameter initialization could also change generated Wasm code. Matched
unused-slot controls reproduced the supposedly strategic difference, so the
earlier macro offsets were not clean isolated parameter experiments. A revised
one-time initializer reduced this footprint but did not prove whole-game parity.

The final retune instead stores strategy parameters in a fixed-length volatile
data table. Every variant must have identical non-custom, non-data Wasm sections,
including the complete code section, within its neural arm. Only data may differ.
This checks the actual artifacts; source-level intent is insufficient. A zero
table and raw parent remain controls because the table scaffold itself can matter.

## Broader tuning, then frozen checks

The bounded pass covers 28 parameter axes in both directions for each of two
anchors, with 48 TRAIN and 48 disjoint FRESH maps. Each selection panel balances
published maps with and without named-profile filename proxies and generated
maps. A filename match is not proof that a profile executes at runtime.

Up to four focused combined, damped, expanded or half-step repairs per arm are
driven by measured effects. Components and controls remain available for
interaction comparisons. The procedure freezes at most one finalist per arm
before either new 60-map final panel or the 44-map published replication starts.
Both finalists finish every panel without switching to a better-looking variant.

A subsequent live-catalog audit found that the original local map directory
contained 128 official maps and two custom fixtures. One generated fixture had
entered the supposedly published final set. Before any finalist was frozen or
played any final game, that entry was replaced with a seeded, unused official
map in the same filename-proxy stratum. All 44 published final maps were checked
byte for byte against a clean official download; all 260 role hashes remained
distinct. Completed training, selection, policies and generated finals were
unchanged. Original plans and the prospective amendment are preserved under
`training/runs/bounded-delivery-retune-v1/published-map-correction-20261108/`
in the snapshot. Future preparation must use `tools/published_pool.py` with
catalog IDs and official bytes; a directory glob is not publication evidence.

Final intervals are candidate-wise 95% map-cluster intervals. With two registered
finalists this supports the specified nominal 90% family accounting per metric
and panel; it is not a blanket joint guarantee across every reported metric,
panel and historical experiment. Selecting a practical delivery bot from final
results must be disclosed as such, not presented as a new independent test.

## Learning from failures without AI calls per game

Native score accounting separates camp collection, champion transfers, deaths,
held gems and actual submissions. Selected failures are decoded with pinned
official visualiser assets and checked against native scores, rosters and bags.
The analyst receives bounded incident evidence and previous intervention results.
Bulk games, accounting, auditing, regression review and checkpoint retention run
locally. Memory improves the evidence available for analysis; it does not retrain
the language model or guarantee rising ELO.

All scheduled cells require current-engine, source, map and Wasm identity checks,
complete paired schedules, both-team fault/error checks and recomputed fuel-event
counts. Native hashes are checked in parallel with bounded queues. Resume paths
preserve completed serialized result order and receipt identities.

## Teammate findings retained

The exact Ishan bush codec was ported and checked, including capacity, memory and
admission repairs. It did not establish a broad upgrade. Max's complete policy
and John's pinned nnfinal were preserved as references. Claude's failed held-out
confirmation and Agent2's optimistic map-selector evaluation informed the
selection protocol. Replay decoding and score-accounting methods were adapted
and integrated. All five tracked branch heads were unchanged on 8 November.
No teammate worker was restarted and no teammate checkout was modified.

Correct features and minor improvements remain indexed as retained components,
conditional opportunities, retry candidates or parked hypotheses. Weight files
and incompatible whole policies are not blindly merged. The final source and
release rationale identify what is actually included in the delivered bot.
