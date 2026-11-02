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


## Second batch (07:55 UTC): the next seven J002 flags at or above baseline

Same gate, commit 0b3703b, `--set FLAG=1`. results.json added to RQ6/.

| line | wins (base 257) | Δ | ladder (143) | styled (114) | fuel-outs (339) | deaths/game (10.84) | gold@R500 (1868) | games changed | verdict |
|---|---|---|---|---|---|---|---|---|---|
| **A2_HIDEREC** | **264** | **+7** | 152 | 112 | 333 (-6) | 10.92 | 1874 | 196 | **pass** |
| **A2_BURST_HOLD** | **260** | **+3** | 147 | 113 | 334 (-5) | 10.61 | 1880 | 238 | **pass** |
| V58_LOCKS | 265 | +8 | 153 | 112 | 358 (+19) | 10.81 | 1860 | 311 | fail (fuel-outs only) |
| A2_DISENGAGE | 264 | +7 | 140 | 124 | 344 (+5) | 10.44 | 1869 | 406 | fail (fuel-outs +5 only) |
| A2_THREAT | 255 | -2 | 137 | 118 | 330 (-9) | 9.97 | 1888 | 476 | fail (total; ladder -2.1 pts) |
| A2_MAP_PROFILE | 251 | -6 | 137 | 114 | 391 (+52) | 10.32 | 1865 | 327 | fail (total, ladder, fuel +52) |
| APEX_STALE_BAG | 246 | -11 | 137 | 109 | 347 (+8) | 10.84 | 1863 | 258 | fail (total, kinds, fuel) |

Remaining J002 flags at or above baseline not yet gated: A2_ASSESS (+3 on the sweep but 607 fuel-outs on 76 games),
A2_TS_VIS, A2_RESETFIX, A2_FIELDFIRST, A2_BELIEF (+1 each). Next in my idle queue.
#### base: 257 wins vs base 257; verdict base

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 68/140 | +0 | 110 (+0) | 0 | 781 | 1777 | 10.89 | 1194 | 1746f2bb7fa3 |
| ladder | x2-s2 | 75/140 | +0 | 102 (+0) | 0 | 815 | 1806 | 10.71 | 1182 | 1746f2bb7fa3 |
| styled | x2 | 55/100 | +0 | 76 (+0) | 0 | 921 | 1946 | 11.16 | 1158 | 1746f2bb7fa3 |
| styled | x2-s2 | 59/100 | +0 | 51 (+0) | 0 | 957 | 2003 | 10.64 | 1164 | 1746f2bb7fa3 |

#### locks: 265 wins vs base 257; verdict **fail** (total +8, fuel-outs +19)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 74/140 | +6 | 119 (+9) | 0 | 779 | 1771 | 10.71 | 1183 | 81ad3024b1a5 |
| ladder | x2-s2 | 79/140 | +4 | 113 (+11) | 0 | 811 | 1784 | 10.79 | 1179 | 81ad3024b1a5 |
| styled | x2 | 56/100 | +1 | 77 (+1) | 0 | 918 | 1943 | 11.10 | 1154 | 81ad3024b1a5 |
| styled | x2-s2 | 56/100 | -3 | 49 (-2) | 0 | 957 | 2007 | 10.68 | 1166 | 81ad3024b1a5 |

#### mapprofile: 251 wins vs base 257; verdict **fail** (total -6, a map kind < -2 points, fuel-outs +52)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 69/140 | +1 | 124 (+14) | 0 | 780 | 1809 | 9.89 | 1185 | f4fbc12d11f4 |
| ladder | x2-s2 | 68/140 | -7 | 132 (+30) | 0 | 800 | 1773 | 10.14 | 1162 | f4fbc12d11f4 |
| styled | x2 | 56/100 | +1 | 75 (-1) | 0 | 917 | 1944 | 11.58 | 1162 | f4fbc12d11f4 |
| styled | x2-s2 | 58/100 | -1 | 60 (+9) | 0 | 947 | 1994 | 9.91 | 1146 | f4fbc12d11f4 |

#### stalebag: 246 wins vs base 257; verdict **fail** (total -11, a map kind < -2 points, fuel-outs +8)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 69/140 | +1 | 112 (+2) | 0 | 775 | 1773 | 10.65 | 1183 | f67cca44e4a7 |
| ladder | x2-s2 | 68/140 | -7 | 111 (+9) | 0 | 811 | 1800 | 10.84 | 1184 | f67cca44e4a7 |
| styled | x2 | 54/100 | -1 | 79 (+3) | 0 | 920 | 1953 | 11.38 | 1157 | f67cca44e4a7 |
| styled | x2-s2 | 55/100 | -4 | 45 (-6) | 0 | 954 | 1986 | 10.55 | 1172 | f67cca44e4a7 |

