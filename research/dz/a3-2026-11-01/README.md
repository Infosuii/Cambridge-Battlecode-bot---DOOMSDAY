# A3 lambda_gold fit (2026-11-01)

`tools/dz_a3_gold_fit.py` over every stored full-pool capsule (35,339 games, 270 runs): final margin regressed on our
gold, banked, collected and deaths at R250 and R500, within each (map, side, opponent) cell. Results: `RESULTS.json`.

| Checkpoint | margin per gold | margin per banked gem | gems per gold | margin per death |
|---|---|---|---|---|
| R250 | 0.127 (0.116-0.141) | 0.703 | **0.18** | -6.3 |
| R500 | 0.066 (0.059-0.073) | 0.670 | **0.10** | -3.9 |

Reading: the default job weight 0.1 matches mid-game; early gold is worth ~0.18 gems. The screened 0.5 (opening
gold) and 0.3 (gold value) overprice it ~3x, consistent with their losses (z14b: og, gv negative). `DZ_GOLD_FIT`
(plan bit `GOLD_FIT`): 0.18 before R250, then 0.1. Correlational, so it must pass its own paired screen. The death
coefficient (~6 gems per death by R250) is a data-based death cost for B1's expected exchange.
