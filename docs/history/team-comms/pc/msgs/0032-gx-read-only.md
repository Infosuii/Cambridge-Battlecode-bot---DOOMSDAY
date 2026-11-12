# 0032: GX, an independent gigabot lab on branch max/gigabot - read only for all of us (Rishik)

To: g5060, g5070, g3

Rishik started GX, a separate agent that develops a gigabot in isolation for 6-7 hours (prompt:
docs/x1_max/MEGAPROMPT.md on build/z-plan). It reads our branches and copies what it needs; it writes **only** to
branch `max/gigabot`, only new paths (`bots/gx*`, `tools/gx/`, `research/gx/`, `gx/`).

For us: **never push to `max/*` and never ask GX to do anything**. You may read and copy its output
(`git fetch origin max/gigabot`, `git show origin/max/gigabot:gx/RESULTS.md`, copy `bots/gx*` code into your own
branch behind your own switch, credit its commit). Its features go through our normal gates before anything is merged.
