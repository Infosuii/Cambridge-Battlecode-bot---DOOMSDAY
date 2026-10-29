# Locked selection protocol

Registered 29 October 2026 before examining any new replay trajectory.

Use the frozen official ladder snapshot retrieved at 12:54 UTC. Include the current top 12 by global rank; identify developer teams separately rather than treating them as eligible competitors. Retrieve up to twelve recent completed ranked groups per focal team (bounded to four listing pages). Deduplicate group and match IDs. Only finished engine 2.0.0 matches dated on or after 27 October with a replay URL qualify. Do not read replay trajectories during selection.

Target 20 matches between two top-20 teams (at least one top-12), six top-12 wins over ranks 21–75, and four top-12 losses to ranks 13–75. Loss labels use metadata only. Results are deliberately stratified and cannot estimate unconditional win rates. If a stratum is too small, disclose the shortfall and fill from elite matches, then competitive matches, in that order.

Within each stratum select greedily by new leading-team coverage, new map coverage, underrepresented starting sides, fewer repeated team pairs, fewer repeated teams/maps, then recency and match ID. Aim for at least six focal teams and eight maps. Prefer at most three games per map and four per pairing; these are soft limits where coverage makes them infeasible. No preferred champion or expected strategic conclusion enters selection. Freeze the manifest and its SHA-256 before downloading or decoding. Any replacement must document a technical failure and apply the same ordering to remaining metadata.

Verify replay engine, official scores, winner, round count and final input cursor against independent official summaries where obtainable. Process every timeline event, retain every round, ordered actor events and bot-visible turn contexts. Keep raw replay files and bulky state ledgers in artifacts/local-only/elite-meta-2026-10-29. Preserve existing research partitions and do not open spent reserved trajectories for tuning. Existing submitted/frozen bots remain unchanged. This is descriptive research, with explicitly labelled hypotheses; no training, new match creation or bot implementation.
