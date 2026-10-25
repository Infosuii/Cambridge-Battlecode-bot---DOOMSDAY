# V52 loss audit — 2026-10-25

Refreshed snapshot: ranked 8/20; unranked 27/55 since 12:02 UTC. Named queued groups are 1/5 against Hidden Altar Keepers and 0/5 against meow. The initial snapshot was ranked 2/5 and unranked 4/15 and is preserved separately. API timestamps place the groups at 12:05 UTC, earlier than the approximate 12:15 handoff note. Version association uses start time; API list responses do not expose a submission hash.

All 40 losses and seven top-team wins decoded with the pinned engine, 47/47 successful. This report is omniscient offline analysis. Deaths are alive→dead transitions sampled once per round; attack counts include basic attacks classified by target tile, exclude spells, and are proxies for fight allocation. Equipment value is original shard purchase gold (five shards per emblem), not raw inventory-entry counts. Full audits and replays are local-only.

## Losses ranked by score deficit

| Map | Kind | Opponent | Score us/them | Deaths us/them | First bank / median amount: us | Winner | Gear purchase value R500 us/them |
|---|---|---|---|---|---|---|---|
| 01concentrated_wealth | unranked | meow | 77/1050 | 14/3 | R396, median 38.5, 2 channels | R71, median 23, 34 channels | 1200/3000 |
| 00stampede | unranked | meow | 80/1040 | 8/5 | R1209, median 40, 2 channels | R834, median 80, 10 channels | 1530/2970 |
| 00gemfight | ranked | error404 | 85/1001 | 10/7 | R558, median 25, 3 channels | R63, median 14, 43 channels | 690/2250 |
| 00fragment | unranked | Crimson Pathfinders | 106/1020 | 10/5 | R174, median 8, 11 channels | R56, median 26, 55 channels | 570/2280 |
| 01concentrated_wealth | unranked | Hidden Altar Keepers | 164/1004 | 9/0 | R63, median 26, 8 channels | R84, median 23, 39 channels | 900/2550 |
| 01yellow_brick_road | unranked | Ninja Turtles | 200/1027 | 30/6 | R167, median 18.5, 12 channels | R33, median 15.5, 48 channels | 1260/3510 |
| 00swirl | unranked | Turbo Gold Clusters | 226/1026 | 22/7 | R56, median 15, 12 channels | R179, median 30, 33 channels | 990/4110 |
| 01concentrated_wealth | ranked | Ding | 233/1006 | 6/7 | R421, median 30, 9 channels | R130, median 22, 34 channels | 1110/2640 |
| 00reverse_spiral | ranked | Ding | 307/1045 | 12/18 | R53, median 22, 11 channels | R120, median 30, 29 channels | 630/1920 |
| 01starfish | unranked | Ninja Turtles | 335/1044 | 45/26 | R66, median 8, 14 channels | R52, median 8, 23 channels | 1440/2070 |
| 00elkring | unranked | Hidden Altar Keepers | 374/1012 | 10/2 | R78, median 22, 14 channels | R64, median 22, 38 channels | 2160/3840 |
| 01corridors | unranked | Crimson Pathfinders | 398/1006 | 11/1 | R657, median 72, 6 channels | R73, median 58, 9 channels | 1860/1410 |
| 01big_world | unranked | meow | 587/1169 | 2/1 | R94, median 30, 20 channels | R154, median 30, 25 channels | 1350/2550 |
| 00elkring | unranked | meow | 462/1001 | 12/1 | R60, median 22, 16 channels | R75, median 22, 28 channels | 1920/2550 |
| 00fragment | unranked | Rogue Elk | 373/899 | 26/9 | R157, median 8, 31 channels | R108, median 26, 33 channels | 1020/1980 |
| 01elk_arena | ranked | Ding | 360/864 | 27/24 | R566, median 72, 5 channels | R345, median 72, 12 channels | 1650/3300 |
| 00swirl | unranked | Rogue Elk | 530/1007 | 19/7 | R56, median 15, 25 channels | R204, median 24.5, 34 channels | 1560/3870 |
| 01islands | unranked | meow | 569/1010 | 2/2 | R73, median 26, 25 channels | R54, median 19, 39 channels | 2190/2580 |
| 00elkring | unranked | Ninja Turtles | 561/1001 | 15/5 | R46, median 22, 22 channels | R60, median 22, 34 channels | 2280/2790 |
| 00ambush | ranked | Manta | 588/1006 | 3/5 | R784, median 37, 13 channels | R306, median 37, 25 channels | 1140/1170 |
| 00rows | ranked | error404 | 630/1048 | 0/2 | R66, median 19, 35 channels | R191, median 35, 16 channels | 2640/3120 |
| 01islands | unranked | Hidden Altar Keepers | 622/1026 | 5/2 | R92, median 29, 25 channels | R50, median 30, 28 channels | 2040/2700 |
| 00fragment | unranked | Ninja Turtles | 458/820 | 36/14 | R59, median 18.5, 26 channels | R74, median 26, 39 channels | 1920/1560 |
| 00fragment | unranked | Turbo Gold Clusters | 440/798 | 15/22 | R157, median 8, 35 channels | R108, median 26, 30 channels | 1350/1980 |
| 00great_wall | ranked | error404 | 722/1075 | 7/6 | R416, median 72.5, 10 channels | R260, median 63.5, 16 channels | 1290/1710 |
| 00great_wall | ranked | Ding | 693/1035 | 7/6 | R308, median 83.5, 8 channels | R148, median 37, 25 channels | 1650/1200 |
| 00corners | unranked | Rogue Elk | 673/1008 | 5/3 | R166, median 19, 30 channels | R49, median 22, 35 channels | 3060/2520 |
| 01islands | unranked | Electric Tributers | 742/1034 | 2/7 | R74, median 29, 28 channels | R52, median 30, 27 channels | 1890/2220 |
| 00eight | unranked | Rogue Elk | 756/1044 | 7/11 | R54, median 19, 30 channels | R150, median 52, 20 channels | 2100/2970 |
| 01big_world | unranked | Hidden Altar Keepers | 758/1032 | 0/0 | R105, median 18.5, 26 channels | R200, median 40.5, 26 channels | 1140/2340 |
| 00collision | unranked | Turbo Gold Clusters | 814/1082 | 10/0 | R86, median 18, 34 channels | R166, median 64, 17 channels | 2400/3750 |
| 00monolith | ranked | Manta | 769/1010 | 19/8 | R207, median 19, 27 channels | R96, median 22, 41 channels | 2520/2760 |
| 00corners | unranked | Electric Tributers | 795/1024 | 2/5 | R156, median 22, 31 channels | R49, median 37, 28 channels | 3540/2880 |
| 01fracture | ranked | Manta | 795/1005 | 8/12 | R98, median 44.5, 16 channels | R290, median 44, 24 channels | 1800/2160 |
| 01islands | unranked | Turbo Gold Clusters | 802/1004 | 3/4 | R74, median 29, 31 channels | R52, median 30, 27 channels | 2190/1920 |
| 01islands | unranked | Rogue Elk | 802/1004 | 3/4 | R74, median 29, 31 channels | R52, median 30, 27 channels | 2190/1920 |
| 00expanse | ranked | Ding | 825/1022 | 1/9 | R41, median 15, 49 channels | R50, median 11, 64 channels | 1980/3060 |
| 00quadrants | ranked | error404 | 827/1006 | 6/4 | R83, median 38, 20 channels | R108, median 39.5, 22 channels | 1200/1410 |
| 00eight | unranked | Electric Tributers | 841/1002 | 10/9 | R151, median 37, 26 channels | R227, median 53.5, 20 channels | 1530/1740 |
| 00quadrants | unranked | Electric Tributers | 906/1033 | 9/5 | R49, median 38, 22 channels | R33, median 36, 26 channels | 1350/2040 |

