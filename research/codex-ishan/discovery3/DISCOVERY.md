# Third Discovery — 4 November 2026

The [frozen sample](DISCOVERY_SAMPLE.json) selected 24 new groups from 191 eligible ranked loss rows in the 48-hour window. It excludes all 48 groups studied before. The census placed DOOMSDAY at rank 63, rating 2,039.54, and the sample was split 16/8 before inspecting outcomes. The native profiles and confirmation criteria are linked below. Submission IDs are unavailable in these ranked rows.

| Directional pattern | Discovery | Confirmation | Mean positive difference in confirmation | Frequency × difference | Check |
|---|---:|---:|---:|---:|---|
| More wards | 14/16 | 6/8 | 93.50 | 70.13 | Pass |
| More opposing-territory clears from R300 | 13/16 | 6/8 | 1.67 | 1.25 | Pass |
| More gems banked before R300 | 10/16 | 6/8 | 148.50 | 111.38 | Pass |
| More Bruiser shards before R300 | 7/16 | 4/8 | 12.00 | 6.00 | Fail |
| More DOOMSDAY deaths before R150 | 7/16 | 1/8 | 1.00 | 0.13 | Fail |
| More DOOMSDAY deaths without PvP basic or cast | 6/16 | 2/8 | 1.50 | 0.38 | Fail |
| Sustained early gold lead | 10/16 | 5/8 | 235.20 | 147.00 | Pass |

Gold swing uses the first qualifying checkpoint. The frequency product describes the size of the observed gap across the eight games, without estimating a causal effect or a win ceiling. The earlier first-deposit pattern appeared in 10/16 discovery and 3/8 confirmation losses, so larger early banked volume remains more consistent than timing. Mean R300 banked gems were 73.31 vs 145.69 in discovery and 100.25 vs 197.13 in confirmation, ours first.

The first sustained gold lead began at R50 in two discovery games, R100 in three, R150 in one, R200 in three and R250 in one. Confirmation begins at R100 in two and R200 in three. Median team gold at R150 was 475 vs 450 in discovery and 576.5 vs 634 in confirmation. By R300 it was 1,098.5 vs 1,170 and 1,176.5 vs 1,588. Unlike the large 3 Nov study, a reliable R150 mean trajectory without deaths is not supported here: only one sampled loss had a R150 gold gap of 100 or more and zero first-phase deaths on both teams. Both studies point to early conversion. This split confirms greater ward use and later invasion but finds a much smaller confirmation invasion difference than the earlier 12.5 winner clears per game. Early Bruiser purchases fell short this time.

The native replay profiler estimates the fraction of living champion-rounds closer to own spawn than the opponent's. Averaged per match, R150–399 own-half fractions were 84.3% vs 77.1% in discovery and 87.9% vs 82.0% in confirmation. Early grouping (nearest ally within four tiles, R0–149) was 61.1% vs 63.7% and 58.0% vs 65.4%. Estimated workers together before R300 averaged 1.42 vs 1.60 and 1.40 vs 1.65. Winner Vesper picks were 13/16 and 7/8 versus 1/16 and 1/8 for DOOMSDAY. These figures describe this loss sample. They do not isolate an effect from champion selection.

| Replay and checkpoint | Team earned gold, ours / winner | Own-view Vendetta snapshots |
|---|---:|---|
| `852937ec-9cc7-4762-8128-02e3b326b82e`, R50 | 220 / 330 | Ours was dead after a camp kill at R27. Winner had 760 HP, saw one enemy and three camps, and moved one tile. |
| `fffebe54-3bbd-456a-b4c9-3cf0a160663c`, R50 | 80 / 263 | Both saw one camp and no enemy. Ours moved one tile at 640 HP, and the winner stayed put at 660 HP. |
| `01a1a600-5552-7b44-aa20-3e74f36acdaf`, R100 | 90 / 369 | Ours was dead after losing 43 carried gems to a champion at R71. Winner had 1,310 HP and moved one tile. |

The [six snapshots](turns) show visible state and actions, not private scoring decisions. The camp-loss candidate paths are `fight_camps` and `go_home_if_needed`; the carrier loss implicates the interaction of `handle_enemies` and later banking priority as a hypothesis, not a reproduced branch. Frozen v92 anchors are `bot.cpp:4962`, `:4604`, `:3165` and `:4718`. Neither case licenses changing the strategy without a repeatable local opportunity. The single same-alive-camp checkpoint does not separate route choice from attacking or holding.

[Discovery rows](LOSS_DISCOVERY.json), [confirmation rows](LOSS_CONFIRM.json) and [criteria](CONFIRMATION.md). The existing [1,280-game ablation](../ABLATIONS.md) covers the same frozen v92 subsystems and dev partition. The new cards are [span flood](../EXP-018.md), [SDK reachability](../EXP-019.md), [bank before an optional shop trip](../EXP-020.md), [reduce exposure of a loaded carrier](../EXP-021.md), and [pair Vesper with a compatible opening](../EXP-022.md). The pool and sealed evaluation partitions were not used to choose replay thresholds.
