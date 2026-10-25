# V55 tooling adoption (2026-10-25)

Pulled branch claude/compare-fix-replay-decoder at2733cf3 (includes bcb8944). Existing bench2/bench28 runs finished before retirement; no running old scripts found. Historical build logs and CHANGES files were left unchanged. New runs use bench3 and must exit0, contain2*maps*seeds games, and have no faults on either team.

Retired bench2.sh, bench28.sh and bench_paired.py; bench_summary.py remains. Updated the live references requested in SETUP, HANDOFF section4, bots README, V55_GPT_PROMPT section6, bench_maps and bench3 comments. Smoke: rows, v54vs v53, seed1; exit0,2games, faults0 both teams. See results/v55-tools-smoke-b3.txt and v55-tools-smoke-compare.txt.

Earlier v55 comparisons were recomputed with bench_compare.py. The baseline E4 is an inert executable-identical v54 control. Gem-margin differences and map-clustered95% intervals:

| Experiment vs control | Mean |95% interval |
|---|---:|---:|
| E1 | -203.8 |[-293.0,-109.0]|
| E1b | -241.4 |[-338.0,-146.8]|
| E1c | -24.1 |[-71.0,12.8]|
| E2 | +7.3 |[-20.6,37.2]|
| E2b | -1.8 |[-38.2,34.4]|
| E3 | -27.9 |[-57.4,1.2]|
| E4b | -71.6 |[-126.2,-19.1]|
| E5 | -12.8 |[-41.6,16.5]|
| E6 | +17.5 |[-25.7,59.4]|

None qualifies for retention against v54. E1c improves on failed E1 (+179.8[85.0,271.6]), but still does not beat v54. No decisions use naive standard errors. All prior development runs contain672games with zero faults; raw replays stay local-only.

The user subsequently asked to restart opponent-driven research and authorized submission once v55 shows a definite improvement over v54. A positive clustered interval is necessary; the existing gate, complete fault-free runs and mechanism checks remain required.