## Map ranking (losses only, not win rates)

| Pattern | Losses | Mean deficit |
|---|---|---|
| 01concentrated_wealth | 3 | 862.0 |
| 00fragment | 4 | 540.0 |
| 00elkring | 3 | 539.0 |
| 01islands | 5 | 308.2 |
| 00swirl | 2 | 638.5 |
| 00stampede | 1 | 960.0 |
| 00gemfight | 1 | 916.0 |
| 01big_world | 2 | 428.0 |
| 01yellow_brick_road | 1 | 827.0 |
| 00reverse_spiral | 1 | 738.0 |
| 01starfish | 1 | 709.0 |
| 00great_wall | 2 | 347.5 |
| 01corridors | 1 | 608.0 |
| 00corners | 2 | 282.0 |
| 01elk_arena | 1 | 504.0 |
| 00eight | 2 | 224.5 |
| 00ambush | 1 | 418.0 |
| 00rows | 1 | 418.0 |
| 00quadrants | 2 | 153.0 |
| 00collision | 1 | 268.0 |
| 00monolith | 1 | 241.0 |
| 01fracture | 1 | 210.0 |
| 00expanse | 1 | 197.0 |

## Opponent ranking (losses only, not win rates)

| Pattern | Losses | Mean deficit |
|---|---|---|
| meow | 5 | 699.0 |
| Ding | 5 | 510.8 |
| Ninja Turtles | 4 | 584.5 |
| Hidden Altar Keepers | 4 | 539.0 |
| error404 | 4 | 466.5 |
| Rogue Elk | 5 | 365.6 |
| Turbo Gold Clusters | 4 | 407.0 |
| Crimson Pathfinders | 2 | 761.0 |
| Manta | 3 | 289.7 |
| Electric Tributers | 4 | 202.2 |

## Our draft set ranking (losses only, not win rates)

