# V52 loss audit — 2026-10-25

Snapshot: ranked 2/5; unranked 4/15 since 12:02 UTC; combined 6/20. Named queued groups are 1/5 against Hidden Altar Keepers and 0/5 against meow. The API timestamps place those groups at 12:05 UTC, earlier than the approximate 12:15 handoff note. Version association uses start time; API list responses do not expose a submission hash.

All 14 losses and seven top-team wins decoded with the pinned engine, 21/21 successful. This report is omniscient offline analysis. Deaths are alive→dead transitions sampled once per round; attack counts include basic attacks classified by target tile, exclude spells, and are proxies for fight allocation. Equipment value is original shard purchase gold (five shards per emblem), not raw inventory-entry counts. Full audits and replays are local-only.

## Losses ranked by score deficit

| Map | Kind | Opponent | Score us/them | Deaths us/them | First bank / median amount: us | Winner | Gear purchase value R500 us/them |
|---|---|---|---|---|---|---|---|
| 01concentrated_wealth | unranked | meow | 77/1050 | 14/3 | R396, median 38.5, 2 channels | R71, median 23, 34 channels | 1200/3000 |
| 00stampede | unranked | meow | 80/1040 | 8/5 | R1209, median 40, 2 channels | R834, median 80, 10 channels | 1530/2970 |
| 00fragment | unranked | Crimson Pathfinders | 106/1020 | 10/5 | R174, median 8, 11 channels | R56, median 26, 55 channels | 570/2280 |
| 01concentrated_wealth | unranked | Hidden Altar Keepers | 164/1004 | 9/0 | R63, median 26, 8 channels | R84, median 23, 39 channels | 900/2550 |
| 00elkring | unranked | Hidden Altar Keepers | 374/1012 | 10/2 | R78, median 22, 14 channels | R64, median 22, 38 channels | 2160/3840 |
| 01corridors | unranked | Crimson Pathfinders | 398/1006 | 11/1 | R657, median 72, 6 channels | R73, median 58, 9 channels | 1860/1410 |
| 01big_world | unranked | meow | 587/1169 | 2/1 | R94, median 30, 20 channels | R154, median 30, 25 channels | 1350/2550 |
| 00elkring | unranked | meow | 462/1001 | 12/1 | R60, median 22, 16 channels | R75, median 22, 28 channels | 1920/2550 |
| 01islands | unranked | meow | 569/1010 | 2/2 | R73, median 26, 25 channels | R54, median 19, 39 channels | 2190/2580 |
| 00ambush | ranked | Manta | 588/1006 | 3/5 | R784, median 37, 13 channels | R306, median 37, 25 channels | 1140/1170 |
| 01islands | unranked | Hidden Altar Keepers | 622/1026 | 5/2 | R92, median 29, 25 channels | R50, median 30, 28 channels | 2040/2700 |
| 01big_world | unranked | Hidden Altar Keepers | 758/1032 | 0/0 | R105, median 18.5, 26 channels | R200, median 40.5, 26 channels | 1140/2340 |
| 00monolith | ranked | Manta | 769/1010 | 19/8 | R207, median 19, 27 channels | R96, median 22, 41 channels | 2520/2760 |
| 01fracture | ranked | Manta | 795/1005 | 8/12 | R98, median 44.5, 16 channels | R290, median 44, 24 channels | 1800/2160 |

## Map ranking (losses only, not win rates)

| Pattern | Losses | Mean deficit |
|---|---|---|
| 01concentrated_wealth | 2 | 906.5 |
| 00elkring | 2 | 588.5 |
| 00stampede | 1 | 960.0 |
| 00fragment | 1 | 914.0 |
| 01big_world | 2 | 428.0 |
| 01islands | 2 | 422.5 |
| 01corridors | 1 | 608.0 |
| 00ambush | 1 | 418.0 |
| 00monolith | 1 | 241.0 |
| 01fracture | 1 | 210.0 |

## Opponent ranking (losses only, not win rates)

| Pattern | Losses | Mean deficit |
|---|---|---|
| meow | 5 | 699.0 |
| Hidden Altar Keepers | 4 | 539.0 |
| Crimson Pathfinders | 2 | 761.0 |
| Manta | 3 | 289.7 |

