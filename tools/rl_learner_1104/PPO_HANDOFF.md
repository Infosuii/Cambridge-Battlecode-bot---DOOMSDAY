# Learner handoff to R1shik123

Implemented under JOHNDOE's learner task; runtime/collector stays on Claude's branch.

`rl_learner_1104/on_policy.py` consumes complete chronological `Trajectory` objects. It does not launch matches or claim a completed RL experiment. Tests use synthetic transitions only. Agent2's 500-field checkpoint stays in the separate native transfer lane; this module accepts CL1/448 only.

## Runtime acceptance contract

Each trajectory contains all decisions for one episode/body, in time order. Use an exact actor JSON SHA256, policy WASM SHA256, encoder SHA256, engine build hash, map hash, episode key, body id, preprocess `jd-cl1-af91-v1`, action schema `target13-cl1`, layout10, sampling `complete`, temperature1.0, reward spec `jd-teamwin-potential-v1`. `incomplete`, `fuel_failed`, `log_cut` must explicitly be false. A fuel failure must not disappear by filtering rows.

Supply int16 raw/next_raw[T,448], int64 sampled and executed actions[T], boolean actual masks[T,13], float old_logp[T], boolean reset[T], reward[T], and lists elapsed/terminated/truncated/bootstrap_valid. Internal next_raw must equal the next chronological raw. At a collector cut the final next_raw must be a real boundary observation; without it the trajectory is rejected. A sequence starting mid-episode needs the actual actor hidden input[1,16]. Prefer complete episodes starting at reset for the first loop.

Terminal boundaries can have elapsed0 when a game ends inside the same round. Other decisions require positive durations. Death/respawn resets recurrent memory but never terminates the team return. Replacing a sampled action is rejected in this first schema; introduce explicit fallback semantics before supporting it.

Before optimization, the learner replays the actor chronologically and compares its log probabilities to the logged values (maximum absolute tolerance0.0002). Wrong weights, input mapping, temperature, masks or memory should fail here. This check alone does not prove collector completeness; producer-side decision counters, lifecycle/phase coverage and fault diagnostics remain required.

## Update and reward

Separate actor and value parameters. The first critic uses legal normalized globals only, not a privileged centralized-state claim. Duration-aware GAE, clipped PPO ratio, entropy bonus, gradient clipping. Hidden state is detached every32 decisions; parameters stay fixed through the full batch and step once afterward. Pass persistent actor/critic Adam optimizers across calls and save both states with actor/critic/RNG/provenance checkpoints. After updates, export a new actor hash and collect fresh trajectories before treating them as a new behaviour batch.

`team_reward` uses public team scores at actual decision boundaries. Phi=0.1*tanh((our_score-enemy_score)/winning_gems). Interval reward = gamma^elapsed * (terminal_outcome + Phi_next) - Phi_current, with Phi_next0 at a true terminal and terminal_outcome in{-1,0,1}. Terminal reward is discounted to interval start. Do not substitute current teacher deposit/100 rewards; the potential telescopes to the discounted game outcome. Match producer and learner gamma (default0.995). No kill, gold-hoard or primitive-outcome reward.

## Verification

22 CPU tests pass across returns, generic actor, CL1 pointer, and PPO consumer. New cases check actual optimizer changes on a synthetic batch, stale-logp rejection before mutation, teacher/fuel-failure rejection, missing boundary observations, action replacement, chronology mismatch, duplicate trajectories, partial-round terminal and potential telescoping. This is a tested update primitive, not a real-game training result. First release gate remains runtime parity + charged fuel + complete own-policy collection, followed by one real batch update and re-export.