| Pattern | Losses | Mean deficit |
|---|---|---|
| Vendetta, Prism, Marcella, Ren, Varg | 6 | 435.2 |
| Vendetta, Marcella, Ren, Varg, Tavi | 3 | 743.7 |
| Vendetta, Cassi+Issac, Marcella, Ren, Varg | 3 | 577.3 |
| Ryth, Vendetta, Ren, Varg | 2 | 638.5 |
| Vendetta, Cassi+Issac, Marcella | 3 | 415.3 |
| Vendetta, Prism, Marcella, Ren, Tavi | 2 | 489.5 |
| Vendetta, Marcella, Ren, Varg, Heart | 2 | 485.0 |
| Vendetta, Marcella, Ren, Heart | 1 | 916.0 |
| Vendetta, Marcella, Heart | 1 | 914.0 |
| Vendetta, Cassi+Issac, Stellar, Prism, Ren | 1 | 827.0 |
| Vendetta, Marcella, Ren, Varg | 1 | 738.0 |
| Vesper, Vendetta, Cassi+Issac, Marcella, Varg | 3 | 232.0 |
| Vendetta, Cassi+Issac, Ren, Varg, Tavi | 2 | 339.0 |
| Ryth, Vendetta, Cassi+Issac, Marcella, Varg | 1 | 608.0 |
| Vesper, Vendetta, Marcella, Ren, Heart | 2 | 266.0 |
| Prism, Willow, Ren, Tavi, Heart | 1 | 504.0 |
| Ryth, Vendetta, Marcella, Ren, Varg | 2 | 234.5 |
| Vesper, Vendetta, Cassi+Issac, Marcella | 1 | 418.0 |
| Vendetta, Cassi+Issac, Varg | 1 | 268.0 |
| Vesper, Vendetta, Prism, Ren, Varg | 1 | 241.0 |
| Vendetta, Prism, Ren, Varg, Tavi | 1 | 210.0 |

## Per-loss farming, banking, fighting and draft comparisons

### 00ambush vs Manta (4b6f7abd-44bf-47bb-b391-f50721e5bcf0)

Our draft: Vendetta, Marcella, Ren, Varg, Tavi. Winner: Vesper, Heart, Marcella, Ryth, Vendetta.
Our first distinct camp attack targets: R51 gem(71,44); R51 gem(41,49); R52 gem(70,44); R53 gem(42,48); R53 gem(71,45); R54 gem(70,45); R57 gem(41,48); R63 gem(58,51).
Winner's first targets: R43 elk(30,44); R112 gem(70,44); R113 gem(71,44); R114 gem(70,45); R115 gem(71,45); R131 gem(28,54); R133 gem(29,54); R136 gem(28,55).
Banks us: R784, median 37, 13 channels; winner: R306, median 37, 25 channels. Basic camp/champion attacks us 750/188, winner 957/538. Deaths 3/5; gear purchase value at R100 120/0, R500 1140/1170. Final carried gems 121/14.

### 00collision vs Turbo Gold Clusters (ad40f6da-b081-4013-bea2-bf7baaada6cf)

Our draft: Vendetta, Cassi+Issac, Varg. Winner: Heart, Vesper, Marcella.
Our first distinct camp attack targets: R7 gem(12,33); R7 wolf(10,35); R8 gem(12,32); R11 gem(17,30); R12 gem(17,29); R18 wolf(15,31); R21 gem(22,25); R22 gem(22,24).
Winner's first targets: R5 gem(12,7); R8 wolf(10,5); R15 gem(14,9); R17 gem(15,10); R19 wolf(15,9); R40 gem(17,11); R47 wolf(19,13); R69 golem(19,14).
Banks us: R86, median 18, 34 channels; winner: R166, median 64, 17 channels. Basic camp/champion attacks us 1147/645, winner 952/421. Deaths 10/0; gear purchase value at R100 300/270, R500 2400/3750. Final carried gems 81/26.

### 00corners vs Rogue Elk (606bd65b-004d-4d3f-9e68-6832ee9dc98c)

Our draft: Vendetta, Varg, Marcella, Ren, Prism. Winner: Heart, Vesper, Marcella, Ryth, Vendetta.
Our first distinct camp attack targets: R6 wolf(60,41); R10 elk(52,22); R19 gem(37,15); R23 gem(61,41); R23 gem(34,15); R54 wolf(54,7); R55 gem(49,9); R55 gem(34,1).
Winner's first targets: R8 golem(17,22); R10 elk(18,22); R24 elk(12,16); R32 wolf(10,41); R44 gem(17,7); R45 wolf(16,7); R52 wolf(9,5); R55 gem(9,41).
Banks us: R166, median 19, 30 channels; winner: R49, median 22, 35 channels. Basic camp/champion attacks us 1052/269, winner 1416/187. Deaths 5/3; gear purchase value at R100 480/120, R500 3060/2520. Final carried gems 42/71.

### 00corners vs Electric Tributers (650baa74-65ec-4a8c-8c43-48f671e6fb00)

Our draft: Vendetta, Varg, Marcella, Ren, Prism. Winner: Heart, Vesper, Marcella, Ryth, Vendetta.
Our first distinct camp attack targets: R6 wolf(60,41); R10 elk(52,22); R19 gem(37,15); R23 gem(61,41); R23 gem(34,15); R54 wolf(54,7); R55 gem(49,9); R55 gem(34,1).
Winner's first targets: R8 golem(17,22); R10 elk(18,22); R24 elk(12,16); R32 wolf(10,41); R44 gem(17,7); R45 wolf(16,7); R52 wolf(9,5); R55 gem(9,41).
Banks us: R156, median 22, 31 channels; winner: R49, median 37, 28 channels. Basic camp/champion attacks us 1164/230, winner 1324/197. Deaths 2/5; gear purchase value at R100 480/120, R500 3540/2880. Final carried gems 97/30.

### 00eight vs Rogue Elk (c2b2fe34-4586-4417-8b4d-4e58eee9d527)

