# EXP-028 release result

Two release builds reproduce 44ecccc5f1a46f588896cc9b3a7ad7a9affc7b49a4af5912deaa35e1ef15ed7b. The switch-off build is byte-identical to platform v80 / repo v92 at 5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47. See [build hashes](OPENING_FINISH_BUILDS.json).

The exact release, without diagnostics, made the same actor/group/round clear in all nine registered development cases. Unmodified v92 matched none at those checkpoints. Both ran with zero faults in these 18 games. The [release mechanism rows](OPENING_FINISH_RELEASE_MECHANISM.json) are selected by observed behavior, so their wins provide no strength estimate. Clarification to the prototype report: the immediate SDK test did not record its return code or post-action health separately. The native record establishes the clear. The reason the earlier check missed it is unverified.

The [172-cell pool screen](OPENING-FINISH_POOL_SAFETY.json) gave 87 wins versus 86, b/c 6/5, +0.581 pp with a 95% map-cluster interval of −2.907 to +4.651 pp. Both arms had zero faults and zero diagnostic codes. Both had 28 round-one suspensions with no round-one cell increases. Total fuel suspensions were 169 versus 160, with six cell increases, including four previously clean cells.

Rejected at the original L0 fuel gate. Preserve the measured mechanism for future opening work. No selection of map, side, thresholds or policy changes from the failed pool result. L1, L2, ladder pairing and holdout were unopened for this candidate.
