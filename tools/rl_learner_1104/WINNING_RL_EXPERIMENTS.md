# Winning RL: experiment specification, 4 November 2026

Status: proposed experiments, not a proven winning architecture. JOHNDOE owns design/review; R1shik123 owns implementation and most execution. Objective is broad ladder strength above a fresh Agent2 challenger, with no opponent-specific overfitting.

## Evidence and decision

The native Agent2 student has 28,889 trainable parameters, 500-field layout 2. Our Mac release reproduction won 4/6 selected map-sides against v92, with 110 fuel-outs and no crashes. Those six deterministic games are a reproduction check, not a reliable strength estimate. Our compact 2,482-parameter actor lost all eight reliability games despite two genuine PPO updates; it is a pipeline testbed, not the main candidate.

Pinned native reproduction: source afb43b886fc348006d48d4f4feb830c16cba5533; checkpoint SHA256 05052b6e8ddeb8eaa4cef760b8b24dda9cfee794207b0a2d12d7b06bfae9e5ec; release WASM a48fe4423cb6a3f0f469266595d08038465288f82fbc67cbd68120a99db6b177. Build recipe/report are at tools/rl_learner_1104/mac_e3/ in commit 7c53e102f3ae09a843670001e18c801f4923c164.

Fresh Agent2 head 6c2244e268e36aa37819e4f6002b8820ba21e48a changes two result files, not weights/source. Its e128_pick.out reports 67.3% in-sample selection versus a labelled 53.2% held-opponent estimate; these are Agent2's reported estimates, not independently reproduced ladder results. This reinforces separating selection from confirmation. [Commit](https://github.com/Infosuii/neural-networkk-battlecode/commit/6c2244e268e36aa37819e4f6002b8820ba21e48a).

## Research translated into decisions