Our draft: Vendetta, Marcella, Ren, Varg, Prism. Winner: Heart, Vesper, Marcella, Ryth, Vendetta.
Our first distinct camp attack targets: R11 wolf(31,15); R18 gem(23,10); R20 wolf(22,10); R20 gem(23,11); R21 wolf(22,11); R28 golem(30,15); R105 wolf(18,10); R196 gem(28,3).
Winner's first targets: R14 gem(17,11); R16 gem(17,10); R17 wolf(18,11); R22 wolf(18,10); R50 elk(13,4); R56 golem(10,15); R57 wolf(9,15); R96 elk(13,3).
Banks us: R54, median 19, 30 channels; winner: R150, median 52, 20 channels. Basic camp/champion attacks us 1012/852, winner 1100/1011. Deaths 7/11; gear purchase value at R100 150/210, R500 2100/2970. Final carried gems 96/8.

### 00eight vs Electric Tributers (3f622948-99e0-42bd-803d-2a2bcf3b73f9)

Our draft: Vendetta, Marcella, Ren, Varg, Prism. Winner: Heart, Vesper, Marcella, Ryth, Vendetta.
Our first distinct camp attack targets: R11 wolf(31,15); R18 gem(23,10); R20 wolf(22,10); R20 gem(23,11); R21 wolf(22,11); R28 golem(30,15); R254 elk(27,3); R288 golem(28,4).
Winner's first targets: R14 gem(17,11); R16 gem(17,10); R17 wolf(18,11); R22 wolf(18,10); R32 wolf(22,11); R60 wolf(22,10); R80 elk(27,4); R89 gem(28,3).
Banks us: R151, median 37, 26 channels; winner: R227, median 53.5, 20 channels. Basic camp/champion attacks us 977/828, winner 1229/1123. Deaths 10/9; gear purchase value at R100 30/390, R500 1530/1740. Final carried gems 67/108.

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

### 00elkring vs Ninja Turtles (7b9acfff-4982-4a80-8209-24358a8fd235)

Our draft: Vendetta, Marcella, Ren, Prism, Tavi. Winner: Heart, Vesper, Willow, Vendetta, Ryth.
Our first distinct camp attack targets: R4 elk(3,6); R8 elk(9,2); R10 golem(9,3); R20 golem(4,6); R21 gem(3,7); R23 elk(3,12); R42 elk(3,20); R54 gem(10,2).
Winner's first targets: R4 elk(26,23); R12 elk(20,27); R23 gem(19,27); R28 elk(26,17); R44 elk(26,9); R60 elk(19,2); R141 elk(10,27); R215 gem(26,10).
Banks us: R46, median 22, 22 channels; winner: R60, median 22, 34 channels. Basic camp/champion attacks us 836/663, winner 1092/232. Deaths 15/5; gear purchase value at R100 300/630, R500 2280/2790. Final carried gems 0/22.

### 00expanse vs Ding (d794d218-3d34-435d-961a-066f5956db4b)

Our draft: Vendetta, Varg, Marcella, Ren, Heart. Winner: Vesper, Vendetta, Cassi+Issac, Marcella, Ryth.
Our first distinct camp attack targets: R8 wolf(5,12); R20 wolf(5,22); R28 gem(30,26); R30 gem(29,26); R31 gem(41,13); R35 gem(42,13); R43 golem(17,33); R47 wolf(17,34).
Winner's first targets: R19 gem(54,63); R20 elk(54,64); R26 gem(50,53); R29 gem(49,53); R31 gem(52,42); R32 gem(51,41); R33 gem(52,41); R34 gem(53,64).
Banks us: R41, median 15, 49 channels; winner: R50, median 11, 64 channels. Basic camp/champion attacks us 1135/472, winner 1616/216. Deaths 1/9; gear purchase value at R100 150/60, R500 1980/3060. Final carried gems 0/15.

### 00fragment vs Crimson Pathfinders (780641d2-b273-4be2-89ad-4f5d468e418f)

Our draft: Vendetta, Marcella, Heart. Winner: Vesper, Vendetta, Tavi.
Our first distinct camp attack targets: R5 wolf(27,18); R9 golem(18,13); R10 elk(17,13); R44 gem(28,18); R49 wolf(27,24); R55 wolf(17,14); R89 gem(28,24); R357 wolf(2,5).
Winner's first targets: R6 golem(11,16); R7 elk(12,16); R7 wolf(12,15); R35 gem(13,15); R42 gem(16,14); R42 wolf(17,14); R70 gem(1,11); R71 wolf(2,11).
Banks us: R174, median 8, 11 channels; winner: R56, median 26, 55 channels. Basic camp/champion attacks us 644/569, winner 1025/775. Deaths 10/5; gear purchase value at R100 0/420, R500 570/2280. Final carried gems 0/0.

### 00fragment vs Rogue Elk (605146f4-cdd8-4f3b-867e-b93ffb04f130)

Our draft: Vendetta, Marcella, Cassi+Issac. Winner: Heart, Vesper, Marcella.
Our first distinct camp attack targets: R6 wolf(27,18); R8 golem(18,13); R9 elk(17,13); R20 wolf(27,24); R22 gem(28,24); R33 gem(28,18); R82 wolf(17,14); R343 wolf(2,11).
Winner's first targets: R5 golem(11,16); R7 wolf(12,15); R16 elk(12,16); R38 wolf(2,5); R39 elk(17,13); R56 gem(1,11); R57 wolf(2,11); R94 wolf(17,14).
Banks us: R157, median 8, 31 channels; winner: R108, median 26, 33 channels. Basic camp/champion attacks us 1015/1209, winner 982/1267. Deaths 26/9; gear purchase value at R100 0/210, R500 1020/1980. Final carried gems 8/26.

