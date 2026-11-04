# Instruction-budget RL: research and design review
Date: 2026-11-04. JOHNDOE research/design pass. Proposals below are unproven until measured in the actual engine.

## Main decision
Optimize playing strength under the real per-turn instruction budget, not parameter count, FLOPs, training GPU utilization or desktop latency alone. Measure the entire path: observation/preprocessing, frozen backbone, new head, sampling, logging, remaining executor and background work. Amortized savings and worst-turn cost are different.

Our current first learned head did not improve development win scores: initial16/30, learned16/30, native19/30. One tiny update is insufficient to judge the architecture, but roughly80% of head opportunities were fuel-skipped. R1's newer staged version cfe27aa3 reports75% coverage on ONE anvil case with parity-test weights; this is not yet independent broad evaluation or a strength gain.

## Papers and what they support
1. **Jacob et al., Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference (CVPR2018).** Jointly design integer inference and simulated-quantization training. For us: profile int16 SIMD versus float kernels, then emulate the actual rounding/saturation in the learner. This paper's hardware latency results do not predict Wasm fuel. Do not just quantize a trained actor and assume its probability distribution is unchanged.
https://openaccess.thecvf.com/content_cvpr_2018/papers/Jacob_Quantization_and_Training_CVPR_2018_paper.pdf

2. **Neil et al., Delta Networks for Optimized Recurrent Network Computation (ICML2017).** Exploit changes rather than recomputing stable activations. Nonzero change thresholds approximate the network and require suitable training; remembered values prevent accumulated subthreshold changes from disappearing forever. For us: exact changed-coordinate updates first; approximate thresholds only with measured action/value error and runtime-state replay. Their audio speedups are not ours.
https://proceedings.mlr.press/v70/neil17a.html

3. **Sharma et al., Learning to Repeat: Fine Grained Action Repetition (2017).** Learn action duration alongside action choice. For us: retain a strategic objective for a learned interval while cheap reactive control continues, with urgent interrupts. This means fewer neural decisions, not freezing movement/combat blindly. Duration and interruption semantics require a new temporal-action contract.
https://arxiv.org/abs/1702.06054

4. **Orenstein et al., Toward Agents That Reason About Their Computation, v3 October2026.** Give agents control over decision frequency and feedback about compute cost; tested on Atari. Particularly relevant to choosing when to invoke expensive policy inference. Their decision rate is a compute proxy, not our exact instruction meter. Our task still selects for winning under a hard budget; a cost-penalized objective would be a separately declared experiment, not a silent reward change.
https://arxiv.org/html/2510.22833v3

5. **He et al., AMC: AutoML for Model Compression and Acceleration on Mobile Devices (ECCV2018).** Hardware-aware compression/search rather than one uniform model-size rule. For us: compare structured widths/ranks using actual fuel and held-out play, not weight count alone. An RL compression controller is unnecessary overhead before a small explicit candidate comparison.
https://openaccess.thecvf.com/content_ECCV_2018/html/Yihui_He_AMC_Automated_Model_ECCV_2018_paper.html

6. **Rusu et al., Policy Distillation (2015).** Transfer stronger policy behavior into a smaller deployment policy. For us: train larger critic/teacher offline, then distill and RL-fine-tune a runtime student, validating the exported student by play. There is no currently demonstrated stronger teacher of ours to compress yet.
https://arxiv.org/abs/1511.06295

7. **Xu et al., DeepCache: Principled Cache for Mobile Deep Vision (2017).** Temporal reuse can reduce repeated inference, but its vision-specific cache matching is not directly our architecture. Useful supporting evidence for reuse; exact fixed-point cache semantics in our source are more directly actionable.
https://arxiv.org/abs/1712.01670

Scope: reviewed primary abstracts and relevant quantization, temporal-control and delta-update methods. No claim to have reproduced these papers or exhaustively surveyed the literature. Do not transfer headline speedup numbers to Battlecode.