Kickstarting combines teacher guidance and reinforcement learning, allowing a student to exceed its teacher. Use the strong pretrained starting policy, with a diminishing reference penalty rather than permanent imitation. No published speedup transfers automatically to Battlecode. [Kickstarting](https://arxiv.org/abs/1803.03835).

MAPPO's ablations support centralized value information, normalized value targets, conservative sample reuse and careful clipping/batch choices. Start with a shared actor and separate team-aware critic; preserve sequence boundaries and use few large minibatches. Its cooperative benchmarks do not establish the optimal settings for our adversarial game. [MAPPO](https://arxiv.org/html/2103.01955v4).

Gym-microRTS identifies action composition and invalid-action masking as essential in its RTS experiments, and studies opponent diversity. Use explicit conditional legal actions and varied opponents. Its single-map results and training duration are not a forecast for this competition. [Gym-microRTS](https://arxiv.org/html/2105.13807v3).

Procgen reports benefits from diverse environments and larger models. Therefore, do not impose a 2.5k-parameter ceiling: test capacity against generalization and measured engine fuel. [Procgen](https://arxiv.org/abs/1912.01588).

A larger training policy can be compressed into a runtime student, but preservation of playing strength must be measured after export. [Policy Distillation](https://arxiv.org/abs/1511.06295).

Report uncertainty and distributions rather than selected point estimates. Use paired, map-family-clustered confidence intervals and a separately frozen confirmation set. [Statistical Precipice](https://arxiv.org/abs/2108.13264).

The settings below are our experimental hypotheses, not settings proven by those papers.

## First gate: a mathematically valid native learning loop

R1 first reproduces the native baseline on PC, then delivers one complete auditable native episode before scaling. Existing Agent2 code already contains a residual option head and a live blend sampler; inspect/reuse useful parts instead of assuming a new head must be invented.

The inference pipeline caches query/context/camp information at different ages. Fresh raw features may not reconstruct the actual distribution. Log the effective inputs or cached latents, cache ages, physical target identities, legal mask, policy version, random seed/counter, sampled choice, effective choice, holds, elapsed rounds, respawn/reset and terminal state. Replay deployed quantized probabilities, not merely float-network approximations.

Clarification to earlier messages: proposal log-probability is NOT inherently invalid when execution changes the action. Two valid schemas exist:
1. Final-action schema: compute p_exec(a|h) = sum over z mapping to a of p(z|h), and record that probability.
2. Latent-action schema: record proposal z and its probability, with the parameter-independent executor treated as part of the environment. Preserve its state/mapping and train on z, never relabel it as a.

For either schema, an acceptance/gate rule that changes with trainable logits is not automatically a fixed executor. Freeze/version the reference gate, model the full distribution, or define a clean categorical action boundary. Do not pass latent proposals into the current CL1 validator, which requires sampled==executed.

Inspect Agent2 nn_ens_sample: sampling/logging inside debug_block does not establish release fuel feasibility; changed actions are logged preferentially unless configured otherwise. Require all actual invocations, counters and a production-equivalent fuel path. A training simulator can be faster, but must reproduce the release executor's actions, suspension and timing. Instrumentation must not silently alter play.

Acceptance: complete episode; no lost/replaced decisions; replay max absolute log-probability error <=0.0002; masks and physical identities agree; export parity; no unexplained action mismatch. Fuel-outs remain recorded events, not crashes and not discarded losses. If the learner cannot model suspension correctly, fix or version the runtime before using those episodes.

## First experiments: preserve competence, then improve decisions

Baseline B0: frozen native policy and executor, pinned artifacts.

E1: frozen pretrained backbone plus trainable target/residual policy at an explicit valid boundary. Initialize to preserve reference behaviour as closely as the stochastic training boundary permits. Acknowledge any deterministic-to-stochastic baseline change and evaluate it separately. Team-aware critic is training-only.

E2: same boundary and data design, unfreeze the upper trunk after E1 is valid. Start trunk learning rate at one tenth the head rate. Stop if representation drift destroys baseline strength.

E3: only after E1/E2 show learning, add recurrent strategic memory and own previous selected action/intent, elapsed time and uncertainty ages. Actor sees only legal runtime information. Critic may use simulator global state at training time; no privileged information in exported actor. Compare against an equally trained non-recurrent model.

Initial optimizer hypothesis: head Adam learning rate 1e-4; critic 3e-4; PPO clip 0.1; two update epochs; global gradient clipping 0.5; entropy coefficient 0.003; target measured old-to-new KL <=0.01 as an update stop diagnostic. Log the KL estimator and clipped fraction. Reference KL coefficient begins 0.03 and is adjusted only from development data. Do not sweep all settings simultaneously.

Use complete games from one fixed actor version per batch. Initial collection target: at least 16 games across several training map families and opponents; size in decisions is measured, not assumed. Compare changes at equal rollout/game budgets, with at least three training seeds for finalists if throughput permits. Report actual throughput before scheduling a large run.

Critical horizon correction: gamma=0.995 PER ROUND discounts a terminal reward 1,000 rounds away to about 0.0067. It optimizes a materially shorter horizon than undiscounted match winning. Main experiment uses gamma=1 for finite complete games and terminal win/draw/loss +1/0/-1; compare gamma=0.9995 as a development ablation. Version reward/return schemas and regenerate rewards rather than silently changing metadata. Optional score potential is bounded and zero at true terminal, so it telescopes without changing the gamma=1 episodic objective. Avoid standalone kill/farm rewards that can pay for losing.

Define GAE explicitly: gamma^elapsed for interval discount; choose lambda per macro decision initially (0.97), not silently lambda^elapsed. Body death resets actor memory but does not terminate the team game. Log truncation and bootstrap rules. Frozen normalization statistics are part of the exported ABI.

## League and confirmation

Freeze a broad opponent manifest: v92, native teacher, historical strong snapshots, contrasting economy/rush/combat bots and own previous policies, subject to verified local availability. Start with equal weights across available opponent families; reserve at most 25% of training games for any single Agent2 version. Later add hard opponents while retaining coverage. Those proportions are design choices, not theoretical guarantees.

Split maps by topology/family, including related variants together, rather than random filenames. Prior exposed corners/oasis/crater/ambush/dunes belong to development. All official maps may already have appeared in Agent2 pretraining: call a subset held out from OUR tuning unless provenance proves truly unseen. New procedurally generated legal maps require engine validation before use.

Use both sides, independent policy seeds and supported game/noise settings. Do not count identical deterministic reruns as new evidence. Keep a sealed confirmation schedule; development failures may guide training, confirmation failures trigger a new version and new confirmation allocation rather than tuning against revealed outcomes.

Screen cheaply on development. Confirm only a few finalists on at least 20 reserved map families if available, both sides, several opponent families and three independent policy/game seeds where stochasticity exists. Pair baseline/candidate settings. Bootstrap families, not individual turns; publish aggregate paired win-score differences, intervals and every family breakdown. Target >55% head-to-head against pinned fresh Agent2 with lower 95% bound >50%, PLUS a positive broad-pool improvement with lower bound >0. These are promotion requirements, not current results. At inadequate sample size report inconclusive. Ladder confirmation follows coordinated LOCK/ACK and includes losses; local success alone does not prove ladder superiority.

Refresh Agent2 challenger at each promotion milestone; preserve old snapshots. A new Agent2 version resets comparative claims. No finite result guarantees superiority over all its future work.

## Compute and ownership

R1: PC reproduction, native adapter, training/evaluation runner, most experiments and implementation. JOHNDOE: review distributions/reward/evaluation, research, experiment decisions, Mac cross-platform checks when needed, Kaggle preparation and execution.

Thirty Kaggle GPU hours are a ceiling, not a target: provisional allocation 2h profiling/parity, 8h initial learning, 12h selected longer runs, 5h larger teacher/distillation only if warranted, 3h reserve. Do not burn GPU while CPU rollout supply is empty; checkpoint and stop. PC/Mac generate local rollouts and test release fuel; Azure/Codespaces are not dependencies. Publish decisions/sec, games/hour, learner utilization and storage growth before allocating the next block.

The path beyond the first improvement is richer team strategy: recurrent role/objective assignment, coordinated banking/contesting and conditional combat heads, with a larger critic/teacher during training and measured runtime deployment. Add one control domain at a time with ablations. Parameter count is a resource choice; held-out wins under fuel limits decide whether capacity helped.

Immediate next artifact from R1: acknowledged ownership/session, pinned PC baseline report, selected native adapter schema and first complete replayable episode. Do not promote the compact policy.