### 00fragment vs Ninja Turtles (ba4eb778-14c4-4984-baaf-93eb9dc2b2d9)

Our draft: Vendetta, Marcella, Cassi+Issac. Winner: Heart, Vendetta, Vesper.
Our first distinct camp attack targets: R6 wolf(2,11); R8 golem(11,16); R9 elk(12,16); R10 wolf(12,15); R36 gem(13,15); R59 wolf(2,5); R69 gem(1,5); R129 wolf(27,18).
Winner's first targets: R8 wolf(17,14); R16 elk(17,13); R32 gem(16,14); R37 wolf(27,18); R63 wolf(27,24); R107 wolf(2,11); R219 gem(28,18); R274 elk(12,16).
Banks us: R59, median 18.5, 26 channels; winner: R74, median 26, 39 channels. Basic camp/champion attacks us 1006/1651, winner 937/1053. Deaths 36/14; gear purchase value at R100 120/180, R500 1920/1560. Final carried gems 0/26.

### 00fragment vs Turbo Gold Clusters (21da60a5-6d86-4f74-982c-cac78411ddc1)

Our draft: Vendetta, Marcella, Cassi+Issac. Winner: Heart, Vesper, Marcella.
Our first distinct camp attack targets: R6 wolf(27,18); R8 golem(18,13); R9 elk(17,13); R20 wolf(27,24); R22 gem(28,24); R33 gem(28,18); R82 wolf(17,14); R520 elk(12,16).
Winner's first targets: R5 golem(11,16); R7 wolf(12,15); R16 elk(12,16); R38 wolf(2,5); R39 elk(17,13); R56 gem(1,11); R57 wolf(2,11); R94 wolf(17,14).
Banks us: R157, median 8, 35 channels; winner: R108, median 26, 30 channels. Basic camp/champion attacks us 1136/1230, winner 852/1275. Deaths 15/22; gear purchase value at R100 0/210, R500 1350/1980. Final carried gems 0/0.

### 00gemfight vs error404 (3f84301f-c60b-421b-8df4-abcf9ee305a1)

Our draft: Vendetta, Marcella, Heart, Ren. Winner: Cassi+Issac, Vendetta, Varg, Marcella.
Our first distinct camp attack targets: R3 gem(23,24); R4 wolf(22,24); R10 golem(27,20); R20 golem(16,14); R22 golem(16,15); R24 gem(27,14); R26 wolf(15,14); R32 golem(15,13).
Winner's first targets: R4 gem(6,5); R4 wolf(7,5); R12 golem(8,1); R17 gem(2,15); R18 golem(2,9); R23 golem(3,20); R31 golem(7,23); R32 elk(8,23).
Banks us: R558, median 25, 3 channels; winner: R63, median 14, 43 channels. Basic camp/champion attacks us 410/546, winner 557/226. Deaths 10/7; gear purchase value at R100 30/330, R500 690/2250. Final carried gems 62/7.

### 00great_wall vs error404 (99485b81-6cfb-45c5-add8-b2b556dea116)

Our draft: Vendetta, Marcella, Vesper, Ren, Heart. Winner: Varg, Ryth, Marcella, Vendetta, Stellar.
Our first distinct camp attack targets: R7 wolf(19,38); R15 golem(19,39); R15 wolf(18,39); R26 gem(41,38); R28 golem(41,37); R31 golem(31,29); R32 gem(4,36); R32 golem(40,38).
Winner's first targets: R30 gem(4,3); R31 golem(19,9); R32 gem(4,4); R35 golem(20,10); R35 elk(20,9); R39 golem(22,9); R45 golem(30,10); R47 golem(31,10).
Banks us: R416, median 72.5, 10 channels; winner: R260, median 63.5, 16 channels. Basic camp/champion attacks us 1154/89, winner 885/115. Deaths 7/6; gear purchase value at R100 0/30, R500 1290/1710. Final carried gems 340/29.

### 00great_wall vs Ding (093d2de6-5a26-4610-82db-2e476af0b7c7)

Our draft: Vendetta, Marcella, Varg, Ryth, Ren. Winner: Vesper, Vendetta, Cassi+Issac, Marcella, Ryth.
Our first distinct camp attack targets: R7 wolf(19,1); R16 golem(19,0); R17 wolf(18,0); R30 gem(4,3); R30 gem(41,1); R31 golem(31,10); R32 gem(4,4); R43 golem(30,10).
Winner's first targets: R12 wolf(19,38); R26 golem(19,30); R33 wolf(18,39); R41 elk(9,31); R52 wolf(37,32); R69 wolf(37,31); R69 gem(4,36); R71 gem(4,35).
Banks us: R308, median 83.5, 8 channels; winner: R148, median 37, 25 channels. Basic camp/champion attacks us 979/100, winner 1470/95. Deaths 7/6; gear purchase value at R100 0/0, R500 1650/1200. Final carried gems 29/214.