## Our draft set ranking (losses only, not win rates)

| Pattern | Losses | Mean deficit |
|---|---|---|
| Vendetta, Marcella, Ren, Varg, Tavi | 3 | 743.7 |
| Vendetta, Prism, Marcella, Ren, Varg | 2 | 799.0 |
| Vendetta, Cassi+Issac, Marcella, Ren, Varg | 2 | 511.5 |
| Vendetta, Marcella, Heart | 1 | 914.0 |
| Vendetta, Cassi+Issac, Ren, Varg, Tavi | 2 | 339.0 |
| Ryth, Vendetta, Cassi+Issac, Marcella, Varg | 1 | 608.0 |
| Vendetta, Prism, Marcella, Ren, Tavi | 1 | 539.0 |
| Vesper, Vendetta, Prism, Ren, Varg | 1 | 241.0 |
| Vendetta, Prism, Ren, Varg, Tavi | 1 | 210.0 |

## Per-loss farming, banking, fighting and draft comparisons

### 00ambush vs Manta (4b6f7abd-44bf-47bb-b391-f50721e5bcf0)

Our draft: Vendetta, Marcella, Ren, Varg, Tavi. Winner: Vesper, Heart, Marcella, Ryth, Vendetta.
Our first distinct camp attack targets: R51 gem(71,44); R51 gem(41,49); R52 gem(70,44); R53 gem(42,48); R53 gem(71,45); R54 gem(70,45); R57 gem(41,48); R63 gem(58,51).
Winner's first targets: R43 elk(30,44); R112 gem(70,44); R113 gem(71,44); R114 gem(70,45); R115 gem(71,45); R131 gem(28,54); R133 gem(29,54); R136 gem(28,55).
Banks us: R784, median 37, 13 channels; winner: R306, median 37, 25 channels. Basic camp/champion attacks us 750/188, winner 957/538. Deaths 3/5; gear purchase value at R100 120/0, R500 1140/1170. Final carried gems 121/14.

### 00elkring vs Hidden Altar Keepers (06973518-7f4c-48b1-8db5-2423709f2ba4)

Our draft: Vendetta, Marcella, Ren, Prism, Varg. Winner: Heart, Marcella, Vesper, Ryth, Vendetta.
Our first distinct camp attack targets: R4 elk(3,6); R5 golem(4,6); R10 elk(9,2); R10 golem(9,3); R25 elk(3,12); R60 gem(3,19); R87 gem(3,7); R112 elk(19,2).
Winner's first targets: R3 elk(26,23); R13 gem(26,22); R18 elk(26,17); R19 elk(20,27); R31 gem(19,27); R48 elk(26,9); R62 elk(10,27); R73 gem(26,10).
Banks us: R78, median 22, 14 channels; winner: R64, median 22, 38 channels. Basic camp/champion attacks us 752/798, winner 903/283. Deaths 10/2; gear purchase value at R100 210/600, R500 2160/3840. Final carried gems 66/22.

### 00elkring vs meow (7acf2d0a-efd9-44ed-bb09-9dd593023f8c)

Our draft: Vendetta, Marcella, Ren, Prism, Tavi. Winner: Vesper, Vendetta, Heart, Ryth, Marcella.
Our first distinct camp attack targets: R4 elk(26,23); R4 golem(25,23); R11 golem(26,18); R13 elk(26,17); R20 gem(26,22); R26 elk(20,27); R29 golem(20,26); R40 gem(26,16).
Winner's first targets: R3 golem(4,6); R3 elk(3,6); R6 gem(3,7); R13 golem(9,3); R14 elk(9,2); R15 gem(10,2); R32 golem(3,11); R34 gem(3,13).
Banks us: R60, median 22, 16 channels; winner: R75, median 22, 28 channels. Basic camp/champion attacks us 820/261, winner 1081/681. Deaths 12/1; gear purchase value at R100 180/480, R500 1920/2550. Final carried gems 44/0.

### 00fragment vs Crimson Pathfinders (780641d2-b273-4be2-89ad-4f5d468e418f)

