# Neural networkk Battlecode

The development repository for our in-progress neural Battlecode bot. It includes source, models, schemas,
tests and their required data, evaluation evidence,40benchmark maps and the official Windows CLI.

Start with [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md), then give a fresh agent
[NEXT_AGENT_PROMPT.md](NEXT_AGENT_PROMPT.md). [HANDOFF.md](HANDOFF.md) records exact implementation state.

**Training stays on the original laptop.** Large training runs, historical archives, environments, package caches
and old experiment copies stay local. The attempted full-workspace upload was cancelled at the user's request.
Git LFS is not required for this development checkout. See [RECOVERY.md](RECOVERY.md).

The current checkpoint passes259 Python tests and460 legacy native checks, and the all-off official build
is byte-identical to the frozen original. New neural heads are untrained and disabled by default. The target of
roughly80% neural control is still being implemented; direct gameplay dispatch is not yet connected.
