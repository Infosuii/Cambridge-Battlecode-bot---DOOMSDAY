# HIDEREC also reads a stale visibility snapshot

Follow-up to 0005; source remains frozen and untouched.

`Bot::play_turn` handles recall/submission channels before its `w.update(round)` block. The A2_HIDEREC exception around bot.cpp:7211 calls `hidden_here()` and returns. `hidden_here()` around :2379 uses `w.enemies` and the cached `w.warded_clusters`; it does not query current SDK visibility. A channel-preserving return also skips the later world refresh, so the cache can remain older than one turn while the recall continues.

If an enemy enters the bush component or a ward appears after the cached observation, the predicate can still report the previous hidden state. This stale-read path exists independently of partial BUSHPRE labels; partial labels/late ward resolution add the separate coherence problem in 0005. The static path is established; no particular measured loss is attributed to it and no fixed version has been tested.

Smallest recommended correction: refresh the enemy/ward evidence before granting the hidden-recall exception, or query fresh vision directly there and return conservative false when component/ward information is unresolved. Moving only the cluster-ID publication guard is insufficient to make old visibility current.

R0 acceptance scenario for a future repair: start recall while alone in a bush; on the next turn an enemy enters the same component or a visible ward is placed in it. The exception must not assert hidden from the prior snapshot. Include a partial-label version of that scenario. Dedicated fresh/stale/unknown and exception-trigger counters would distinguish activation from fuel-driven summary changes; diagnostics are not strength evidence.

After the repair is available behind a switch and the off build preserves the original binary, re-gate HIDEREC on BP+the corrected component/ward baseline, both sides, x2/x2-s2, ladder/styled/maze. Keep the original 6efc360 K004-K006 results as historical implementation measurements. Status: implementation uncertainty / repair-and-retest recommended, not a strategic rejection of hidden recalls.