Our draft: Vendetta, Marcella, Heart. Winner: Vesper, Vendetta, Tavi.
Our first distinct camp attack targets: R5 wolf(27,18); R9 golem(18,13); R10 elk(17,13); R44 gem(28,18); R49 wolf(27,24); R55 wolf(17,14); R89 gem(28,24); R357 wolf(2,5).
Winner's first targets: R6 golem(11,16); R7 elk(12,16); R7 wolf(12,15); R35 gem(13,15); R42 gem(16,14); R42 wolf(17,14); R70 gem(1,11); R71 wolf(2,11).
Banks us: R174, median 8, 11 channels; winner: R56, median 26, 55 channels. Basic camp/champion attacks us 644/569, winner 1025/775. Deaths 10/5; gear purchase value at R100 0/420, R500 570/2280. Final carried gems 0/0.

### 00monolith vs Manta (8f3e85d0-4719-4a0b-97fe-75a67275d1c7)

Our draft: Vendetta, Vesper, Varg, Ren, Prism. Winner: Heart, Marcella, Ryth, Vesper, Vendetta.
Our first distinct camp attack targets: R10 elk(36,11); R13 gem(36,12); R16 golem(35,12); R25 gem(45,18); R26 golem(39,24); R28 wolf(46,18); R28 wolf(40,25); R31 wolf(41,25).
Winner's first targets: R12 wolf(15,46); R16 elk(13,38); R24 golem(15,45); R42 wolf(3,31); R48 gem(25,31); R49 wolf(8,24); R49 gem(26,31); R63 wolf(9,24).
Banks us: R207, median 19, 27 channels; winner: R96, median 22, 41 channels. Basic camp/champion attacks us 1281/754, winner 1197/669. Deaths 19/8; gear purchase value at R100 270/180, R500 2520/2760. Final carried gems 278/4.

### 00stampede vs meow (276e80d1-b6ee-414c-bb86-936ce58bede5)

Our draft: Vendetta, Marcella, Varg, Ren, Prism. Winner: Vesper, Vendetta, Heart, Ryth, Marcella.
Our first distinct camp attack targets: R11 gem(13,48); R11 gem(13,47); R23 gem(24,48); R25 gem(24,47); R28 gem(19,25); R29 gem(3,25); R31 gem(3,24); R32 gem(2,24).
Winner's first targets: R9 gem(13,1); R10 gem(13,2); R23 gem(24,1); R25 gem(24,2); R31 gem(18,24); R32 gem(19,24); R39 gem(34,1); R41 gem(34,2).
Banks us: R1209, median 40, 2 channels; winner: R834, median 80, 10 channels. Basic camp/champion attacks us 220/135, winner 898/228. Deaths 8/5; gear purchase value at R100 120/480, R500 1530/2970. Final carried gems 0/0.

### 01big_world vs meow (f11b26b7-f7e1-4027-b9a1-04271ebaa535)

Our draft: Vendetta, Ren, Varg, Cassi+Issac, Marcella. Winner: Vesper, Vendetta, Heart, Varg, Marcella.
Our first distinct camp attack targets: R6 gem(87,3); R7 elk(88,3); R42 gem(74,24); R43 wolf(73,24); R83 gem(27,21); R98 gem(59,65); R100 gem(59,66); R104 golem(13,15).
Winner's first targets: R10 gem(12,96); R11 elk(11,96); R11 gem(10,96); R40 gem(38,89); R41 wolf(39,89); R42 gem(40,89); R43 elk(38,88); R47 golem(40,88).
Banks us: R94, median 30, 20 channels; winner: R154, median 30, 25 channels. Basic camp/champion attacks us 1139/27, winner 1455/178. Deaths 2/1; gear purchase value at R100 120/420, R500 1350/2550. Final carried gems 79/56.

### 01big_world vs Hidden Altar Keepers (567a930d-6de3-45f6-b091-486d0684e6a4)

Our draft: Vendetta, Cassi+Issac, Varg, Ren, Tavi. Winner: Heart, Marcella, Vesper, Ryth, Vendetta.
Our first distinct camp attack targets: R6 elk(11,96); R7 gem(12,96); R48 wolf(26,75); R61 gem(25,75); R71 gem(72,78); R84 gem(59,65); R86 gem(59,66); R92 golem(47,71).
Winner's first targets: R11 elk(88,3); R43 elk(60,11); R43 elk(61,11); R63 wolf(60,10); R79 wolf(73,24); R102 gem(74,24); R304 golem(59,11); R384 gem(61,10).
Banks us: R105, median 18.5, 26 channels; winner: R200, median 40.5, 26 channels. Basic camp/champion attacks us 1057/149, winner 1409/10. Deaths 0/0; gear purchase value at R100 120/180, R500 1140/2340. Final carried gems 111/8.

