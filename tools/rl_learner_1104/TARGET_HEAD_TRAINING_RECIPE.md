# First substantial target-head run

This refines WINNING_RL_EXPERIMENTS after the release logger proof. It is an experiment, not evidence of strength. R1 owns implementation/execution; no new long engineering prerequisite before the first valid head batch.

## Start and objective

Use the optimized11826-parameter head from target_head_reference, frozen native28889, frozen/versioned executor. Final count40715 if all layers used. Integrate exact runtime observations and a NEW complete release schema first; CNR1 cannot supply missing context/camp inputs. Export/probability fixtures are synthetic and do not replace first real episode replay. Keep collected actor and all parameters fixed throughout each batch. Do not strip logging at evaluation and call it the same runtime.

First16 complete TRAINING-split games are a bounded mechanism run, both sides and several map families. Report actual decision counts, wall time, logging bytes, fuel-outs and faults. Check every map SHA against the manifest. Do not tune on development games or use confirmation_reserved. One opponent is enough for a mechanism proof but NOT a broad training campaign or generalized-strength claim. The present strong-opponent inventory remains limited: v92, frozen native Agent2 and own near-native snapshots are correlated. Historical public bots failed current-fuel smoke and must not inflate headline breadth. Build a genuinely broader versioned pool/current-team evidence before committing a long GPU budget; disclose any interim departure from the league proportions in the main plan.

Gamma1 complete-game MC, team terminal win/draw/loss+1/0/-1. Body death is not team termination. Every admitted stochastic action of every body participates; fixed executor actions are not additional stochastic actor samples. A game's actor surrogate is the SUM over its decisions; average over games. Do not average each game by its number of decisions and silently change the objective. Batch-size normalization by one common constant is only an optimizer scaling choice; record it and learning rate.

Initial head Adam1e-4, PPO clip.1,2epochs, gradient norm.5; these are declared development starting settings, not Battlecode-proven optima. Fresh batch after each update cycle, no indefinitely recycled initial dataset. Preserve optimizer/checkpoint/ABI/source/engine/normalization/executor provenance on resume; verify old probability at the actual collection checkpoint. First run should not be delayed for recurrent memory, a large critic or a hyperparameter sweep.

## Baseline and credit assignment

For the first head batch, zero baseline is an acceptable simple reference. Prefer a baseline frozen from PREVIOUS independent training games once enough exist. Do not require mixed win/loss to make the algorithm run: all-win outcomes contain a score-function signal with a fixed zero baseline, whereas subtracting that same batch's all-win mean erases it. Refusing an all-equal batch is a guard specific to the current batch-centered gate learner, not a general impossibility of learning. Record the estimator. Do not train a value network on each episode's own final result and then reuse an overfit prediction as if it were independent of that episode's sampled actions.

Next variance ablation: a training-only history-aware value baseline. Fit to complete-game MC outcomes on prior batches; freeze/detach predictions for actor updates. Alternatively whole-GAME cross-fitting can be tested, never splitting individual decision rows from the same game between fit and prediction folds. Evaluate held-game prediction error/calibration and measured gradient variance, not training MSE alone. This critic has no deployed parameter/fuel cost. Its legal observation/history inputs and normalization must be versioned separately from the actor. Actor export remains free of privileged simulator information.

A state-only centralized critic is not automatically a solution under partial observability and stale memory. Lyu et al. analyze potential bias/variance disadvantages and motivate history-state critics: https://arxiv.org/html/2408.14597v1 . This is a reason to test critic choices, not a claim that the currently proposed MC baseline is biased or that every centralized critic fails. Keep actual MC returns as the first numerator; introducing bootstrapped TD/GAE is a separate versioned estimator with chronology/death/truncation requirements.

COMA uses an action-marginalized counterfactual baseline for individual credit: https://arxiv.org/html/1705.08926v3 . Its synchronous StarCraft setup is not our asynchronous macro/executor environment. Do not bolt a guessed Q-value for unchosen groups onto current shards and call it COMA. Consider only after a reliable joint-history/action critic and matched-budget value-baseline comparison exist. Neither paper guarantees improved Battlecode learning.

## Distribution diagnostics and regularization

Compute distributions on legal PHYSICAL support, after merging alias/fallback routes. Full mixture pi=(1-alpha)delta_ref+alpha*q. Include both routes when chosen=reference. Gate may exceed.5; otherwise greedy full-mixture export can never override reference. Report stochastic and greedy deployment separately and evaluate the intended one.

At initialization, zero residual query/far preserve supplied native SLOT logits; this is not sufficient to claim equality with the old physical-q boundary unless boost/mask/mapping/reference match. Nonzero keys allow query gradients; first-step zero key gradients are expected with zero query, not a broken optimizer.

Use stable log-probability computation; reject invalid support/nonfinite inputs. Avoid arbitrary clipping/floors that alter collection probabilities without defining the same runtime policy. Source and export arithmetic order may differ, so every chosen logp must replay within2e-4 on the actual new schema. Synthetic32case export maximum error8.8e-7 is encouraging but not runtime coverage.

Measure FINAL post-update/post-float32-export full-support KL(old||new) where feasible, not just pre-step chosen-action logp differences. Clip fraction, entropy of physical policy, alpha distribution, non-reference choices, teacher/far aliases, support size and approximate sampled KL are separate named diagnostics. Large KL or broken replay stops that update; use a saved previous checkpoint. Do not equate low KL with strength. A reference penalty must specify full-support reference or finite teacher CE; KL(student||deterministic teacher) is infinite for overrides. Avoid a permanent hard teacher tether.

## Decision after first cycles

Compare initial logging head vs trained logging head vs untouched native on IDENTICAL development cells with all failures/fuel-outs retained. Paired family-clustered differences, not only separate win rates. Fresh Agent2 pin at the promotion milestone; retain older challengers. If no credible gain, inspect actual override rate, policy changes, reward/gradient variance and objective coverage before merely enlarging the network or sweeping learning rates.

Gate evidence is informative but not a reason to stay with9trained parameters. Conversely40715total is not a permanent cap or a promise of fuel feasibility. Head arithmetic alone measured33.6kfuel in one isolated optimized probe, excluding native/logging/softmax; integrated decision cost must decide scheduling/optimization. Wider global target support, recurrent strategic memory, upper-trunk tuning and larger training-only teacher/critic are subsequent controlled experiments. Broad ladder superiority still requires the full validation in WINNING_RL_EXPERIMENTS.
