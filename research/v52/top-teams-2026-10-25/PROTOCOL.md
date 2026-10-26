# Bounded descriptive replay study — 25 October 2026

Declared before downloading or decoding the selected replays. Code baseline:
`2e1dcc1cf859a3a9162e58c5f2b6285c8217bd8f`.

- Budget: aim for 90 minutes; reserve at least 30 minutes for interpretation,
  checks, report and GitHub push. Never spend the full five-hour usage window on acquisition.
- Public official ladder snapshot, top six teams. Inspect at most 12 public
  match-group listing pages per team and the latest five finished ranked groups.
- Select four distinct maps per top team (24 unique replays maximum), preferring
  the declared weak maps and top-25 opponents, then recency. Do not select by result.
- Comparison: latest 12 finished DOOMSDAY ranked groups; at most 12 replays whose
  match metadata explicitly says version 52. Prefer maps shared with top teams,
  cap two games per map. Report exact map/side/opponent differences.
- Focus maps: boss_battle, concentrated_wealth, elkring, swirl,
  yellow_brick_road, plus the recently fixed stampede, big_world and islands.
- Use the repo's pinned official engine 1.0.3 decoder, action sequence and final
  state; add descriptive round/state metrics only where needed. Check final
  score/outcome/draft against official metadata. Do not interpret incomplete or
  failed decodes as completed games.
- Compare banking timing, submitted and carried gems, combat/movement/purchases,
  deaths, draft and map-specific objective behaviour. Distinguish observations,
  source-code facts and proposed explanations.
- This is a small purposive sample, not a strength benchmark or causal test.
  No new games, model fitting, parameter updates or submissions are part of it.
- Keep downloads, raw actions and state traces local and ignored. Share only the
  report, compact per-match/per-team metrics, provenance/checksums and tools.
- Baseline for source comparison is `bots/v52` (documented live); `bots/v53`
  contains a rejected disabled gate rule. Do not revive policy-v2 or change gameplay.

## Metadata-only amendment, before any replay download/decode

The public API hides every submission version (`null`), including DOOMSDAY's.
Use at most 12 finished DOOMSDAY games created after 12:05 UTC, following the
documented v52 deployment at 12:02 UTC. Call these **post-v52 deployment** games;
their exact submission identity is unverified. Never claim byte identity with
`bots/v52` from timestamps alone. The source comparison remains specifically v52.
The public spelling of swirl is `00swirl`; correct that identifier in selection.

The public bundle endpoint requires sign-in. The user agreed to sign in on this
device. Downloads may use that existing CLI session with `--cli`; the acquisition
tool never reads credentials or starts login. Public metadata selection is fixed.
