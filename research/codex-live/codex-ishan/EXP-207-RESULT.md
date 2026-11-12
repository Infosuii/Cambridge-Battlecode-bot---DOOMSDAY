# EXP-207 result — Both changes together still fail development safety

MEASURED: duplicate clean joint release `816420c2e4030e8e76c37861e73379caa1059f57e5dda2c245889029eaf980cc`; cold-only `e2494463`, cache-only `086a14aa`, all-off exact `0896a189`. All 120 reused rows reproduce their raw native values and input pins in `LIVE111_INIT_BUDGET_REUSED_AUDIT.json`. The 120 new games complete the four-arm, 240-cell study on the same 60 independent large-development cases.

| Arm | Fixed wins /60 | Fuel-outs | R1 fuel-outs |
|---|---:|---:|---:|
| Stock111 |52|836|36|
| Cache only |51|810|0|
| Cold reservation only |46|815|36|
| Both |48|782|0|

Joint has 24 per-cell fuel increases versus stock, zero faults/codes and no draft changes. Cold-only has 23 increases. Fixed-build wins are diagnostic context, not strength evidence. The joint source fails its preregistered native filter, so no full pool, noisy full development, selection, holdout or ladder test follows. The successful fixed-state R70 repair does not establish a generally safe or stronger executor. Preserve every arm; reject this hash without changing the gate.

Resume full Discovery after the consecutive failures. The team's independent configuration-bit screens at `51f3e88f` also reject all tested variants; do not repeat them or use their exposed generated maps as a new final holdout. No platform action or training.
