# v55: complete camp missions and execute Heart's farming kit

Frozen release candidate R10, based on v54. Submission is authorized by the user after the release checks pass.
Current status and final results belong in `artifacts/claude_ops/V55_RELEASE.json`; restart research and rejected
experiments are in `artifacts/claude_ops/V55_RESTART.md`. No claim of reaching international rank25 yet.

## Retained changes

- `V55_COMMIT_EVENT=1`: release a learned camp commitment when that group becomes respawning. A completed capture
  must not hold the old destination for another40rounds. Independent foundation test:726/1344wins over24seeds,
  +19.8gems, map-clustered95% interval[+3.5,+37.1]. First12-seed ledger: dead-camp waiting -11.1%, capture gold per
  actor +3.9% byR500.
- `V55_HEART_CAMP=1`: deliberately land Heart's damaging/stunning dash beside members of its selected camp group.
  Use personal visible targets, the SDK's dash range/radius, available landing tiles, and avoid waking another
  known living group. A healthy Heart can preserve its cast for this strike; the existing late shield pass remains.
  Added to the validated completion foundation: +79.2gems,95%[+4.2,+160.6] over672paired games against v54.
- `V55_DRAFT_LEGAL=1`: only our own picks exclude champions from the learned selector. Enemy picks still inform
  its model. Cross-team mirror picks are legal. R1 alone produced exactly the same672games as v54; this necessary
  contract correction carries no claimed competitive gain.

R10 versus frozen v54: **414/672wins (61.6%),+106.0mean gems,95%[+44.5,+174.9]**,28maps,both sides,12policy seeds.
Both teams:0native faults. Fuel-exhausted turns:965versus962. Source reconstruction hash:
`11a6f5e9a9ae08a1d87bcc8b4b62fae8d3d5ce674b5a35c3ecace688d94cf9e1`.

R500 mechanism measurements: capture gold363.2versus321.8per actor (+12.9%); equipment1911.6versus1670.0
(+14.5%); dead-camp wait127.2versus135.3champion-rounds (-6.0%). Heart capture gold319.4versus235.0 (+35.9%).
Actual successful Heart dash casts45.24versus35.21per drafted actor; landings adjacent to a living camp8.56versus1.23.
That adjacency marker uses post-cast geometry, can miss lethal casts, and is not causal damage attribution. The
separate timeline kind23 movement-step count is not an exhaustive count of ability casts.

## Ablations and limits

Heart strikes plus draft legality alone (R9):386/672,+83.9,[+34.5,+144.9]. Adding completion to R9 gives+22.1,
[-6.2,+48.7], so the reverse ablation is inconclusive. Retention follows the independently validated R2 foundation,
then the positive Heart addition; it does not establish that completion independently improves every Heart context.

The proposed damage-model/cache and spell-kill retarget changes lack incremental evidence and are disabled:
`V55_HEART_MODEL=0`, `V55_CAST_RETARGET=0`. Forced economic drafts, global reward funnels, more wards, changed
banking thresholds, gear-aware fighting, and invariant-work optimizations were tested and rejected or unproven.
Exact awake-camp tactical lists remain an unretained correctness candidate. Their findings are preserved in
`artifacts/claude_ops/V55_CONTRACT_AUDIT.md` and reconstructible experiment patches.

The five-map brawl set won81/120,+98.7; its interval[-27.7,+252.9] is inconclusive. Gold-rush regressed by107.9mean
gems in this test, while eight improved390.1. These are tradeoffs, not universal map fixes. The general controller
change declares no map-specific all-seed victory target. Development is entirely against available lineage bots;
external team sources are unavailable. All40maps are reused benchmarks, and hooks was previously used in development.
The once-only reserved12-map pass and v53/v48 checks are recorded separately in the release manifest.