### 00monolith vs Manta (8f3e85d0-4719-4a0b-97fe-75a67275d1c7)

Our draft: Vendetta, Vesper, Varg, Ren, Prism. Winner: Heart, Marcella, Ryth, Vesper, Vendetta.
Our first distinct camp attack targets: R10 elk(36,11); R13 gem(36,12); R16 golem(35,12); R25 gem(45,18); R26 golem(39,24); R28 wolf(46,18); R28 wolf(40,25); R31 wolf(41,25).
Winner's first targets: R12 wolf(15,46); R16 elk(13,38); R24 golem(15,45); R42 wolf(3,31); R48 gem(25,31); R49 wolf(8,24); R49 gem(26,31); R63 wolf(9,24).
Banks us: R207, median 19, 27 channels; winner: R96, median 22, 41 channels. Basic camp/champion attacks us 1281/754, winner 1197/669. Deaths 19/8; gear purchase value at R100 270/180, R500 2520/2760. Final carried gems 278/4.

### 00quadrants vs error404 (00fdf26c-2f06-4add-8e52-cf415e474053)

Our draft: Vendetta, Marcella, Heart, Ren, Vesper. Winner: Varg, Ryth, Vendetta, Stellar, Cassi+Issac.
Our first distinct camp attack targets: R13 golem(23,22); R15 golem(22,23); R18 golem(22,21); R21 golem(22,22); R24 golem(21,22); R25 golem(19,27); R26 wolf(18,27); R37 wolf(17,26).
Winner's first targets: R7 elk(14,14); R34 golem(5,4); R35 golem(4,5); R35 golem(6,4); R36 golem(6,5); R37 elk(5,5); R42 golem(34,2); R43 wolf(35,2).
Banks us: R83, median 38, 20 channels; winner: R108, median 39.5, 22 channels. Basic camp/champion attacks us 927/168, winner 969/217. Deaths 6/4; gear purchase value at R100 0/150, R500 1200/1410. Final carried gems 25/100.

### 00quadrants vs Electric Tributers (3928614c-8445-4fbe-819c-07f6be710ac4)

Our draft: Vendetta, Marcella, Varg, Ryth, Ren. Winner: Heart, Vesper, Marcella, Ryth, Vendetta.
Our first distinct camp attack targets: R4 elk(30,30); R32 golem(19,27); R33 wolf(27,18); R34 wolf(18,27); R45 wolf(26,17); R59 golem(41,8); R60 golem(40,8); R61 golem(41,7).
Winner's first targets: R4 elk(14,14); R5 golem(13,13); R5 golem(13,14); R28 wolf(10,28); R32 wolf(28,10); R47 golem(5,4); R48 golem(4,5); R49 golem(4,6).
Banks us: R49, median 38, 22 channels; winner: R33, median 36, 26 channels. Basic camp/champion attacks us 852/266, winner 876/100. Deaths 9/5; gear purchase value at R100 0/150, R500 1350/2040. Final carried gems 0/36.

### 00reverse_spiral vs Ding (8a0274bf-e359-452c-be05-8dce185a89d0)

Our draft: Vendetta, Marcella, Ren, Varg. Winner: Vesper, Vendetta, Cassi+Issac, Marcella.
Our first distinct camp attack targets: R2 golem(10,11); R9 golem(23,11); R23 golem(23,22); R52 golem(19,18); R52 golem(13,27); R54 wolf(14,27); R56 wolf(15,27); R148 wolf(3,22).
Winner's first targets: R11 golem(6,18); R17 golem(6,7); R18 wolf(3,22); R38 wolf(26,7); R48 wolf(27,7); R59 gem(28,7); R72 gem(1,22); R73 wolf(2,22).
Banks us: R53, median 22, 11 channels; winner: R120, median 30, 29 channels. Basic camp/champion attacks us 445/170, winner 1106/685. Deaths 12/18; gear purchase value at R100 0/210, R500 630/1920. Final carried gems 7/0.

### 00rows vs error404 (89fa5dcb-3543-412b-a2c7-f1bf5388670f)

Our draft: Vendetta, Cassi+Issac, Marcella, Vesper. Winner: Varg, Ryth, Stellar, Cassi+Issac.
Our first distinct camp attack targets: R11 wolf(31,44); R19 wolf(31,45); R28 gem(30,44); R29 gem(30,45); R30 wolf(31,46); R38 gem(30,46); R41 gem(32,5); R44 gem(1,31).
Winner's first targets: R13 wolf(18,3); R15 wolf(18,4); R17 wolf(18,5); R19 gem(19,3); R36 wolf(31,3); R38 wolf(31,4); R40 gem(32,5); R41 golem(32,4).
Banks us: R66, median 19, 35 channels; winner: R191, median 35, 16 channels. Basic camp/champion attacks us 1370/564, winner 1291/544. Deaths 0/2; gear purchase value at R100 150/330, R500 2640/3120. Final carried gems 26/0.

### 00stampede vs meow (276e80d1-b6ee-414c-bb86-936ce58bede5)