#### disengage: 264 wins vs base 257; verdict **fail** (total +7, fuel-outs +5)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 69/140 | +1 | 116 (+6) | 0 | 778 | 1766 | 10.88 | 1200 | 709bbdb5fbd0 |
| ladder | x2-s2 | 71/140 | -4 | 104 (+2) | 0 | 814 | 1819 | 10.01 | 1160 | 709bbdb5fbd0 |
| styled | x2 | 61/100 | +6 | 72 (-4) | 0 | 923 | 1950 | 10.90 | 1152 | 709bbdb5fbd0 |
| styled | x2-s2 | 63/100 | +4 | 52 (+1) | 0 | 947 | 2002 | 9.98 | 1149 | 709bbdb5fbd0 |

#### hiderec: 264 wins vs base 257; verdict **pass** (total +7)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 72/140 | +4 | 106 (-4) | 0 | 787 | 1776 | 10.75 | 1184 | 2bc3d23a5049 |
| ladder | x2-s2 | 80/140 | +5 | 103 (+1) | 0 | 831 | 1839 | 11.02 | 1190 | 2bc3d23a5049 |
| styled | x2 | 55/100 | +0 | 73 (-3) | 0 | 916 | 1948 | 11.08 | 1143 | 2bc3d23a5049 |
| styled | x2-s2 | 57/100 | -2 | 51 (+0) | 0 | 952 | 1988 | 10.86 | 1168 | 2bc3d23a5049 |

#### threat: 255 wins vs base 257; verdict **fail** (total -2, a map kind < -2 points)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 70/140 | +2 | 108 (-2) | 0 | 823 | 1850 | 9.14 | 1164 | 413f45b08b10 |
| ladder | x2-s2 | 67/140 | -8 | 109 (+7) | 0 | 815 | 1781 | 9.59 | 1180 | 413f45b08b10 |
| styled | x2 | 58/100 | +3 | 61 (-15) | 0 | 904 | 1995 | 10.68 | 1158 | 413f45b08b10 |
| styled | x2-s2 | 60/100 | +1 | 52 (+1) | 0 | 921 | 1984 | 10.95 | 1158 | 413f45b08b10 |

#### bursthold: 260 wins vs base 257; verdict **pass** (total +3)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 71/140 | +3 | 114 (+4) | 0 | 780 | 1787 | 10.69 | 1197 | 7a575a97f2a2 |
| ladder | x2-s2 | 76/140 | +1 | 105 (+3) | 0 | 816 | 1809 | 10.42 | 1185 | 7a575a97f2a2 |
| styled | x2 | 58/100 | +3 | 66 (-10) | 0 | 928 | 1963 | 10.94 | 1155 | 7a575a97f2a2 |
| styled | x2-s2 | 55/100 | -4 | 49 (-2) | 0 | 960 | 2026 | 10.45 | 1151 | 7a575a97f2a2 |


## Third batch (08:17 UTC): the last J002 flags at or above baseline

| line | wins (base 257) | Δ | ladder (143) | styled (114) | fuel-outs (339) | deaths/game (10.84) | gold@R500 (1868) | games changed | verdict |
|---|---|---|---|---|---|---|---|---|---|
| A2_TS_VIS | 268 | +11 | 150 | 118 | 423 (+84) | 10.47 | 1888 | 335 | fail (fuel-outs +84 only) |
| A2_BELIEF | 262 | +5 | 144 | 118 | 349 (+10) | 10.67 | 1875 | 233 | fail (fuel-outs only) |
| A2_RESETFIX | 253 | -4 | 140 | 113 | 341 (+2) | 10.86 | 1862 | 119 | fail (total, fuel) |
| A2_FIELDFIRST | 244 | -13 | 139 | 105 | 336 (-3) | 10.80 | 1873 | 402 | fail (total; styled -4.5 pts) |
| A2_ASSESS | 222 | -35 | 108 | 114 | **5214 (+4875)** | 9.50 | 1795 | 471 | fail (total, ladder, fuel) |

