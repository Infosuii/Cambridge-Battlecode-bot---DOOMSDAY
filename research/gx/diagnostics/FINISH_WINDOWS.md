# How often a late deposit could matter

Replayed all 175 x3mf pool non-wins against v92, v86h and x1bru. Compared the final scores and ending round against the engine's match summary for every replay. Counted banked gems plus the live carried bags at the start of each champion phase in the selected window.

| Before match end | Any live bags reach 1,000 | A single bag reaches 1,000 | Bags already at altar range reach 1,000 | Bags fit travel and channel estimate |
| --- | ---: | ---: | ---: | ---: |
| 12 rounds | 24 | 13 | 6 | 10 |
| 25 rounds | 25 | 13 | 7 | 16 |
| 50 rounds | 27 | 14 | 9 | 18 |
| 100 rounds | 28 | 14 | 9 | 20 |

The travel estimate uses straight-line distance, two tiles per round, and one channel round per ten gems rounded up. It ignores blocked tiles, locks, enemies, channels already in progress and turn order. These are opportunity counts, not recoverable wins. Even in-place deposits need a safe channel. A single in-place policy addresses a narrow subset; earlier collection, faster bank travel and multi-carrier scheduling can affect different cells.

The complete per-match observations are in [terminal-window-audit.json](terminal-window-audit.json).