## Agent2: fresh source audit
Fresh GitHub head remains6c2244e268e36aa37819e4f6002b8820ba21e48a. That commit only updates two result files. Relevant code remains afb43b886fc348006d48d4f4feb830c16cba5533. Fresh connected reads verified nn_infer.h blob8b8c6d87215f1d6aa41eb2e26e30e8913643044c and nnrec.cpp blob8dd93f8c11a63cd9e7a911b7a5aaae4c94172ed0.

- **Int16 SIMD fixed-point inference:** q15 rounded multiplication, saturating addition, eight int16 lanes per128-bit vector; input-major dense kernels skip zero inputs. Scaling is layer-specific, not a generic cast.
- **Incremental encoders:** kept_sum caches self/camp accumulators and updates changed raw inputs. Camp caches are keyed by physical group, so changing nearest-slot order doesn't mean another camp's embedding can be reused.
- **Incremental first trunk layer:** live_in applies changed-coordinate columns to a retained accumulator instead of rerunning the whole160-to64 matrix.
- **Periodic rebuilds:** encoder kQReset32 and trunk live_rebuild address accumulated rounding/state drift. Saturating fixed-point addition is order-sensitive; a fresh float forward need not reproduce it.
- **Folded pointer:** live_top computes transformed query r=Wk^Tq once; live_target uses16-wide dot products per camp, avoiding a fresh key projection for each candidate.
- **Fuel-aware scheduling:** nn_lazy_score estimates cost and reserves later-executor fuel, with separate enemy-proximity categories. Slow feature blocks refresh opportunistically. Optional cheaper-tier/holding branches exist, but are compile-flag dependent; do not say all experimental branches are active.
- **Feature priority:** A2_NN_FIELDS_FIRST delays neural scoring until walking-distance fields are ready, so the opening doesn't use unknown-distance features. Optional A2_NN_ENSEVERY restricts reevaluation when a target hasn't changed; again distinguish code option from confirmed active flag.
- **Selective network work:** live_target computes the target output; live_top only builds relevant hidden/query state. Full training-model output heads are not automatically evaluated every turn.

Pinned source:
https://github.com/Infosuii/neural-networkk-battlecode/blob/afb43b886fc348006d48d4f4feb830c16cba5533/research/agent2-neural/code/nn_infer.h
https://github.com/Infosuii/neural-networkk-battlecode/blob/afb43b886fc348006d48d4f4feb830c16cba5533/research/agent2-neural/code/nnrec.cpp

This is substantial existing engineering. Merely announcing quantization/caching would not distinguish our work. Our measured contribution so far includes the folded SIMD head kernel, exact SIMD logging, valid real-data learner and paired evaluation; none has yet produced demonstrated stronger play.

## Our proposed adaptations and independent ideas
These are our task-specific designs, not claims of new inventions in the wider field.

### A. Cheap intervention policy before expensive inference (highest-value new hypothesis)
Current full-mixture training computes q even when the sampled physical action is the reference. Instead use a genuinely cheap learned gate alpha(cheap legal state), sample z in{hold,invoke}, and only compute q_theta when invoke is selected.

Define the LATENT policy:
- z=hold: probability1-alpha; execute the fixed reference.
- z=invoke, group=g: probabilityalpha*q_theta(g); run the existing fixed downstream executor.

Log z explicitly. Its logp is log(1-alpha) on hold, log(alpha)+log(q_theta(g)) on invoke. If invoke also chooses the reference, it remains a different latent event. This is a valid latent-action formulation; it is NOT our current marginal physical-action logp. Do not replace marginal pi(ref)=(1-alpha)+alpha*q(ref) with1-alpha while retaining the old schema.

Benefits to test: expensive head and large context logs only on invoke rows; all gate rows retain cheap consumed inputs/counters. With a2% initial invocation gate,97-98% of expensive invocations might be avoided in expectation, but this is arithmetic intuition, NOT a measured total-fuel reduction: native reference work remains, and fewer q samples can hurt learning. Gate can learn beyond.5; no permanent low-intervention ceiling.

