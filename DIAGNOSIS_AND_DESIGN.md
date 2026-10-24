# Diagnosis and design decisions

This checkpoint is an untrained framework build. No new match-strength or training result is claimed. The original
failure evidence is specified in [USER_REQUEST](agents/USER_REQUEST.md#2-learn-from-the-actual-failures); current
engine sensitivity evidence is [neutral_equivalence_bisect.json](evaluation/evidence/neutral_equivalence_bisect.json).

| Original failure point | Assessment | Design response and remaining proof |
|---|---|---|
|1. Zero correction changed play | **Confirmed integration effect.** Current bisection shows even a few dozen pre-decision fuel units can shift teacher choices. | Teacher choice computed first, bounded admission and deferred output; teacher_exact must be byte-identical. Neutral_real is an overhead control, not an equivalence claim. Engine costs remain pending. |
|2. Pooled selection concealed original regression | **Confirmed by prior results.** | Per-opponent gate plus map-cluster uncertainty; original regression cannot be traded for pooled gains. Synthetic gate tests reproduce the failure. |
|3. More training stopped helping | **Confirmed plateau in prior run; cause uncertain.** | Bounded experiments, persisted deadlines, checkpoint/optimizer pairing and independent selection partition. No additional training is authorized here. |
|4. Training/deployment differences | **Confirmed semantics and overhead differences.** | Shared bounded logits/masks, true sampled logp, explicit argmax deployment, option timing, schema/checkpoint guards and export tests. Real post-hook record parity and logging-cost comparison remain pending. |
|5. Reward may misprice carry/banking/risk | **Hypothesis, not established reward hacking.** | Terminal team outcome plus separately ablatable deposit/carry-potential/economy/death/damage/objective terms; synthetic bank-win/lost-bag and telescoping tests. Reward quality still requires later engine experiments. |
|6. Release tracing audit was too narrow | **Confirmed audit gap; inherited host controls affect fuel.** | Audit beyond kTraining and package verification. Current profiles preserve lab layout to protect the teacher; no post-Wave2 release package exists. Removed lab controls cannot be assumed inert. |
|7. Fuel matters but does not explain all losses | **Confirmed.** | Report crashes, invalid actions, fuel exhaustion/tails and decision changes separately. No fuel-only explanation or playing-strength claim. |
|8. Missing baseline candidate hypothesis | **Not observed in prior diagnostic tests.** | Candidate0 and stable-tie/mask tests protect the invariant without presenting the hypothesis as the regression cause. |
|9. Logging removal / deferred features were not established upgrades | **Confirmed mixed/failed controls.** | Keep interventions separate, preserve all results, pair against original and overhead control, and measure complete call sites. No default promotion of v50 or an untrained residual. |

The [pre-integration review](agents/H/REVIEW_WAVE2_PREINTEGRATION.md) also identified new framework defects. The lead
fixed zero-layer initialization, external model-directory installation, canonical record/observation adapters,
leaf admission accounting, value checkpoint persistence, margin units, actual rollout stop guards and schema drift
checks. These have native/synthetic regressions; they still require official integration verification.

The review's carry-risk, belief and search-leaf label/loss coverage issue remains open. A forward pass and a callable
hook do not by themselves make an auxiliary head trainable. Official build access is also unresolved. Accordingly
the current status is **incomplete**, not ready to train or proven stronger.
