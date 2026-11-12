# EXP-238 result — exploratory signals remain unsafe

MEASURED: LIVE111D_HEAVY_RESULT.json /RECOUNT,960games,160paired cells per arm against stock,8new disjoint development maps,5frozen opponents,both sides,77171/80309own-score noise on allarms. CategoriesC1/C3/C4/C5 only; C2/C6/C7 have no remaining eligible maps under the frozen exclusions. Original release/source manifests are exact; all noisy builds fresh. Zero faults/codes/R1/draft differences.

| Removed package | Wins vs stock98/160 | Delta pp [map-cluster95%] | Fuel vs stock792 | Per-cell increases |
|---|---:|---|---:|---:|
| Lab stack |105|+4.375[-10,18.125]|1003|86|
| ForcedA3 |110|+7.5[3.75,11.875]|771|24|
| Duo |109|+6.875[1.25,13.125]|740|51|
| Tactical verdict search |120|+13.75[3.75,24.375]|757|36|
| Route depth |126|+17.5[6.875,28.75]|739|32|

All fail the strict per-cell native safety filter; this is a multiple-arm exploratory census,not a new release or ladder estimate. Route3ad0ab94's prior EXP220 disjoint -5.833pp/subgroup veto remains binding. Do not choose the most favourable panel or add rejected switches together. No global off hash advances to selection/holdout/live. Structural compute/decision interactions need their own evidence and fresh gates.
