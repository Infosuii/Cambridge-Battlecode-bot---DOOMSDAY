# Second fresh-loss Discovery — 4 November 2026

The 14:39 GMT ladder snapshot placed DOOMSDAY 63rd at 2,043.8051 with 62 teams above it. The [frozen sample](DISCOVERY_SAMPLE.json) draws 24 new groups from 240 eligible engine 2.0.0 losses in the preceding 48 hours, excludes every group from the first Discovery, and caps each opponent at four. The 16 discovery and eight confirmation groups were frozen before profiling. The [confirmation rule](CONFIRMATION.md) was committed before reading those eight profiles. These are team-level observations because the match API omits the historical submission IDs.

| Pattern | Discovery | Confirmation | Mean positive swing in confirmation | Frequency × swing | Directional check |
|---|---:|---:|---:|---:|---:|
| More wards over the match | 12/16 | 8/8 | 81.75 | 81.75 | Pass |
| More opposing-territory clears from round 300 | 11/16 | 6/8 | 9.17 | 6.88 | Pass |
| More banked gems before round 300 | 9/16 | 8/8 | 55.25 | 55.25 | Pass |
| More Bruiser shards before round 300 | 8/16 | 7/8 | 5.57 | 4.88 | Pass |
| Sustained early gold lead | 9/16 | 5/8 | 212.40 | 132.75 | Pass |
| More DOOMSDAY deaths before round 150 | 7/16 | 3/8 | 1.33 | 0.50 | Fail |
| More DOOMSDAY deaths with no PvP basic or cast | 9/16 | 4/8 | 1.75 | 0.88 | Fail |

The swing uses the pattern's units. Gold swing is measured at the first qualifying checkpoint. Frequency × swing gives a descriptive ceiling on the observed differences. The losses alone cannot estimate how many wins a change would recover. “Before round 300” follows the profiler's half-open phase boundary, so the bank and Bruiser buckets exclude round 300 itself. The no-PvP proxy counts a narrow death window through round 600.

Wards, early banking volume and Bruiser timing repeat the first Discovery's confirmed patterns. Enemy-territory clears and sustained early gold pass this split after falling short on the earlier split. The first deposit came earlier for the winner in only 6/16 and 3/8 games. Just one discovery loss and zero confirmation losses had a round-150 gold gap of at least 100 while both teams had no deaths in the first 150-round bucket. The early death and no-hit proxies missed the five-of-eight criterion. The earlier approximate win controls found the early gold marker in 8/23 wins and 15/23 opponent-matched losses. This split adds no independently matched win sample. See [Discovery rows](LOSS_DISCOVERY.json), [confirmation rows](LOSS_CONFIRM.json) and [first Discovery](../DISCOVERY.md).

The earliest sustained gold lead starts at round 50 in one discovery loss, at 100 in two, at 150 in three, and at 200 in three. The other seven lack the marker. In confirmation the first qualifying rounds are 50, 150 twice, 200 and 250. Median team earned gold at rounds 150/300/600 was 455/972.5/2,190.5 versus 461.5/1,113/2,596.5 in discovery and 425/955.5/1,963.5 versus 540.5/1,314/2,758.5 in confirmation. These are per-team medians.

| Discovery loss and checkpoint | Earned gold, ours / winner | Own-view trace at the checkpoint |
|---|---:|---|
| `420e34ac-4100-4b5a-a9d4-8194b5b37952`, round 50 | 80 / 209 | Both Vendettas saw one camp and no enemies, and each moved one tile. Both held no gold or gems at turn start. Ours had 640/1,000 HP versus 540/1,000. |
| `b44c5cae-fd2b-45c3-9dd6-7b118eef0f76`, round 100 | 240 / 496 | Our Vendetta had 220/1,200 HP, 16 gems, 100 gold, no camp or enemy in view, and no recorded movement in the sampled turn. The opposing Vendetta saw ten camps, held no gems, and moved. |
| `1d024092-69bd-4e14-a859-95abe8365780`, round 150 | 480 / 861 | Our Vendetta had full HP, no gems or gold, and one camp in view. It moved one tile. The opposing Vendetta held 19 gems and 65 gold with no camp or enemy in view and no recorded movement. |

The six [acting-view snapshots](turns) preserve raw step codes. A movement or lack of it does not identify a stage, recall or bank decision. No matching source identity or private state is available for exact historical branch reconstruction. For a verified future counterfactual, reproduce the staging branch on a frozen dev game before using this as evidence for why an action differed. In v92, the relevant code is `bot.cpp:5007` for staging, `:4718` for banking and `:7596` for home priority, at df2975cb. The loss trace at round 100 provides a health and banking tradeoff to test, without establishing that either action was legal then.

The existing [1,280-game subsystem ablation](../ABLATIONS.md) supplies the development comparison for lab, A3, duo and tactical search. Each arm had 256 cells with two own-score seeds and four opponents. The [runtime diagnostic](../RUNTIME_TRACES.json) directs fuel work toward ward/world refresh and movement. It does not implicate duo as the primary cost. The new cards separate [staging](../EXP-011.md), [staged chip damage](../EXP-012.md), [nearby banking priority](../EXP-013.md), [early combat shopping](../EXP-014.md), and [visible home invasion](../EXP-015.md). Stage changes use Agent 2's published local results only as a hypothesis source.

Reproduce the native summaries with `profile.ps1 -Partition discovery` and then `profile.ps1 -Partition confirm` from the repository root using the frozen archive cache. The profile invokes summary, archetype, winner, death, camp clear and loss-study tooling. Trace arguments are match replay, round, team and actor from each snapshot and the engine-2 assets. Recount frequency × swing by summing positive differences and dividing by the full split size. Keep holdout data sealed.
