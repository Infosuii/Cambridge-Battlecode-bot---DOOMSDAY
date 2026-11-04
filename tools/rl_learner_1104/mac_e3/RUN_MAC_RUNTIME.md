# RL execution checkpoint, 4 November 2026

This is development infrastructure and experimental policies, not a submission package or proof of competitive strength.

The compact CL1 lane now completes real engine games and two PPO update/checkpoint/re-export cycles. It has2482parameters, uses72k minimum fuel before invocation, an8-round physical-target hold with invalid-target events, and skips the initialization round. Every actual invocation is logged with its action/mask/probability, plus an actual monotonic counter; deterministic holds are separately logged and have no invented log probabilities. The actor replaces v92 target search. Main input ABI remains448int16, with explicit architecture/hidden width8 in the export.

## Reproduce the compact runtime

1. Copy `bots/claude-rlenv-1104/src` from pinned source commit `ccfea3421e0dd379e2929803804e067d2bea3749` into a **new** local bot directory `bots/jd-rl-e3-integration/src`. Do not edit the worker's branch or tree. `base_file_hashes.json` identifies the five changed source files before patching.
2. Apply `runtime_changes.patch` inside the new bot directory with `patch -p1` (paths inside the patch start with `a/src/`). A clean reassembly was verified byte-for-byte for all five files.
3. From the learner directory run `python export_runtime_actor.py mac_e3/latest_actor.json PATH/TO/BOT/src/clrl_actor_weights.h`. It validates dimensions and emits exact float32 constants and transposed SIMD matrices.
4. Build with the official cambc4.0.0 and wasi-sdk33. The SDK/engine used here is2.0.0. Run only local matches. No upload/activation/duel was performed.

The patch sets `CLRL_ACT=1` in this experimental bot. The unpatched baseline remains unchanged. Scalar-host and WASM floating accumulation may differ slightly: verify actual logged probabilities with the learner before using a game for PPO.

## Collect and train

`write_policy_shard.py` consumes a completed replay bundle/summary from this runtime, using a **local copy** of R1's `contract.py`, `collect.py`, `collect_policy.py` from the pinned commit. It additionally verifies the runtime counter rows and records budget/hold/source provenance. In this workspace the copied modules are in `mac-project/tools/rl_env_1104_mac_e3`. No failed row or fuel-failed episode is filtered into eligibility.

`train_ppo.py` accepts the resulting shard and exact source actor JSON, replays behavior probabilities, updates separate actor/critic networks, saves persistent Adam/RNG state and re-exports runtime weights/fixtures. The next rollout must use the new actor identity. `--resume` restores the continuing trainer and refuses a different policy. See `FIRST_PPO_RUN.md` for the column contract. `actor_hidden_size` distinguishes the actor's hidden width from optional logged `h0` storage width.

## Evidence and limits

`STATUS.json` contains the measured games and update lineage.28CPU tests pass. Two real PPO updates used819decisions from2games. The current post-update policy completed8checks over5maps,4001decisions, with no faults/fuel-outs/malformed/replaced decisions. It lost all8games against v92. One-step host stress covered1024real observations/random bounded hidden inputs and512recurrent steps; actual real-game probability replay errors were below0.000001.

The compact model is our own weak BC warm start and two tiny PPO updates. **It does not contain Agent2's pretrained weights.** The Agent2 student_i2m checkpoint (28889trainable parameters) was separately verified and now also reconstructed in its **native500-field bot/runtime** as the main pretrained starting point. It must not be silently loaded into the incompatible CL1 architecture. Native transfer/fine-tuning and paired-observation distillation are the next main route; the compact lane remains a testbed unless match results justify promotion.

No GPU training has run on Kaggle. No cloud billing was enabled. Larger offline training is not constrained to the compact runtime dimensions; any compression must preserve measured playing strength. No current evidence establishes an improvement over Agent2 or v92.
