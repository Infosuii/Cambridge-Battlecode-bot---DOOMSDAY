# Discovery 4 — Opening camp economy

The [sample](DISCOVERY_SAMPLE.json) froze 24 previously unstudied ranked groups from 189 eligible loss rows in the latest 48-hour census, excluding 72 groups from earlier studies and exact opponent/map/side/draft repeats. DOOMSDAY was rank 67 at capture. The 16 discovery games and eight confirmation games used the same engine 2.0.0 replay tools. These are measured differences in losses. The historical match rows have no submission identities.

| Directional pattern | Discovery | Confirmation | Mean positive difference in confirmation | Frequency × difference |
|---|---:|---:|---:|---:|
| Winner places more wards | 14/16 | 7/8 | 122.00 | 106.75 |
| Winner clears more camps in opposing territory from R300 | 11/16 | 4/8 | 4.75 | 2.38 |
| Winner banks more gems by R300 | 10/16 | 5/8 | 119.40 | 74.63 |
| Winner buys more early Bruiser shards | 8/16 | 3/8 | 7.67 | 2.88 |
| DOOMSDAY has more early deaths | 3/16 | 1/8 | 3.00 | 0.38 |
| DOOMSDAY has more deaths with no PvP basic or cast | 5/16 | 5/8 | 1.20 | 0.75 |
| Winner sustains an early gold lead | 9/16 | 7/8 | 281.57 | 246.38 |
| Winner collects more inferred positive camp gold through R300 | 10/16 | 8/8 | 387.75 | 387.75 |
| DOOMSDAY takes longer from clear to capture | 6/14 supported | 2/8 | 1.00 rounds | 0.25 |
| DOOMSDAY has more occupation interruptions near enemies | 1/16 | 1/8 | 1.00 | 0.13 |
| Winner captures more groups with only opposing attacks attributed | 3/16 | 0/8 | — | 0.00 |

The frozen confirmation rule was five of eight. Gold-lead swing is measured at the first qualifying checkpoint. The frequency product expresses observed units per sampled game. It gives no causal effect or win estimate. Median earned gold at R150 was 520 vs 496 in discovery and 315 vs 585.5 in confirmation, ours first. At R300 it was 976.5 vs 1,234 and 804.5 vs 1,229. Four confirmation games had a gold gap of at least 100 at R150 with zero early deaths on both teams. First deposits were earlier for the winner in 9/16 and 4/8. The stronger historical territorial-clear gap and the early item signal did not repeat to the threshold.

Through R300, discovery inferred 170 versus 162 positive-gold captures and 14,061 versus 15,607 gold, ours first. Confirmation inferred 80 versus 84 and 5,312 versus 8,414 gold. Configured gold for those groups was 13,680 versus 13,810 in discovery and 5,230 versus 7,240 in confirmation. Captures with only the opponent's attacks attributed produced 180 versus 348 inferred gold in discovery and zero on either side in confirmation. Captures with no attacker attribution numbered 0 versus 1 and 2 versus 1. The attribution method and caveats are in [the freeze](CONFIRMATION.md). More gold despite similar counts makes clear selection and reward value better directions to investigate than trying to hold an occupied region longer.

In the native descriptive profile, early grouping was 62.1% versus 72.1% and 61.1% versus 68.0%, with 1.526 versus 1.734 and 1.411 versus 1.671 workers together. Winner Vesper picks were 11/16 and 8/8 versus 2/16 and 1/8. Draft and camp route are still confounded.

## Early turning points

| Match and round | Earned gold, ours / winner | Same-role own-view evidence |
|---|---:|---|
| 50e198e3-e24f-493d-815c-be0744f508fd at R50 | 90 / 220 | Vendetta had zero gold, no gems and attacked. Winning Vendetta held 90 gold and 29 gems while staying put. Neither saw an enemy. |
| 01a1a54c-708b-7935-8d14-ef2217244268 at R100 | 280 / 633 | Both Vendettas moved with no enemy in view. Ours saw two camps and carried no gold or gems. Winner saw three camps with 100 gold and seven gems. |
| 076fd4ef-ec17-4d45-86ec-1e16ef84e690 at R100 | 220 / 400 | Marcella had 26 gems and moved. Winning Marcella made a basic attack. Neither saw an enemy. |

The [six snapshots](turns) show executed actions and visible state. They do not recover historical private claims or scoring state. Frozen v92's decision path is score_groups at bots/v92/src/bot.cpp:5688, the early prune at :5816, the campwatch and dominant bonuses at :5905 and :5920, and fight_camps at :4962. The observed sequences motivate a charged local trace of pruned boosted groups and early retargets. They do not prove that a historical replay followed either branch.

Use the existing [1,280-game subsystem ablation](../ABLATIONS.md) as the measured dev control for the same frozen v92 subsystems. It uses four varied opponents and two noise seeds. The new cards are [campwatch pruning](../EXP-026.md), [dominant-group pruning](../EXP-027.md), [finish an in-range camp](../EXP-028.md), [first-job assignment](../EXP-029.md), and [two-job opening schedule](../EXP-030.md).

Run profile.ps1 separately for discovery and confirm. With NFS_REPLAY_ENGINE=2.0.0 and NFS_FUNNEL_UNTIL=300, run tools/replay/capture_pressure.mjs on the partition's extracted replays, writing analysis/capture_pressure.json. Run capture_metrics.py with the same partition. [Loss discovery](LOSS_DISCOVERY.json), [loss confirmation](LOSS_CONFIRM.json), [capture discovery](CAPTURES_DISCOVERY.json), [capture confirmation](CAPTURES_CONFIRM.json).
