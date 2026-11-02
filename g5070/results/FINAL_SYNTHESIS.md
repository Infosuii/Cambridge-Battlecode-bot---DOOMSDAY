# x1 experimental synthesis

Original K004–K006 campaign and focused diagnostics are complete and verified. The supplied K007 reserve work is also complete. The bounded supplied K009/WALKTAIL comparisons are reported separately below and in [K009](K009.md); their final interpretation will be added when that queue finishes.

## What the original campaign establishes

There is **no demonstrated universal replacement for no-switch x1**. AF5/W400 has the highest observed standard/fresh win averages among the original six finalists, but fails the standard fuel clause. Siege45 is the only original finalist passing standard K006 R1 and has the clearest fuel-saving profile, but ties BP's fresh wins and trails original x1's standard wins. These are different conclusions; the largest grid score is not the recommended universal configuration.

All rows below use identical opponent/map/side cells within each column. Standard:149 maps, three opponents, both sides,894 cells. Fresh:40 layouts frozen before robustness outcomes, three opponents, both sides,240 cells. Original source:6efc360. All own/opponent faults are zero.

| Configuration | Standard wins (%) | Δ BP / Δ x1 | Standard real/maze fuel | Fresh wins (%) | Δ BP / Δ x1 | Fresh fuel | Standard R1 versus BP |
|---|---:|---:|---:|---:|---:|---:|---|
| Original x1 | 494/894 (55.26%) | +30 /0 | 505/445 | 123/240 (51.25%) | +3 /0 |89| Reference; more fuel than BP |
| BP |464/894 (51.90%)|0 /-30|319/454|120/240 (50.00%)|0 /-3|84|Reference|
| BP+AF5/W400 |487/894 (54.47%)|+23 /-7|359/460|138/240 (57.50%)|+18 /+15|114|Fail: real fuel+40|
| BP+siege45 |474/894 (53.02%)|+10 /-20|294/441|120/240 (50.00%)|0 /-3|81|Pass|
| BP+plan4/R150 |472/894 (52.80%)|+8 /-22|295/455|125/240 (52.08%)|+5 /+2|89|Fail: styled-3 pp|
| BP+plan4/R100 |465/894 (52.01%)|+1 /-29|352/456|132/240 (55.00%)|+12 /+9|90|Fail: styled/fuel|
| BP+plan4/R50 |452/894 (50.56%)|-12 /-42|306/456|106/240 (44.17%)|-14 /-17|90|Fail: styled/total|
| BP+plan4/R200 |443/894 (49.55%)|-21 /-51|307/456|118/240 (49.17%)|-2 /-5|84|Fail: ladder/total|

Map-cluster95% intervals versus BP include zero for the standard finalists. AF's fresh estimate is +7.50 pp, interval approximately [0,15], touching zero after rounding; versus original x1 it is +6.25 pp, [-1.25,15]. AF's31-map conservative unknown-profile subset gives108/186 versus BP93 and x1 94, with its interval including zero. These are promising observations, not conclusive superiority claims. Fresh-map fuel is fully reported, but this generated suite has no established official fuel gate; a displayed fresh win-rule pass is not a reliability endorsement.

## Exploration, interactions and failure diagnosis

K004's six non-BP stacks all lose against BP. P3 is the best at320/596 versus327; P5 gives314 and the P5+AF+P4 stack280. The P5 factorial has a -8 win contrast with an interval spanning zero. The P3 secure/hold ablations give -2/-4 wins and their joint -6, zero observed map win interaction. This does not warrant rejecting the component ideas.

All35 K005 lines were completed. Plan4/R150 is the original exploration maximum,347/596 (+20), but adds21 real-map fuel-outs. AF5/W400 gives335 (+8), passes exploration, and has two losing immediate neighbours. Plan4/R200 is a neutral, lower-fuel exploration pass that subsequently loses21 standard validation wins: passing exploration is insufficient. Bush/lazy settings have a broad50–60 plateau but every setting loses7 maze wins versus x1. Siege45/55 tie BP wins with lower fuel;65 loses8.

The selected AF+plan joint scores306. Its original factorial is -49 wins, paired -8.22 pp,95% [-14.60,-1.85]. After never-switch controls, actual plan activation has a -40 win interaction, -6.71 pp,[-12.58,-0.84]. A common hook alone does not explain the non-additivity. Source inspection shows duplicated territory control and compounded aggression scaling to0.39; this is a supported conflict hypothesis, not complete causal attribution.