Cheap gate must not require computing the large head first. Candidate inputs: health/carrying/enemy proximity/target validity/age/remaining budget. Before sampling, a hard resource mask can disallow invoke when insufficient budget. Version/mask/log every decision. New joint-latent PPO/diagnostics/regularization required; existing marginal-head datasets cannot simply be reinterpreted. Compare learning efficiency at equal games and equal actual fuel, not only decisions.

### B. Reuse native representation plus low-rank learned residual
We currently add another160->64 projection although native already maintains related trunk state. Expose a precisely defined cached native preactivation/embedding. Learn h=relu(h_native+U(Vx)) as one candidate, with rank8, rather than a second full matrix. This retains a learned adaptation, not just frozen teacher imitation.

Projection multiply-add count:10240 for160x64 versus1792 for160x8+8x64, an82.5% theoretical reduction for THAT projection alone. Not a measured fuel reduction or equal expressive power. With biases and the existing remaining layers, one such head would have3386 parameters (native+head32275), rather than11826. Larger rank remains allowed. Zero-initialize one residual factor, not both.

Must train/evaluate a new architecture. Use actual cached native values and quantization scales, not reconstructed float features; account for cache age. Snapshot readiness and teacher-branch costs count. Compare strength, effective coverage and total fuel, not preference for larger/smaller count.

### C. Learn when to reconsider an objective; react cheaply between decisions
Jointly choose target and a1/2/4/8-round reconsideration interval. Continue reactive movement/combat and immediately interrupt on new nearby enemies, sharp damage, invalid target, failed path or a bank-critical carrying change. Those triggers use legal available observations and are tested across families. This applies temporal-abstraction research to our macro boundary instead of repeating raw movement blindly.

Duration is part of the action distribution; log chosen duration, actual elapsed time and interruptions. A learned interrupt is also a policy decision. Never assign one stochastic logp to every deterministic continuation turn. This requires fresh data and a new schema.

### D. Optimize whole-pipeline information timing
Include cache ages/ready flags in strategic inputs, and prioritize urgent self/enemy changes over low-value slow refreshes. Profile context age against carrying losses, target changes and enemy contact. End-of-turn staging moves cost; it doesn't erase it. Fast stale decisions can lose to slower fresh ones. Do not equate75% coverage on one map with a superior bot.

### Ideas I would NOT prioritize
- Unstructured weight pruning without a matching sparse Wasm kernel: fewer nonzero weights do not automatically skip instructions.
- Heavy attention/mixture-of-experts routers before profiling the cheap alternative.
- Counterfactual scoring/branch-and-bound to save a handful of16-wide camp dots while context/preprocessing dominates.
- Quantization after training with unverified probability mismatch.
- Compressing our present weaker learner and expecting distillation itself to create strategic skill.

## Execution order
1. Independently verify R1's staged implementation: exact actual-input replay with nonzero weights; multi-map coverage, context ages and complete total fuel; head0/staged/reference matched comparison.
2. Keep real on-policy training moving on the validated runtime. First tiny update had very small KL; diagnose effective intervention and gradient signal using training data, not repeated development selection.
3. Prototype cheap joint-latent intervention A as a separate bounded ablation. B is the next architecture candidate if staging/fuel remains limiting; do not interrupt a valid current batch for a large redesign.
4. Quantization-aware actor training and duration policy C after the first loop/ABI is stable. Distillation only after a stronger teacher exists.
5. Final selection remains broad opponents, fresh Agent2 snapshots, reserved maps and real ladder evidence. Training-only critic size need not fit runtime, but the actor, feature construction and control all must.

Report the actual fuel distribution (including upper tails and suspensions), background cost per round, effective neural coverage, observation ages, log volume and held-out paired win differences. Never infer Battlecode instruction savings from FLOPs or paper latency alone.
