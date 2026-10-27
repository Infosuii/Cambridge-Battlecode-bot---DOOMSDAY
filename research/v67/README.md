# v67: unfinished research checkpoint

The goal is at least 220 wins in the fixed 240-game local comparison with unmodified v65. It has **not** been met.
Best tested candidate: b06-life15, 137/240, mean gem margin +108.0. An identical-source baseline scored 136/240,
so this does not establish a meaningful improvement. There is no evidence that the target is impossible.

Continue from [HANDOFF.md](HANDOFF.md). The user requested this checkpoint because their usage is low and they
want another agent on the same device to continue. This is not a release or a completed strength claim.

- [RESULTS.md](RESULTS.md): every complete experiment, with economy, kills, deaths, faults and fuel.
- [RESULTS.jsonl](RESULTS.jsonl): source hashes, both teams' metrics and per-map outcomes.
- [BENCHMARK_OUTPUTS.txt](BENCHMARK_OUTPUTS.txt): actual saved benchmark stdout/stderr, including failed builds.
- [MAPS.md](MAPS.md): all 70 pool maps, using 1,177 opening replays and the engine-2 meta crawl.
- [MAPS.json](MAPS.json): winning-team opening examples behind the report.
- [OPENINGS.json](OPENINGS.json): the intact winning-team example selected for each map.

Seeds 3/4 have never been used for v67 development or validation. The required checks against v61, v58 and v66b
have not run. No ladder games or submissions were requested. v65 and mimic remain unmodified.

Latest/current source is b18-public-camp-state: 126/240, +55.7, zero faults, fuel-outs 941 versus v65's 359.
CHECKPOINT.json verifies that the saved source hashes match this full run. All benchmark processes have finished.

The independent team controller regressed badly: its first version scored 0/240, the camp-execution revision
3/240, and the local-farming revision 6/240 with excessive fuel use. A position/focus/rally protocol works at the
encoding level, but coordination has not yet translated into efficient farming or winning combat. Copying
winning drafts, routes and item milestones into the existing executor also regressed, to 76–81 wins. Read the
handoff's concrete suspected fuel/startup bug before attempting another large controller rewrite.

All full comparisons use the exact 120-slot plan with seeds 1/2. The runner only adds replay retention and output
audits. Per-map tables and economic diagnostics are research evidence; no retrospective combination of separate
candidates is represented as an implemented bot result.