Our draft: Vendetta, Marcella, Varg, Ren, Prism. Winner: Vesper, Vendetta, Heart, Ryth, Marcella.
Our first distinct camp attack targets: R11 gem(13,48); R11 gem(13,47); R23 gem(24,48); R25 gem(24,47); R28 gem(19,25); R29 gem(3,25); R31 gem(3,24); R32 gem(2,24).
Winner's first targets: R9 gem(13,1); R10 gem(13,2); R23 gem(24,1); R25 gem(24,2); R31 gem(18,24); R32 gem(19,24); R39 gem(34,1); R41 gem(34,2).
Banks us: R1209, median 40, 2 channels; winner: R834, median 80, 10 channels. Basic camp/champion attacks us 220/135, winner 898/228. Deaths 8/5; gear purchase value at R100 120/480, R500 1530/2970. Final carried gems 0/0.

### 00swirl vs Turbo Gold Clusters (d36631b9-13f3-4314-a049-46efb35790e7)

Our draft: Vendetta, Varg, Ren, Ryth. Winner: Heart, Vesper, Marcella, Ryth.
Our first distinct camp attack targets: R4 gem(24,21); R5 gem(24,20); R7 gem(24,16); R8 elk(24,15); R8 gem(25,16); R86 gem(35,11); R87 gem(36,11); R108 gem(25,15).
Winner's first targets: R6 gem(19,13); R8 gem(19,14); R8 elk(20,14); R66 gem(15,12); R68 gem(15,13); R70 wolf(14,12); R78 wolf(13,12); R84 wolf(43,9).
Banks us: R56, median 15, 12 channels; winner: R179, median 30, 33 channels. Basic camp/champion attacks us 381/284, winner 1032/298. Deaths 22/7; gear purchase value at R100 180/390, R500 990/4110. Final carried gems 0/0.

### 00swirl vs Rogue Elk (1eb9f4f1-3219-425f-b589-4f30d930fcb0)

Our draft: Vendetta, Varg, Ren, Ryth. Winner: Heart, Vesper, Marcella, Ryth.
Our first distinct camp attack targets: R4 gem(24,21); R5 gem(24,20); R7 gem(24,16); R8 elk(24,15); R8 gem(25,16); R86 gem(35,11); R87 gem(36,11); R108 gem(25,15).
Winner's first targets: R6 gem(19,13); R8 gem(19,14); R8 elk(20,14); R66 gem(15,12); R68 gem(15,13); R70 wolf(14,12); R78 wolf(13,12); R84 wolf(43,9).
Banks us: R56, median 15, 25 channels; winner: R204, median 24.5, 34 channels. Basic camp/champion attacks us 606/269, winner 1107/316. Deaths 19/7; gear purchase value at R100 180/390, R500 1560/3870. Final carried gems 30/0.

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

### 01concentrated_wealth vs Ding (e457f44a-e791-4552-b704-5c89ce1412a3)

Our draft: Vendetta, Ren, Marcella, Heart, Varg. Winner: Vesper, Vendetta, Cassi+Issac, Marcella, Ryth.
Our first distinct camp attack targets: R22 wolf(29,13); R36 gem(29,12); R36 wolf(30,13); R52 wolf(43,17); R78 golem(59,2); R80 wolf(59,1); R81 wolf(58,1); R357 gem(1,2).
Winner's first targets: R27 wolf(31,47); R31 gem(32,29); R32 gem(59,58); R33 gem(32,30); R34 gem(32,31); R36 gem(31,28); R38 golem(31,29); R39 golem(31,30).
Banks us: R421, median 30, 9 channels; winner: R130, median 22, 34 channels. Basic camp/champion attacks us 1029/302, winner 1489/1058. Deaths 6/7; gear purchase value at R100 90/0, R500 1110/2640. Final carried gems 78/38.

### 01corridors vs Crimson Pathfinders (f80ae529-6c2e-41a4-9291-6710b05cd050)

Our draft: Vendetta, Varg, Ryth, Marcella, Cassi+Issac. Winner: Tavi, Vesper, Prism, Willow, Ryth.
Our first distinct camp attack targets: R24 wolf(9,20); R36 wolf(45,20); R37 wolf(9,19); R38 gem(8,20); R48 wolf(45,19); R192 gem(44,20); R210 gem(44,19); R324 wolf(6,19).
Winner's first targets: R16 golem(22,19); R17 golem(20,19); R18 golem(22,20); R19 elk(21,19); R19 golem(20,20); R28 elk(21,20); R84 golem(2,19); R85 gem(0,19).
Banks us: R657, median 72, 6 channels; winner: R73, median 58, 9 channels. Basic camp/champion attacks us 1361/480, winner 793/101. Deaths 11/1; gear purchase value at R100 180/210, R500 1860/1410. Final carried gems 232/0.

### 01elk_arena vs Ding (79769bb3-4f10-453f-8d16-2090f88e3cd0)

Our draft: Prism, Ren, Willow, Heart, Tavi. Winner: Vesper, Vendetta, Cassi+Issac, Marcella, Ryth.
Our first distinct camp attack targets: R3 gem(20,24); R4 gem(7,17); R5 gem(7,16); R5 gem(21,24); R9 gem(22,27); R12 gem(0,21); R13 gem(23,27); R14 gem(0,22).
Winner's first targets: R8 gem(42,32); R10 gem(32,36); R10 gem(42,33); R11 gem(31,36); R12 gem(44,17); R13 gem(30,14); R13 gem(44,16); R15 gem(49,27).
Banks us: R566, median 72, 5 channels; winner: R345, median 72, 12 channels. Basic camp/champion attacks us 238/2514, winner 1177/543. Deaths 27/24; gear purchase value at R100 330/270, R500 1650/3300. Final carried gems 0/0.

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

