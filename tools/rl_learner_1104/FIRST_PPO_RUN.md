# First real-game PPO update: collector handoff

Learner checkpoint: current epoch3 on `johndoe/rl-learner-e3-1104`. The tested command does not launch matches or touch platform state.

From `tools/rl_learner_1104`, with CPU PyTorch/NumPy available:

```bash
python train_ppo.py --actor path/to/actor.json --shard path/to/shard_00000 --out runs/jd-cl1-e3/update-01 --epochs 2
```

Output directory must be new. Output: `actor_checkpoint.pt`, `trainer_state.pt` (critic, optimizer states, RNG), `report.json`, and `export/{actor.json,actor_weights.h,parity.json}`. The export automatically compares NumPy/PyTorch predictions. After runtime export/integration, collect a fresh batch using its new actor SHA. For the next update, pass `--resume runs/jd-cl1-e3/update-01/trainer_state.pt` along with that new actor JSON. Resume refuses a different policy hash.

## Manifest additions

Use rlenv-2, layout10, action schema **target13-cl1-nofarm-v1** (row0..11 selects that actual camp group;12 means no farm target), sampling complete, preprocess `jd-cl1-af91-v1`, temperature1, observation_point `farm-pre-actor`, data_origin `engine`. Synthetic tests must say `synthetic-test`; their reports/checkpoints are explicitly labelled and never real training evidence.

`policy` contains `actor_json_sha256`, `wasm_sha256`, `encoder_sha256`. Each episode contains `ppo_eligible:true`, status terminated/truncated, explicit `incomplete:false`, `fuel_failed:false`, `log_cut:false`, `engine_build_hash`, `map_hash`, unique `key`. A terminated episode additionally supplies `final_scores:{ours,theirs}`, `terminal_outcome` in{-1,0,1}, and the actual integer `end_round` (partial final rounds included).

The adapter reads `columns` name/dtype/shape plus corresponding little-endian `.bin` files. Required columns: x_fresh, episode, body_id, boundary, action, executed, mask, logp, has_logp, reset, dt_rounds, terminated, truncated, bootstrap_valid, act_round, feat_round, **decision_index**. h0 is optional for reset-started trajectories, otherwise required. decision_index must be consecutive per body; invocation rounds must strictly increase for this first round-duration schema. Repeated same-round decisions require a new timing schema, not deduplication.

The adapter recomputes team-win/potential rewards from public score observations and true final scores; it does not consume teacher-smoke reward columns. At truncation, exactly one real boundary observation per body is required. At game terminal, bootstrap is0 and a final observation is unnecessary. Chronology, masks, actual action equality and behaviour logp parity are checked before optimization.

## Current verification and limits

26 CPU tests pass, including a complete **synthetic** binary shard -> loader -> probability replay -> PPO optimizer -> checkpoint -> runtime export/parity fixture command. No real-game PPO result is implied. A fuel-failed game is rejected in full. Producer-side counters and phase coverage must prove every actual macro decision was logged; loader checks do not prove the producer omitted nothing. New game data can pass only after the charged runtime finishes reliably.
