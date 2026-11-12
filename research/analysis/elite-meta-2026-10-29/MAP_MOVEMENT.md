# Map geometry, routing and information

Thirty different maps provide broad geometry coverage, with one primary match per map. They do not provide controlled within-map estimates of champion or item strength. MAP_GEOMETRY.json preserves dimensions, wall/hole/altar counts, group count and largest group HP/rewards. Every match's rich initial state preserves neutral spawn positions and the static bitboards needed to reconstruct access.

Classify maps by measurable jobs: resource dispersion, cluster versus monster reward shares, ratio of route distance to clear time, number of independent farm regions, altar-front connectivity, mandatory gates, and thin barriers bridgeable by dash/crystal. Named maps are examples of properties, not the intended policy keys.

| Archetype | Evidence case | Candidate adaptation |
|---|---|---|
| Gated altar frontage | boss_battle group 16,40000HP | Solve the access fight, align capture and tribute, keep other bodies' bags deliverable. |
| Fragmented routes | islands, fracture | Plan feasible front tiles and ability/crystal edges; compare delivery delay with marginal farming. |
| Sparse repeated contention | fragment, packs | Avoid returning repeatedly to a losing fight; protect the next productive cycle. |
| Low-economy gem combat | adgato_gemcombat2, stalactites | Immediate bag safety and delivery; do not price every job using a long scaling horizon. |
| Large late conversion race | contest, tangle | Compare accumulated bags plus feasible finishing times, not merely current score. |
| Close distributed delivery | rows, expanse | Coordinate completion times across bodies and keep useful secondary routes. |

Ordinary movement has eight neighbours. Walls, holes, altars, enemy spawns and occupied destinations constrain landing. Dashes can cross holes along a legal short path but not walls; crystals reach three tiles in each axis and ignore intervening terrain, with a three-tick channel and a legal landing. An altar itself cannot be occupied: target a free tile within legal tribute range. A static shortest path that ignores living gate camps can propose a physically unusable scoring route.

The movement mask is limited by what the acting champion sees. An unseen occupant can cause a legal-looking action to return false, reveal the tile and preserve the allowance. Event 23 is movement blocked; event 22 is teleport completion. Counting blocked events as dashes invents mobility and can invert a route diagnosis. Failed attempts are not necessarily bot errors or fuel failures.

Vision is personal, including the body's own ward. Allies do not share their views automatically. Walls/bushes occlude sight; standing within a connected bush changes visibility. Ward placement can support a route or interruption decision, but more wards alone does not establish better information use. The extractor retains every personal view rather than supplying a union of allied vision as a legal policy input.

Draft can see the full map and has additional compute. Precompute compact route frontiers, gate associations and useful crystal/dash transitions there; refresh transient occupancy at runtime. Cache static distances rather than repeating expensive geometry work inside every camp loop. Evaluate routing on unseen property combinations and alternative barrier layouts, not only on the same dimensions/group-count tuple. The conditional-v71 source still has named-pool lookup signatures, which motivates a generalisation test rather than an immediate removal of useful known-map handling.
