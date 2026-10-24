# Direct-policy NFS2 records and offline loss path

Worker: inherited configured Codex child agent `tactics` (reassigned from legacy E implementation/review). Exact
inherited model ID was not exposed; no Opus run is claimed. No actual collection, game, optimizer step, training,
submission, browser or desktop operation was performed. Every new test fixture is labelled synthetic.

## Delivered

| File | Purpose |
|---|---|
| `bot/src/nn_policy_log.h` | Pure bounded NFS2 writer; separate magic/version/checksum; context, decision and execution acknowledgement; constant-initialized arrays and circular queue; no SDK/model/NFS1 dependencies. |
| `python/nfs/policy/records.py` | Strict binary/base64 roundtrip, version/checksum/schema/bounds/finite/canonical ID/mask/teacher validation. |
| `python/nfs/policy/dataset.py` | Compact-v2 observation adapter, identity-safe context/decision/ack joins, actual execution eligibility masks, behavior logp validation, group partition checks, explicit option intervals, padded tensor collation and checksummed NPZ/manifest. |
| `python/nfs/policy/losses.py` | Direct masked imitation, selected logp, PPO clipping/entropy/KL metrics, optional critic regression, variable-gap SMDP returns/GAE. Computes loss only; no optimizer/job entry point. |
| `tests/cpp/test_policy_records_roundtrip.cpp` | Synthetic native writer/queue validation plus128 varied direct-policy sample fixtures using the existing pure masked sampler. |
| `tests/python/test_policy_records_roundtrip.py` | Codec/dataset/gradient/parity/execution/option/group/roundtrip tests. |
| `agents/v2_records/WIRE.md` | Exact frozen wire and C++ API contract for root runtime integration. |

Context payload follows the lead's compact v2 observation change:173 normalized float32 values,692 bytes,
observation schema0x831AC800, decoded using `nfs.policy.observation.encode_bytes`. Legacy RawTurn/NFS1 is preserved
and is never decoded as v2. The codec keeps context opaque; the dataset validates normalized observation layout,
finite values and padding through the dedicated adapter.

## Runtime contract

Namespace `nnp_log`. Root enqueues a context with `Header.decision_id=0`, then independent canonical direct-policy
decisions with nonzero call IDs, then acknowledges the exact dispatched intent/result with the same header and
option identity. Header.action_hash is the combined policy-v2 action schema hash, not a per-head hash.

`DecisionRec` has no prior or teacher-feature input. `teacher=-1/teacher_id=kNoAction` is absent. A computed but
unrepresentable teacher annotation keeps its explicit stable ID with teacher=-1; it is counted and excluded from
imitation. A representable teacher index, including index0, is valid only when explicitly supplied and matched to
the same legal stable ID. It never reorders candidates or changes model inputs.

The32768-byte circular queue uses bounded copies with no compaction. Invalid inputs are refused and counted;
overflow is counted and bounded. Runtime must gate `flush_one` by measured `next_line_bytes` cost and a tail reserve
after play_turn. Header logging itself does not query or override engine fuel. Fuel accounting fields are supplied
by runtime; they are not claimed to be engine-measured by this worker.

## Offline execution eligibility

- PPO accepts only an acknowledged direct-policy start, sampled under the exact logged logits, reason0, with
  present same-turn context and matching executed stable ID/source/option. Missing/pending ack, guard refusal,
  override, different ID/source, continued option, deterministic argmax, teacher fallback and safety override
  never silently enter the actor ratio.
- A guarded intent counts only when its decision explicitly declares a defined option with nonzero option ID and
  the acknowledgement uses that same defined option. A generic failed guard is not relabelled as success.
- Imitation requires a representable legal teacher annotation actually executed or defined by the recorded stream.
  Unexecuted counterfactual labels are excluded by default. Teacher collection must therefore deliberately execute
  its annotated label; direct-policy candidate0 is never manufactured as a teacher label.
- Continuations share explicit option/episode/champion/head identity and never create additional actor starts.
  Variable-duration return/GAE helpers discount by actual round gaps, not by the number of log lines.
- A collector must supply episode and provenance group IDs plus engine version and synthetic status. Dataset joins
  reject duplicate decisions, duplicate/final acks, snapshot/schema/round conflicts, and invalid logp. Group splits
  reject overlap; collectors remain responsible for assigning groups that include near-duplicate bot/team/map provenance.

## Verification

Command actually run from ROOT, with `PYTHONPATH=ROOT/python`, `TMP=TEMP=ROOT/artifacts/tmp`:

```
python -m unittest tests.python.test_policy_records_roundtrip -v
```

Result before the final added sampler/SMDP assertions: **15/15 pass**. The final test rerun is recorded in the
completion message. Checks include:

- Native C++ context/decision/ack -> Python decode -> compact observation -> dataset/tensor path.
- Native masked sampler and Torch logp agreement within2e-6 across128 synthetic fixtures: eight heads x K1..16,
  varied masks/context and choices; no teacher prior or teacher index convention.
- Optional/absent/outside teacher IDs; no implicit teacher0; illegal teacher/selected actions rejected.
- NaN/Inf, noncanonical/duplicate IDs, invalid binary mask, bad dimensions/context/version/checksum/schema rejection.
- Queue wrapping500 times, bounded overflow and three writer invalid-input rejections.
- Exact execution eligibility, pending-to-final ack, missing/mismatched ack, safety/fallback/continuation/argmax masks.
- Source separation, duplicate stream rejection, grouped partition leakage rejection and checksummed dataset roundtrip.
- Actual untrained `DirectPolicyNet` synthetic forward/backward gradient flow, masked illegal gradients0, empty-row
  finite gradients, PPO ratio exclusion, critic gradient, variable-gap returns and GAE. **No optimizer step.**

## Limits

No real NFS2 record has been collected by this worker, and no official Wasm/fuel claim follows from native tests.
Root owns runtime integration, legality/execution acknowledgements, model checks, source control-rate telemetry,
official build/off-path identity, and engine smoke/fuel verification. Current wrappers must not omit acknowledgement
or silently replace a sampled action and still call it executed. Dropped records cannot be used to inflate coverage.

This is an executable dataset/loss library, not authorization to train. Legacy `nfs.train`/CLI remains NFS1-oriented;
any full later v2 training driver must explicitly use these adapters/losses, model interpretation2, grouped provenance,
and the existing training authorization/deadline/checkpoint controls. No claim is made that legacy training commands
already run the new direct-policy path. A critic target may be supplied to `critic_loss`; optional belief/carry-risk/
leaf models are outside this milestone and no fictitious targets are added.
