# R1 full gates for the J002 sweep leaders (idle work; RETRY_QUEUE #6 / #8 / #9 owe R1 vs x2), 2 Nov 07:45 UTC

Commit 0b3703b. Lines: `--set V58_VISION=1`, `--set A2_BURST2=1`, `--set APEX_ESCORT=1` (each +7 on J002's 76
sweep games). Gate: x2 + x2-s2, ladder 70 + styled 50, both sides, 480 games a line; no maze cell. Base = x1
1746f2bb7fa3. Verdicts by tools/x1_gate_report.py, rule R1. results.json in RQ6/.

| line | wins (base 257) | Δ | ladder (143) | styled (114) | fuel-outs (339) | deaths/game (10.84) | gold@R500 (1868) | games changed | verdict |
|---|---|---|---|---|---|---|---|---|---|
| **APEX_ESCORT** | **265** | **+8** | 147 | 118 | 332 (-7) | 10.40 | 1845 | 382 | **pass** |
| A2_BURST2 | 270 | +13 | 151 | 119 | 359 (+20) | 10.05 | 1897 | 334 | fail (fuel-outs only) |
| V58_VISION | 244 | -13 | 132 | 112 | 323 (-16) | 10.60 | 1887 | 480 | fail (total; ladder -3.9 pts) |

V58_VISION's +7 on the 76 sweep games did not hold on the full 480 (-13): the sweep cells are a screen, as the PC
said. APEX_ESCORT passes; A2_BURST2 gains the most wins but adds 20 fuel-outs.

## Per cell
### base: 257 wins vs base 257; verdict base

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 68/140 | +0 | 110 (+0) | 0 | 781 | 1777 | 10.89 | 1194 | 1746f2bb7fa3 |
| ladder | x2-s2 | 75/140 | +0 | 102 (+0) | 0 | 815 | 1806 | 10.71 | 1182 | 1746f2bb7fa3 |
| styled | x2 | 55/100 | +0 | 76 (+0) | 0 | 921 | 1946 | 11.16 | 1158 | 1746f2bb7fa3 |
| styled | x2-s2 | 59/100 | +0 | 51 (+0) | 0 | 957 | 2003 | 10.64 | 1164 | 1746f2bb7fa3 |

### vision: 244 wins vs base 257; verdict **fail** (total -13, a map kind < -2 points)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 67/140 | -1 | 104 (-6) | 0 | 801 | 1778 | 10.76 | 1162 | b5f84253f7d1 |
| ladder | x2-s2 | 65/140 | -10 | 93 (-9) | 0 | 813 | 1813 | 11.00 | 1171 | b5f84253f7d1 |
| styled | x2 | 58/100 | +3 | 69 (-7) | 0 | 933 | 2007 | 9.81 | 1146 | b5f84253f7d1 |
| styled | x2-s2 | 54/100 | -5 | 57 (+6) | 0 | 931 | 2025 | 10.59 | 1150 | b5f84253f7d1 |

### burst2: 270 wins vs base 257; verdict **fail** (total +13, fuel-outs +20)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 75/140 | +7 | 116 (+6) | 0 | 782 | 1800 | 10.85 | 1195 | e734a973a32f |
| ladder | x2-s2 | 76/140 | +1 | 114 (+12) | 0 | 818 | 1846 | 9.51 | 1184 | e734a973a32f |
| styled | x2 | 59/100 | +4 | 76 (+0) | 0 | 907 | 1986 | 9.75 | 1157 | e734a973a32f |
| styled | x2-s2 | 60/100 | +1 | 53 (+2) | 0 | 941 | 2017 | 9.96 | 1126 | e734a973a32f |

### escort: 265 wins vs base 257; verdict **pass** (total +8)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 70/140 | +2 | 113 (+3) | 0 | 763 | 1724 | 10.81 | 1212 | 3bdbdc32a554 |
| ladder | x2-s2 | 77/140 | +2 | 103 (+1) | 0 | 805 | 1789 | 9.88 | 1171 | 3bdbdc32a554 |
| styled | x2 | 63/100 | +8 | 53 (-23) | 0 | 938 | 1984 | 9.82 | 1137 | 3bdbdc32a554 |
| styled | x2-s2 | 55/100 | -4 | 63 (+12) | 0 | 908 | 1955 | 11.13 | 1165 | 3bdbdc32a554 |

