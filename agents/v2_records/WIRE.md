# NFS2 direct-policy record protocol

NFS2 is separate from legacy NFS1. No weights, records or teacher-index conventions are reinterpreted.
One stdout line is `NFS2 <RFC4648 padded base64>\n`; NUL padding from engine bundles is ignored by the parser.
All integers and float32 words are little-endian. Payload maximum8192 bytes; queue32768 bytes; no heap allocation.

## Common header and integrity

| Offset | Type | Meaning |
|---|---|---|
|0|u32|magic0x3253464E, bytes NFS2|
|4|u16|version2|
|6|u16|kind0 context,1 decision,2 execution acknowledgement|
|8|u32|total payload bytes including trailing checksum|
|12|u32|observation schema hash, nonzero|
|16|u32|combined direct-policy action schema hash, nonzero|
|20|i32|actual game round, nonnegative|
|24|u32|champion handle|
|28|u32|snapshot identity, monotonic/unique per champion as assigned by runtime|
|32|u64|decision/call ID;0 for context, nonzero for decision/ack|

Every record ends in u32 FNV-1a32 of **all preceding payload bytes**, with basis2166136261 and multiplier16777619.
The common header is40 bytes. Collection metadata supplies the episode/match identity; a decision key is
`(episode_id, champion, decision_id)`, and a snapshot key additionally includes its observation/action schema hashes.
Do not concatenate games while discarding their episode/provenance identities.

## Context: kind0

`u32 raw_bytes` followed by exactly `raw_bytes` opaque observation bytes. For the first direct-policy milestone these
are173 **already normalized** little-endian float32 values (692 bytes), under the new compact v2 observation hash.
They are **not** legacy `nnobs::RawTurn` bytes. `nfs.policy.observation.encode_bytes` validates length and finite
values and returns the173-vector. Runtime owns which legal observation is captured and must enqueue it before the
decisions that refer to that snapshot. Snapshot encoding does not include teacher annotations or future targets.

Context payload size is48+raw_bytes, normally740 bytes.

## Decision: kind1

The52-byte fixed body, following the common header:

```
u16 head, u16 K, u16 F, i16 chosen, i16 teacher
u8 context, u8 sampled, u8 source, u8 flags, u16 reason
u64 option_id, u32 selected_id, u32 teacher_id, f32 behavior_logp
u32 candidate_fuel, u32 observation_fuel, u32 inference_fuel, u32 log_fuel
```

Then arrays in order: `u32 id[K]`, `u8 legal[K]`, `f32 logits[K]`, `f32 feat[K*12]` row-major. No prior or
is_teacher feature exists. K<=16, F=12, call context0..3. Stable IDs are strictly ascending and unique, independent
of the teacher;0xFFFFFFFF is reserved as no-action/annotation-absent. Head IDs are the legacy identities1 strategy,
2 objective,3 role,4 bank,5 shop,6 move,7 combat,8 engage. No optional auxiliary head is implied by this protocol.

`chosen=-1` represents no policy action, permissible for teacher fallback/safety/continuation failure records.
Direct-policy source requires an actual legal chosen index and matching selected stable ID. Candidate0 has no
teacher meaning. `teacher=-1, teacher_id=0xFFFFFFFF` means the teacher was not computed. A computed teacher outside
the independent set is `teacher=-1` with its explicit stable `teacher_id`; it is counted as unrepresentable and
never silently made candidate0. A represented teacher index must be legal and match `teacher_id` exactly.

Sources:0 direct_policy,1 continued_option,2 teacher_fallback,3 safety_override. Only direct-policy starts may be
sampled. A sampled record's logp is the chosen action's true probability under the exact logged masked direct
logits; deterministic argmax records use sampled0 and behavior logp0. All features and legal logits must be finite;
illegal logits may be finite or-negative-infinity, never NaN/+infinity. Masks must be binary. Invalid input is
refused by the writer and counted as `g_invalid`; parsers raise `RecordError`.

Flags: bit0 option_start, bit1 option_end, bit2 defined_guarded_option. Any option flag requires nonzero option_id.
A continued option retains its initiating ID/source lineage and is excluded from fresh PPO ratios. An execution
guard failure is not automatically a valid sampled action: only an explicitly declared guarded option can use the
defined-option acknowledgement outcome below. Fuel fields are runtime-supplied accounting, not measured constants.
Log fuel may be an actual measured preceding enqueue/ack cost or an explicit estimate; reports must label which.

Decision total size is96+57K bytes, maximum1008.

## Execution acknowledgement: kind2

The24-byte body is:

```
u32 executed_id, u8 outcome, u8 source, u16 reason, u64 option_id,
u32 action_fuel, u32 log_fuel
```

Outcomes:0 pending,1 executed,2 defined_option,3 guard_refused,4 overridden,5 failed. Header identity, option_id and
final source must match the decision being acknowledged. A pending ack may be followed by one final ack; multiple
final acks are rejected by the dataset join. A missing ack remains missing and is never assumed successful.

For outcome1, executed_id identifies the actual dispatched intent. For outcome2, it identifies the selected
**declared** guarded option, whose deterministic executor may produce the specified no-op/refusal outcome. Do not
label an unrelated teacher/safety substitution as a successful defined option. Guard refusal3, override4 and failed5
are excluded from the actor ratio. A changed source or different executed ID is also excluded.

Total execution record size68 bytes. Runtime must retain each pending call's header/schema/snapshot metadata until
acknowledgement and call `enqueue_execution` after its deterministic executor determines the outcome.

## C++ API

Pure header `bot/src/nn_policy_log.h`, namespace `nnp_log`:

```
Header h{obs_hash,action_hash,round,champion,snapshot,decision_id};
ContextRec context{h,raw,raw_bytes};  // h.decision_id=0
DecisionRec decision;               // see field names in header, defaults teacher=-1/teacher_id=kNoAction
ExecutionRec execution;             // acknowledgement, same nonzero decision ID
bool enqueue_context(const ContextRec&);
bool enqueue_decision(const DecisionRec&);
bool enqueue_execution(const ExecutionRec&);
bool queue_empty(); int next_bytes(); int next_line_bytes();
bool flush_one(FILE* out=stdout); void reset();
```

Root runtime fuel-gates `flush_one` **after play_turn** using next_line_bytes plus its measured encoding/write
allowance and tail reserve. No game/SDK/fuel calls exist in the pure writer. Enqueue ring writes are bounded and
require no compaction. Full queue increments g_dropped; invalid input increments g_invalid; short writes increment
g_write_failed and discard that record rather than duplicate a partial line. g_queued and g_written count records.
The root runtime's per-turn limit and source/override accounting must expose any drops.

## Offline acceptance

`nfs.policy.records` checks magic/version/length/checksum/schema identities, bounds, finite values, canonical IDs,
legality and optional teacher integrity. `nfs.policy.dataset` joins by explicit episode/champion/call/snapshot:

- PPO: source direct, sampled, reason0, context present, final matching executed acknowledgement or matching
  explicitly defined guarded option; logged logp must match logged masked logits within2e-5.
- Imitation: an explicit representable legal teacher label whose stable ID was actually executed/defined by this
  stream; absent/outside labels and unexecuted counterfactual teacher choices are excluded.
- Continuations, argmax-only records, teacher fallbacks, safety overrides and missing/mismatched execution are never
  silently promoted into on-policy actor samples.
- Independent episode and provenance-group IDs prevent accidental train/validation stream splitting. The collector
  remains responsible for assigning groups that also respect bot/team/map near-duplicate provenance.

All current tests are synthetic. No collector or training job was run by the record worker.
