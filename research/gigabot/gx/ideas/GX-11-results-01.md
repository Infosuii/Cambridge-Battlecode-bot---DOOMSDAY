# GX-11: Side and geometry checks

The neutral rendering has the x3mf digest; all nine strategy arms have identical executable sections. The baseline has 341 wins (96, 115, 130) and 548 fuel-outs. All arms completed all 516 games with zero faults.

| Arm | v92 | v86h | x1bru | Total | Gained/lost | Paired z | Fuel-outs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 92 | 100 | 119 | 311 | 68/98 | -2.33 | 566 |
| 2 | 90 | 80 | 102 | 272 | 66/135 | -4.87 | 566 |
| 3 | 80 | 86 | 109 | 275 | 70/136 | -4.60 | 521 |
| 4 | 88 | 102 | 111 | 301 | 70/110 | -2.98 | 506 |
| 5 | 93 | 88 | 105 | 286 | 70/125 | -3.94 | 542 |
| 6 | 88 | 101 | 95 | 284 | 61/118 | -4.26 | 541 |
| 7 | 86 | 82 | 95 | 263 | 70/148 | -5.28 | 566 |
| 8 | 93 | 94 | 105 | 292 | 75/124 | -3.47 | 541 |
| 9 | 86 | 91 | 103 | 280 | 55/116 | -4.66 | 521 |

The side A fit chose 14 of 86 maps. It gained 29 wins and lost none on side A (202/258 versus 173/258). On untouched side B it gained one and lost 15 (154/258 versus 168/258, paired z −3.50): −8 vs v92, −4 vs v86h and −2 vs x1bru. Side B had 293 fuel-outs versus 295. The combined 356/516 would disguise the holdout loss, so the table stays out of release.

Two geometry fits selected on 43 side A maps gained six and four on their training folds. The other maps scored +1 and −4 on side A and −7 and −4 on side B. These thresholds do not transfer. The [frozen map choices](GX-11-selected.json) and [geometry folds](GX-11-topology.json) are recorded separately.
