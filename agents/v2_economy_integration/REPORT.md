# Direct policy economy integration

Implemented `bot/src/nn_policy_economy.cpp`, gated entirely by `NN_POLICY_V2`.
Bank/shop each emit at most 16 canonical F12 candidates through the existing normalizer. No teacher scores,
teacher buy plan, teacher preference, prior, or training data are consulted.

Bank has continue, explicit travel destinations, and in-range deposits. An SDK walking field rooted at self
is computed once with a64-expansion limit, and each public altar's submission ring is queried separately. This gives actual separate
static path distances, including maze detours; it does not reuse the nearest-altar aggregate. The graph is
`World::static_blocked` (actual holes remain blocked) and ignores temporary champion/camp occupancy, which must
be rechecked by the local movement executor. Goals are reachable submission-ring tiles with canonical tie order.
All directly legal deposits are retained first (subject to K16), then one nearest destination per canonical
quadrant and nearest remaining destinations. Stable IDs are exactly `1+2*i` travel and `2+2*i` deposit.

Bank field scratch is plain `constinit` storage: three 8KiB boards and a 128KiB field plus a small cache key.
Host chunked buffer sizes are checked before every computation; oversized maps refuse instead of overflowing.
The cache key is champion/round/dimensions/actual self position, so same-turn travel execution rechecks its
destination against the already computed graph. Only static terrain is cached. No per-decision heap allocation
or global constructors are introduced. Candidate generation must be admitted before calling the builder.
The metadata/count-only `bank_candidate_fuel(const Bot&)` estimate includes the cap64 chunk tariff, buffer
storage, altar enumeration, candidate and enemy overhead. It does no SDK feature reads or traversal. A matching
owner/turn/position cache hit removes only the field term. Unsupported layouts/radii return `UINT64_MAX`, which
the caller must reject before arithmetic/admission. Builder refuses stale Bot position snapshots before field
work. Travel execution refuses a missing/stale cache instead of starting a cold search inside its action reserve.
These conservative estimates use the existing SDK field cost model; official calibration remains lead work.
No fuel measurement or gameplay claim is made here.

The64-expansion cap does not silently narrow away farther reachable altars. If the cap is hit and any altar has
no reached submission-ring tile, the entire builder fails with K0 and takes explicit runtime fallback. If the
search exhausts before the cap, disconnected altars are proven unreachable. If every altar has a reached ring
tile, every ring minimum is exact even if farther map areas remain beyond the cap. Existing candidate/action
schemas stay unchanged. Long maze decisions may fail more often, so bank coverage remains incomplete.

Lock state uses an enemy-team SDK query with visible absence=0, observed enemy lock=1, hidden=-1. A deposit
rechecks actual self, carried gems, channel/state/restriction/range/lock preconditions immediately before calling
`sdk_submit_gems`. The host's final success is authoritative: failure returns an unexecuted result. Travel is an
acknowledged macro selection that writes an altar and reachable ring goal; physical walking belongs to move.
Continue/save are acknowledged no-effect decisions; `changed` remains false.

Shop candidates are explicit one-shard purchases, live consumable raw ABI IDs 0 and 2, and save. Raw consumable
inventory is **four slots indexed by ABI ID**, matching the SDK wrapper, not a two-element dense array. Retired
raw ID1 and all nonpurchasable emblems are excluded. Narrowing reserves one affordable choice from each of seven
item families and both affordable consumables, then fills by family round robin with canonical IDs within each.
Execution independently refreshes can-shop, prices, gold and consumable capacity and calls a single buy API.
It refreshes Bot self stats after a successful purchase so subsequent heads see combined stats and new gold.
An exception in that follow-up read preserves the already successful purchase acknowledgment; a subsequent
fresh observation can recover the snapshot. Failed host buys are never acknowledged as executed.

Features use current SDK stats and metadata. Item health/strength/focus gains multiply stat points by champion
growth and include automatic fifth-shard combination deltas. Damage gain describes basic attack strength gain;
context-specific emblem passive damage is not folded into it. No current consumable heals, so heal_amount=0.
The SDK exposes no item inventory limit or exact can-buy inventory/stats-overflow predicate: capacity_remaining=0
is an unknown sentinel for items/save, while consumable capacity is exact. SDK buy success remains the final
inventory/stats-overflow check. This observable-schema limitation is explicit; no invented capacity is supplied.

Validation performed locally, with no training, games, submission, or reference changes:

- Active C++20 syntax against the actual bundled SDK passed using the installed w64devkit compiler, with a copied
  header tree enabling NN_POLICY_V2 only in scratch. The default checked-in configuration remains off.
- `run_synthetic.py --cxx <compiler>` compiles the production economy source with include-only SDK substitution
  and the real candidate normalizer. The executable passed, with no compiler warnings. Receipt:
  `synthetic_result.json`. Assertions cover distinct maze distances for different altars, field cache reuse,
  inaccessible altars, cap-hit unresolved whole-decision refusal, cap-hit all-altars-proven acceptance,
  metadata-only cold/warm estimates, stale-snapshot no-search refusal, canonical coordinate reflection,
  deposit lock/channel/API refusal, unknown lock sentinel,
  zero-gem continue, oversized layouts, >16 altar quadrant preservation, seven-family shop diversity, raw ABI
  consumable slots/retired-ID rejection, automatic combination gains, dead shopping, fresh affordability,
  failed buy acknowledgments, and immediate self refresh after purchase.

The synthetic host verifies geometry, option and execution logic; it is not an official engine/fuel measurement.
Lead owns full default-byte identity, runtime dispatch integration, engine release/default-fuel checks and docs.
No commits were made by this worker.
