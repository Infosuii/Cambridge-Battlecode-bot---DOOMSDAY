# EXP-007 frozen implementation plan

Before observing candidate outcomes: copy v92 into `bots/codex-bruiser/src`. `CODEX_BRUISER` defaults on in this candidate only; compiling it off must reproduce v92. No changes to draft or existing sources.

Latch an own-view enemy sighting within eight tiles by round 300. For a ranged champion with that history and a completed Monster emblem, replace the first unstarted Capture milestone with five Bruiser health shards. Only choose the substitution while able to buy a shard. Persist the choice for that champion so partial purchases are completed and future visits do not buy the replaced milestone. Keep every other milestone and its order unchanged. Never substitute if a Capture item was already bought or the existing plan has no Capture milestone. Shopping already has item counts; no extra SDK queries in the turn loop.

Prediction: at least one development game has a completed Bruiser emblem through this path; counts before round 300 should increase when a qualifying shop visit exists. This is not a strength target. L0: reproducible release, switches-off identity, no faults or increased fuel (including per-cell and round one). Start with the previously frozen 16-map development stress subset against v92/x3inv/p65pack/public-khiri, both sides and own-score jitter seeds 301/607. Reject on any safety regression or the prescribed strength thresholds; if it survives, use the full dev and selection partitions. Do not inspect holdout.

Behavior is measured from native purchase events in release matches. No diagnostic logging in the candidate.
