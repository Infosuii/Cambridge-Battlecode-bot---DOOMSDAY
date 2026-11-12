# EXP-269 result — reject both clean terrain-cache candidates

MEASURED: LIVE111_TERRAIN_FACTORIAL_RESULT.json contains300fresh games,60per arm. All180stock/dual-cache/old-graph native JSONs exactly reproduce. New releases duplicate: terrain e146bf63b5ad1b097b1b50baa05f46dd214f4893dd87ed7d2a15c6be4c50cfeb; preselected joint6f1e2948d8990aac44c610e75641245cfccd5ac1ec86b8f1c37c0e4674c70701; all-off8b8813b7. Both derive from official111source, not platform submissions. Server WASM hash unavailable.

|Arm|Fixed wins/60|Native exhaustions|R1|Cell increases vs stock|
|---|---:|---:|---:|---:|
|Stock1110896a189|52|836|36|—|
|Dual-cache086a14aa|51|810|0|6|
|Old graph joint8b8813b7|49|197|0|1|
|Terrain e146bf63|47|1006|0|42|
|Preselected joint6f1e2948|47|311|0|4|

All drafts match60/60 and all arms have zero faults/codes/R1 cell increases. Joint fixed difference -8.333pp, map-cluster interval[-20,1.667]; terrain -8.333pp[-21.667,3.333]. Deterministic wins are context, not strength. Data/schema/100k numerical prerequisites did not establish whole-game safety; a cached static fact can still be expensive to load in the actual gameplay context. Do not infer a specific new private-state cause from this table.

Reject both new hashes under the frozen strict per-cell safety rule. No official fullpool/noisy/selection/holdout/live test for them, no alternative arm selected. This reaches the third scored candidate failure after full DiscoveryD; return to full fresh Discovery before another scored candidate, not an estimate/TTL/cache-size tweak. No platform action or quota used.
