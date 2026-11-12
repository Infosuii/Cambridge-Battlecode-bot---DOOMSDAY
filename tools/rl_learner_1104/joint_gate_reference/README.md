# Joint-latent conditional-compute reference

This is a checked mathematical/sampler reference, not an integrated Battlecode bot or measured speedup. It supports proposal A in INSTRUCTION_BUDGET_RESEARCH.md. R1's current cached-query/memoisation runtime work remains the immediate experiment.

A cheap gate samples hold/invoke before expensive policy inference. Conditional q is a masked distribution over physical groups, with all slot/fallback aliases already merged. Hold executes the fixed reference. Invoke may also choose that same reference group, but it is a different LATENT event. Log the branch, not merely the resulting physical action.

- hold logp = log(1-alpha)
- invoke logp = log(alpha)+log q(chosen)

Summing both routes recovers the marginal reference probability. Enumerated expected task gradients match the marginal policy gradient; sample-gradient variance need not match. PPO clipping on joint-latent ratios is a NEW surrogate and action schema. No claim that it equals clipping marginal-action ratios. Existing CNR2/CNR3 physical-action datasets cannot be relabelled as these branch choices.

The callback receives only invoked indices. Admitted hold rows consume/log cheap gate inputs, reference, branch probability, actor/executor hashes and counters; they do not need fictional uncomputed large-head inputs. Invoke rows log all expensive consumed inputs, mapping/masks, branch and group likelihood, and execution association. Record EVERY stochastic gate decision, not only overrides or invocations. Resource-disallowed rows use the deterministic reference, have no stochastic logp, and remain in skip/coverage/complete-game accounting. The guard mask is decided before the gate draw from available fuel and a declared conservative cost/reserve.

The gate must not run the large context projection or compute q first. Avoid unconditional added-head background staging on hold turns, otherwise proposed savings may disappear. Native reference computation still costs fuel. Larger invocation rates increase conditional-policy data but may damage behavior/runtime; gate has no permanent small cap. Count actual total fuel, overrides, q examples, logging and strength at equal rollout budgets.

If regularizing, distinguish Bernoulli gate entropy/KL from conditional q entropy/KL. The current exact full-marginal KL monitor cannot be computed on hold rows without q; use a declared joint estimator or explicit diagnostic inference, never pretend absent q values were observed. A training-only diagnostic that executes q changes runtime if charged, so separate it from the deployed collection artifact.

`check.py` verifies marginal/latent expected gradient equivalence and score-function gradients by enumeration; reference alias routes; no callback invocation on holds; deterministic resource masks; finite recorded likelihoods for admitted samples. Tests use synthetic probabilities only. `result.json` reports those checks. Actual C++ export/replay, complete collection, fuel and paired gameplay remain unverified.
