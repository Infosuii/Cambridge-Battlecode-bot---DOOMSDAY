# Next architecture experiment: global objective coverage

This is a later ablation, not a prerequisite for the first native-head training update.

Verified local SDK audit: 86 maps; 71 have more than ten physical camp groups; median19.5; maximum51. Pinned native source afb43b886fc348006d48d4f4feb830c16cba5533, research/agent2-neural/code/nnrec.cpp:15 fixes kC=10. Its nearest-group feature block and far-score blend allow local pointer choices plus the baseline's outside-group anchor; the learned head cannot freely name any omitted physical group.

Inference: this is a candidate-coverage limit, not evidence that it causes the observed losses. More hidden units or recurrent state alone cannot select an action absent from the action support. Evaluate this hypothesis after the initial learning loop works.

Proposed ablation: retain the competent native policy as a frozen reference, add a separate all-group encoder/pointer with shared weights, and compare it to the ten-nearest head at equal rollout budgets and measured fuel limits. Use legal observed/remembered dynamic information and cached static group facts; carry information age. Do not expose simulator-only camp/enemy state to the actor. Include own committed objective, team commitments only where legally available, path-distance/travel costs, reward/respawn information, carrying value and nearby risk. This requires a NEW feature/action ABI and fresh rollouts, not reshaping the existing checkpoint.

Start with shared per-group embeddings and permutation-invariant pooling, recurrent team/own context if justified, and an equivariant pointer score over physical group IDs plus explicit non-farming macro options. The all-group pointer need not multiply weight count by the number of camps: weights are shared, while runtime and memory still grow with entities. Do not assume the 51-group version fits fuel. Profile periodic strategic decisions and incremental/cached updates, preserving actual timing in the learner. Avoid full quadratic attention until a cheaper scorer is shown inadequate.

Architectural grounding: [Deep Sets](https://arxiv.org/abs/1703.06114) studies invariant/equivariant models for unordered inputs; [Pointer Networks](https://arxiv.org/abs/1506.03134) provides variable-size output selection over input elements. These motivate the entity/pointer design, not a claim of Battlecode superiority. The native baseline already uses related pooling/pointer ideas; the proposed difference is broader support and measured strategic context, not merely renaming an existing architecture.

Required diagnostics: candidate coverage and outside-ten selection frequency; physical ID stability under row reorder; shuffled-input distribution equivariance; exact legal masks; chosen-target executability; cost/decision and update ages; export parity; sample efficiency and held-out win differences against the local-head baseline. Different action support means a new on-policy run, not PPO reuse of old actions under an incompatible distribution.

No map IDs, opponent IDs or hand-tuned routes to fit Agent2. Do not select architecture from reserved-map performance. R1 continues the current collector/head first; JOHNDOE owns this hypothesis and experiment review.
