# Neural networkk Battlecode

Latest scouting: [top-team replay findings and comparison with DOOMSDAY, 25 October 2026](analysis/top-teams-2026-10-25/REPORT.md).
36 official replays, validated analysis, watchable match index and ranked follow-up experiments; raw downloads stay local.
For the v52/v53 competition lineage, read [ops/HANDOFF.md](ops/HANDOFF.md).

The development repository for our in-progress neural Battlecode bot. It includes source, models, schemas,
tests and their required data, evaluation evidence,40benchmark maps and the official Windows CLI.

Start with [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md), then give a fresh agent
[NEXT_AGENT_PROMPT.md](NEXT_AGENT_PROMPT.md). [HANDOFF.md](HANDOFF.md) records exact implementation state.

**Training stays on the original laptop.** Large training runs, historical archives, environments, package caches
and old experiment copies stay local. The attempted full-workspace upload was cancelled at the user's request.
Git LFS is not required for this development checkout. See [RECOVERY.md](RECOVERY.md).

The direct gameplay framework is integrated across eight heads. New heads are untrained and disabled by default; the inherited trained draft network remains separate. The goal is the strongest validated competition bot, with no neural percentage quota.

Current checks pass287 Python tests,460 legacy C++ checks and the SDK fixtures. All-off official Wasm matches the frozen original byte-for-byte. A heads-off clean release ZIP/Wasm is independently rebuilt and verified under [artifacts/release/2026-10-24](artifacts/release/2026-10-24-final).

See [STATUS.md](STATUS.md) for measured limitations and [TRAINING_LATER.md](TRAINING_LATER.md) for the guarded later training/export workflow. No training or match-data parameter update has run. Current diagnostic data is too sparse for fitting by itself; later collection must pass data and parity gates.

GPU training operations, metrics, checkpoint/resume and model comparisons: [OPERATIONS_HANDOFF.md](OPERATIONS_HANDOFF.md). Copyable agent prompt: [DEEPSEEK_TRAINING_PROMPT.md](DEEPSEEK_TRAINING_PROMPT.md). Tiny synthetic CPU/CUDA recovery tests passed; no match-data training ran.