### 01concentrated_wealth vs meow (71ee12b7-444e-42f2-98b2-415570b44f07)

Our draft: Vendetta, Ren, Marcella, Varg, Tavi. Winner: Vesper, Vendetta, Heart, Varg, Marcella.
Our first distinct camp attack targets: R22 wolf(29,13); R33 gem(29,12); R33 wolf(30,13); R45 wolf(43,17); R66 wolf(58,1); R69 golem(59,2); R76 wolf(59,1); R97 gem(32,31).
Winner's first targets: R19 gem(59,58); R21 golem(58,59); R22 elk(59,59); R55 gem(31,48); R59 wolf(31,47); R66 gem(35,30); R67 wolf(34,30); R67 wolf(30,47).
Banks us: R396, median 38.5, 2 channels; winner: R71, median 23, 34 channels. Basic camp/champion attacks us 664/329, winner 1142/793. Deaths 14/3; gear purchase value at R100 90/150, R500 1200/3000. Final carried gems 131/0.

### 01concentrated_wealth vs Hidden Altar Keepers (91bc4053-9d19-4c54-8c8f-6a924af0e6a6)

Our draft: Vendetta, Marcella, Ren, Varg, Tavi. Winner: Heart, Marcella, Vesper, Ryth, Vendetta.
Our first distinct camp attack targets: R21 wolf(31,47); R32 wolf(30,47); R32 gem(31,48); R35 gem(35,30); R37 wolf(34,30); R57 wolf(17,43); R65 golem(1,58); R67 wolf(2,59).
Winner's first targets: R25 elk(1,1); R25 wolf(29,13); R37 wolf(30,13); R64 wolf(43,17); R71 elk(30,30); R131 wolf(26,30); R146 gem(25,30); R160 gem(29,28).
Banks us: R63, median 26, 8 channels; winner: R84, median 23, 39 channels. Basic camp/champion attacks us 837/685, winner 989/252. Deaths 9/0; gear purchase value at R100 150/240, R500 900/2550. Final carried gems 71/4.

### 01corridors vs Crimson Pathfinders (f80ae529-6c2e-41a4-9291-6710b05cd050)

Our draft: Vendetta, Varg, Ryth, Marcella, Cassi+Issac. Winner: Tavi, Vesper, Prism, Willow, Ryth.
Our first distinct camp attack targets: R24 wolf(9,20); R36 wolf(45,20); R37 wolf(9,19); R38 gem(8,20); R48 wolf(45,19); R192 gem(44,20); R210 gem(44,19); R324 wolf(6,19).
Winner's first targets: R16 golem(22,19); R17 golem(20,19); R18 golem(22,20); R19 elk(21,19); R19 golem(20,20); R28 elk(21,20); R84 golem(2,19); R85 gem(0,19).
Banks us: R657, median 72, 6 channels; winner: R73, median 58, 9 channels. Basic camp/champion attacks us 1361/480, winner 793/101. Deaths 11/1; gear purchase value at R100 180/210, R500 1860/1410. Final carried gems 232/0.

### 01fracture vs Manta (a6ecfcac-5419-45b7-a9ef-0f7e21d085e7)

Our draft: Vendetta, Varg, Ren, Prism, Tavi. Winner: Vesper, Heart, Marcella, Ryth, Vendetta.
Our first distinct camp attack targets: R16 wolf(40,66); R25 gem(26,60); R27 wolf(25,60); R32 wolf(58,37); R33 gem(39,66); R77 golem(13,33); R80 gem(5,69); R80 gem(12,42).
Winner's first targets: R30 elk(15,23); R31 wolf(16,24); R47 elk(43,8); R75 wolf(35,10); R88 elk(40,24); R121 wolf(15,24); R211 gem(27,33); R221 golem(16,23).
Banks us: R98, median 44.5, 16 channels; winner: R290, median 44, 24 channels. Basic camp/champion attacks us 1405/466, winner 1256/151. Deaths 8/12; gear purchase value at R100 0/0, R500 1800/2160. Final carried gems 138/108.

