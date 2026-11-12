# EXP-156 balance metadata verified

The fully charged release probe confirmed every one of the 13 properties listed in Patch 4.0.0, including Skirmish's 0.10 damage multiplier and Greed's 40-point strength, focus and health emblem values. It recorded all 13 champion designs with their base stats and per-shard growth. [Metadata, source and binary hashes](BALANCE_METADATA_ENGINE3.json), [official balance review](../../docs/codex/BALANCE_20261105.md).

The frozen experimental and v92 sources already enable the runtime metadata reader. The compiled fallback stat tables are inactive. SDK5's cambc.h differs from SDK4 here by occupancy-snapshot documentation. Duplicate SDK5 release builds of v92 and EXP-154 retained their exact prior hashes. [Rebuilds](ENGINE3_REBASELINE_BUILDS.json).
