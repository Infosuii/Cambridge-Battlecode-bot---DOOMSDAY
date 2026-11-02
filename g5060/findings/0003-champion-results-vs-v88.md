# 0003: retry queue #4 step 1, per-champion results from x1's own games vs v88 (facts)

Source: the 480 base-gate games (x1 1746f2bb7fa3 vs x2 and x2-s2, 70 ladder + 50 styled maps, both sides; summaries
in this machine's artifacts). x1 won 257. Per champion x1 drafted (per-pick averages over the games it was picked):

| champion | picks | win rate | ladder | styled | deaths | kills | earned gold | collected | banked |
|---|---|---|---|---|---|---|---|---|---|
| Tavi | 12 | 66.7% | - | 67% (12) | 6.42 | 1.75 | 707 | 150 | 118 |
| Ryth | 76 | 55.3% | 53% (60) | 62% (16) | 2.67 | 1.58 | 1203 | 232 | 191 |
| Cassi | 276 | 54.0% | 51% (124) | 57% (152) | 2.66 | 0.72 | 831 | 148 | 108 |
| Issac | 276 | 54.0% | 51% (124) | 57% (152) | 2.66 | 0.78 | 956 | 182 | 130 |
| Vendetta | 480 | 53.5% | 51% (280) | 57% (200) | 2.18 | 3.59 | 1473 | 304 | 229 |
| Marcella | 380 | 52.4% | 50% (208) | 55% (172) | 1.92 | 1.73 | 1159 | 182 | 152 |
| Heart of Ruin | 360 | 52.2% | 50% (212) | 56% (148) | 1.40 | 1.04 | 914 | 199 | 173 |
| Ren | 48 | 52.1% | 50% (40) | 62% (8) | 3.12 | 2.27 | 1736 | 270 | 134 |
| Vesper Vale | 56 | 51.8% | 52% (40) | 50% (16) | 1.88 | 0.68 | 1444 | 209 | 162 |
| Varg | 392 | 51.5% | 50% (236) | 53% (156) | 1.88 | 1.17 | 1155 | 243 | 186 |
| Willow | 40 | 45.0% | 45% (40) | - | 4.62 | 0.42 | 436 | 101 | 82 |

Limits: x1's draft is deterministic per map and side, so each champion's games are a fixed set of maps; a champion's
win rate is confounded with its maps (Cassi and Issac are always picked together; Vendetta is in every game). Same-map
comparisons of different lineups do not exist in these games, so these rates cannot rank champions on their own.

What stands out: **Willow** (40 picks, all ladder) 45% with 4.6 deaths, 0.4 kills and 436 earned gold a game, the
lowest of all; **Tavi** (12, styled) dies 6.4 times a game; **Ryth** has the best record with picks ≥ 50 (55%, 2.7
deaths, 1203 gold), matching the ladder note (Ryth our best pick). Vendetta carries the team's kills (3.6 a game).

Next step for #4 (R2): needs a draft-bias knob (`X1_MASTERY` bias 0.25 / 0.5, per the queue) to test "avoid Willow /
Tavi" as a switch; I can gate it as soon as it exists. A measured alternative without new code: branch the draft only
(a farm over lineups per map), which needs a draft hook.