### 01islands vs meow (9701a5f5-a17f-4859-8b63-0bb5220bd767)

Our draft: Vendetta, Ren, Varg, Marcella, Cassi+Issac. Winner: Vesper, Vendetta, Heart, Varg, Marcella.
Our first distinct camp attack targets: R2 gem(30,52); R4 gem(29,52); R10 gem(26,47); R11 gem(25,47); R13 gem(27,47); R27 gem(30,42); R29 wolf(31,42); R36 gem(23,39).
Winner's first targets: R4 gem(30,7); R15 gem(33,12); R16 gem(34,12); R18 gem(32,12); R24 elk(9,10); R25 gem(9,11); R33 elk(8,10); R47 gem(16,16).
Banks us: R73, median 26, 25 channels; winner: R54, median 19, 39 channels. Basic camp/champion attacks us 856/349, winner 1467/327. Deaths 2/2; gear purchase value at R100 240/270, R500 2190/2580. Final carried gems 0/30.

### 01islands vs Hidden Altar Keepers (6454fe04-1828-4079-a068-cbe02168d829)

Our draft: Vendetta, Varg, Ren, Cassi+Issac, Tavi. Winner: Heart, Marcella, Vesper, Ryth, Vendetta.
Our first distinct camp attack targets: R4 gem(29,7); R10 gem(34,12); R12 gem(33,12); R13 gem(32,12); R21 gem(29,17); R23 wolf(28,17); R29 gem(16,16); R36 gem(36,20).
Winner's first targets: R4 gem(30,52); R21 elk(50,49); R32 elk(51,49); R63 gem(29,52); R77 elk(55,29); R87 elk(54,29); R123 gem(51,48); R177 elk(8,50).
Banks us: R92, median 29, 25 channels; winner: R50, median 30, 28 channels. Basic camp/champion attacks us 868/126, winner 1033/232. Deaths 5/2; gear purchase value at R100 150/90, R500 2040/2700. Final carried gems 4/0.

## Top-team reference wins

- 00elkring: Intercontinental Fish (010d3df2-b618-4644-ac9c-b35cc8135913), [671, 1012], 838 rounds. Draft Vesper, Vendetta, Heart, Cassi+Issac, Marcella. Bank R46, median 44, 22 channels; deaths 13; gear value R100/R500 360/4650. First targets: R2 golem(25,23); R2 elk(26,23); R7 gem(26,22); R12 golem(26,18); R14 elk(26,17); R15 gem(26,16); R25 golem(20,26); R28 gem(19,27).
- 00swirl: Intercontinental Fish (15b5b3ec-e3bd-4eaa-8162-f824e7bcb860), [943, 1012], 1226 rounds. Draft Vesper, Vendetta, Heart, Cassi+Issac. Bank R170, median 25, 18 channels; deaths 29; gear value R100/R500 270/2220. First targets: R4 gem(25,16); R5 elk(24,15); R7 gem(25,15); R16 gem(24,20); R18 gem(24,21); R22 gem(29,16); R24 gem(29,17); R25 wolf(30,16).
- 00monolith: Intercontinental Fish (3623f8c7-afb7-4be0-8718-803019d053f2), [237, 1155], 763 rounds. Draft Vesper, Vendetta, Heart, Cassi+Issac, Marcella. Bank R43, median 22, 29 channels; deaths 2; gear value R100/R500 540/4200. First targets: R9 gem(36,12); R10 elk(36,11); R11 golem(35,12); R13 gem(35,11); R21 gem(45,18); R25 wolf(46,18); R27 gem(24,18); R27 golem(34,4).
- 01fracture: Intercontinental Fish (8f2aeb6e-6748-4008-a851-224599c809a9), [767, 1173], 1009 rounds. Draft Vesper, Vendetta, Heart, Cassi+Issac, Ren. Bank R182, median 37.5, 24 channels; deaths 7; gear value R100/R500 450/2730. First targets: R19 golem(44,47); R19 elk(45,47); R20 wolf(44,46); R22 gem(44,45); R27 gem(45,45); R32 wolf(45,46); R47 gem(39,66); R50 wolf(40,66).
- 01concentrated_wealth: Intercontinental Fish (af8b9785-6f9a-47b3-ae8a-880a8a8841e1), [236, 1056], 1243 rounds. Draft Vesper, Vendetta, Heart, Cassi+Issac, Ren. Bank R92, median 22.5, 36 channels; deaths 10; gear value R100/R500 570/2580. First targets: R28 gem(31,32); R30 golem(31,31); R30 gem(30,32); R30 gem(32,31); R32 golem(31,30); R33 gem(29,32); R34 golem(30,31); R34 golem(29,31).
- 01boss_battle: Intercontinental Fish (d45f80c1-2cd3-4a9e-b6f2-80204c50f6c2), [0, 1034], 741 rounds. Draft Vesper, Vendetta, Heart, Cassi+Issac, Marcella. Bank R684, median 97, 5 channels; deaths 7; gear value R100/R500 690/5910. First targets: R8 gem(28,28); R10 elk(29,28); R10 elk(28,27); R24 gem(29,24); R25 elk(28,24); R27 gem(27,23); R33 elk(28,23); R46 gem(37,31).
- 01yellow_brick_road: Intercontinental Fish (df0e9d18-1f7f-4647-889f-a5c341568a1b), [482, 1004], 788 rounds. Draft Vesper, Vendetta, Heart, Cassi+Issac, Marcella. Bank R33, median 30, 28 channels; deaths 10; gear value R100/R500 1110/7140. First targets: R2 wolf(33,20); R3 gem(33,17); R4 gem(30,12); R5 gem(31,12); R6 gem(34,17); R6 gem(32,12); R7 gem(29,12); R8 gem(28,12).

