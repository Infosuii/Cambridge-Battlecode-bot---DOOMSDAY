# Direct v2 candidate interface

This pure layer is implemented and tested. World option generation, admission, inference and exact
SDK execution belong to the lead's runtime/glue. The default teacher path is unchanged by this worker.

## C++

```cpp
#include "nn_policy_candidates.h"
// namespace nnpc
struct Candidate { std::uint32_t id; std::uint8_t legal; float raw[12]; };
struct Decision {
    nncfg::H head; int K, F; std::uint8_t context;
    float feat[16*12]; std::uint8_t legal[16]; std::uint32_t id[16];
};
nnpc::Error nnpc::build(nncfg::H head, const nnpc::Candidate* rows, int count,
                      std::uint8_t context, nnpc::Decision& out);
int nnpc::teacher_index(const nnpc::Decision&, std::int64_t stable_action_id = -1);
```

Heads use legacy H ids: strategy1, objective2, role3, bank4, shop5, move6, combat7, engage8.
All have F12, K<=16 and context0ordinary/1combat/2retreat/3positioning. Index0 has no special
meaning. The builder canonicalizes every row by ascending unsigned stable action ID, including
masked rows. It preserves masks; the first row may be illegal. Ties resolve to the lowest legal
canonical ID when the shared masked-argmax kernel selects the first legal maximum.

`Error` numeric values: ok0, unsupported_head1, bad_count2, bad_context3, duplicate_id4,
bad_mask5, non_finite6, empty7, no_legal8. Every failure leaves K0; inference failure/empty must
deliberately enter teacher fallback, never silently select candidate0. More than16 rows rejects
rather than truncates. A mask must be exactly0 or1. Duplicate IDs reject even when duplicates are
masked. Every raw float is checked finite before normalization, including masked rows.

Call admission before building candidates/features. Then fill every raw[12] in schema order and
call build. No per-decision heap allocation, SDK reads, global constructors or teacher computation
exist in this module. A bounded insertion sort uses16 integer slots. Output padding beyondK is
ignored and deliberately not zeroed; initialize only when a consumer incorrectly needs padding.

`teacher_index` is separate: absent(-1), not present, invalid uint32 or masked returns-1. A valid
label does not alter input features, ordering or masks. Record missing labels rather than injecting
the teacher's choice. Candidate construction takes no teacher argument and has no prior field.

## Feature order and stable IDs

[policy_v2.json](../../schemas/policy_v2.json) is authoritative for all96 feature names, raw units,
normalization bounds, option enums and caller narrowing rules. Each feature computes one float32
multiply by a float32 reciprocal scale, then clips. Raw option kinds distinguish the available
decisions; no teacher preference or index-first flags are inputs.

| Head | Stable action IDs |
|---|---|
| strategy | 0farm,1bank,2defend,3contest,4regroup,5attack,6retreat |
| objective | Public static group id |
| role | 0farmer,1carrier,2fighter,3escort,4scout |
| bank | 0continue;1+2*altar_index travel;2+2*altar_index deposit |
| shop | 0save;1+item_type item;1000+raw_ABI_id consumable |
| move | `(kind<<30)|(canonical_y<<15)|canonical_x`; kind0walk/1mobility_slot0/2mobility_slot1/3hold |
| combat | `(target_handle<<2)|kind`; kind0basic/1slot0/2slot1/3hold; hold target0 |
| engage | 0fight,1disengage,2hold |

Checked helpers `nnpc::move_id(kind,canonical_x,canonical_y,out)` and
`nnpc::combat_id(kind,target_handle,out)` return false on overflow/invalid bounds. They never mask
off high bits to fabricate an aliased ID. Execution retains a separate mapping to original World
coordinates/SDK handles. Map coordinates supplied to move_id must already use the canonical team
frame. Action IDs are local to a head, so cross-head equal numbers are harmless.

Caller narrowing is part of the semantic schema, not implemented by the pure sort/normalizer.
It must use independent legal geometry and diversity rules; original teacher scoring is excluded.
If the actual generator adopts a different rule, update the schema/hash before exporting models.

## Python and hashing

```python
from nfs.policy.candidates import Candidate, build, try_build, teacher_index
d = build('strategy', [Candidate(6, 1, raw_retreat), Candidate(0, 0, raw_farm)], context=2)
# canonical ids [0,6], masks [0,1]; teacher need not be computed
annotation = teacher_index(d, teacher_stable_id)  # optional collection label only
```

`build` returns a Decision or raises CandidateBuildError with `.code`. `try_build` returns
`(Error, Decision)`, with an empty decision on errors. Python additionally rejects IDs outside
uint32 before conversion. `Decision.K/F/head/context/feat/legal/id` match the C++ meaning.

Python exports ACTION_HASHES(name->uint32), ACTION_HASH_BY_ID, ACTION_SCHEMA_HASH, HEAD_IDS,
HEAD_NAMES, FEATURE_NAMES and head_spec. `head_action_hash(name|id|head_dict)` recomputes FNV1a32
over canonical sorted-key ASCII JSON of the entire head object, excluding its own action_hash.
`schema_hash(optional_schema)` recomputes over the full top-level semantic object excluding the
top-level action_schema_hash and every stored per-head action_hash. Interpretations, feature
descriptions/units, option IDs, contexts and narrowing semantics all contribute to hashes.

C++ exposes `nnpc::kActionSchemaHash`, `kHeadActionHash[13]` and constexpr `action_hash(H)` (zero
for unsupported heads). `agents/v2_candidates/generate_schema.py` deterministically regenerates
the JSON and header constant/table block. Python recomputes and verifies stored hashes on import.
