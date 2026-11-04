# Target-head learner handoff

`train_head.py` is a CPU reference learner implemented by JOHNDOE to shorten R1's critical path. It has passed explicitly SYNTHETIC integration checks only. It is NOT a trained bot. R1 owns actual feature ABI, CNR2 parsing, runtime, data collection and broad evaluation. Adapt field names at ONE explicit boundary to this bundle; do not invent missing latents or reinterpret old CNR1 zero columns.

## Initialization before collection

Freeze the runtime observation/feature ABI file first. Its SHA256 is `--feature-abi` below. Run:

```
python train_head.py --init --feature-abi <64-hex-frozen-ABI-SHA> --out <new-initial-dir>
```

This creates `head.pt`, `head_weights.h` and an initialization-only report. The exact exported float32 parameter hash is stored in the checkpoint. Integrate THIS header with `optimized_head.h`; do not generate a different random initial head in the runtime. No game training occurs during initialization. Initial gate .02, zero residual query/far, nonzero randomly initialized keys/context. Seed defaults1104 and is explicit.

## Bundle

New directory with `manifest.json` and `data.npz`. NPZ loaded with allow_pickle=False. Float arrays should be exact float32 values actually consumed by the runtime after declared scaling; integral metadata must be integer dtype. N rows, K camps (normally10), P physical support indices (normally<=14). Final SLOT is far/fallback. Physical action IDs are mapped to local indices0..P-1; the mapping is metadata, never fed to learned layers.

- context[N,160], camps[N,K,16], features[N,K,4], native_logits[N,K+1]
- valid[N,K+1] bool/0/1, mapping[N,K+1] integral. Invalid mappings may be -1; valid mappings must lie0..P-1.
- reference[N], action[N] are LOCAL PHYSICAL indices, not original slot indices. Both must have valid slot support. Merge all duplicate/fallback routes in the policy probability.
- old_logp[N] is actual full physical mixture log probability of sampled latent action. It is NOT final executor action probability.
- game[N] contiguous0..G-1, body_id[N], decision_index[N]. The last counter is1..number of actual stochastic decisions for each game/body, without skips or duplicates. If existing collector counter includes deterministic guard skips, adapt with an auditable separate stochastic counter and validate original invocations separately.

Manifest required keys:

```
{
 "schema":"jd-head-training-adapter-v1",
 "architecture":"jd-target-head-160-16-4-v1",
 "data_origin":"engine",
 "feature_abi_sha256":"...",
 "policy_weights_sha256":"...",
 "executor_sha256":"...",
 "collector_source_sha256":"...",
 "wasm_sha256":"...",
 "engine_sha256":"...",
 "data_sha256":"SHA256(data.npz)",
 "camp_count":10,
 "physical_count":14,
 "episodes":[{
   "key":"unique complete-game identity with source/seed/side/opponent",
   "map_sha256":"actual map FILE SHA, matching evaluation manifest",
   "status":"terminated",
   "truncated":false,
   "all_decisions_present":true,
   "terminal_outcome":1,
   "decisions":1234
 }]
}
```

Keep full native collector provenance alongside this compact adapter manifest. Hash field presence is checked, but this learner cannot prove that a producer's provenance statements are true or recover records never emitted. Collector completeness proof remains necessary. All supplied episodes are required eligible: no silently dropping inconvenient games. All actual stochastic rows must be present. Decision-free completed games remain in the manifest with decisions=0 and contribute zero to the surrogate numerator while remaining in the game-count denominator. Do not omit them. An entire batch without stochastic decisions cannot update this actor and is refused.

The feature/executor schema must define exact ordering/scales, pub snapshot pairing and readiness/age. Stored context/camps must come from that effective snapshot, not a fresh float backbone. No privileged simulator state in actor inputs. Body death resets are not team-game terminal outcomes; this feed-forward MC learner does not need recurrent sequences or bootstrapped GAE.

## Update and continuation

```
python train_head.py --checkpoint <initial-or-current-dir>/head.pt \
 --data <fresh-bundle> --map-manifest <EVALUATION_MAP_MANIFEST.json> \
 --out <new-updated-dir> --epochs 2 --lr 0.0001 --clip 0.1
```

The map manifest is REQUIRED and every episode's map FILE hash must be in its training split. Collection parameter/feature hashes must match the loaded checkpoint. Initial probability replay tolerance2e-4. Parameters remain frozen in a rollout batch. Resume on FRESH data collected at the resumed checkpoint; never combine old batches from a different actor as if they were on-policy.

Default actor objective is game-SUM of decision clipped surrogates, averaged over games. Gamma1 outcome returns, fixed-zero baseline. All-win/all-loss batches can update; no same-batch centering that erases their signal. No critic/GAE or reward shaping is implied. Entropy is physical-policy entropy. Two full-batch gradient steps; chunks only accumulate the SAME total gradient to bound memory, not additional optimizer steps or sample reuse. Global grad norm .5. Adam state continues; resumed optimizer learning rate is preserved and reported along with requested rate. Changing LR on resume requires explicit optimizer-state policy, not pretending the flag overrode it.

After each proposed optimizer step, full physical KL(old||new) is measured; >.01 rolls back model AND optimizer and ends that update. Diagnostics report pre-step clip fraction, post-step KL, final float32 export metrics, parent/data/map hashes, actual11826params and accepted update count. Low KL is not evidence of strength. Headers export exact float32 values in input-major order.

Still required after learner passes real data: release export replay on ACTUAL new head rollouts; capture-vs-discard; complete-game return/collector audit; matched development games vs initial head/untouched native/fresh Agent2 and diverse opponents. The standalone synthetic checks do not replace these.

## Verification

`python check_learner.py` uses temporary SYNTHETIC data with an explicit test flag. Checks initialization/export, all-win update, optimizer continuation on fresh matching-policy data, stale-policy rejection, synthetic-data rejection in normal mode, KL rollback, truncated-game rejection. No game performance claimed. `check.py` and the release WASM export probe cover complementary math/export paths.
