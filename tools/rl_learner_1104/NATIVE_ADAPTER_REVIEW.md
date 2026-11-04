# Native RL adapter review: frozen runtime features first

Reviewed 2026-11-04. This is an implementation design review, not a measured improvement.

## Verified source

Pinned Agent2 source: afb43b886fc348006d48d4f4feb830c16cba5533.

- [nn_infer.h](https://github.com/Infosuii/neural-networkk-battlecode/blob/afb43b886fc348006d48d4f4feb830c16cba5533/research/agent2-neural/code/nn_infer.h), blob 8b8c6d87215f1d6aa41eb2e26e30e8913643044c.
- [nnrec.cpp](https://github.com/Infosuii/neural-networkk-battlecode/blob/afb43b886fc348006d48d4f4feb830c16cba5533/research/agent2-neural/code/nnrec.cpp), blob 8dd93f8c11a63cd9e7a911b7a5aaae4c94172ed0.

Q16 Live at nn_infer.h:355 stores integer context x, accumulated trunk state acc0, pointer r and per-camp embeddings ec. live_top at line 541 computes the pointer from retained acc0. live_target at line 556 computes each camp logit from dot16(ec[i],r)+c0 with scale 1/(65536*sqrt(16)). Context width in the exported student is 160; camp embeddings are 16 wide.

add_col16 at line 371 uses saturating int16 additions and rounded multiplication. kept_sum caches are rebuilt periodically (kQReset=32); trunk sums are rebuilt separately. Thus raw-feature replay into a fresh float network is not guaranteed to recover a deployed probability, even when observations are aligned in time. A purely illustrative saturation example: sat(sat(30000+10000)-10000)=22767, while sat(30000+sat(10000-10000))=30000. This proves order can matter; it does not claim those particular activations occurred in a match.

nnrec.cpp:788 nn_lazy_score has explicit field-ready, fuel and optional contact/hold gates. The live blend sampler at line 1068 reads nn_lo.target, boosts the v92 slot, samples inside debug_block, then maps valid camp slots to physical groups; other outcomes fall back to v92. Line 1082 subsamples unchanged actions unless configuration makes every invocation retained. Those logs alone do not certify a complete production rollout.

## Recommended first adapter

Freeze the entire native backbone, preprocessing, quantization, cache update schedule and baseline executor. Treat the actual runtime outputs as observations for a newly versioned trainable head. This makes replay of that head well defined without differentiating through every rounded cache update. It does NOT permit changing the backbone and pretending the old logged latents came from the new backbone.

At every admitted policy decision log:
- monotonic episode/body decision counter and round, actual delta to next decision;
- reference physical action after the frozen native executor, not just v92 anchor;
- ordered physical candidate IDs, validity and canonical mapping of the far/fallback slot;
- exact frozen native target logits (before any sampled-rank mutation), actual quantized r/ec and context x if consumed;
- context/camp freshness and ready flags, previous effective action/intent, legal observation information;
- sampled policy action, effective physical action, old logp and random counter;
- policy/backbone/executor hashes, masks, timing, terminal/truncation and memory reset information.

Only log inputs the head actually consumes; don't inflate every row with an unused full runtime snapshot. Keep enough debug trace separately to audit cache transitions. When a policy gate skips a decision, record the skip/hold reason and advance round timing without inventing a stochastic logp. Compare debug collection actions and release actions under the same seed.

### Preserve initial competence explicitly

A softmax of teacher logits is not the same bot as the deterministic teacher. First evaluate the exploration boundary against the untouched native baseline.

One auditable initial boundary is a mixture:
pi(a|h) = (1-epsilon) * indicator[a=reference(h)] + epsilon * softmax(masked residual/native logits)(a).

Merge candidates mapping to the same physical action. The head's probability for the reference includes BOTH the teacher mass and any exploratory mass assigned there. Record and replay this full probability. During each rollout/update, epsilon and the reference executor are fixed and versioned. Suggested development comparison is epsilon=0.02 versus 0.10 at macro decision points; these are experimental choices, not known good settings. They cannot be extrapolated to an every-turn intervention rate. If a later run changes epsilon, collect a new batch under that version.

At evaluation compare the declared stochastic policy AND any intended deterministic export separately. Argmax export is a different policy and requires its own matches. Do not present a training mixture's results as deterministic deployment results.

Alternatively use a latent-action policy with its fixed executor, as explained in the main experiment spec. Don't mix schemas.

### Candidate capacity, without a tiny ceiling

The first learning test can use a context160->64 ReLU, query64->16, camp16->16 key and four explicit per-camp features projected4->16, plus separate far/gate outputs. With biases in every listed linear layer, this illustrative non-recurrent head is 11,826 parameters; native28,889 + head11,826 = 40,715 total. The frozen native teacher's memory remains included in the deployed total. If the gate output is unused, omit it and report the smaller actual count. This is a candidate to profile, not an imposed architecture.

Zero-initialize final residual outputs to begin near the declared reference distribution. Avoid zeroing both factors of a bilinear pointer, which can make its initial gradients zero. Use nonzero keys and a zero residual query (or a separate zero-output final layer). Preserve the non-residual teacher logits outside that branch.

Actor capacity can then grow with recurrent strategic memory or a larger offline teacher, conditional on held-out strength and measured fuel. A training-only centralized critic has no runtime parameter/fuel charge. Frozen context cannot reveal enemy information that the runtime never observed: critic privileges must not leak into actor features.

## Acceptance evidence before the first long run

1. Untouched reference reproduction with pinned source/model/flags and real fuel.
2. Exploration-only baseline, separating behaviour loss from learning gain.
3. One complete replayable head episode, every actual invocation counted.
4. Head probability replay max error <=0.0002, including duplicate/fallback mass.
5. Actual export/release action parity and measured added fuel; no assumed capacity fit.
6. One small gamma=1 terminal-win training batch, then fresh development evaluation against the identical exploration-only baseline and the untouched reference.
7. If improvement is absent, diagnose distribution, intervention rate and credit assignment before spending the remaining GPU budget.

R1 owns implementation and most runs. JOHNDOE reviews the selected schema and first replay report. This route reduces an engineering obstacle; it does not by itself establish an advantage over Agent2.
