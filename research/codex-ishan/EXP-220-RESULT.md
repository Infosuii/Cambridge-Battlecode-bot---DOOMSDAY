# EXP-220 result — Route lead does not confirm; all relevant architectures vetoed

MEASURED: LIVE111_ROUTE_RUNTIME_CONFIRM.json completes960 real100k games on12 dev maps disjoint from the EXP209 selection panel,five pinned styles,both sides,fresh paired61879/64223 seeds. LIVE111_ROUTE_RUNTIME_RECOUNT.json independently checks all960native hashes/outcomes/safety values,all evaluated binary/source/noise pins,and every overall/stratum/filter result. No draft changes,faults,codes orR1exhaustion.

| Arm | Wins/240 | Delta vs stock,95% map-cluster interval | Fuel-outs | Per-cell increases vs stock |
|---|---:|---:|---:|---:|
| Stock111 |177|reference|1145|reference|
| Route-off3ad0ab94 |163|-5.833[-17.083,+4.583]|534|41|
| Historical NN-offd731130a |177|0[-10.000,+9.167]|102|0|
| Jointbd3f9976 |179|+0.833[-7.500,+9.167]|103|0|

Route-off fails opponentv92 -10.417pp,categoryC1 -15,C2 -20. NN-off fails x3inv -12.5 andC1 -16.667; its prior fullL0failure still stands. Joint failsC2 -12.5 versus stock; versus NN-off,C2 -20 and103vs102total fuel also veto. Joint versus route alone passes a local filter,but that secondary contrast cannot replace the preregistered stock comparison. None qualifies. Do not add a cache or tweak a threshold to rescue these hashes.

The selected route-only +12.917pp exploratory result from EXP209 reverses on separate dev maps. It is not a ladder advantage and does not justify a release. All arms,including the uncertain aggregate joint result,remain recorded. No fullpool/L1/selection/holdout/ladder stage for these rejected sources. EXP221's fixed-state pruning also leaves native exhaustion,despite completing a score. Next work returns to a measured compute/executor mechanism or the remaining preregistered cards; no category-specific policy or individual official-pool tuning.