Never-switch plan R5000 scores329 versus BP327; unreachable AF K16/W0 scores304. Plan4/6 R150 reproduce the common plan hook at R100 exactly on recorded checkpoints, while each differs from BP on31/480 real cells. Changed games therefore cannot be counted as intended feature triggers. AF still needs direct trigger/death-history telemetry.

Two reachable source concerns require main-PC attention: incomplete bush IDs/ward-cache coherence, and HIDEREC reading cached visibility before world refresh. Their match frequency/loss contribution is unmeasured; no repair is claimed. Strict-cache controls do not rescue siege65. The preregistered plan4/R150+siege45 attempt reduces parent real fuel227→212 but still fails versus BP206 and loses3 pp on styled maps. See [diagnostics](DIAGNOSTICS.md) for functions, evidence, minimal proposed corrections and exact R0/full-gate retests.

## Supplied walking-fuel work

K007's isolated source6ed38b9 preserves the earlier off/BP/P150 binaries. Its expanded179-map pool includes mazeB and has716 cells per line; raw scores are not interchangeable with the original596-cell exploration pool. Reserve10 lowers P150 real fuel227→193 and gives+18 wins over BP, but loses6 pp on styled maps. Reserve12 gives+3 with205 real fuel and a7 pp styled loss; reserve15 loses8 overall and raises real fuel versus BP. BP+reserve12 loses5. Fuel is not monotonic in the reserve because decisions/game paths change.

P100/reserve12 is the sole positive R1-passing novel reserve setting:412/716 versus BP393, real fuel185 versus206. The declared rule selects it before its fresh outcomes. It then scores456/894 versus BP464 (-8), fails maze/total R1, and trails x1 by38. Fresh131 versus BP120 (+11) and x1 123 (+8) is inconclusive. The original six finalists are unchanged. Full chronology, mazeA/B splits, uncertainty and binary-equivalence receipts are in [K007](K007.md).

K009 tests the main PC's supplied WALKTAIL guard at isolated source2732245, plus secure and base-only controls and the two additional K007 tail settings. Its candidate already passes the expanded x2 gate at419/716 versus BP393 (+26), real fuel172 versus206, but scores378/720 versus BP380 (-2) on the supplied three-opponent ladder/styled validation. Remaining bounded comparisons are pending; no ship/ladder/upload authorization or universal-strength claim follows the job title. At most one setting passing both complete gates may receive the declared supplemental40-map check. That suite has already been inspected for other configurations, so it will not be described as a newly untouched suite.

## Actionable recommendation

1. Preserve original x1 as a paired reference. BP and fuel-saving variants trade strength across opponents; a BP-relative pass alone is not an x1 upgrade.
2. Repair atomic bush-ID/ward coherence and fresh HIDEREC observations behind main-PC-controlled switches, preserving the repair-off binary. Verify counters/scenarios before strength tests. Do not expand the affected stacks first.
3. Retain AF5/W400 as the strongest observed-average follow-up. Verify actual triggers, address computation with the measured hotspots, and jointly tune caution. Avoid another blind fuel/threshold grid after the focused attempts.
4. Retain siege45 as the original campaign's conservative R1/fuel candidate. Its fresh win neutrality and x1 deficit must remain visible in any integration decision.
5. Retain AF on bush-rich fresh layouts as an adaptive-strategy hypothesis: +11.59 pp on23 maps, nominal95% [2.17,21.74]. Many correlated descriptors/settings were inspected; validate a fixed rule on a new suite before using it as map adaptation.

The40-map holdout uses related official components and structural screening, not demonstrated finals realism. Its maximum bush component80 leaves a gap against official358; an optional forest generator produced no qualifying set and no strength results. Standard149 maps retain those forests. Descriptors cover geometry/resources/connectivity proxies, not invented travel/contact times. Map, side/opponent and deterministic duplicate distinctions are preserved in [campaign verification](verification.json) and [K007 verification](K007/verification.json). Cached rows and repeated configuration references add no independent evidence; uncertainty resamples maps and is descriptive/unadjusted for selection/template ancestry. No feature is permanently rejected, and main PC retains integration authority.

Reports: [K004](K004.md), [K005](K005.md), [K006](K006.md), [K007](K007.md), [K009/addendum](K009.md), [diagnostics](DIAGNOSTICS.md). Numerical results/provenance accompany each line; native replay evidence stays local.
