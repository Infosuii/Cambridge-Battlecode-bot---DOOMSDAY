# Rule 15 check (pc/IDEATION_RULES.md): the best lines vs v86h and v81hl, 2 Nov ~17:45 UTC

Commit 30af738. OPPS = v86h v81hl, SETS = ladder styled (rule 15), both sides: 480 games a line, base = x1 (1746f2bb7fa3;
its v86h ladder cell 79/140 equals the PC's x1e-cw-ladder-v86h-01). results.json in results/RQ15/.

| line | vs v86h ladder /140 | v86h styled /100 | vs v81hl ladder /140 | v81hl styled /100 | total /480 | Δ vs x1 | fuel-outs (x1 352) | deaths/game | gained / lost | z | rule 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| base | 79 | 59 | 81 | 47 | 266 | +0 | 352 | 9.74 | 0 / 0 | +0.00 | base |
| bp | 75 | 60 | 70 | 43 | 248 | -18 | 218 | 10.23 | 64 / 82 | -1.49 | fail |
| p4 | 76 | 57 | 69 | 41 | 243 | -23 | 255 | 8.54 | 94 / 117 | -1.58 | fail |
| bpp4r150 | 75 | 57 | 68 | 44 | 244 | -22 | 188 | 8.49 | 80 / 102 | -1.63 | fail |

**All three fail rule 15** (total below x1; v81hl ladder -11..-13 the largest part). Plan 4 still cuts deaths
(9.74 -> 8.5 a game) and BUSHPRE still cuts fuel-outs (352 -> 218), but neither turns into wins against these two.

Pooled over both opponent pairs (sign test, findings/0006):

| line | vs x2 + x2-s2 (gained / lost) | vs v86h + v81hl (gained / lost) | pooled gained / lost | pooled z |
|---|---|---|---|---|
| bpp4r150 | 137 / 106 (596 games, maze A) | 80 / 102 (480) | 217 / 208 | +0.44 |
| bp | 98 / 87 (596, maze A) | 64 / 82 (480) | 162 / 169 | -0.38 |

So the ship candidates' gain over x1 is not shown once a second opponent pair is added. x1 itself remains as good as
anything gated here against v86h / v81hl.