A2_ASSESS (v81hl's fight-or-run net, RETRY_QUEUE #9) runs out of fuel ~11 times a game: a fuel problem before it is a
strategy result. Every J002 flag at or above baseline now has its R1 gate.
#### base: 257 wins vs base 257; verdict base

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 68/140 | +0 | 110 (+0) | 0 | 781 | 1777 | 10.89 | 1194 | 1746f2bb7fa3 |
| ladder | x2-s2 | 75/140 | +0 | 102 (+0) | 0 | 815 | 1806 | 10.71 | 1182 | 1746f2bb7fa3 |
| styled | x2 | 55/100 | +0 | 76 (+0) | 0 | 921 | 1946 | 11.16 | 1158 | 1746f2bb7fa3 |
| styled | x2-s2 | 59/100 | +0 | 51 (+0) | 0 | 957 | 2003 | 10.64 | 1164 | 1746f2bb7fa3 |

#### tsvis: 268 wins vs base 257; verdict **fail** (total +11, fuel-outs +84)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 74/140 | +6 | 133 (+23) | 0 | 797 | 1852 | 10.01 | 1172 | 0fcc43b35b79 |
| ladder | x2-s2 | 76/140 | +1 | 141 (+39) | 0 | 817 | 1805 | 10.48 | 1177 | 0fcc43b35b79 |
| styled | x2 | 55/100 | +0 | 80 (+4) | 0 | 928 | 1961 | 11.31 | 1169 | 0fcc43b35b79 |
| styled | x2-s2 | 63/100 | +4 | 69 (+18) | 0 | 950 | 1981 | 10.27 | 1153 | 0fcc43b35b79 |

#### resetfix: 253 wins vs base 257; verdict **fail** (total -4, fuel-outs +2)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 66/140 | -2 | 110 (+0) | 0 | 776 | 1764 | 10.76 | 1182 | 8dd0cba97d1a |
| ladder | x2-s2 | 74/140 | -1 | 102 (+0) | 0 | 815 | 1798 | 10.85 | 1183 | 8dd0cba97d1a |
| styled | x2 | 53/100 | -2 | 75 (-1) | 0 | 916 | 1942 | 11.42 | 1158 | 8dd0cba97d1a |
| styled | x2-s2 | 60/100 | +1 | 54 (+3) | 0 | 954 | 2007 | 10.47 | 1158 | 8dd0cba97d1a |

#### fieldfirst: 244 wins vs base 257; verdict **fail** (total -13, a map kind < -2 points)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 68/140 | +0 | 106 (-4) | 0 | 799 | 1796 | 10.16 | 1172 | 5f2ef0720d35 |
| ladder | x2-s2 | 71/140 | -4 | 114 (+12) | 0 | 804 | 1791 | 10.81 | 1179 | 5f2ef0720d35 |
| styled | x2 | 54/100 | -1 | 64 (-12) | 0 | 922 | 1972 | 12.07 | 1170 | 5f2ef0720d35 |
| styled | x2-s2 | 51/100 | -8 | 52 (+1) | 0 | 938 | 1997 | 10.40 | 1136 | 5f2ef0720d35 |

#### belief: 262 wins vs base 257; verdict **fail** (total +5, fuel-outs +10)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 69/140 | +1 | 110 (+0) | 0 | 784 | 1786 | 10.62 | 1186 | 30c07b75377c |
| ladder | x2-s2 | 75/140 | +0 | 115 (+13) | 0 | 808 | 1808 | 10.91 | 1213 | 30c07b75377c |
| styled | x2 | 59/100 | +4 | 70 (-6) | 0 | 918 | 1933 | 11.28 | 1160 | 30c07b75377c |
| styled | x2-s2 | 59/100 | +0 | 54 (+3) | 0 | 961 | 2038 | 9.79 | 1152 | 30c07b75377c |

#### assess: 222 wins vs base 257; verdict **fail** (total -35, a map kind < -2 points, fuel-outs +4875)

| kind | opp | wins | Δ base | fuel-outs (Δ) | faults | gold@R250 | gold@R500 | deaths/game | finish round | sha |
|---|---|---|---|---|---|---|---|---|---|---|
| ladder | x2 | 56/140 | -12 | 1441 (+1331) | 0 | 775 | 1725 | 9.11 | 1180 | 644e399edeaf |
| ladder | x2-s2 | 52/140 | -23 | 1609 (+1507) | 0 | 771 | 1703 | 9.52 | 1198 | 644e399edeaf |
| styled | x2 | 55/100 | +0 | 1172 (+1096) | 0 | 869 | 1877 | 9.92 | 1154 | 644e399edeaf |
| styled | x2-s2 | 59/100 | +0 | 992 (+941) | 0 | 868 | 1938 | 9.57 | 1160 | 644e399edeaf |