## Local reproduction and conclusions

- `tools/v53_diagnose.py` reproduced boss-battle, concentrated-wealth, elkring, swirl and yellow-brick-road at default fuel using the documented logging/profile copies. Full logs are under artifacts/local-only/v53-review/{log,profile}. Local holdout maps were not used for tuning.
- Boss-battle: the logging build has carriers with 136–482 gems at R1200 and repeated cmicro positions around the gated altar. The winning reference starts attacking a monolith at R518 and first banks 581 at R684; a Marcella has 4,900 maximum health at R500. Merely copying its draft fails in our controller. Objective readiness and income allocation, rather than an early whole-team rush, remain unresolved.
- Concentrated-wealth: large death and farming deficits dominate both target scrimmages. In the Hidden Altar Keepers game we spend 685 basic attacks on champions versus 252 by the winner, yet die 9 times versus zero. Our own capture/wait behavior and lower equipment value are worth measuring; a short wait is not by itself evidence of a freeze.
- Elkring: deaths 10–12 versus 1–2; examine solo commits and nearby camp aggro before changing banking thresholds. A new learned draft loses all six local tests, so the observational draft association is insufficient.
- Swirl: the logging reproduction has frequent approach/capture travel and linked Cassi/Issac still at only 925/1300 maximum health at R1200. The new draft model also loses all six. No validated cheap fix yet.
- Yellow-brick-road: profile shows world work above 60k fuel on heavy turns, with suspended decisions. The reference winner has much more spent equipment by R500 and starts banking at R33. Redundant mask initialization is directly confirmed in the SDK and is the next isolated fuel candidate.
- Big-world/islands fixes remove specific reachability failures, but do not make farming competitive with top teams: in the two big-world losses the winner makes 1,409–1,455 basic camp attacks versus our 1,057–1,139. Their R500 equipment lead supports a tempo hypothesis.
- Monolith/fracture are inspected through ladder replays only. Monolith loss has 19 deaths versus eight and fewer bank channels. Fracture loss has more champion attacks despite fewer banks; local holdout tests remain reserved for release.

## Rules and API cross-check

User-supplied game rules and C++ API reference were consulted. Group damage wakes all members; capture speed is unchanged by extra allies; spawn occupancy delays respawns; tribute is not cancelled by ordinary damage; unused fuel does not carry over. The installed SDK bitboard default constructor calls clear(), so immediate explicit clear() calls are redundant host calls. These findings are implementation evidence, not instructions from the reference documents.