### 01islands vs Electric Tributers (bf0746fd-8316-407c-933d-904efb445603)

Our draft: Vendetta, Varg, Vesper, Cassi+Issac, Marcella. Winner: Heart, Ren, Ryth, Prism, Cassi+Issac.
Our first distinct camp attack targets: R4 gem(30,52); R10 gem(26,47); R11 gem(25,47); R13 gem(27,47); R15 gem(43,44); R19 gem(43,43); R26 gem(30,42); R28 wolf(31,42).
Winner's first targets: R19 elk(9,10); R24 gem(8,11); R31 elk(8,10); R57 elk(4,30); R64 golem(5,31); R69 elk(5,30); R111 gem(29,7); R112 gem(30,7).
Banks us: R74, median 29, 28 channels; winner: R52, median 30, 27 channels. Basic camp/champion attacks us 966/465, winner 1292/147. Deaths 2/7; gear purchase value at R100 270/210, R500 1890/2220. Final carried gems 71/0.

### 01islands vs Turbo Gold Clusters (5660eef3-34b0-4f4f-9679-84322b405847)

Our draft: Vendetta, Varg, Vesper, Cassi+Issac, Marcella. Winner: Heart, Ren, Ryth, Prism, Cassi+Issac.
Our first distinct camp attack targets: R4 gem(30,52); R10 gem(26,47); R11 gem(25,47); R13 gem(27,47); R15 gem(43,44); R19 gem(43,43); R26 gem(30,42); R28 wolf(31,42).
Winner's first targets: R19 elk(9,10); R24 gem(8,11); R31 elk(8,10); R57 elk(4,30); R64 golem(5,31); R69 elk(5,30); R111 gem(29,7); R112 gem(30,7).
Banks us: R74, median 29, 31 channels; winner: R52, median 30, 27 channels. Basic camp/champion attacks us 920/374, winner 1347/144. Deaths 3/4; gear purchase value at R100 270/210, R500 2190/1920. Final carried gems 0/0.

### 01islands vs Rogue Elk (b273d25f-7754-4273-8fc6-2aaa7f8e1342)

Our draft: Vendetta, Varg, Vesper, Cassi+Issac, Marcella. Winner: Heart, Ren, Ryth, Prism, Cassi+Issac.
Our first distinct camp attack targets: R4 gem(30,52); R10 gem(26,47); R11 gem(25,47); R13 gem(27,47); R15 gem(43,44); R19 gem(43,43); R26 gem(30,42); R28 wolf(31,42).
Winner's first targets: R19 elk(9,10); R24 gem(8,11); R31 elk(8,10); R57 elk(4,30); R64 golem(5,31); R69 elk(5,30); R111 gem(29,7); R112 gem(30,7).
Banks us: R74, median 29, 31 channels; winner: R52, median 30, 27 channels. Basic camp/champion attacks us 920/374, winner 1347/144. Deaths 3/4; gear purchase value at R100 270/210, R500 2190/1920. Final carried gems 0/0.

### 01starfish vs Ninja Turtles (a97d93dd-762d-4ce1-9f82-fa77c2e53112)

Our draft: Vendetta, Marcella, Ren, Varg, Cassi+Issac. Winner: Heart, Vesper, Willow, Vendetta, Ryth.
Our first distinct camp attack targets: R11 wolf(17,10); R15 gem(18,9); R16 gem(18,11); R17 gem(18,10); R17 wolf(19,10); R194 wolf(3,36); R215 golem(1,36); R278 gem(31,11).
Winner's first targets: R11 wolf(32,10); R18 wolf(30,10); R59 wolf(28,25); R70 wolf(28,27); R81 wolf(21,27); R188 elk(20,37); R271 wolf(28,29); R275 wolf(21,29).
Banks us: R66, median 8, 14 channels; winner: R52, median 8, 23 channels. Basic camp/champion attacks us 697/1276, winner 946/786. Deaths 45/26; gear purchase value at R100 210/240, R500 1440/2070. Final carried gems 0/0.

### 01yellow_brick_road vs Ninja Turtles (849ac288-4c7a-4a1a-b742-c23309a28b3e)

Our draft: Cassi+Issac, Vendetta, Ren, Stellar, Prism. Winner: Heart, Vesper, Varg, Vendetta, Ryth.
Our first distinct camp attack targets: R2 gem(34,12); R3 gem(32,12); R3 gem(31,12); R4 gem(30,12); R4 gem(29,12); R5 gem(28,12); R6 gem(27,12); R7 gem(26,12).
Winner's first targets: R4 wolf(6,9); R5 wolf(9,14); R7 wolf(9,15); R14 wolf(6,8); R24 wolf(0,5); R25 wolf(12,4); R74 elk(13,14); R115 elk(0,4).
Banks us: R167, median 18.5, 12 channels; winner: R33, median 15.5, 48 channels. Basic camp/champion attacks us 484/239, winner 1369/214. Deaths 30/6; gear purchase value at R100 90/120, R500 1260/3510. Final carried gems 0/22.

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
