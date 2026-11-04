# Temporal control and tournament training

The current objective is broad tournament performance. Agent2 is one benchmark, not the sole optimization target. This note separates measured behavior, literature, and an unproven design hypothesis.

## Measured problem

Across 160 local training games, 486,076 command decisions and 12,487 departures from the reference, the next logged decision arrives after one round at the median and 90th percentile. The observed time to a different group command has median three rounds. These are command logs; downstream cancellation, banking and safety logic mean they do not establish executed action duration.

The single-update dense reward pilot worsened both collection margins and wins relative to its matched terminal-only update. That rejects promoting this particular recipe; it does not demonstrate that all reward shaping, larger critics or longer training fail.

## Research grounding

[The Option-Critic Architecture, Bacon, Harb and Precup](https://arxiv.org/abs/1609.05140) develops learning for temporally extended policies and their termination conditions. It motivates testing whether decisions need duration to affect this game. It does not establish that any particular duration, safety condition, or implementation wins Battlecode. Our fixed eight-round prototype does not implement learned Option-Critic.

[The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games, Yu et al.](https://arxiv.org/html/2103.01955v4), sections 3.2 and 5, studies shared-reward PPO, centralized critic inputs, value normalization, data reuse and clipping. The paper supports treating critic representation and update stability as substantive design choices. Its benchmark results do not transfer automatically to our partial observations, respawning bodies, quantized inference, or instruction budget.

## Current bounded experiment

Keep v107 weights, reserve1000, native feature/score pipeline and low-level executor. A chosen group may be returned on later eligible farm opportunities for up to eight rounds. End the hold on invalid group state, visible enemies, health below half, or timeout. Existing context/fuel admission still applies, and downstream logic may cancel or change the command. Test a fixed 60 development cells against the existing control. No duration sweep or training occurs in this feasibility test.

## If duration is viable

A proper option collector must log the decision-time consumed state, canonical candidate identities, support mask, actual selection likelihood, option identity and start/end clock, and termination reason. Held returns are not new random decisions. Do not relabel the old per-call JNP3 dataset as option trajectories. Distinguish logical termination from physical execution and use elapsed-round discounts. Preserve deaths, respawns and final transitions, rather than dropping difficult samples.

A training-only critic can combine current team context with the deciding body's observable state without adding inference cost to the deployed actor. Its features must contain no future events. Evaluate critic prediction on separate families; report calibration rather than assuming a larger critic helps. A new collector/ABI needs exact native likelihood replay before sustained training.

## Tournament validation

Use diverse strong opponents, both sides, map-family exposure tracking and live unrated evidence. Treat repeated deterministic local cells as development comparisons, not new independent ladder evidence. Keep fuel fixes and policy changes separate before testing their integration. A successful prototype earns a fresh training experiment; it does not establish tournament superiority.
