# Target-head learner reference

This is checked learner-side math, NOT an integrated actor, trained model or fuel benchmark. See check_result.json; run `python check.py` with PyTorch. Initial head11826 parameters; native28889 + head =40715 deployed parameters if all these layers are used. No centralized critic counted.

Layers (bias included): context160->64:10304; query64->16:1040; camp16->16:272; four explicit camp features->16:80; far64->1:65; gate64->1:65. Total11826. Query and far residual start at zero; keys nonzero; gate starts.02 but may exceed.5. Initial learned residuals zero preserve the supplied native slot-logit distribution, NOT automatically the existing gate collector's physical q if its logits/mapping differ. Reproduce the chosen runtime boundary exactly before accepting initial equivalence.

Input contract to implement/freeze BEFORE collection:
- Actual frozen-runtime context160 and camp embeddings16, with explicit integer-to-float scale, cache readiness/age, ordering and hashes. These are not reconstructed fresh float-network latents.
- Exactly four declared legal per-camp features, named/scaled/clipped and versioned by the integrator. This reference does not prescribe unknown runtime feature offsets; do not invent inputs or feed missing features as zeros.
- Native slot logits, valid masks and metadata mapping every valid slot to a physical action index; last slot is the far/fallback. Duplicate routes aggregate AFTER slot softmax. Numeric physical IDs index the output only and never enter learned layers. Candidate logits preserve native boost/fallback semantics at the selected boundary.
- Teacher reference physically present in valid support. Fixed downstream executor remains part of the environment, with sampled action and execution associations retained.

The current CNR1 eight-feature gate dataset cannot train this head: it lacks the actual runtime context/camp inputs. Integrate a new versioned complete release schema and collect fresh data; do not reinterpret old zeros or reuse incompatible on-policy logp. Measure logging volume/fuel and every invocation, capture-vs-discard and export replay. Keep all parameters frozen during each rollout batch. Log all consumed inputs; exact hex is the current correctness baseline, optimize encoding only with verified replay.

The checks cover full physical mixture probability including teacher/far aliases, legal masks, row permutation equivariance, finite-difference gate gradient, nonzero query gradient at initialization and key/feature gradient after one step, override ability, missing support rejection, and actual parameter count. They do not cover C++ export, arbitrary production inputs, fuel or playing strength.

This is the first local target head. It does not remove the native nearest-ten action-support limit or add strategic recurrence. Those remain measured follow-on ablations, not reasons to delay a valid first substantial training run. No permanent parameter cap.
