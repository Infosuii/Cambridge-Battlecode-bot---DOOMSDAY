# Frozen checks for the eight confirmation losses

Written after the 16 discovery replays, before computing any confirmation metric. A pattern persists in this sample only if its paired direction repeats in at least five of eight held-back games; record actual counts. These checks are descriptive and do not show prediction against wins or a causal effect on wins.

1. Winner earns a lead of at least 100 gold and 15% of our earned gold at two consecutive sampled rounds, starting by round 250. Samples: 50, 100, 150, 200, 250, 300, 600. Discovery 14/16.
2. Winner clears more camps on the opposing half after round 300 than we clear on theirs (Chebyshev spawn territory, >3 tile margin). Discovery 11/16.
3. Winner places more wards across the whole game. Discovery 12/16.
4. Winner banks more gems before round 300. Discovery 10/16. Earlier first bank was only 6/16; do not use that as the claimed mechanism.
5. Winner buys more Bruiser shards before round 300. Discovery 9/16. Treasure first was only 2/16. No-attack/no-cast deaths were not more frequent for DOOMSDAY in the discovery subset; this strict replay proxy differs from the older hit-back metric.

Each match group stays entirely in one partition. Scope is only ranked losses against sampled opponents ranked 36–66; platform submission IDs are unavailable. See `DISCOVERY_SAMPLE.json`.
