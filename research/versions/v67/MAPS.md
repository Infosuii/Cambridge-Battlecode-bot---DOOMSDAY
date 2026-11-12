# v67 map evidence

Offline study of 1,177 engine-2 replays, plus the 2026-10-27 crawl. Opening routes cover rounds 1–150.
Winning replay sides count twice in route/item summaries. Draft win rates use all finished engine-2 crawl games; small samples are descriptive, not counterfactual strength.
G numbers are official map-API group indices. Routes list basic-attack targets; capture may follow later. Crew is the maximum distinct same-team attackers in a 15-round interval.
The spawn-occupancy measure is an opening occupation of an empty camp tile; it does not prove intentional denial. First fight means first basic attack on a champion; spells may precede it.
Altar-lock use is unavailable in the native summary. No zero is inferred for this missing measurement.
Baseline self-play uses the fixed seeds 1/2. External v65 results are the 120 existing top-team ladder games, never newly queued games.

## 00ambush

| Measure | Observed evidence |
|---|---|
| Coverage | 47 crawl games, 17 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Ren/Cassi+Issac 13/14; Vesper/Heart/Vendetta/Varg/Marcella 3/4; Vesper/Cassi+Issac/Ren/Vendetta/Heart 5/8 |
| Modal opening attack route by hero | Cassi: 7→10→0; Heart: 7→10→9→0; Issac: 7→10→0; Marcella: 5→4; Prism: 6→11→1; Ryth: 10; Stellar: 11; Tavi: 10→7; Varg: 7→10; Vendetta: 6→11; Vesper: 7→0; Willow: 11→6 |
| Crew by group (median attackers) | 0:3, 1:3, 2:1, 3:1, 4:1, 5:1, 6:4, 7:4, 8:1, 9:1, 10:4, 11:3 |
| First fight | median R84; most common tile [((55, 50), 2)] |
| Banking | 151 submissions; median bag 47, R797; altar tiles [((33, 20), 67), ((66, 79), 50)] |
| Denial evidence in opening | contested groups [(5, 4), (2, 1)]; empty-tile occupation team:group→rounds [('0:4', 31), ('0:11', 30), ('1:7', 29), ('1:5', 23)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: monster_shard_of_focus, jungle_shard_of_health, power_shard_of_focus, power_shard_of_focus; Heart of Ruin: monster_shard_of_focus, jungle_shard_of_health, power_shard_of_focus, power_shard_of_focus; Issac: monster_shard_of_strength, jungle_shard_of_health, power_shard_of_strength, power_shard_of_strength; Marcella: jungle_shard_of_strength, prospector_shard_of_focus, durability_shard_of_health, monster_shard_of_focus; Ryth: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health; Tavi: treasure_shard_of_health, treasure_shard_of_strength, bruiser_shard_of_strength, monster_shard_of_strength; Varg: monster_shard_of_strength, jungle_shard_of_health, power_shard_of_strength, power_shard_of_strength; Vendetta: monster_shard_of_strength, jungle_shard_of_health, power_shard_of_strength, power_shard_of_strength; Vesper Vale: treasure_shard_of_strength, monster_shard_of_strength, jungle_shard_of_health, power_shard_of_strength |
| Game endings | {'gems': 47}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 0/2 / 1/1 |

## 00anvil

| Measure | Observed evidence |
|---|---|
| Coverage | 53 crawl games, 19 opening replays |
| Drafts (wins/appearances) | Heart/Vesper/Marcella 12/14; Vesper/Heart/Marcella 11/13; Heart/Vendetta/Vesper 6/10 |
| Modal opening attack route by hero | Heart: 0→2→0; Marcella: 0→2→4→11; Prism: 8→9→2→8→9; Ryth: 4→0→2→4→0→2→8; Tavi: 5→12→7→9→8→5→12; Varg: 6→10; Vendetta: 1→5→3→8→12→5→1→7; Vesper: 4→2→9 |
| Crew by group (median attackers) | 0:2, 1:1, 2:2, 3:2, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1, 10:1, 11:1, 12:1 |
| First fight | median R65; most common tile [((18, 8), 3)] |
| Banking | 389 submissions; median bag 21, R887; altar tiles [((18, 8), 389)] |
| Denial evidence in opening | contested groups [(8, 8), (9, 6)]; empty-tile occupation team:group→rounds [('1:5', 91), ('0:4', 85), ('1:9', 83), ('0:8', 78)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: jungle_shard_of_focus, treasure_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Marcella: jungle_shard_of_focus, treasure_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Tavi: treasure_shard_of_strength, prospector_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_strength; Vendetta: hunter_shard_of_strength, jungle_shard_of_strength, durability_shard_of_health, bruiser_shard_of_strength; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength |
| Game endings | {'gems': 48, 'tiebreak_gems': 5}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 2/2 / 0/1 |

## 00breadcrumbs

| Measure | Observed evidence |
|---|---|
| Coverage | 25 crawl games, 7 opening replays |
| Drafts (wins/appearances) | Marcella/Vendetta/Heart 5/5; Vesper/Heart/Vendetta 11/20; Heart/Ryth/Marcella 2/4 |
| Modal opening attack route by hero | Heart: 24→1→3→22→30→32→20→18; Marcella: 22→16→12→10→2→0→6→10; Ryth: 24→18→14→8→2→12→14→16; Tavi: 25→27→29→31→23→21→19→17; Vendetta: 31→29→25→33→19→17→13→11; Vesper: 23→27→5→31→27→25→33→21 |
| Crew by group (median attackers) | 0:1, 1:1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1, 10:1, 11:1, 12:1, 13:2, 14:1, 15:1, 16:1, 17:1, 18:1, 19:1, 20:1, 21:1, 22:1, 23:1.5, 24:1, 25:2, 26:1.5, 27:2, 28:1, 29:1, 30:1, 31:1, 32:1, 33:1 |
| First fight | median R46; most common tile [((12, 16), 1)] |
| Banking | 424 submissions; median bag 8, R656; altar tiles [((14, 14), 424)] |
| Denial evidence in opening | contested groups [(0, 1), (1, 1), (13, 1), (11, 1)]; empty-tile occupation team:group→rounds [('1:33', 24), ('1:17', 22), ('1:29', 21), ('1:27', 21)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: prospector_shard_of_health; Marcella: prospector_shard_of_focus, monster_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_focus; Tavi: treasure_shard_of_strength; Vendetta: prospector_shard_of_health, durability_shard_of_health, bruiser_shard_of_health; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health |
| Game endings | {'gems': 25}; winning-side gems lost to champions median 14 |
| v65 self-play / existing top-team duel record | 2/2 / 1/1 |

## 00collision

| Measure | Observed evidence |
|---|---|
| Coverage | 56 crawl games, 19 opening replays |
| Drafts (wins/appearances) | Vesper/Heart/Vendetta 17/23; Marcella/Vendetta/Vesper 4/5; Heart/Vendetta/Vesper 6/10 |
| Modal opening attack route by hero | Heart: 1→3→5→13→15→9→3→5; Marcella: 0→2→10→4→6→7→2→8; Prism: 3→11→5→15→1→3→5→17; Ryth: 15→9→13; Tavi: 1→3→13→5→7→6→12→13; Vendetta: 0→2→4→12→6→0→2→4; Vesper: 9→3→5→15→1→3→5→1 |
| Crew by group (median attackers) | 0:2.5, 1:3, 2:3, 3:3, 4:2, 5:3, 6:2, 7:2, 8:1, 9:1, 10:1, 11:1, 12:1, 13:1, 14:2.5, 15:3, 16:1, 17:1 |
| First fight | median R64; most common tile [((20, 20), 3)] |
| Banking | 297 submissions; median bag 22, R700; altar tiles [((27, 20), 296), ((39, 20), 1)] |
| Denial evidence in opening | contested groups [(6, 3), (7, 1), (12, 1)]; empty-tile occupation team:group→rounds [('0:10', 128), ('0:8', 126), ('1:9', 115), ('1:11', 103)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_focus; Marcella: treasure_shard_of_focus, prospector_shard_of_focus, jungle_shard_of_health, durability_shard_of_health; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ryth: prospector_shard_of_health, treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health; Tavi: prospector_shard_of_focus, hunter_shard_of_focus, monster_shard_of_focus, jungle_shard_of_focus; Vendetta: treasure_shard_of_strength, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Vesper Vale: treasure_shard_of_strength, prospector_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health |
| Game endings | {'gems': 56}; winning-side gems lost to champions median 15.0 |
| v65 self-play / existing top-team duel record | not on fixed plan / no duel evidence |

## 00contest

| Measure | Observed evidence |
|---|---|
| Coverage | 46 crawl games, 18 opening replays |
| Drafts (wins/appearances) | Heart/Ryth/Vendetta/Tavi/Marcella 10/11; Vesper/Vendetta/Heart/Varg/Marcella 6/7; Vesper/Vendetta/Heart/Cassi+Issac/Marcella 9/11 |
| Modal opening attack route by hero | Cassi: 3→5→3→13→5; Heart: 3; Issac: 13→3→5→10→9→5; Marcella: 3; Prism: 4→5→3; Ryth: 4; Tavi: 4→3; Varg: 13; Vendetta: 3; Vesper: 3→2; Willow: 2 |
| Crew by group (median attackers) | 2:2, 3:2, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1, 10:1, 11:1, 12:1, 13:1 |
| First fight | median R26; most common tile [((28, 24), 2)] |
| Banking | 53 submissions; median bag 200, R1172; altar tiles [((25, 24), 35), ((24, 25), 18)] |
| Denial evidence in opening | contested groups [(2, 6), (5, 5), (3, 4), (4, 4)]; empty-tile occupation team:group→rounds [('1:5', 115), ('1:2', 101), ('0:4', 99), ('0:3', 73)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus, durability_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_health; Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_health; Issac: treasure_shard_of_strength, power_shard_of_strength, home_shard_of_health, durability_shard_of_health; Marcella: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Ryth: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Tavi: treasure_shard_of_health, treasure_shard_of_strength; Varg: jungle_shard_of_strength, treasure_shard_of_strength; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health |
| Game endings | {'gems': 34, 'tiebreak_gems': 7, 'tiebreak_gold': 5}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 0/2 / 0/1 |

## 00corners

| Measure | Observed evidence |
|---|---|
| Coverage | 60 crawl games, 24 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Varg/Marcella 14/16; Vesper/Vendetta/Heart/Cassi+Issac/Marcella 9/12; Heart/Marcella/Ryth/Vendetta/Vesper 8/14 |
| Modal opening attack route by hero | Cassi: 26→28→29→27→3→21→6; Heart: 7→29→28; Issac: 6→28→29→27→2→3→18→16; Marcella: 7→3→29→28; Prism: 19→27→26→29→28→27; Ren: 18→10→9; Ryth: 19→17→13→15→19→17; Stellar: 6→28→29→27→3→20→26; Tavi: 27→26→28→29→27→26→28→29; Varg: 6→28→26; Vendetta: 19→17→27→19→17; Vesper: 18→10→24→22→6; Willow: 19→17→9→13→15→19→17 |
| Crew by group (median attackers) | 2:1, 3:1, 4:5, 5:5, 6:1, 7:2, 8:1, 9:1, 10:1, 11:1, 12:1, 13:1, 14:2, 15:2, 16:2, 17:2, 18:4, 19:3, 20:1, 21:1, 22:2, 23:3, 24:2, 25:1.5, 26:3, 27:2.5, 28:2, 29:2 |
| First fight | median R47; most common tile [((37, 18), 2)] |
| Banking | 535 submissions; median bag 22, R617; altar tiles [((35, 34), 497), ((69, 69), 13)] |
| Denial evidence in opening | contested groups [(3, 5), (2, 3), (28, 2), (29, 1)]; empty-tile occupation team:group→rounds [('0:26', 89), ('1:3', 66), ('1:19', 64), ('0:2', 56)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: jungle_shard_of_focus, treasure_shard_of_focus; Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_focus; Issac: treasure_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Marcella: treasure_shard_of_focus, capture_shard_of_focus, jungle_shard_of_focus, monster_shard_of_focus; Prism: monster_shard_of_health, bruiser_shard_of_focus, jungle_shard_of_health, bruiser_shard_of_focus; Ryth: jungle_shard_of_health, monster_shard_of_health, durability_shard_of_health, bruiser_shard_of_health; Stellar: treasure_shard_of_focus, power_shard_of_focus; Tavi: treasure_shard_of_strength, durability_shard_of_health, monster_shard_of_strength, bruiser_shard_of_strength; Varg: treasure_shard_of_strength, prospector_shard_of_strength, jungle_shard_of_health, monster_shard_of_strength; Vendetta: treasure_shard_of_strength, jungle_shard_of_strength, monster_shard_of_strength, bruiser_shard_of_health; Vesper Vale: treasure_shard_of_strength, prospector_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health; Willow: jungle_shard_of_strength, power_shard_of_strength, bruiser_shard_of_strength, durability_shard_of_health |
| Game endings | {'gems': 60}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 0/4 / 0/2 |

## 00crater

| Measure | Observed evidence |
|---|---|
| Coverage | 58 crawl games, 15 opening replays |
| Drafts (wins/appearances) | Prism/Marcella/Ryth/Heart/Vesper 8/9; Marcella/Vendetta/Ryth/Vesper/Heart 9/12; Vesper/Vendetta/Heart/Varg/Marcella 9/12 |
| Modal opening attack route by hero | Cassi: 2→4; Heart: 5; Issac: 4→2; Marcella: 5; Prism: 2; Ren: 2; Ryth: 4→2; Tavi: 5; Varg: 2; Vendetta: 2; Vesper: 2→4; Willow: 1→5→2 |
| Crew by group (median attackers) | 0:1, 1:1, 2:3, 3:4, 4:2, 5:3 |
| First fight | median R36; most common tile [((32, 20), 2)] |
| Banking | 228 submissions; median bag 30, R723; altar tiles [((30, 3), 228)] |
| Denial evidence in opening | contested groups [(2, 11), (4, 6), (5, 5)]; empty-tile occupation team:group→rounds [('1:5', 79), ('1:2', 40), ('0:4', 36), ('0:2', 34)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus, durability_shard_of_focus; Heart of Ruin: jungle_shard_of_focus, bruiser_shard_of_health; Issac: treasure_shard_of_strength, power_shard_of_strength; Marcella: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ryth: jungle_shard_of_health; Tavi: treasure_shard_of_health, treasure_shard_of_health, treasure_shard_of_strength, bruiser_shard_of_strength; Varg: jungle_shard_of_strength, treasure_shard_of_strength; Vendetta: hunter_shard_of_health, monster_shard_of_strength, jungle_shard_of_strength, durability_shard_of_health; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Willow: jungle_shard_of_strength, power_shard_of_strength, bruiser_shard_of_strength |
| Game endings | {'gems': 57, 'tiebreak_gems': 1}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 2/4 / 0/2 |

## 00dunes

| Measure | Observed evidence |
|---|---|
| Coverage | 53 crawl games, 15 opening replays |
| Drafts (wins/appearances) | Heart/Ryth/Vendetta/Tavi/Marcella 8/8; Prism/Vendetta/Marcella/Tavi/Heart 6/6; Marcella/Vendetta/Ryth/Vesper/Heart 11/17 |
| Modal opening attack route by hero | Cassi: 4→2→0; Heart: 4→2; Issac: 4→2→0→4; Marcella: 4→2→0; Prism: 4→2→0→4→0; Ren: 4→2→0; Ryth: 3→1→0→3; Tavi: 3→10→3; Varg: 0; Vendetta: 3→0; Vesper: 3→1→3→1; Willow: 9→2→4 |
| Crew by group (median attackers) | 0:2, 1:3, 2:3.5, 3:5, 4:5, 5:1, 6:1, 7:1, 8:1, 9:1, 10:1 |
| First fight | median R62; most common tile [((38, 36), 3)] |
| Banking | 296 submissions; median bag 38, R572; altar tiles [((39, 35), 214), ((39, 43), 82)] |
| Denial evidence in opening | contested groups [(0, 3), (2, 2), (3, 1), (1, 1)]; empty-tile occupation team:group→rounds [('1:4', 78), ('0:1', 71), ('0:3', 67), ('1:2', 50)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: jungle_shard_of_focus, bruiser_shard_of_health, durability_shard_of_health; Issac: treasure_shard_of_strength, power_shard_of_strength; Marcella: bruiser_shard_of_strength, bruiser_shard_of_health, bruiser_shard_of_focus, bruiser_shard_of_strength; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ren: bruiser_shard_of_health, durability_shard_of_health; Ryth: jungle_shard_of_strength; Tavi: treasure_shard_of_health, treasure_shard_of_health, treasure_shard_of_strength, bruiser_shard_of_strength; Varg: jungle_shard_of_strength; Vendetta: treasure_shard_of_strength, jungle_shard_of_strength, monster_shard_of_strength, bruiser_shard_of_health; Vesper Vale: jungle_shard_of_strength, bruiser_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health |
| Game endings | {'gems': 53}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 6/12 / 1/6 |

## 00eight

| Measure | Observed evidence |
|---|---|
| Coverage | 53 crawl games, 21 opening replays |
| Drafts (wins/appearances) | Prism/Vendetta/Marcella/Tavi/Heart 8/8; Vesper/Vendetta/Heart/Cassi+Issac/Tavi 8/11; Vesper/Vendetta/Heart/Varg/Marcella 10/14 |
| Modal opening attack route by hero | Cassi: 6→2→0→2→0; Heart: 4→2→0; Issac: 2→0→6→2→0; Marcella: 2→0; Prism: 2→0→2→0; Ren: 3→2; Ryth: 6→2→0→6→2→0; Tavi: 6→2→0; Varg: 4→0→6→3; Vendetta: 1→7→1; Vesper: 1→3→7; Willow: 0→2→6→2→0 |
| Crew by group (median attackers) | 0:5, 1:5, 2:3, 3:4, 4:5, 5:4, 6:2, 7:2 |
| First fight | median R52; most common tile [((18, 12), 3)] |
| Banking | 317 submissions; median bag 38, R671; altar tiles [((20, 15), 317)] |
| Denial evidence in opening | contested groups [(2, 13), (3, 8), (6, 1), (1, 1)]; empty-tile occupation team:group→rounds [('1:3', 183), ('0:2', 85), ('1:1', 53), ('0:0', 47)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus, durability_shard_of_focus; Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_focus; Issac: treasure_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health, bruiser_shard_of_health; Marcella: treasure_shard_of_focus, jungle_shard_of_focus, monster_shard_of_focus, bruiser_shard_of_health; Prism: monster_shard_of_health, bruiser_shard_of_focus, jungle_shard_of_health, bruiser_shard_of_focus; Ren: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Ryth: jungle_shard_of_health, treasure_shard_of_health, durability_shard_of_health, bruiser_shard_of_health; Tavi: treasure_shard_of_health, treasure_shard_of_strength, bruiser_shard_of_strength, monster_shard_of_strength; Varg: jungle_shard_of_strength; Vendetta: treasure_shard_of_strength, jungle_shard_of_strength, monster_shard_of_strength, bruiser_shard_of_health; Vesper Vale: treasure_shard_of_strength, monster_shard_of_strength, power_shard_of_strength; Willow: jungle_shard_of_strength, power_shard_of_strength, power_shard_of_strength |
| Game endings | {'gems': 53}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 6/6 / 1/3 |

## 00elkring

| Measure | Observed evidence |
|---|---|
| Coverage | 48 crawl games, 16 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Varg/Marcella 9/11; Marcella/Vendetta/Ryth/Vesper/Heart 7/10; Vesper/Vendetta/Heart/Cassi+Issac/Marcella 8/12 |
| Modal opening attack route by hero | Cassi: 0→4→2→6→9→0→4→2; Heart: 0→9→6→4→6; Issac: 0→4→2→6→9→7→4→2; Marcella: 1→3→5; Prism: 1→5→7→3→1→5; Ren: 0→2→4→9; Ryth: 1→3→5→7→5; Tavi: 0→4→9→6→2→0→4→9; Varg: 1→5→3→7→3→5; Vendetta: 0→4→9→2→0→4→9; Vesper: 0→2→4; Willow: 0→4→9→4 |
| Crew by group (median attackers) | 0:5, 1:5, 2:4, 3:4, 4:4, 5:4, 6:2, 7:2, 8:2, 9:3 |
| First fight | median R70; most common tile [((20, 7), 2)] |
| Banking | 136 submissions; median bag 44, R482; altar tiles [((3, 26), 81), ((26, 3), 55)] |
| Denial evidence in opening | contested groups [(7, 3), (6, 3), (9, 2), (3, 1)]; empty-tile occupation team:group→rounds [('1:1', 109), ('0:0', 82), ('1:5', 76), ('0:4', 73)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus; Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_focus; Marcella: treasure_shard_of_focus, jungle_shard_of_focus, capture_shard_of_focus, monster_shard_of_focus; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ryth: jungle_shard_of_health, treasure_shard_of_health, monster_shard_of_strength, jungle_shard_of_strength; Tavi: bruiser_shard_of_strength, durability_shard_of_health; Vendetta: treasure_shard_of_strength, jungle_shard_of_strength, monster_shard_of_strength, bruiser_shard_of_health; Vesper Vale: treasure_shard_of_strength, monster_shard_of_strength, capture_shard_of_strength, power_shard_of_strength |
| Game endings | {'gems': 48}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 4/6 / 0/3 |

## 00expanse

| Measure | Observed evidence |
|---|---|
| Coverage | 48 crawl games, 20 opening replays |
| Drafts (wins/appearances) | Heart/Ren/Ryth/Vesper/Marcella 9/11; Vesper/Vendetta/Heart/Varg/Marcella 6/8; Marcella/Vendetta/Ryth/Vesper/Heart 8/13 |
| Modal opening attack route by hero | Cassi: 18→20→6→12→2; Heart: 3→15→8→21→7; Issac: 2→16→6→16→6; Marcella: 17→15→3; Prism: 2→22; Ren: 2→14→17→15→2→6; Ryth: 19→21→15→13; Tavi: 19→21→7; Varg: 3→13→23→3→19; Vendetta: 19→7→21→3; Vesper: 19→17→15→13→11→3; Willow: 19→21→19→21 |
| Crew by group (median attackers) | 0:1.5, 1:3, 2:4, 3:5, 6:1, 7:2, 8:2.5, 9:2.5, 10:1, 11:1, 12:1, 13:1, 14:1, 15:1, 16:1, 17:1, 18:2, 19:2, 20:2, 21:1, 22:1, 23:3 |
| First fight | median R95; most common tile [((52, 39), 1)] |
| Banking | 406 submissions; median bag 15, R611; altar tiles [((14, 4), 157), ((13, 26), 76)] |
| Denial evidence in opening | contested groups [(17, 1), (8, 1), (12, 1)]; empty-tile occupation team:group→rounds [('1:3', 101), ('0:2', 71), ('0:16', 60), ('0:20', 54)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: monster_shard_of_focus, power_shard_of_focus, durability_shard_of_focus, bruiser_shard_of_health; Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Issac: monster_shard_of_strength, power_shard_of_strength, home_shard_of_health, durability_shard_of_health; Marcella: jungle_shard_of_strength, durability_shard_of_health, bruiser_shard_of_focus, bruiser_shard_of_health; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health; Ren: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Ryth: jungle_shard_of_health, treasure_shard_of_health; Tavi: treasure_shard_of_focus, bruiser_shard_of_health, durability_shard_of_focus, jungle_shard_of_focus; Varg: treasure_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vendetta: jungle_shard_of_strength, bruiser_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vesper Vale: jungle_shard_of_strength, bruiser_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Willow: treasure_shard_of_strength, jungle_shard_of_strength |
| Game endings | {'gems': 48}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 3/6 / 1/3 |

## 00fragment

| Measure | Observed evidence |
|---|---|
| Coverage | 50 crawl games, 15 opening replays |
| Drafts (wins/appearances) | Vesper/Heart/Vendetta 14/18; Marcella/Vendetta/Heart 5/6; Ren/Heart/Tavi 3/3 |
| Modal opening attack route by hero | Cassi: 4→0→4→2→0; Heart: 5→1→5→3→0→1; Issac: 0; Marcella: 5→1→3→0; Prism: 1; Ryth: 4→2→0→4; Tavi: 0→1→0; Varg: 0→4→2→0→1; Vendetta: 4→2→0→4→0; Vesper: 5→1→5→3→0→1; Willow: 0→4→2→0 |
| Crew by group (median attackers) | 0:3, 1:3, 2:2, 3:2, 4:2, 5:2 |
| First fight | median R49; most common tile [((17, 12), 3)] |
| Banking | 449 submissions; median bag 26, R940; altar tiles [((14, 5), 236), ((15, 24), 213)] |
| Denial evidence in opening | contested groups [(1, 12), (0, 8)]; empty-tile occupation team:group→rounds [('1:1', 85), ('0:0', 62), ('0:2', 33), ('0:4', 24)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_focus; Marcella: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Ryth: prospector_shard_of_health, treasure_shard_of_health, bruiser_shard_of_health, jungle_shard_of_focus; Tavi: bruiser_shard_of_strength, durability_shard_of_health, monster_shard_of_strength, treasure_shard_of_strength; Vendetta: treasure_shard_of_strength, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Vesper Vale: treasure_shard_of_strength, durability_shard_of_health, power_shard_of_strength, jungle_shard_of_health |
| Game endings | {'gems': 44, 'tiebreak_gems': 6}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 3/6 / 0/3 |

## 00galaxy

| Measure | Observed evidence |
|---|---|
| Coverage | 57 crawl games, 21 opening replays |
| Drafts (wins/appearances) | Marcella/Ren/Heart/Vendetta/Vesper 6/7; Vesper/Ryth/Vendetta/Varg/Marcella 6/9; Heart/Marcella/Ryth/Vendetta/Vesper 6/9 |
| Modal opening attack route by hero | Cassi: 5→0; Heart: 5→6; Issac: 6→7; Marcella: 5; Prism: 4→8→4; Ren: 6; Ryth: 5→8; Tavi: 4; Varg: 4; Vendetta: 4; Vesper: 5; Willow: 5→6 |
| Crew by group (median attackers) | 0:1, 1:1, 4:4, 5:4, 6:2, 7:1, 8:1 |
| First fight | median R68; most common tile [((53, 40), 2)] |
| Banking | 547 submissions; median bag 21, R614; altar tiles [((38, 46), 300), ((54, 46), 247)] |
| Denial evidence in opening | contested groups [(6, 7), (7, 2), (0, 1), (8, 1)]; empty-tile occupation team:group→rounds [('0:6', 51), ('1:5', 47), ('1:6', 43), ('0:1', 36)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: treasure_shard_of_health; Issac: treasure_shard_of_strength; Marcella: treasure_shard_of_focus, jungle_shard_of_focus, monster_shard_of_focus, bruiser_shard_of_health; Ren: bruiser_shard_of_health, durability_shard_of_health; Ryth: jungle_shard_of_health, prospector_shard_of_health; Tavi: treasure_shard_of_strength; Varg: jungle_shard_of_strength; Vendetta: treasure_shard_of_strength, jungle_shard_of_strength, monster_shard_of_strength, bruiser_shard_of_health; Vesper Vale: treasure_shard_of_strength |
| Game endings | {'gems': 57}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 4/4 / 0/2 |

## 00gem-fields

| Measure | Observed evidence |
|---|---|
| Coverage | 45 crawl games, 14 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Cassi+Issac/Marcella 8/8; Vesper/Vendetta/Heart/Varg/Marcella 4/5; Prism/Marcella/Ryth/Heart/Vesper 7/10 |
| Modal opening attack route by hero | Cassi: 5→2→5→4; Heart: 5; Issac: 5→2→5→4; Marcella: 5; Prism: 4→10→12; Ren: 5; Ryth: 5; Tavi: 4→5; Vendetta: 5→4→5; Vesper: 4; Willow: 5→2→5→4 |
| Crew by group (median attackers) | 0:1, 1:1, 2:3, 3:3, 4:4, 5:5, 6:2, 7:1.5, 8:1, 9:1, 10:2, 11:2, 12:1, 13:1, 14:1, 15:1, 16:1, 17:1 |
| First fight | median R27; most common tile [((23, 20), 2)] |
| Banking | 213 submissions; median bag 35, R419; altar tiles [((32, 10), 177), ((45, 4), 20)] |
| Denial evidence in opening | contested groups [(4, 9), (5, 4)]; empty-tile occupation team:group→rounds [('1:5', 155), ('0:4', 107), ('1:4', 46), ('0:14', 19)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus; Heart of Ruin: hunter_shard_of_health; Issac: treasure_shard_of_strength; Marcella: hunter_shard_of_focus, jungle_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ren: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health; Ryth: prospector_shard_of_health; Vendetta: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Vesper Vale: jungle_shard_of_strength |
| Game endings | {'gems': 45}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 1/2 / 1/1 |

## 00gemfight

| Measure | Observed evidence |
|---|---|
| Coverage | 48 crawl games, 21 opening replays |
| Drafts (wins/appearances) | Prism/Vendetta/Marcella/Heart 5/6; Stellar/Heart/Ryth/Marcella 6/10; Varg/Vendetta/Marcella/Ryth 3/5 |
| Modal opening attack route by hero | Cassi: 12→13→0; Heart: 11→14→0→11→14→11; Issac: 12→13→12; Marcella: 0; Prism: 11→14→0→14; Ren: 0→13→9→2→5→9→2; Ryth: 12→13→0→12; Stellar: 14→0→11; Tavi: 13; Vendetta: 11→14→4→0→11; Vesper: 11→17→1→6→12; Willow: 11→14→10→0→11 |
| Crew by group (median attackers) | 0:3, 1:1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1, 10:1, 11:4, 12:4, 13:3.5, 14:3, 15:1, 16:1, 17:1, 18:1 |
| First fight | median R53; most common tile [((14, 12), 3)] |
| Banking | 446 submissions; median bag 26, R539; altar tiles [((12, 17), 229), ((17, 12), 217)] |
| Denial evidence in opening | contested groups [(0, 17), (12, 1), (4, 1), (3, 1)]; empty-tile occupation team:group→rounds [('1:0', 199), ('0:0', 189), ('0:14', 53), ('0:11', 45)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: treasure_shard_of_focus, jungle_shard_of_focus; Heart of Ruin: hunter_shard_of_health; Issac: treasure_shard_of_strength, power_shard_of_strength; Marcella: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ryth: treasure_shard_of_health, jungle_shard_of_strength; Stellar: treasure_shard_of_focus, power_shard_of_focus; Tavi: treasure_shard_of_strength; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Willow: treasure_shard_of_strength, prospector_shard_of_strength |
| Game endings | {'gems': 48}; winning-side gems lost to champions median 7.0 |
| v65 self-play / existing top-team duel record | 0/2 / 0/1 |

## 00great-wall

| Measure | Observed evidence |
|---|---|
| Coverage | 62 crawl games, 23 opening replays |
| Drafts (wins/appearances) | Marcella/Vendetta/Ryth/Vesper/Heart 12/12; Vesper/Heart/Vendetta/Varg/Marcella 4/4; Vesper/Heart/Vendetta/Ryth/Marcella 3/4 |
| Modal opening attack route by hero | Cassi: 6; Heart: 6→8→4; Issac: 4→6→16→6; Marcella: 8→16; Prism: 10→8→14→8; Ren: 15→11→15→7→13; Ryth: 6→16→12; Tavi: 8; Varg: 6→16→6→16; Vendetta: 8→16→12→6; Vesper: 6→8→6→16; Willow: 15→3→15→7 |
| Crew by group (median attackers) | 2:1, 3:3, 4:2, 5:3, 6:3, 7:2.5, 8:3, 9:1, 10:1, 11:1, 12:1, 13:1, 14:1, 15:3, 16:3 |
| First fight | median R104; most common tile [((32, 9), 1)] |
| Banking | 199 submissions; median bag 57, R631; altar tiles [((32, 19), 65), ((17, 20), 58)] |
| Denial evidence in opening | contested groups [(10, 1), (13, 1)]; empty-tile occupation team:group→rounds [('0:11', 142), ('1:8', 118), ('1:12', 115), ('0:7', 71)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: prospector_shard_of_health; Issac: monster_shard_of_strength, power_shard_of_strength; Marcella: treasure_shard_of_focus, prospector_shard_of_focus, jungle_shard_of_health, durability_shard_of_health; Prism: monster_shard_of_health, bruiser_shard_of_focus; Ryth: prospector_shard_of_health, jungle_shard_of_health, treasure_shard_of_health, monster_shard_of_health; Tavi: treasure_shard_of_strength, durability_shard_of_health; Varg: jungle_shard_of_strength, treasure_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vendetta: treasure_shard_of_strength; Vesper Vale: treasure_shard_of_strength, prospector_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health; Willow: jungle_shard_of_strength |
| Game endings | {'gems': 62}; winning-side gems lost to champions median 7.0 |
| v65 self-play / existing top-team duel record | 0/6 / 0/3 |

## 00interlock

| Measure | Observed evidence |
|---|---|
| Coverage | 38 crawl games, 17 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Cassi+Issac 15/15; Varg/Vendetta/Marcella/Ryth 5/5; Stellar/Heart/Ryth/Marcella 4/5 |
| Modal opening attack route by hero | Cassi: 1→3; Heart: 1→4; Issac: 1→7; Marcella: 0→2; Prism: 1→7→1→3; Ryth: 0→2→10; Stellar: 4→12→4→6→4→10; Tavi: 1→9; Varg: 4→9→12; Vendetta: 1→11→5→11→13; Vesper: 1→3; Willow: 13→5→8→11 |
| Crew by group (median attackers) | 0:4, 1:4, 2:2, 3:2, 4:2, 5:2, 6:1, 7:1, 8:1, 9:1, 10:2, 11:2, 12:2, 13:3 |
| First fight | median R52; most common tile [((24, 8), 2)] |
| Banking | 265 submissions; median bag 37, R738; altar tiles [((20, 23), 114), ((19, 16), 80)] |
| Denial evidence in opening | contested groups [(12, 1), (8, 1), (9, 1)]; empty-tile occupation team:group→rounds [('1:5', 48), ('1:13', 45), ('1:11', 40), ('0:12', 35)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: treasure_shard_of_focus, jungle_shard_of_focus; Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_focus; Issac: treasure_shard_of_strength, capture_shard_of_strength, power_shard_of_strength, monster_shard_of_strength; Marcella: treasure_shard_of_focus, jungle_shard_of_strength, monster_shard_of_strength, bruiser_shard_of_strength; Prism: treasure_shard_of_focus, power_shard_of_focus, durability_shard_of_health, bruiser_shard_of_health; Ryth: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Stellar: treasure_shard_of_focus, power_shard_of_focus, home_shard_of_health, durability_shard_of_health; Tavi: treasure_shard_of_strength, durability_shard_of_health, monster_shard_of_strength, bruiser_shard_of_strength; Vendetta: treasure_shard_of_strength, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, power_shard_of_strength, durability_shard_of_health; Willow: treasure_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health, bruiser_shard_of_health |
| Game endings | {'gems': 38}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 2/2 / 0/1 |

## 00lanes

| Measure | Observed evidence |
|---|---|
| Coverage | 47 crawl games, 16 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Cassi+Issac/Marcella 7/7; Vesper/Ryth/Vendetta/Varg/Marcella 7/8; Vesper/Vendetta/Heart/Varg/Marcella 5/6 |
| Modal opening attack route by hero | Cassi: 26→24→27→25; Heart: 19→21→39; Issac: 20→22→24→22→24→23; Marcella: 7→1; Prism: 20→24→16→18→14→16; Ren: 17→27→39→5; Ryth: 17→21→27→41; Tavi: 30→8→30→34→32→2; Varg: 37→41→31→39→3; Vendetta: 15→27→21→37; Vesper: 14→16→18→20→24→14→16→18; Willow: 7→39→19→15→27 |
| Crew by group (median attackers) | 0:1, 1:1, 2:1.5, 3:1, 4:2, 5:1.5, 6:3, 7:3, 8:3, 9:2, 10:2, 11:1, 12:3, 13:1, 14:1, 15:1, 16:1, 17:1, 18:1, 19:1, 20:2.5, 21:2, 22:1, 23:2, 24:2, 25:2, 26:1, 27:2, 28:2, 29:1, 30:2, 31:1, 32:2, 33:2, 34:2, 35:1, 36:2, 37:2, 38:2.5, 39:1, 40:2, 41:1 |
| First fight | median R56; most common tile [((40, 22), 2)] |
| Banking | 582 submissions; median bag 22, R648; altar tiles [((12, 13), 175), ((60, 4), 109)] |
| Denial evidence in opening | contested groups [(27, 1), (25, 1), (19, 1), (2, 1)]; empty-tile occupation team:group→rounds [('1:19', 57), ('1:25', 52), ('1:17', 51), ('0:36', 43)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus, durability_shard_of_focus, bruiser_shard_of_health; Heart of Ruin: treasure_shard_of_focus, jungle_shard_of_focus, power_shard_of_focus, durability_shard_of_health; Issac: treasure_shard_of_strength, power_shard_of_strength, home_shard_of_health, durability_shard_of_health; Marcella: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Prism: monster_shard_of_focus, jungle_shard_of_health, bruiser_shard_of_focus, bruiser_shard_of_focus; Ryth: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Tavi: bruiser_shard_of_strength, durability_shard_of_health; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Willow: treasure_shard_of_focus, jungle_shard_of_focus, durability_shard_of_focus |
| Game endings | {'gems': 47}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 4/4 / 0/2 |

## 00lost-world

| Measure | Observed evidence |
|---|---|
| Coverage | 46 crawl games, 12 opening replays |
| Drafts (wins/appearances) | Prism/Vendetta/Marcella/Tavi/Heart 6/7; Vesper/Ryth/Vendetta/Varg/Marcella 4/5; Vesper/Vendetta/Heart/Cassi+Issac/Marcella 9/13 |
| Modal opening attack route by hero | Cassi: 15→9→14→11→10; Heart: 19→6; Issac: 8→13→8; Marcella: 5; Prism: 16→14→13→17; Ryth: 16→6; Tavi: 17→9→14→2→3→13→9→14; Varg: 24; Vendetta: 17→16→15; Vesper: 0; Willow: 28→26 |
| Crew by group (median attackers) | 0:1, 1:1, 2:1, 3:1, 4:1, 5:2.5, 6:2, 7:1, 8:1, 9:1, 10:1, 11:1, 12:1, 13:1, 14:1, 15:1, 16:1.5, 17:1, 18:1, 19:1, 20:1, 21:1, 22:1, 24:1, 25:1, 26:1, 27:1, 28:2, 30:2, 33:1 |
| First fight | median R18; most common tile [((3, 14), 5)] |
| Banking | 550 submissions; median bag 14, R352; altar tiles [((18, 15), 523), ((33, 29), 16)] |
| Denial evidence in opening | contested groups [(15, 3), (16, 3), (11, 2), (17, 1)]; empty-tile occupation team:group→rounds [('1:17', 94), ('1:16', 80), ('1:2', 74), ('1:4', 64)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus; Issac: treasure_shard_of_strength; Marcella: hunter_shard_of_focus, jungle_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Prism: durability_shard_of_health; Ryth: jungle_shard_of_health, prospector_shard_of_health; Tavi: treasure_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Varg: jungle_shard_of_strength, treasure_shard_of_strength, durability_shard_of_health; Vendetta: hunter_shard_of_strength, jungle_shard_of_strength, durability_shard_of_health, bruiser_shard_of_strength; Vesper Vale: treasure_shard_of_strength |
| Game endings | {'gems': 46}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 2/2 / 0/1 |

## 00monolith

| Measure | Observed evidence |
|---|---|
| Coverage | 39 crawl games, 20 opening replays |
| Drafts (wins/appearances) | Prism/Vendetta/Marcella/Tavi/Heart 4/4; Vesper/Vendetta/Heart/Cassi+Issac/Marcella 6/8; Marcella/Vendetta/Ryth/Vesper/Ren 8/12 |
| Modal opening attack route by hero | Cassi: 11→19→9→19→9; Heart: 10→8→18→4→10→8→18; Issac: 11→19→16→11→19→16→7; Marcella: 4→10; Prism: 10→18→8→4→14→18; Ren: 10→8→2; Ryth: 11→19→11→19; Stellar: 10→18→8; Tavi: 4→12→14; Varg: 10→8→18→17→3; Vendetta: 11→5→19→11; Vesper: 10→6→4→10→8→18; Willow: 11→7→9 |
| Crew by group (median attackers) | 2:1, 3:1, 4:2, 5:1, 6:1, 7:1, 8:2, 9:2, 10:4.5, 11:5, 12:1, 13:1, 14:1, 15:1, 16:2, 17:3, 18:3, 19:4 |
| First fight | median R84; most common tile [((24, 19), 2)] |
| Banking | 312 submissions; median bag 23, R629; altar tiles [((19, 19), 98), ((30, 30), 95)] |
| Denial evidence in opening | contested groups [(12, 5), (13, 2)]; empty-tile occupation team:group→rounds [('0:11', 96), ('1:10', 94), ('0:19', 58), ('0:13', 46)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus, durability_shard_of_focus, bruiser_shard_of_health; Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_health; Issac: treasure_shard_of_strength; Marcella: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Ryth: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Tavi: bruiser_shard_of_strength, prospector_shard_of_health, durability_shard_of_health, monster_shard_of_strength; Varg: prospector_shard_of_strength, treasure_shard_of_health, jungle_shard_of_strength, monster_shard_of_health; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Willow: treasure_shard_of_focus |
| Game endings | {'gems': 39}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 4/6 / 0/3 |

## 00oasis

| Measure | Observed evidence |
|---|---|
| Coverage | 47 crawl games, 17 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Cassi+Issac 13/20; Marcella/Vesper/Vendetta/Tavi 3/5; Prism/Vendetta/Marcella/Heart 7/12 |
| Modal opening attack route by hero | Cassi: 1→3→7→3→1→6; Heart: 0→2→9; Issac: 1→7→1→6; Marcella: 1→5; Prism: 0→6→0→5; Ryth: 1→6→3; Stellar: 0→2→5; Tavi: 6→5; Vendetta: 0→2→6→0→5; Vesper: 6→0; Willow: 1→8→5 |
| Crew by group (median attackers) | 0:4, 1:4, 2:1, 3:1.5, 4:2, 5:2, 6:3, 7:3, 8:1, 9:1 |
| First fight | median R30; most common tile [((14, 11), 2)] |
| Banking | 372 submissions; median bag 22, R828; altar tiles [((19, 9), 201), ((9, 19), 171)] |
| Denial evidence in opening | contested groups [(6, 5), (3, 5), (2, 5), (7, 3)]; empty-tile occupation team:group→rounds [('1:3', 95), ('0:2', 42), ('0:0', 42), ('1:7', 38)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: treasure_shard_of_focus, jungle_shard_of_focus, durability_shard_of_focus, bruiser_shard_of_health; Heart of Ruin: treasure_shard_of_focus, power_shard_of_focus, durability_shard_of_health, home_shard_of_health; Issac: treasure_shard_of_strength, capture_shard_of_strength, power_shard_of_strength, monster_shard_of_strength; Marcella: treasure_shard_of_focus, prospector_shard_of_focus, jungle_shard_of_health, durability_shard_of_health; Prism: monster_shard_of_focus, bruiser_shard_of_focus, bruiser_shard_of_focus, bruiser_shard_of_focus; Ryth: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Stellar: treasure_shard_of_focus, power_shard_of_focus, home_shard_of_health, durability_shard_of_health; Vendetta: treasure_shard_of_strength, prospector_shard_of_strength, jungle_shard_of_health, monster_shard_of_strength; Vesper Vale: treasure_shard_of_strength, prospector_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health; Willow: treasure_shard_of_strength |
| Game endings | {'gems': 43, 'tiebreak_gems': 4}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | not on fixed plan / no duel evidence |

## 00packs

| Measure | Observed evidence |
|---|---|
| Coverage | 51 crawl games, 22 opening replays |
| Drafts (wins/appearances) | Marcella/Vendetta/Heart 6/6; Marcella/Vendetta/Varg 5/6; Vesper/Heart/Vendetta 14/20 |
| Modal opening attack route by hero | Cassi: 2; Heart: 2→3→0→4; Issac: 1; Marcella: 1→3→5→3; Prism: 2→0; Ryth: 3→2→3→2→0; Tavi: 2→3→1→3→2; Varg: 5→1→5→1; Vendetta: 2→3→2→4; Vesper: 2→3→0→2→0; Willow: 3→0→2→3 |
| Crew by group (median attackers) | 0:2, 1:3, 2:2, 3:2, 4:2, 5:2, 6:1, 7:1.5 |
| First fight | median R36; most common tile [((19, 19), 2)] |
| Banking | 410 submissions; median bag 28, R608; altar tiles [((28, 24), 201), ((2, 6), 125)] |
| Denial evidence in opening | contested groups [(2, 11), (3, 9)]; empty-tile occupation team:group→rounds [('1:3', 97), ('0:2', 81), ('1:1', 80), ('0:0', 70)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: prospector_shard_of_focus, durability_shard_of_health, monster_shard_of_focus, capture_shard_of_health; Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Issac: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Marcella: prospector_shard_of_focus, treasure_shard_of_focus, jungle_shard_of_strength, monster_shard_of_strength; Tavi: durability_shard_of_strength, bruiser_shard_of_strength, treasure_shard_of_health, monster_shard_of_health; Varg: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Vendetta: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, monster_shard_of_strength, durability_shard_of_health; Willow: treasure_shard_of_strength, bruiser_shard_of_health |
| Game endings | {'gems': 51}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 4/6 / 3/3 |

## 00pilgrimage

| Measure | Observed evidence |
|---|---|
| Coverage | 51 crawl games, 17 opening replays |
| Drafts (wins/appearances) | Marcella/Vendetta/Vesper/Heart/Tavi 6/7; Vesper/Vendetta/Heart/Cassi+Issac/Willow 9/11; Prism/Vendetta/Marcella/Tavi/Heart 7/10 |
| Modal opening attack route by hero | Cassi: 11; Heart: 5→11; Issac: 7→9→11→20; Marcella: 10; Prism: 11; Ren: 9→11; Ryth: 10; Stellar: 11; Tavi: 10→8; Varg: 10; Vendetta: 5→7→9→3→14; Vesper: 4→6→8→10; Willow: 11→7 |
| Crew by group (median attackers) | 0:1, 2:1, 3:1, 4:1, 5:2, 6:1.5, 7:2, 8:1, 9:1, 10:5, 11:5, 12:1.5, 13:1, 14:1, 15:1, 17:1, 18:1, 19:1, 20:1, 21:1, 22:1 |
| First fight | median R82; most common tile [((16, 55), 1)] |
| Banking | 208 submissions; median bag 44, R1086; altar tiles [((44, 58), 139), ((5, 58), 61)] |
| Denial evidence in opening | contested groups [(10, 1), (11, 1)]; empty-tile occupation team:group→rounds [('0:10', 92), ('0:8', 73), ('1:5', 59), ('0:4', 55)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus, durability_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_health; Heart of Ruin: prospector_shard_of_health, jungle_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Issac: treasure_shard_of_strength, power_shard_of_strength, home_shard_of_health, durability_shard_of_health; Marcella: treasure_shard_of_focus, prospector_shard_of_focus, jungle_shard_of_health, durability_shard_of_health; Prism: durability_shard_of_health, monster_shard_of_health; Ren: bruiser_shard_of_health, durability_shard_of_health, power_shard_of_focus, power_shard_of_focus; Ryth: jungle_shard_of_health, treasure_shard_of_health; Stellar: treasure_shard_of_focus, jungle_shard_of_focus, power_shard_of_focus, durability_shard_of_health; Tavi: treasure_shard_of_health, capture_shard_of_strength, treasure_shard_of_strength, bruiser_shard_of_strength; Varg: jungle_shard_of_strength, treasure_shard_of_strength; Vendetta: treasure_shard_of_strength, prospector_shard_of_strength, jungle_shard_of_health, monster_shard_of_strength; Vesper Vale: treasure_shard_of_strength, prospector_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health; Willow: treasure_shard_of_strength, prospector_shard_of_strength |
| Game endings | {'gems': 50, 'tiebreak_gems': 1}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 2/2 / 1/1 |

## 00quadrants

| Measure | Observed evidence |
|---|---|
| Coverage | 59 crawl games, 22 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Varg/Marcella 11/17; Prism/Marcella/Ryth/Heart/Vesper 10/16; Heart/Marcella/Ryth/Vendetta/Vesper 8/13 |
| Modal opening attack route by hero | Cassi: 14→2→16→12; Heart: 1→13→16; Issac: 14→2→16→14→2; Marcella: 1→13→16; Prism: 1→13→16; Ryth: 1→13→16; Tavi: 14→10→6→8→4→10→6→8; Varg: 14→2→20→12; Vendetta: 14→2→16→12→2; Vesper: 1→13→16; Willow: 13→16→13→15 |
| Crew by group (median attackers) | 0:1, 1:3, 2:3, 3:1, 4:1, 5:2, 6:2, 7:2, 8:1, 9:1.5, 10:2, 11:1, 12:2, 13:5, 14:5, 15:2, 16:4, 17:1, 18:1.5, 19:1, 20:1 |
| First fight | median R74; most common tile [((20, 36), 1)] |
| Banking | 192 submissions; median bag 50, R316; altar tiles [((22, 43), 59), ((22, 1), 57)] |
| Denial evidence in opening | contested groups [(3, 4), (7, 2), (9, 2), (5, 1)]; empty-tile occupation team:group→rounds [('1:6', 118), ('0:9', 115), ('1:14', 113), ('0:13', 112)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: prospector_shard_of_health; Marcella: prospector_shard_of_focus, bruiser_shard_of_focus, jungle_shard_of_focus, bruiser_shard_of_focus; Prism: monster_shard_of_focus, jungle_shard_of_health; Ryth: jungle_shard_of_health; Tavi: treasure_shard_of_strength; Vendetta: treasure_shard_of_health, jungle_shard_of_strength; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, power_shard_of_strength, durability_shard_of_health |
| Game endings | {'gems': 59}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 3/6 / 0/3 |

## 00quarry

| Measure | Observed evidence |
|---|---|
| Coverage | 56 crawl games, 19 opening replays |
| Drafts (wins/appearances) | Heart/Ryth/Vesper/Marcella 7/9; Vesper/Vendetta/Heart/Cassi+Issac 15/23; Marcella/Vendetta/Ryth/Vesper 4/6 |
| Modal opening attack route by hero | Cassi: 3→1→7→5→3→1; Heart: 6→8→12→10; Issac: 3→1→7→5; Marcella: 8→10; Prism: 8; Ren: 2→8→6→10; Ryth: 8→11→8; Stellar: 5→1→9→5→7; Tavi: 8; Vendetta: 4→9→6→4→6→4; Vesper: 4→9→4→6→9; Willow: 7→1→8→13 |
| Crew by group (median attackers) | 0:2, 1:2, 2:1, 3:1, 4:1, 5:2, 6:1, 7:2, 8:2, 9:2, 10:1, 11:1, 12:1, 13:1 |
| First fight | median R30; most common tile [((22, 19), 2)] |
| Banking | 335 submissions; median bag 23, R665; altar tiles [((16, 14), 188), ((18, 14), 147)] |
| Denial evidence in opening | contested groups [(8, 12), (9, 8), (6, 1), (13, 1)]; empty-tile occupation team:group→rounds [('1:5', 93), ('1:7', 72), ('0:9', 68), ('0:4', 67)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus; Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Issac: treasure_shard_of_strength, power_shard_of_strength; Marcella: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Ryth: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Stellar: treasure_shard_of_focus, power_shard_of_focus, home_shard_of_health; Tavi: bruiser_shard_of_strength, prospector_shard_of_health, durability_shard_of_health, monster_shard_of_strength; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, monster_shard_of_strength, durability_shard_of_health; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, monster_shard_of_strength, durability_shard_of_health |
| Game endings | {'gems': 56}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 1/2 / 0/1 |

## 00reverse-spiral

| Measure | Observed evidence |
|---|---|
| Coverage | 44 crawl games, 13 opening replays |
| Drafts (wins/appearances) | Stellar/Heart/Ryth/Marcella 3/4; Marcella/Vendetta/Ryth/Vesper 7/10; Heart/Ryth/Vesper/Marcella 4/7 |
| Modal opening attack route by hero | Cassi: 7→3→9→7; Heart: 12; Issac: 7→9→7; Marcella: 6; Prism: 13→8→2; Ryth: 4→6→1; Stellar: 13→6→0; Tavi: 13→8→6; Vendetta: 13→3→6→0→13; Vesper: 13→7→13; Willow: 7→1→8 |
| Crew by group (median attackers) | 0:2, 1:1, 2:1, 3:1, 4:1, 5:1, 6:2, 7:2, 8:2, 9:3, 10:2.5, 12:1, 13:1 |
| First fight | median R1; most common tile [((15, 16), 5)] |
| Banking | 122 submissions; median bag 36, R794; altar tiles [((27, 27), 65), ((2, 2), 57)] |
| Denial evidence in opening | contested groups [(12, 3), (13, 2), (7, 1), (9, 1)]; empty-tile occupation team:group→rounds [('1:3', 33), ('1:13', 32), ('0:12', 25), ('1:6', 21)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus, durability_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_health; Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_health; Marcella: bruiser_shard_of_strength, bruiser_shard_of_health, bruiser_shard_of_focus, bruiser_shard_of_strength; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ryth: jungle_shard_of_strength, bruiser_shard_of_health; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vesper Vale: jungle_shard_of_strength, bruiser_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health |
| Game endings | {'tiebreak_gems': 2, 'gems': 42}; winning-side gems lost to champions median 7 |
| v65 self-play / existing top-team duel record | not on fixed plan / no duel evidence |

## 00ribs

| Measure | Observed evidence |
|---|---|
| Coverage | 48 crawl games, 20 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Varg/Marcella 9/12; Prism/Vesper/Marcella/Ryth/Heart 8/12; Vesper/Heart/Vendetta/Varg/Marcella 3/3 |
| Modal opening attack route by hero | Cassi: 2→1; Heart: 2; Issac: 2→1; Marcella: 2; Prism: 2; Ren: 2→1; Ryth: 2; Tavi: 2→0→1; Vendetta: 2; Vesper: 2; Willow: 7 |
| Crew by group (median attackers) | 0:1, 1:2, 2:3, 3:1, 4:1, 5:1, 6:1, 7:1, 8:1, 11:1, 12:1.5 |
| First fight | median R69; most common tile [((21, 65), 3)] |
| Banking | 259 submissions; median bag 25, R829; altar tiles [((22, 71), 160), ((28, 71), 99)] |
| Denial evidence in opening | contested groups [(2, 7), (0, 2), (1, 1)]; empty-tile occupation team:group→rounds [('1:2', 83), ('0:2', 74), ('0:0', 56), ('0:12', 41)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: hunter_shard_of_health, durability_shard_of_health; Marcella: bruiser_shard_of_strength, bruiser_shard_of_health, bruiser_shard_of_focus, bruiser_shard_of_strength; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ryth: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength; Tavi: hunter_shard_of_strength, bruiser_shard_of_strength, durability_shard_of_health, prospector_shard_of_strength; Vendetta: hunter_shard_of_health, durability_shard_of_health; Vesper Vale: jungle_shard_of_strength, bruiser_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health |
| Game endings | {'gems': 44, 'tiebreak_gems': 4}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 1/2 / 0/1 |

## 00road-of-riches

| Measure | Observed evidence |
|---|---|
| Coverage | 43 crawl games, 18 opening replays |
| Drafts (wins/appearances) | Prism/Vesper/Marcella/Ryth/Heart 9/9; Prism/Vendetta/Marcella/Tavi/Heart 5/7; Vesper/Vendetta/Heart/Ren/Cassi+Issac 6/9 |
| Modal opening attack route by hero | Cassi: 8→6→22→36→8→18→22; Heart: 7→15→5→21; Issac: 8→6→20→0→2→32→28→0; Marcella: 8→34→10→50; Prism: 7→21→33→39→45→49; Ryth: 7→17→33→49; Tavi: 8→6→22→34→10; Varg: 7→21; Vendetta: 27→1→0→2→4→27→0→2; Vesper: 8→6→18→20→8; Willow: 7→19→23→33→37→43→49 |
| Crew by group (median attackers) | 0:1, 1:1, 2:1.5, 3:1, 4:2, 5:1, 6:1, 7:5, 8:5, 9:2, 10:3, 11:1, 12:1, 13:1, 14:1, 15:1, 16:1, 17:1.5, 18:1, 19:1, 20:1, 21:1, 22:1, 23:1, 24:1, 27:1, 28:1, 30:1, 31:1, 32:1, 33:4, 34:4, 35:2, 36:2, 37:1, 38:1, 39:1, 40:1, 41:1, 42:1, 43:1, 44:1, 45:1, 46:1, 47:1, 48:1, 49:3, 50:3 |
| First fight | median R78; most common tile [((20, 17), 1)] |
| Banking | 309 submissions; median bag 28, R480; altar tiles [((20, 22), 166), ((19, 17), 143)] |
| Denial evidence in opening | contested groups [(0, 3), (31, 1), (1, 1), (2, 1)]; empty-tile occupation team:group→rounds [('1:20', 89), ('1:6', 78), ('1:8', 72), ('0:5', 65)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: monster_shard_of_focus, power_shard_of_focus, power_shard_of_focus, power_shard_of_focus; Marcella: monster_shard_of_strength, power_shard_of_strength, power_shard_of_strength, power_shard_of_strength; Prism: monster_shard_of_focus; Ryth: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Tavi: jungle_shard_of_focus, treasure_shard_of_focus; Varg: jungle_shard_of_strength, treasure_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, monster_shard_of_strength, durability_shard_of_health; Vesper Vale: monster_shard_of_strength, power_shard_of_strength, power_shard_of_strength, power_shard_of_strength; Willow: jungle_shard_of_health |
| Game endings | {'gems': 43}; winning-side gems lost to champions median 7 |
| v65 self-play / existing top-team duel record | 4/4 / 0/2 |

## 00rows

| Measure | Observed evidence |
|---|---|
| Coverage | 40 crawl games, 16 opening replays |
| Drafts (wins/appearances) | Prism/Vesper/Marcella/Vendetta 11/11; Marcella/Vendetta/Ryth/Vesper 6/7; Vesper/Vendetta/Heart/Ren 6/8 |
| Modal opening attack route by hero | Cassi: 0→2→0→4→2; Heart: 1→3→1→3; Issac: 0→2→0→2; Marcella: 0→2→0→2; Prism: 0→4→0→2; Ryth: 0→2→0; Stellar: 1→3→5→3; Tavi: 1→3→5→1→3→5; Varg: 1→3→5→1→3→5; Vendetta: 0→2→4→0→2; Vesper: 1→3 |
| Crew by group (median attackers) | 0:4, 1:4, 2:3, 3:3, 4:3, 5:3, 7:1, 8:1 |
| First fight | median R100; most common tile [((41, 24), 1)] |
| Banking | 292 submissions; median bag 26, R690; altar tiles [((15, 16), 166), ((34, 33), 126)] |
| Denial evidence in opening | contested groups []; empty-tile occupation team:group→rounds [('1:1', 136), ('0:0', 116), ('0:2', 111), ('1:3', 97)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: treasure_shard_of_focus, jungle_shard_of_focus, monster_shard_of_focus, durability_shard_of_focus; Heart of Ruin: monster_shard_of_focus, jungle_shard_of_health, power_shard_of_focus, power_shard_of_focus; Issac: treasure_shard_of_strength, monster_shard_of_strength, power_shard_of_strength, capture_shard_of_strength; Marcella: prospector_shard_of_focus, jungle_shard_of_focus, bruiser_shard_of_focus, bruiser_shard_of_focus; Prism: monster_shard_of_focus, bruiser_shard_of_focus, bruiser_shard_of_focus, jungle_shard_of_health; Ryth: prospector_shard_of_health, jungle_shard_of_health; Varg: monster_shard_of_strength, jungle_shard_of_health, power_shard_of_strength, power_shard_of_strength; Vendetta: treasure_shard_of_strength, jungle_shard_of_strength, monster_shard_of_strength, durability_shard_of_strength; Vesper Vale: treasure_shard_of_strength, monster_shard_of_strength, jungle_shard_of_health, power_shard_of_strength |
| Game endings | {'gems': 40}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 2/4 / 0/2 |

## 00rushbait-v2

| Measure | Observed evidence |
|---|---|
| Coverage | 46 crawl games, 17 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Cassi+Issac 18/20; Varg/Vendetta/Marcella/Ryth 4/5; Vesper/Heart/Vendetta/Varg 6/9 |
| Modal opening attack route by hero | Cassi: 11→13→17; Heart: 11→13→17; Issac: 11→2→4→6→8; Marcella: 3→1→5; Prism: 0→11→15→13; Ren: 6→4→5→7; Ryth: 10→12→14→10→12; Stellar: 11→0→2→4→0→2; Tavi: 0→2→12→6→8→4→6; Vendetta: 11→0→2→4→6→11; Vesper: 1 |
| Crew by group (median attackers) | 0:2, 1:2, 2:2, 3:2, 4:1.5, 5:2, 6:2, 7:2, 8:2, 9:1.5, 10:2, 11:2, 12:3, 13:2, 14:2, 15:2, 16:1, 17:2 |
| First fight | median R3; most common tile [((14, 38), 5)] |
| Banking | 259 submissions; median bag 48, R788; altar tiles [((14, 0), 166), ((15, 79), 93)] |
| Denial evidence in opening | contested groups [(11, 6), (10, 3), (13, 2), (0, 2)]; empty-tile occupation team:group→rounds [('0:0', 91), ('1:1', 75), ('0:6', 63), ('1:3', 56)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: treasure_shard_of_focus, jungle_shard_of_focus; Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_focus; Issac: treasure_shard_of_strength, capture_shard_of_strength, power_shard_of_strength, monster_shard_of_strength; Marcella: bruiser_shard_of_strength, bruiser_shard_of_health, bruiser_shard_of_focus, bruiser_shard_of_strength; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ren: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Ryth: jungle_shard_of_health, treasure_shard_of_health, durability_shard_of_health, bruiser_shard_of_health; Tavi: treasure_shard_of_strength, durability_shard_of_health, monster_shard_of_strength, bruiser_shard_of_strength; Vendetta: treasure_shard_of_strength, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Vesper Vale: treasure_shard_of_strength |
| Game endings | {'gems': 46}; winning-side gems lost to champions median 24.0 |
| v65 self-play / existing top-team duel record | 0/4 / 1/2 |

## 00split

| Measure | Observed evidence |
|---|---|
| Coverage | 50 crawl games, 18 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Cassi+Issac/Marcella 5/7; Prism/Vendetta/Marcella/Tavi/Heart 10/15; Marcella/Vesper/Vendetta/Tavi/Heart 4/6 |
| Modal opening attack route by hero | Cassi: 5→13→3→11→7; Heart: 31→5→21→1→9→5; Issac: 5→13→3→11→7; Marcella: 7→1→7; Prism: 12→10→2→12; Ren: 30→4→10→30→4; Ryth: 7→5→1→7→5; Tavi: 5→11→15; Varg: 1→7→5→11→7; Vendetta: 7→5→15→14; Vesper: 5→13→3→11; Willow: 7→5→15→23→7→5→21 |
| Crew by group (median attackers) | 0:3, 1:2, 2:3.5, 3:4, 4:2, 5:4, 6:2.5, 7:4, 8:1, 9:1, 10:3, 11:4, 12:5, 13:4, 14:2, 15:2, 16:1, 17:2, 20:1, 21:1, 22:1, 23:1, 24:1, 25:1, 26:1, 27:1, 28:1, 29:1, 30:1, 31:1 |
| First fight | median R99; most common tile [((27, 30), 1)] |
| Banking | 231 submissions; median bag 29, R503; altar tiles [((22, 32), 126), ((26, 2), 83)] |
| Denial evidence in opening | contested groups [(14, 3), (23, 1)]; empty-tile occupation team:group→rounds [('0:30', 108), ('1:31', 73), ('0:12', 43), ('1:7', 35)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus; Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Issac: treasure_shard_of_strength; Marcella: jungle_shard_of_strength, durability_shard_of_health, bruiser_shard_of_focus, bruiser_shard_of_health; Prism: monster_shard_of_health; Ryth: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Tavi: treasure_shard_of_health, treasure_shard_of_health, capture_shard_of_strength, treasure_shard_of_health; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, power_shard_of_strength, durability_shard_of_health; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, power_shard_of_strength, durability_shard_of_health; Willow: jungle_shard_of_strength |
| Game endings | {'gems': 50}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 2/2 / 0/1 |

## 00stampede

| Measure | Observed evidence |
|---|---|
| Coverage | 43 crawl games, 15 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Cassi+Issac/Marcella 7/7; Ryth/Prism/Vesper/Marcella/Heart 7/10; Vesper/Vendetta/Heart/Varg/Marcella 3/3 |
| Modal opening attack route by hero | Heart: 12; Issac: 2→0→4→0→4→6→8; Marcella: 3; Prism: 12→3→12; Ryth: 3; Tavi: 11→12; Varg: 0→2→0; Vendetta: 11; Vesper: 2→0→4→6→8; Willow: 11→0 |
| Crew by group (median attackers) | 0:1, 1:1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1, 11:1, 12:2 |
| First fight | median R31; most common tile [((4, 25), 2)] |
| Banking | 61 submissions; median bag 148, R1328; altar tiles [((31, 23), 40), ((31, 26), 21)] |
| Denial evidence in opening | contested groups [(12, 8), (11, 6)]; empty-tile occupation team:group→rounds [('1:3', 58), ('1:11', 53), ('1:12', 45), ('0:2', 44)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Marcella: jungle_shard_of_strength, durability_shard_of_health, bruiser_shard_of_focus, bruiser_shard_of_health; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ryth: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Tavi: treasure_shard_of_health, capture_shard_of_strength, treasure_shard_of_strength, treasure_shard_of_health; Varg: treasure_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health, bruiser_shard_of_health; Vendetta: treasure_shard_of_strength, power_shard_of_strength, jungle_shard_of_strength, durability_shard_of_health; Vesper Vale: jungle_shard_of_strength, bruiser_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Willow: jungle_shard_of_strength, treasure_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health |
| Game endings | {'gems': 30, 'tiebreak_gems': 13}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 2/4 / 1/2 |

## 00swirl

| Measure | Observed evidence |
|---|---|
| Coverage | 46 crawl games, 11 opening replays |
| Drafts (wins/appearances) | Heart/Marcella/Vendetta/Vesper 4/4; Prism/Vendetta/Marcella/Heart 4/6; Marcella/Vendetta/Ryth/Vesper 9/15 |
| Modal opening attack route by hero | Cassi: 11→21→10→11→19→21→11→10; Heart: 11→19→11→19→11→10→11→19; Issac: 11→21→19→11→19→21→11→10; Marcella: 11→19→21→11; Prism: 10→18→10→20→11; Ryth: 10→11; Stellar: 10→18→10→20→11; Tavi: 11→21→19→9→11; Varg: 10→11→18→10→11; Vendetta: 11→10→19→11→10→11→10→19; Vesper: 11→10→19 |
| Crew by group (median attackers) | 0:2, 7:3, 8:1, 9:1, 10:4, 11:4, 13:1, 18:2.5, 19:3.5, 20:2, 21:1 |
| First fight | median R16; most common tile [((21, 13), 5)] |
| Banking | 230 submissions; median bag 23, R718; altar tiles [((23, 10), 129), ((21, 19), 101)] |
| Denial evidence in opening | contested groups [(10, 9), (11, 8), (18, 1)]; empty-tile occupation team:group→rounds [('1:11', 218), ('0:10', 127), ('0:20', 51), ('1:10', 40)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus, durability_shard_of_focus, bruiser_shard_of_health; Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_health; Issac: treasure_shard_of_strength, power_shard_of_strength, home_shard_of_health, durability_shard_of_health; Marcella: treasure_shard_of_focus, jungle_shard_of_strength, monster_shard_of_strength, bruiser_shard_of_strength; Prism: monster_shard_of_focus, home_shard_of_health, bruiser_shard_of_focus, bruiser_shard_of_focus; Ryth: prospector_shard_of_health, treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health; Tavi: treasure_shard_of_strength, bruiser_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Vendetta: treasure_shard_of_strength, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Vesper Vale: prospector_shard_of_strength, treasure_shard_of_strength, capture_shard_of_strength, jungle_shard_of_health |
| Game endings | {'gems': 46}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | not on fixed plan / no duel evidence |

## 00the-line

| Measure | Observed evidence |
|---|---|
| Coverage | 44 crawl games, 16 opening replays |
| Drafts (wins/appearances) | Prism/Marcella/Ryth/Heart 11/13; Vesper/Vendetta/Heart/Cassi+Issac 10/14; Stellar/Heart/Ryth/Marcella 3/4 |
| Modal opening attack route by hero | Cassi: 2→0→1; Heart: 2; Issac: 2; Marcella: 2; Prism: 2→8→2; Ryth: 2→8; Stellar: 2; Tavi: 2; Varg: 2→8→3; Vendetta: 2; Vesper: 2; Willow: 2→8→4 |
| Crew by group (median attackers) | 0:1.5, 1:1, 2:3, 3:1, 4:2, 5:1, 6:2, 7:2, 8:1 |
| First fight | median R13; most common tile [((16, 17), 2)] |
| Banking | 165 submissions; median bag 44, R554; altar tiles [((3, 16), 165)] |
| Denial evidence in opening | contested groups [(2, 16), (5, 1)]; empty-tile occupation team:group→rounds [('1:2', 111), ('0:2', 51), ('1:1', 25), ('0:7', 15)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus, durability_shard_of_focus, bruiser_shard_of_health; Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health; Issac: treasure_shard_of_strength, power_shard_of_strength; Marcella: bruiser_shard_of_strength, bruiser_shard_of_health, bruiser_shard_of_focus, bruiser_shard_of_strength; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ryth: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Stellar: treasure_shard_of_focus, power_shard_of_focus, home_shard_of_health, durability_shard_of_health; Tavi: bruiser_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Vendetta: durability_shard_of_strength, treasure_shard_of_strength; Vesper Vale: hunter_shard_of_strength, jungle_shard_of_health, durability_shard_of_health, bruiser_shard_of_strength |
| Game endings | {'gems': 44}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 2/2 / 0/1 |

## 00vault

| Measure | Observed evidence |
|---|---|
| Coverage | 32 crawl games, 9 opening replays |
| Drafts (wins/appearances) | Prism/Marcella/Ryth/Heart 5/5; Marcella/Heart/Vesper/Ryth 6/8; Vesper/Vendetta/Heart/Ryth 3/4 |
| Modal opening attack route by hero | Cassi: 4→0; Heart: 0; Issac: 4→0→6; Marcella: 0; Prism: 0; Ryth: 0; Varg: 4→0; Vendetta: 0→1→0; Vesper: 0 |
| Crew by group (median attackers) | 0:4, 1:1, 2:1, 3:1, 4:1, 5:1, 6:1 |
| First fight | median R39; most common tile [((19, 15), 4)] |
| Banking | 28 submissions; median bag 171, R306; altar tiles [((25, 5), 16), ((5, 25), 12)] |
| Denial evidence in opening | contested groups [(0, 9), (2, 1)]; empty-tile occupation team:group→rounds [('1:0', 116), ('0:0', 30), ('0:3', 20), ('1:4', 19)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: treasure_shard_of_focus, jungle_shard_of_focus; Heart of Ruin: jungle_shard_of_focus, treasure_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Issac: treasure_shard_of_strength; Marcella: jungle_shard_of_focus; Ryth: treasure_shard_of_strength, bruiser_shard_of_health; Vendetta: hunter_shard_of_strength, jungle_shard_of_strength, durability_shard_of_health, bruiser_shard_of_strength; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength |
| Game endings | {'gems': 32}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 0/2 / 0/1 |

## 01big-world

| Measure | Observed evidence |
|---|---|
| Coverage | 51 crawl games, 17 opening replays |
| Drafts (wins/appearances) | Marcella/Vendetta/Ryth/Vesper/Heart 9/9; Vesper/Vendetta/Heart/Ren/Cassi+Issac 7/7; Vesper/Heart/Vendetta/Ryth/Marcella 5/7 |
| Modal opening attack route by hero | Cassi: 7→19→7→19; Heart: 7→23→7→23; Issac: 7→23→7; Marcella: 23→7; Prism: 23→7→19; Ren: 22→12; Ryth: 22→6→22→6; Tavi: 19→23→7; Varg: 7→23→7→23; Vendetta: 23; Vesper: 22→6; Willow: 23→7→13 |
| Crew by group (median attackers) | 0:1, 1:1, 2:1, 3:1, 4:1, 5:1, 6:5, 7:4, 8:2.5, 9:1.5, 10:1, 11:1, 12:1, 13:1, 18:2, 19:2, 20:1, 21:2, 22:4, 23:5 |
| First fight | median R133; most common tile [((67, 50), 1)] |
| Banking | 284 submissions; median bag 37, R626; altar tiles [((43, 20), 152), ((56, 79), 93)] |
| Denial evidence in opening | contested groups [(10, 1)]; empty-tile occupation team:group→rounds [('1:23', 56), ('1:7', 54), ('0:6', 51), ('0:22', 47)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: jungle_shard_of_focus; Heart of Ruin: jungle_shard_of_health; Issac: monster_shard_of_strength, power_shard_of_strength, home_shard_of_health, durability_shard_of_health; Marcella: prospector_shard_of_health, treasure_shard_of_strength, jungle_shard_of_health, monster_shard_of_strength; Ryth: jungle_shard_of_strength, treasure_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Varg: monster_shard_of_strength, power_shard_of_strength, home_shard_of_health, durability_shard_of_health; Vendetta: monster_shard_of_strength, jungle_shard_of_strength, durability_shard_of_health, bruiser_shard_of_strength; Vesper Vale: prospector_shard_of_strength, treasure_shard_of_strength, jungle_shard_of_strength, monster_shard_of_health |
| Game endings | {'gems': 51}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 2/4 / 0/2 |

## 01boss-battle

| Measure | Observed evidence |
|---|---|
| Coverage | 40 crawl games, 10 opening replays |
| Drafts (wins/appearances) | Heart/Marcella/Ryth/Vendetta/Vesper 8/8; Heart/Ren/Ryth/Vesper/Marcella 8/8; Vesper/Ryth/Vendetta/Varg/Marcella 4/4 |
| Modal opening attack route by hero | Cassi: 24→5→26→24; Heart: 11→22→11→22→13; Issac: 24→22→13; Marcella: 11→15; Prism: 2→14→10; Ren: 28→24→7→22→5; Ryth: 11→22→15; Stellar: 28→24→7→22→5; Tavi: 9→24→30→13→9; Varg: 11→22→15→18; Vendetta: 2→14; Vesper: 11→22→11→22→15 |
| Crew by group (median attackers) | 0:2, 2:4, 3:4.5, 4:1, 5:2, 6:2, 7:4, 8:1, 9:5, 10:2, 11:4, 12:1, 13:1, 14:5, 15:4, 16:1.5, 17:4, 18:3.5, 21:3, 22:3, 23:4, 24:3, 25:1, 26:1, 27:5, 28:5, 29:5, 30:3.5 |
| First fight | no basic-attack fight by R150 |
| Banking | 49 submissions; median bag 34, R1030; altar tiles [((25, 20), 49)] |
| Denial evidence in opening | contested groups []; empty-tile occupation team:group→rounds [('1:9', 25), ('0:29', 24), ('1:22', 23), ('1:5', 20)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: prospector_shard_of_focus, durability_shard_of_health, monster_shard_of_focus, capture_shard_of_health; Heart of Ruin: treasure_shard_of_focus, power_shard_of_focus, durability_shard_of_health, home_shard_of_health; Issac: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Marcella: treasure_shard_of_strength, jungle_shard_of_focus, treasure_shard_of_focus, jungle_shard_of_strength; Prism: durability_shard_of_health, prospector_shard_of_focus, monster_shard_of_focus, capture_shard_of_health; Ren: treasure_shard_of_health, bruiser_shard_of_health, jungle_shard_of_focus, durability_shard_of_health; Ryth: treasure_shard_of_health, jungle_shard_of_strength, monster_shard_of_health, bruiser_shard_of_health; Stellar: treasure_shard_of_focus, power_shard_of_focus, home_shard_of_health, durability_shard_of_health; Tavi: treasure_shard_of_strength, bruiser_shard_of_strength; Varg: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vendetta: jungle_shard_of_strength, treasure_shard_of_strength, monster_shard_of_strength, home_shard_of_strength; Vesper Vale: jungle_shard_of_strength, treasure_shard_of_strength, power_shard_of_strength, monster_shard_of_health |
| Game endings | {'tiebreak_gems': 9, 'gems': 31}; winning-side gems lost to champions median 47.0 |
| v65 self-play / existing top-team duel record | 6/8 / 1/4 |

## 01broken-curve

| Measure | Observed evidence |
|---|---|
| Coverage | 41 crawl games, 11 opening replays |
| Drafts (wins/appearances) | Marcella/Vendetta/Heart 6/8; Vesper/Heart/Vendetta 8/11; Marcella/Vendetta/Varg 3/4 |
| Modal opening attack route by hero | Heart: 6→8→2→6; Marcella: 6→20→6; Prism: 2→4→6→2; Ryth: 3→11→9→3; Tavi: 21→18→19→16→14→17→15→16; Varg: 16→18→19; Vendetta: 7→15→14→21→19; Vesper: 8→6→2→6 |
| Crew by group (median attackers) | 2:2, 3:2, 4:2, 5:1, 6:3, 7:3, 8:1, 9:1, 10:2, 11:2, 14:1, 15:1, 16:1, 17:1, 18:2, 19:2, 20:1, 21:2 |
| First fight | median R45; most common tile [((22, 18), 2)] |
| Banking | 151 submissions; median bag 19, R469; altar tiles [((10, 22), 64), ((19, 16), 35)] |
| Denial evidence in opening | contested groups [(16, 2), (17, 2), (20, 1), (15, 1)]; empty-tile occupation team:group→rounds [('1:9', 46), ('0:8', 42), ('1:16', 35), ('1:7', 29)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus; Marcella: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Ryth: prospector_shard_of_health, treasure_shard_of_health, jungle_shard_of_health, monster_shard_of_health; Vendetta: monster_shard_of_strength, jungle_shard_of_strength, durability_shard_of_health, bruiser_shard_of_strength; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health |
| Game endings | {'gems': 41}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 2/2 / 0/1 |

## 01concentrated-wealth

| Measure | Observed evidence |
|---|---|
| Coverage | 53 crawl games, 14 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Cassi+Issac/Willow 8/9; Vesper/Vendetta/Heart/Varg/Marcella 11/14; Vesper/Heart/Vendetta/Ryth/Marcella 4/5 |
| Modal opening attack route by hero | Cassi: 2→6→2→6; Heart: 0; Issac: 2→0→2; Marcella: 1; Prism: 0; Ren: 0; Ryth: 0; Stellar: 1→9→3; Tavi: 1; Varg: 2→6→2→6; Vendetta: 0; Vesper: 2→0→2; Willow: 2→6 |
| Crew by group (median attackers) | 0:2, 1:2, 2:2, 3:1, 4:1.5, 5:2, 6:2, 7:1, 8:1, 9:1, 10:2 |
| First fight | median R74; most common tile [((31, 27), 2)] |
| Banking | 351 submissions; median bag 22, R680; altar tiles [((37, 36), 214), ((23, 24), 137)] |
| Denial evidence in opening | contested groups [(0, 11), (7, 5), (8, 4)]; empty-tile occupation team:group→rounds [('0:0', 196), ('1:0', 72), ('0:8', 54), ('1:2', 16)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus, durability_shard_of_focus, bruiser_shard_of_health; Heart of Ruin: treasure_shard_of_focus, bruiser_shard_of_health, durability_shard_of_health, bruiser_shard_of_health; Issac: treasure_shard_of_strength, power_shard_of_strength, home_shard_of_health; Marcella: prospector_shard_of_focus, treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ren: treasure_shard_of_focus, bruiser_shard_of_health, jungle_shard_of_focus, durability_shard_of_health; Ryth: jungle_shard_of_strength, treasure_shard_of_strength; Tavi: treasure_shard_of_health, treasure_shard_of_strength, bruiser_shard_of_strength, monster_shard_of_strength; Varg: treasure_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health, bruiser_shard_of_health; Vendetta: jungle_shard_of_strength, bruiser_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vesper Vale: jungle_shard_of_strength, bruiser_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Willow: jungle_shard_of_strength, treasure_shard_of_strength |
| Game endings | {'gems': 53}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 4/4 / 0/2 |

## 01corridors

| Measure | Observed evidence |
|---|---|
| Coverage | 53 crawl games, 18 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Cassi+Issac/Tavi 13/14; Marcella/Vesper/Vendetta/Tavi/Heart 3/4; Prism/Vesper/Marcella/Vendetta/Heart 6/9 |
| Modal opening attack route by hero | Cassi: 1→6→1→6; Heart: 1→6→1; Issac: 1→6→1→6; Marcella: 5; Prism: 1→6→1; Ren: 4; Ryth: 10→7; Tavi: 1→6; Varg: 11; Vendetta: 1→6→1→6; Vesper: 1→5; Willow: 1→6→1→6 |
| Crew by group (median attackers) | 1:4, 2:1, 3:3, 4:1.5, 5:2, 6:3, 7:3, 9:1, 10:5, 11:2 |
| First fight | median R58; most common tile [((18, 28), 1)] |
| Banking | 174 submissions; median bag 65, R844; altar tiles [((13, 20), 106), ((13, 19), 68)] |
| Denial evidence in opening | contested groups [(5, 9), (1, 7), (7, 5), (6, 2)]; empty-tile occupation team:group→rounds [('1:5', 53), ('0:1', 46), ('0:6', 44), ('1:7', 43)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: treasure_shard_of_focus, bruiser_shard_of_health, jungle_shard_of_focus, durability_shard_of_focus; Heart of Ruin: treasure_shard_of_focus, bruiser_shard_of_health, durability_shard_of_health, bruiser_shard_of_health; Issac: treasure_shard_of_strength; Marcella: treasure_shard_of_focus, jungle_shard_of_focus, capture_shard_of_focus, monster_shard_of_focus; Prism: monster_shard_of_focus, jungle_shard_of_health, bruiser_shard_of_health, home_shard_of_health; Ren: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Ryth: jungle_shard_of_strength, treasure_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Tavi: treasure_shard_of_health, treasure_shard_of_health, treasure_shard_of_health, treasure_shard_of_health; Varg: jungle_shard_of_strength, treasure_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Willow: treasure_shard_of_strength |
| Game endings | {'gems': 53}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 2/4 / 1/2 |

## 01elk-arena

| Measure | Observed evidence |
|---|---|
| Coverage | 55 crawl games, 23 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Cassi+Issac/Marcella 8/9; Prism/Vendetta/Marcella/Tavi/Heart 7/9; Marcella/Vendetta/Ryth/Vesper/Heart 7/10 |
| Modal opening attack route by hero | Cassi: 4→0→20→26→22; Heart: 0; Issac: 0→6→28→17→9→0; Marcella: 0; Prism: 0; Ren: 3→2→0→4; Ryth: 0; Stellar: 0→2→4→3→4; Tavi: 0→3→2→4→0→3; Varg: 0→1→5; Vendetta: 0; Vesper: 3→1→3→1→0→4→0→4; Willow: 0→3→0→3→1→5→19→0 |
| Crew by group (median attackers) | 0:4, 1:1, 2:2, 3:2, 4:2, 5:1, 6:1, 8:1, 9:1, 10:1, 11:1, 12:1, 13:1, 14:1, 16:1, 17:1, 18:1, 19:1, 20:1, 21:1, 22:1, 23:1, 24:1, 25:1.5, 26:1, 27:1, 28:1 |
| First fight | median R23; most common tile [((25, 23), 6)] |
| Banking | 346 submissions; median bag 36, R794; altar tiles [((27, 27), 186), ((22, 22), 160)] |
| Denial evidence in opening | contested groups [(0, 22), (1, 6), (3, 5), (2, 5)]; empty-tile occupation team:group→rounds [('1:0', 354), ('0:0', 311), ('0:3', 253), ('1:4', 218)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus, durability_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_health; Heart of Ruin: prospector_shard_of_health, treasure_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Issac: treasure_shard_of_strength, power_shard_of_strength, home_shard_of_health, durability_shard_of_health; Marcella: prospector_shard_of_health, treasure_shard_of_focus, capture_shard_of_health, jungle_shard_of_focus; Prism: prospector_shard_of_health, monster_shard_of_focus, home_shard_of_health, bruiser_shard_of_focus; Ren: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Ryth: prospector_shard_of_health, jungle_shard_of_focus, treasure_shard_of_health, bruiser_shard_of_health; Tavi: treasure_shard_of_health, capture_shard_of_strength, treasure_shard_of_strength, bruiser_shard_of_strength; Varg: jungle_shard_of_strength, treasure_shard_of_strength, durability_shard_of_health, bruiser_shard_of_strength; Vendetta: prospector_shard_of_health, treasure_shard_of_strength, capture_shard_of_health, jungle_shard_of_strength; Vesper Vale: prospector_shard_of_strength, treasure_shard_of_strength, jungle_shard_of_strength, capture_shard_of_health; Willow: power_shard_of_strength, power_shard_of_strength, power_shard_of_strength, power_shard_of_strength |
| Game endings | {'gems': 52, 'tiebreak_gems': 3}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 2/4 / 1/2 |

## 01fracture

| Measure | Observed evidence |
|---|---|
| Coverage | 42 crawl games, 13 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Varg/Marcella 8/9; Marcella/Vendetta/Ryth/Vesper/Ren 8/10; Vesper/Cassi+Issac/Ren/Vendetta/Heart 3/5 |
| Modal opening attack route by hero | Cassi: 13→5→13; Heart: 2→8→16; Issac: 13→3→13; Marcella: 8→6; Prism: 12→2; Ren: 13→9→17→22→13; Ryth: 13→11; Stellar: 12→2; Tavi: 4→18→24→27; Varg: 13→11→13; Vendetta: 4→8→2→4; Vesper: 2→8→16; Willow: 12→2→12 |
| Crew by group (median attackers) | 0:1, 1:1, 2:2, 3:2, 4:1.5, 5:1, 6:1, 7:2, 8:3.5, 9:4, 10:1, 11:1, 12:4, 13:4, 15:1.5, 16:2, 17:4, 18:1, 19:1, 22:1.5, 23:3, 24:1, 25:1, 26:1, 27:1 |
| First fight | median R126; most common tile [((30, 36), 1)] |
| Banking | 136 submissions; median bag 44, R688; altar tiles [((26, 35), 72), ((34, 35), 46)] |
| Denial evidence in opening | contested groups []; empty-tile occupation team:group→rounds [('0:24', 42), ('0:2', 40), ('1:13', 36), ('1:3', 29)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: monster_shard_of_focus; Heart of Ruin: monster_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_health; Issac: monster_shard_of_strength, power_shard_of_strength, home_shard_of_health, durability_shard_of_health; Marcella: prospector_shard_of_health, jungle_shard_of_strength, treasure_shard_of_health, monster_shard_of_focus; Ren: bruiser_shard_of_health, durability_shard_of_health, power_shard_of_focus, power_shard_of_focus; Ryth: prospector_shard_of_health, jungle_shard_of_health, treasure_shard_of_health; Tavi: treasure_shard_of_health, capture_shard_of_strength, treasure_shard_of_health, treasure_shard_of_strength; Varg: prospector_shard_of_strength, jungle_shard_of_health; Vendetta: prospector_shard_of_health, treasure_shard_of_strength, jungle_shard_of_health, monster_shard_of_strength; Vesper Vale: prospector_shard_of_strength, treasure_shard_of_strength, jungle_shard_of_strength, monster_shard_of_health; Willow: treasure_shard_of_strength |
| Game endings | {'gems': 42}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 1/2 / 0/1 |

## 01gold-rush

| Measure | Observed evidence |
|---|---|
| Coverage | 37 crawl games, 16 opening replays |
| Drafts (wins/appearances) | Vesper/Heart/Vendetta 12/13; Ryth/Vendetta/Marcella 10/12; Marcella/Vesper/Vendetta 5/6 |
| Modal opening attack route by hero | Heart: 10→14; Marcella: 2; Prism: 3→10; Ryth: 4→3; Tavi: 11→1→4→3→5→13; Vendetta: 1→3→10; Vesper: 10→3 |
| Crew by group (median attackers) | 0:1, 1:1, 2:1, 3:2, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1, 10:1, 11:2, 12:1, 13:1, 14:1 |
| First fight | median R26; most common tile [((16, 19), 2)] |
| Banking | 259 submissions; median bag 11, R909; altar tiles [((7, 4), 81), ((23, 26), 76)] |
| Denial evidence in opening | contested groups [(3, 9), (4, 4), (1, 4), (14, 2)]; empty-tile occupation team:group→rounds [('0:4', 68), ('1:3', 68), ('0:3', 53), ('0:2', 52)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_focus; Marcella: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Ryth: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Vesper Vale: capture_shard_of_strength, treasure_shard_of_strength, durability_shard_of_health, power_shard_of_strength |
| Game endings | {'gems': 37}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | not on fixed plan / no duel evidence |

## 01hooks

| Measure | Observed evidence |
|---|---|
| Coverage | 59 crawl games, 24 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Cassi+Issac 24/30; Varg/Vendetta/Marcella/Ryth 4/5; Prism/Vendetta/Marcella/Heart 5/9 |
| Modal opening attack route by hero | Cassi: 5→6→11→3→11→5; Heart: 9→5→6→1→5→9; Issac: 9→5→3→11; Marcella: 4; Prism: 2→9→10→8→7→8; Ryth: 4→0; Stellar: 9→11→3→7→2; Tavi: 5→9→3→6→1; Varg: 10→5→4→10; Vendetta: 8→4→3→4; Vesper: 10→7→9→0→4 |
| Crew by group (median attackers) | 0:1, 1:1, 2:3, 3:3, 4:3, 5:3, 6:1, 7:1, 8:2, 9:2, 10:1, 11:1 |
| First fight | median R28; most common tile [((14, 17), 5)] |
| Banking | 612 submissions; median bag 22, R792; altar tiles [((15, 15), 612)] |
| Denial evidence in opening | contested groups [(3, 8), (2, 6), (11, 4), (9, 4)]; empty-tile occupation team:group→rounds [('1:9', 239), ('0:8', 204), ('1:3', 117), ('0:2', 101)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus, durability_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_health; Heart of Ruin: jungle_shard_of_focus, treasure_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Issac: treasure_shard_of_strength, power_shard_of_strength; Marcella: bruiser_shard_of_strength, bruiser_shard_of_health, bruiser_shard_of_focus, bruiser_shard_of_strength; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ryth: jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health, power_shard_of_strength; Tavi: treasure_shard_of_strength, bruiser_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Varg: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vesper Vale: jungle_shard_of_strength, bruiser_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health |
| Game endings | {'gems': 59}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 4/6 / 1/3 |

## 01islands

| Measure | Observed evidence |
|---|---|
| Coverage | 46 crawl games, 13 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Ren/Cassi+Issac 10/13; Marcella/Vendetta/Ryth/Vesper/Heart 5/8; Prism/Vesper/Marcella/Ryth/Heart 9/16 |
| Modal opening attack route by hero | Cassi: 38→2→40→38→2; Heart: 38; Issac: 44→38→2→40→38→8→12; Marcella: 39→40; Prism: 39→3→39; Ren: 30→8→12; Ryth: 45→39→3→39; Tavi: 3→38; Varg: 44; Vendetta: 38; Vesper: 39→3→39; Willow: 39→40→39 |
| Crew by group (median attackers) | 2:4.5, 3:3, 8:1, 9:1, 11:1, 12:2, 13:1.5, 14:1, 15:1, 16:2, 17:2, 20:1, 21:1, 22:1, 23:1, 24:1, 26:1, 28:1, 29:1, 30:1.5, 31:1, 36:1, 37:1, 38:4, 39:4.5, 40:3, 41:2, 42:1, 44:1, 45:2 |
| First fight | median R88; most common tile [((3, 27), 1)] |
| Banking | 245 submissions; median bag 30, R543; altar tiles [((25, 4), 120), ((34, 55), 83)] |
| Denial evidence in opening | contested groups [(40, 2), (3, 1), (2, 1)]; empty-tile occupation team:group→rounds [('0:44', 128), ('1:39', 67), ('0:38', 48), ('1:45', 42)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, monster_shard_of_strength, bruiser_shard_of_health; Issac: monster_shard_of_strength, jungle_shard_of_health, power_shard_of_strength, power_shard_of_strength; Marcella: prospector_shard_of_health, treasure_shard_of_focus, jungle_shard_of_strength, monster_shard_of_health; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ryth: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Varg: jungle_shard_of_strength, treasure_shard_of_strength, durability_shard_of_health, bruiser_shard_of_strength; Vendetta: treasure_shard_of_strength, jungle_shard_of_strength, monster_shard_of_strength, bruiser_shard_of_health; Vesper Vale: prospector_shard_of_strength, treasure_shard_of_strength, jungle_shard_of_strength, capture_shard_of_health; Willow: treasure_shard_of_focus, jungle_shard_of_focus |
| Game endings | {'gems': 46}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 4/4 / 0/2 |

## 01shortcut

| Measure | Observed evidence |
|---|---|
| Coverage | 44 crawl games, 12 opening replays |
| Drafts (wins/appearances) | Vesper/Heart/Ryth/Marcella 5/6; Heart/Varg/Vendetta/Ryth 7/10; Vesper/Heart/Vendetta/Varg 5/8 |
| Modal opening attack route by hero | Cassi: 3→7→2; Heart: 3→9→3; Issac: 19→0→2→7→3; Marcella: 4; Prism: 3→9→3; Ren: 4→10→4→20→10; Ryth: 3→2→0; Stellar: 3→19; Tavi: 4→10→20→4→0→2; Varg: 19→3→11; Vendetta: 4→0→16; Vesper: 3→19→0→2→19→3 |
| Crew by group (median attackers) | 0:1, 1:2, 2:2, 3:4, 4:4, 7:2, 8:2, 9:1, 10:1, 11:1, 16:1, 17:1, 19:1, 20:1 |
| First fight | median R106; most common tile [((16, 21), 2)] |
| Banking | 140 submissions; median bag 50, R684; altar tiles [((32, 12), 79), ((32, 27), 61)] |
| Denial evidence in opening | contested groups [(0, 9), (2, 5)]; empty-tile occupation team:group→rounds [('1:19', 95), ('0:20', 73), ('1:3', 46), ('1:2', 37)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: treasure_shard_of_focus, jungle_shard_of_focus; Marcella: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Ryth: treasure_shard_of_health; Tavi: hunter_shard_of_focus, hunter_shard_of_focus, durability_shard_of_focus, bruiser_shard_of_focus; Vendetta: treasure_shard_of_strength, jungle_shard_of_health, durability_shard_of_health, bruiser_shard_of_strength; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_strength, durability_shard_of_health |
| Game endings | {'gems': 44}; winning-side gems lost to champions median 21 |
| v65 self-play / existing top-team duel record | 2/4 / 0/2 |

## 01starfish

| Measure | Observed evidence |
|---|---|
| Coverage | 39 crawl games, 11 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Varg/Marcella 7/10; Prism/Marcella/Vendetta/Heart/Vesper 8/13; Vesper/Vendetta/Heart/Cassi+Issac/Tavi 5/8 |
| Modal opening attack route by hero | Cassi: 2→4→3; Heart: 1; Issac: 1→2→1→3; Marcella: 0; Prism: 0; Ren: 0; Ryth: 1; Stellar: 0→7→0→9; Tavi: 0; Varg: 1; Vendetta: 1; Vesper: 1; Willow: 0 |
| Crew by group (median attackers) | 0:5, 1:4.5, 2:2, 3:4, 4:1.5, 5:2, 6:1, 7:1, 8:1, 9:2, 10:1, 11:1, 12:1, 13:1, 15:2.5 |
| First fight | median R30; most common tile [((23, 12), 3)] |
| Banking | 176 submissions; median bag 36, R716; altar tiles [((23, 17), 117), ((26, 17), 59)] |
| Denial evidence in opening | contested groups [(0, 2)]; empty-tile occupation team:group→rounds [('0:0', 75), ('1:1', 68), ('1:0', 11), ('0:7', 6)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus; Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_health; Issac: treasure_shard_of_strength, power_shard_of_strength; Marcella: treasure_shard_of_focus, capture_shard_of_focus, jungle_shard_of_focus, monster_shard_of_focus; Prism: monster_shard_of_health, jungle_shard_of_health, bruiser_shard_of_focus, bruiser_shard_of_focus; Ryth: prospector_shard_of_health, bruiser_shard_of_focus, bruiser_shard_of_health; Tavi: treasure_shard_of_health, treasure_shard_of_strength, treasure_shard_of_health, bruiser_shard_of_strength; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Willow: jungle_shard_of_strength, durability_shard_of_health, power_shard_of_strength, bruiser_shard_of_strength |
| Game endings | {'gems': 38, 'tiebreak_gems': 1}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 2/4 / 0/2 |

## 01starvation

| Measure | Observed evidence |
|---|---|
| Coverage | 45 crawl games, 15 opening replays |
| Drafts (wins/appearances) | Heart/Ryth/Vendetta/Tavi/Marcella 8/8; Heart/Marcella/Ryth/Vendetta/Vesper 9/10; Vesper/Vendetta/Heart/Varg/Marcella 9/10 |
| Modal opening attack route by hero | Heart: 3→5; Issac: 7; Marcella: 5; Prism: 6; Ren: 7→6→5; Ryth: 12; Tavi: 5; Varg: 7; Vendetta: 1→9→8; Vesper: 12; Willow: 7 |
| Crew by group (median attackers) | 0:1, 1:1, 2:1, 3:1, 4:1, 5:2, 6:1, 7:2, 8:1, 9:1, 12:1, 13:1 |
| First fight | median R84; most common tile [((40, 4), 2)] |
| Banking | 258 submissions; median bag 28, R1102; altar tiles [((35, 15), 178), ((44, 15), 80)] |
| Denial evidence in opening | contested groups [(5, 5), (6, 2)]; empty-tile occupation team:group→rounds [('1:0', 20), ('1:4', 19), ('0:3', 18), ('1:5', 17)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Marcella: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Ryth: treasure_shard_of_health; Tavi: treasure_shard_of_strength, durability_shard_of_health; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, monster_shard_of_strength, durability_shard_of_health; Willow: treasure_shard_of_focus, jungle_shard_of_focus |
| Game endings | {'gems': 39, 'tiebreak_gems': 6}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 2/2 / 0/1 |

## 01the-farm

| Measure | Observed evidence |
|---|---|
| Coverage | 60 crawl games, 16 opening replays |
| Drafts (wins/appearances) | Marcella/Vendetta/Heart 6/7; Marcella/Vendetta/Varg 10/13; Marcella/Vendetta/Ryth 10/13 |
| Modal opening attack route by hero | Heart: 10→0→12→7; Marcella: 11→1→8→11→8; Prism: 8→11; Ren: 0→16→12→26→2→12; Ryth: 1→8→2→1; Stellar: 0→7→10→7; Tavi: 11→1→13→11→8→1; Varg: 0→16→12→16; Vendetta: 11→1→13→11→8→1; Vesper: 10→0→26→5→7 |
| Crew by group (median attackers) | 0:3, 1:3, 2:2, 3:1.5, 4:2.5, 5:1, 6:1, 7:3, 8:3, 10:3, 11:3, 12:2, 13:2, 16:1, 18:3, 19:3, 20:3, 26:1, 27:1 |
| First fight | median R118; most common tile [((24, 16), 1)] |
| Banking | 141 submissions; median bag 59, R635; altar tiles [((26, 22), 72), ((23, 22), 47)] |
| Denial evidence in opening | contested groups [(16, 2)]; empty-tile occupation team:group→rounds [('1:8', 40), ('1:1', 30), ('0:10', 27), ('1:11', 24)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: monster_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_health; Marcella: prospector_shard_of_health, treasure_shard_of_strength, jungle_shard_of_health, monster_shard_of_strength; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ryth: prospector_shard_of_health, jungle_shard_of_health, bruiser_shard_of_focus, bruiser_shard_of_health; Tavi: jungle_shard_of_strength, monster_shard_of_strength, bruiser_shard_of_strength, durability_shard_of_health; Vendetta: jungle_shard_of_strength, treasure_shard_of_strength, monster_shard_of_strength, home_shard_of_strength; Vesper Vale: monster_shard_of_strength, jungle_shard_of_health, durability_shard_of_health, bruiser_shard_of_strength |
| Game endings | {'gems': 60}; winning-side gems lost to champions median 11.5 |
| v65 self-play / existing top-team duel record | 0/2 / 0/1 |

## 01yellow-brick-road

| Measure | Observed evidence |
|---|---|
| Coverage | 71 crawl games, 30 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Cassi+Issac/Marcella 14/15; Prism/Vendetta/Marcella/Tavi/Heart 12/13; Vesper/Ryth/Vendetta/Varg/Marcella 5/6 |
| Modal opening attack route by hero | Cassi: 2→4→0→2→0→4→1→8; Heart: 0; Issac: 2→4→2→4→1→12→8; Marcella: 0; Prism: 9→1→3→27→23→9; Ren: 1→0→3; Ryth: 9→0→27→23→9→0; Stellar: 0→1; Tavi: 1→0→7→0→1; Varg: 1→0→4→1→14; Vendetta: 9→0→27→23→1; Vesper: 0; Willow: 9→0→3→0→5→0→5→0 |
| Crew by group (median attackers) | 0:2.5, 1:3, 2:3, 3:3, 4:4, 5:4, 6:2, 7:2, 8:3, 9:3, 10:2, 11:1, 12:1, 13:2, 14:2, 15:1, 16:2.5, 17:2.5, 18:1, 19:1, 20:4, 22:2, 23:3, 24:3, 26:2, 27:3 |
| First fight | median R29; most common tile [((32, 14), 3)] |
| Banking | 607 submissions; median bag 23, R598; altar tiles [((6, 5), 174), ((33, 24), 145)] |
| Denial evidence in opening | contested groups [(0, 28), (1, 27), (7, 2), (6, 2)]; empty-tile occupation team:group→rounds [('0:1', 226), ('1:5', 123), ('1:1', 122), ('1:0', 103)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus, durability_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_health; Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_health; Issac: treasure_shard_of_strength, power_shard_of_strength, home_shard_of_health, durability_shard_of_health; Marcella: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Prism: monster_shard_of_focus, bruiser_shard_of_focus, bruiser_shard_of_focus, bruiser_shard_of_focus; Ren: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Ryth: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Tavi: treasure_shard_of_strength, durability_shard_of_health, monster_shard_of_strength, bruiser_shard_of_strength; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Willow: jungle_shard_of_strength, power_shard_of_strength |
| Game endings | {'gems': 70, 'tiebreak_gems': 1}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 2/2 / 1/1 |

## 02arena

| Measure | Observed evidence |
|---|---|
| Coverage | 51 crawl games, 16 opening replays |
| Drafts (wins/appearances) | Marcella/Vendetta/Heart 7/8; Vesper/Heart/Marcella 9/11; Marcella/Vesper/Vendetta 6/8 |
| Modal opening attack route by hero | Cassi: 2→13→2; Heart: 1→11→13→10→3; Issac: 4→2→13→2→4; Marcella: 5→3→5→3; Ryth: 3→5→2→13; Tavi: 1→5→3→5; Vendetta: 4→2; Vesper: 1→11→1→11→2→13→1 |
| Crew by group (median attackers) | 0:1, 1:2, 2:2, 3:2, 4:2, 5:2, 6:1, 7:1, 8:1, 9:1, 10:1, 11:1, 12:1, 13:1 |
| First fight | median R52; most common tile [((13, 10), 2)] |
| Banking | 651 submissions; median bag 18, R883; altar tiles [((12, 16), 336), ((17, 13), 315)] |
| Denial evidence in opening | contested groups [(2, 5), (5, 4), (4, 4), (3, 2)]; empty-tile occupation team:group→rounds [('1:3', 76), ('0:2', 62), ('1:5', 39), ('0:4', 34)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_health; Marcella: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Ryth: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Tavi: durability_shard_of_strength, bruiser_shard_of_strength; Vendetta: treasure_shard_of_strength, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health |
| Game endings | {'gems': 47, 'tiebreak_gems': 4}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 4/6 / 0/3 |

## 02crossing

| Measure | Observed evidence |
|---|---|
| Coverage | 47 crawl games, 14 opening replays |
| Drafts (wins/appearances) | Vesper/Heart/Vendetta/Ryth/Marcella 6/6; Vesper/Vendetta/Heart/Varg/Marcella 7/10; Heart/Marcella/Ryth/Vendetta/Vesper 7/10 |
| Modal opening attack route by hero | Cassi: 0→16→9→16→18; Heart: 0→16→9→0→16; Issac: 0→16→9→16; Marcella: 1; Prism: 0→19→14→0→18→21; Ryth: 0→14→15; Tavi: 1→17→6; Varg: 0→14; Vendetta: 7→16; Vesper: 0→7→0; Willow: 0 |
| Crew by group (median attackers) | 0:5, 1:5, 2:1.5, 3:2, 4:1, 5:2, 6:2, 7:1.5, 8:4, 9:4.5, 10:1, 11:1, 12:1, 13:1, 14:1, 15:1.5, 16:1.5, 17:1.5, 18:1, 19:1, 20:1, 21:1, 22:1, 23:1 |
| First fight | median R47; most common tile [((24, 24), 2)] |
| Banking | 303 submissions; median bag 14, R421; altar tiles [((25, 25), 206), ((25, 2), 58)] |
| Denial evidence in opening | contested groups [(19, 2), (15, 2), (0, 2), (14, 2)]; empty-tile occupation team:group→rounds [('1:0', 84), ('0:1', 52), ('0:19', 41), ('1:19', 28)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: prospector_shard_of_health, jungle_shard_of_focus; Marcella: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ryth: jungle_shard_of_strength, bruiser_shard_of_health; Tavi: treasure_shard_of_health; Varg: prospector_shard_of_health; Vendetta: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Vesper Vale: prospector_shard_of_strength; Willow: treasure_shard_of_focus, jungle_shard_of_focus |
| Game endings | {'gems': 47}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 0/2 / 1/1 |

## 02cuts

| Measure | Observed evidence |
|---|---|
| Coverage | 51 crawl games, 15 opening replays |
| Drafts (wins/appearances) | Heart/Ryth/Vendetta/Tavi/Marcella 8/10; Heart/Ren/Ryth/Vesper/Marcella 6/8; Prism/Vendetta/Marcella/Tavi/Heart 10/14 |
| Modal opening attack route by hero | Cassi: 17→15→1; Heart: 22→17; Issac: 2→12→4→12; Marcella: 18→14→0; Prism: 5→3→20→13→15; Ren: 15→1→17→15→20; Ryth: 14→4; Tavi: 4→14; Varg: 4; Vendetta: 20→11→17; Vesper: 21→22→10; Willow: 5→3→13→20→13→17 |
| Crew by group (median attackers) | 0:2, 1:2, 2:2, 3:3, 4:2, 5:3, 6:1, 7:1, 8:1, 9:3, 10:1, 11:1, 12:1.5, 13:1.5, 14:2, 15:2, 16:2, 17:3, 18:2, 19:1, 20:2, 21:3, 22:1 |
| First fight | median R118; most common tile [((37, 17), 1)] |
| Banking | 250 submissions; median bag 29, R540; altar tiles [((34, 34), 84), ((45, 45), 71)] |
| Denial evidence in opening | contested groups [(12, 1), (10, 1), (22, 1)]; empty-tile occupation team:group→rounds [('0:14', 37), ('0:10', 28), ('1:15', 28), ('0:4', 27)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: monster_shard_of_focus, power_shard_of_focus; Heart of Ruin: hunter_shard_of_focus, jungle_shard_of_focus, bruiser_shard_of_health; Issac: monster_shard_of_strength, power_shard_of_strength, home_shard_of_health, durability_shard_of_health; Marcella: prospector_shard_of_strength, jungle_shard_of_strength, durability_shard_of_health, bruiser_shard_of_strength; Prism: jungle_shard_of_health, monster_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Ryth: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Tavi: treasure_shard_of_health, treasure_shard_of_health, treasure_shard_of_strength, treasure_shard_of_health; Varg: monster_shard_of_strength, power_shard_of_strength, home_shard_of_health, durability_shard_of_health; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength; Vesper Vale: monster_shard_of_strength; Willow: jungle_shard_of_strength |
| Game endings | {'gems': 51}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | not on fixed plan / no duel evidence |

## 02famine

| Measure | Observed evidence |
|---|---|
| Coverage | 48 crawl games, 18 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Cassi+Issac/Marcella 14/14; Marcella/Vendetta/Ryth/Vesper/Heart 7/7; Heart/Marcella/Ryth/Vendetta/Vesper 7/10 |
| Modal opening attack route by hero | Cassi: 3; Heart: 2→9; Issac: 3→8→3→8; Marcella: 3; Prism: 2→4→2; Ren: 3→8→6→8; Ryth: 2; Tavi: 5→7; Varg: 3→8; Vendetta: 3→8→3→8; Vesper: 3→8→3; Willow: 2 |
| Crew by group (median attackers) | 0:1.5, 2:5, 3:5, 4:1, 5:1, 6:1, 7:1, 8:2, 9:1 |
| First fight | median R69; most common tile [((54, 21), 2)] |
| Banking | 373 submissions; median bag 29, R795; altar tiles [((45, 50), 171), ((45, 24), 155)] |
| Denial evidence in opening | contested groups [(8, 3), (9, 3), (4, 1), (7, 1)]; empty-tile occupation team:group→rounds [('0:4', 47), ('1:8', 46), ('1:3', 43), ('1:5', 40)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus; Heart of Ruin: treasure_shard_of_focus, power_shard_of_focus, home_shard_of_health, durability_shard_of_health; Issac: treasure_shard_of_strength, power_shard_of_strength, home_shard_of_health; Marcella: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Prism: monster_shard_of_health, jungle_shard_of_health, bruiser_shard_of_focus; Ryth: treasure_shard_of_health, durability_shard_of_health, bruiser_shard_of_strength, bruiser_shard_of_strength; Tavi: prospector_shard_of_strength, bruiser_shard_of_strength, durability_shard_of_health; Varg: jungle_shard_of_strength; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Willow: jungle_shard_of_health, power_shard_of_strength |
| Game endings | {'gems': 48}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 4/10 / 1/5 |

## 02fields

| Measure | Observed evidence |
|---|---|
| Coverage | 41 crawl games, 13 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Cassi+Issac/Marcella 7/7; Prism/Vesper/Marcella/Ryth/Heart 8/9; Marcella/Ren/Heart/Vendetta/Vesper 5/7 |
| Modal opening attack route by hero | Cassi: 0→10→2→6→10; Heart: 1→11; Issac: 0→10→2→6→0→6→10; Marcella: 10→2→3→0; Prism: 1→18→12→1; Ren: 2→3→5→15; Ryth: 10→2→19→2; Tavi: 1→18→4→3→11; Varg: 1→3→2→3→2; Vendetta: 3→11→1; Vesper: 1→3→20→4→3→4; Willow: 11→7→11 |
| Crew by group (median attackers) | 0:3, 1:3, 2:3, 3:3, 4:2, 5:1, 6:4, 7:3, 10:5, 11:2.5, 12:2, 14:1, 15:1, 16:1, 17:1, 18:1, 19:1, 20:1, 21:1 |
| First fight | median R52; most common tile [((23, 26), 2)] |
| Banking | 268 submissions; median bag 14, R489; altar tiles [((33, 25), 141), ((17, 25), 76)] |
| Denial evidence in opening | contested groups [(3, 5), (2, 5), (10, 1), (0, 1)]; empty-tile occupation team:group→rounds [('1:1', 49), ('1:3', 41), ('0:2', 41), ('0:0', 33)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Marcella: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Ryth: prospector_shard_of_health; Tavi: treasure_shard_of_health, capture_shard_of_strength, treasure_shard_of_health, treasure_shard_of_strength; Varg: treasure_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health, jungle_shard_of_strength; Vendetta: treasure_shard_of_strength, jungle_shard_of_strength, monster_shard_of_strength, bruiser_shard_of_health; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Willow: treasure_shard_of_strength |
| Game endings | {'gems': 41}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 2/4 / 0/2 |

## 02geodes

| Measure | Observed evidence |
|---|---|
| Coverage | 61 crawl games, 26 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Ren/Cassi+Issac 16/17; Vesper/Ryth/Vendetta/Varg/Marcella 5/5; Marcella/Vendetta/Ryth/Vesper/Ren 7/8 |
| Modal opening attack route by hero | Cassi: 3→9→12; Heart: 9→11; Issac: 12→3→11→3; Marcella: 2→8→2; Prism: 3→7→9→7→5→11; Ren: 5→9→8; Ryth: 5→3→1; Tavi: 3→5→9→3; Varg: 8→4→10→8→4; Vendetta: 3→5→7→11→3; Vesper: 3→7→9→5; Willow: 11→3→1 |
| Crew by group (median attackers) | 0:2, 1:2, 2:3, 3:2, 4:3, 5:3, 6:1, 7:1, 8:3, 9:3, 10:2, 11:2, 12:3, 13:3 |
| First fight | median R54; most common tile [((31, 56), 1)] |
| Banking | 438 submissions; median bag 33, R548; altar tiles [((44, 35), 176), ((78, 40), 137)] |
| Denial evidence in opening | contested groups [(8, 2), (2, 1), (9, 1)]; empty-tile occupation team:group→rounds [('0:4', 73), ('1:9', 66), ('0:8', 61), ('0:2', 60)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: monster_shard_of_focus, jungle_shard_of_health, power_shard_of_focus, power_shard_of_focus; Issac: monster_shard_of_strength, jungle_shard_of_health; Marcella: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ryth: jungle_shard_of_health, monster_shard_of_health, durability_shard_of_health; Tavi: jungle_shard_of_strength, bruiser_shard_of_strength; Varg: prospector_shard_of_strength; Vendetta: treasure_shard_of_strength, jungle_shard_of_strength, monster_shard_of_strength, bruiser_shard_of_health; Vesper Vale: jungle_shard_of_strength, monster_shard_of_strength, treasure_shard_of_strength, home_shard_of_strength; Willow: treasure_shard_of_focus |
| Game endings | {'gems': 61}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 2/4 / 0/2 |

## 02gift-wrapping

| Measure | Observed evidence |
|---|---|
| Coverage | 44 crawl games, 14 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Cassi+Issac/Marcella 7/8; Marcella/Vendetta/Ryth/Vesper/Heart 6/7; Vesper/Vendetta/Heart/Varg/Marcella 6/9 |
| Modal opening attack route by hero | Cassi: 6→10→2→6→10→0; Heart: 6→10→2→6→10→0; Issac: 6→10→2→6→10→0; Marcella: 6→10→2→6→10; Prism: 5→0→7→9→5; Ryth: 4→6→2→10; Tavi: 5→9→1→0; Vendetta: 6→10→2→6→10→0; Vesper: 6→10→2→6→10→0; Willow: 4→6→2→0 |
| Crew by group (median attackers) | 0:4, 1:5, 2:4, 3:3, 4:5, 5:5, 6:5, 7:3, 8:3, 9:5, 10:5 |
| First fight | median R34; most common tile [((27, 19), 1)] |
| Banking | 197 submissions; median bag 38, R431; altar tiles [((32, 24), 88), ((14, 28), 55)] |
| Denial evidence in opening | contested groups [(0, 6)]; empty-tile occupation team:group→rounds [('1:6', 93), ('0:9', 67), ('0:5', 58), ('0:1', 41)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus, durability_shard_of_focus; Heart of Ruin: treasure_shard_of_health; Issac: treasure_shard_of_strength; Marcella: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Prism: monster_shard_of_focus, bruiser_shard_of_focus, bruiser_shard_of_focus, bruiser_shard_of_focus; Tavi: treasure_shard_of_health, treasure_shard_of_health, treasure_shard_of_health, treasure_shard_of_strength; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Willow: jungle_shard_of_strength, power_shard_of_strength, power_shard_of_strength, power_shard_of_strength |
| Game endings | {'gems': 44}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | not on fixed plan / no duel evidence |

## 02guardians

| Measure | Observed evidence |
|---|---|
| Coverage | 50 crawl games, 18 opening replays |
| Drafts (wins/appearances) | Vesper/Marcella/Vendetta/Ryth 10/10; Vesper/Heart/Vendetta/Varg 3/4; Marcella/Vesper/Vendetta/Ren 5/9 |
| Modal opening attack route by hero | Cassi: 15→13→8; Heart: 5→18→6→5; Issac: 5→15→13→4; Marcella: 12; Prism: 15→12→16→15; Ren: 3→4→14→1; Ryth: 4→13; Stellar: 4; Tavi: 17; Varg: 12→14→9; Vendetta: 12; Vesper: 4 |
| Crew by group (median attackers) | 0:1, 1:1, 2:1, 3:1, 4:2, 5:2, 6:1, 7:2, 8:2, 9:1, 10:1, 11:1.5, 12:2, 13:2, 14:1, 15:3, 16:1, 17:2, 18:1.5, 19:1 |
| First fight | median R21; most common tile [((8, 29), 1)] |
| Banking | 65 submissions; median bag 140, R1352; altar tiles [((20, 20), 65)] |
| Denial evidence in opening | contested groups [(12, 2), (16, 1), (4, 1)]; empty-tile occupation team:group→rounds [('1:12', 27), ('1:4', 23), ('0:2', 23), ('1:16', 17)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: power_shard_of_focus; Heart of Ruin: treasure_shard_of_focus, power_shard_of_focus, durability_shard_of_health, home_shard_of_health; Issac: treasure_shard_of_strength, capture_shard_of_strength; Marcella: treasure_shard_of_focus, prospector_shard_of_focus, jungle_shard_of_health, durability_shard_of_health; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ren: treasure_shard_of_health, bruiser_shard_of_health, jungle_shard_of_focus, durability_shard_of_health; Ryth: treasure_shard_of_health, jungle_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Stellar: treasure_shard_of_focus, power_shard_of_focus, home_shard_of_health, durability_shard_of_health; Tavi: treasure_shard_of_strength, durability_shard_of_health, monster_shard_of_strength, bruiser_shard_of_strength; Varg: treasure_shard_of_strength, prospector_shard_of_strength, jungle_shard_of_health, monster_shard_of_strength; Vendetta: treasure_shard_of_strength, prospector_shard_of_strength, jungle_shard_of_health, monster_shard_of_strength; Vesper Vale: treasure_shard_of_strength, prospector_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health |
| Game endings | {'gems': 46, 'tiebreak_gems': 4}; winning-side gems lost to champions median 9.0 |
| v65 self-play / existing top-team duel record | 4/6 / 0/3 |

## 02harvest

| Measure | Observed evidence |
|---|---|
| Coverage | 38 crawl games, 14 opening replays |
| Drafts (wins/appearances) | Vesper/Vendetta/Heart/Varg/Marcella 6/6; Heart/Ren/Ryth/Vesper/Marcella 5/6; Vesper/Vendetta/Heart/Ren/Cassi+Issac 5/7 |
| Modal opening attack route by hero | Cassi: 14; Heart: 12→14→16; Issac: 13→5→13→5; Marcella: 5→17; Prism: 13→15→13→15; Ren: 12→14→16→17; Ryth: 5→7→5; Tavi: 5→15; Varg: 13→7→3→5; Vendetta: 13→7; Vesper: 12→4→12; Willow: 4→12→14 |
| Crew by group (median attackers) | 1:2, 2:1, 3:1, 4:1, 5:3, 6:1, 7:1, 10:1, 11:1, 12:4, 13:4, 14:3.5, 15:3, 16:1, 17:1, 18:1 |
| First fight | median R108; most common tile [((59, 41), 2)] |
| Banking | 253 submissions; median bag 29, R620; altar tiles [((61, 38), 79), ((51, 80), 66)] |
| Denial evidence in opening | contested groups [(17, 2)]; empty-tile occupation team:group→rounds [('1:13', 58), ('0:12', 46), ('1:7', 32), ('0:14', 30)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: monster_shard_of_focus; Heart of Ruin: monster_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_health; Issac: monster_shard_of_strength, power_shard_of_strength, home_shard_of_health, durability_shard_of_health; Marcella: jungle_shard_of_focus, treasure_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ryth: jungle_shard_of_health, treasure_shard_of_health; Tavi: treasure_shard_of_health, treasure_shard_of_health, treasure_shard_of_health, treasure_shard_of_strength; Varg: monster_shard_of_strength, power_shard_of_strength, home_shard_of_health, durability_shard_of_health; Vendetta: jungle_shard_of_strength, treasure_shard_of_strength, durability_shard_of_strength, monster_shard_of_health; Vesper Vale: monster_shard_of_strength, jungle_shard_of_health, durability_shard_of_health, bruiser_shard_of_strength |
| Game endings | {'gems': 38}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 2/4 / 0/2 |

## 02stalactites

| Measure | Observed evidence |
|---|---|
| Coverage | 60 crawl games, 17 opening replays |
| Drafts (wins/appearances) | Heart/Ryth/Vesper/Marcella 5/6; Prism/Vendetta/Marcella/Heart 8/10; Heart/Marcella/Vendetta/Vesper 7/10 |
| Modal opening attack route by hero | Cassi: 8→11→8; Heart: 8; Issac: 8→6; Marcella: 8; Prism: 8; Ryth: 9→8→11; Stellar: 8; Tavi: 8; Varg: 11; Vendetta: 9→8; Vesper: 8→6→8→6→7; Willow: 12→10→5→12→10→7 |
| Crew by group (median attackers) | 0:1, 1:1, 2:2, 3:1, 4:1.5, 5:3, 6:1, 7:1, 8:3, 9:2, 10:2.5, 11:2, 12:2, 13:1, 14:1 |
| First fight | median R22; most common tile [((15, 15), 2)] |
| Banking | 149 submissions; median bag 77, R351; altar tiles [((14, 14), 106), ((15, 14), 43)] |
| Denial evidence in opening | contested groups [(8, 10), (7, 2), (6, 1)]; empty-tile occupation team:group→rounds [('0:8', 183), ('1:8', 87), ('1:10', 70), ('0:9', 42)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: jungle_shard_of_focus, treasure_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Marcella: jungle_shard_of_focus, treasure_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Prism: prospector_shard_of_health, monster_shard_of_health; Ryth: prospector_shard_of_health, bruiser_shard_of_focus; Varg: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Vendetta: prospector_shard_of_health, jungle_shard_of_strength; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength |
| Game endings | {'gems': 60}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 0/4 / 2/2 |

## 02tangle

| Measure | Observed evidence |
|---|---|
| Coverage | 41 crawl games, 18 opening replays |
| Drafts (wins/appearances) | Marcella/Vendetta/Ryth/Vesper/Heart 7/7; Prism/Vendetta/Marcella/Tavi/Heart 7/8; Vesper/Vendetta/Heart/Varg/Marcella 7/10 |
| Modal opening attack route by hero | Cassi: 9→7→9→7; Heart: 2→27; Issac: 9→7→32→9→7; Marcella: 2→8→2; Prism: 27→25; Ren: 27→25; Ryth: 0→8→6→0→8; Tavi: 2→27→25; Varg: 9→7→9; Vendetta: 9→3→1; Vesper: 9→32→9→7; Willow: 27→25 |
| Crew by group (median attackers) | 0:2, 1:1, 2:2, 3:1, 4:1, 5:1, 6:2, 7:3.5, 8:3, 9:5, 10:1, 11:1, 12:1, 13:1, 14:1, 15:1, 16:1, 17:1, 21:1, 24:2, 25:2, 26:2, 27:3, 28:1, 29:1, 31:1, 32:1 |
| First fight | median R84; most common tile [((70, 30), 1)] |
| Banking | 295 submissions; median bag 43, R747; altar tiles [((23, 68), 183), ((76, 11), 64)] |
| Denial evidence in opening | contested groups [(14, 1), (1, 1), (7, 1), (8, 1)]; empty-tile occupation team:group→rounds [('1:9', 88), ('0:8', 60), ('0:2', 59), ('0:16', 42)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: monster_shard_of_focus; Heart of Ruin: prospector_shard_of_health; Issac: jungle_shard_of_strength, treasure_shard_of_strength; Marcella: treasure_shard_of_focus, jungle_shard_of_focus, monster_shard_of_focus, capture_shard_of_focus; Prism: treasure_shard_of_focus; Ren: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Ryth: prospector_shard_of_health, jungle_shard_of_health; Tavi: treasure_shard_of_health; Varg: monster_shard_of_strength, jungle_shard_of_health, power_shard_of_strength, power_shard_of_strength; Vendetta: prospector_shard_of_health; Vesper Vale: treasure_shard_of_strength, monster_shard_of_strength, power_shard_of_strength, jungle_shard_of_health; Willow: treasure_shard_of_focus |
| Game endings | {'gems': 41}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 0/2 / 1/1 |

## 02the-pack

| Measure | Observed evidence |
|---|---|
| Coverage | 55 crawl games, 21 opening replays |
| Drafts (wins/appearances) | Heart/Vendetta/Vesper 11/14; Heart/Vesper/Marcella 8/11; Marcella/Vendetta/Vesper 3/3 |
| Modal opening attack route by hero | Heart: 1→5→17→21→10→7; Marcella: 19→12→7; Ryth: 19→5→17→19→7→25→3→19; Tavi: 19→1→5→20→26; Vendetta: 15→12→7→18→19→5→18; Vesper: 5→18→22→18 |
| Crew by group (median attackers) | 0:1, 1:1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1, 10:1, 11:1, 12:1, 13:1, 14:1, 15:1, 16:1, 17:1, 18:1, 19:1, 20:1, 21:1, 22:1, 23:1, 24:1, 25:1, 26:2, 27:1.5, 28:1, 29:1, 30:1, 31:1, 32:1, 33:1, 34:1 |
| First fight | median R54; most common tile [((23, 29), 2)] |
| Banking | 75 submissions; median bag 64, R1146; altar tiles [((22, 22), 75)] |
| Denial evidence in opening | contested groups [(19, 7), (26, 3), (17, 2), (0, 1)]; empty-tile occupation team:group→rounds [('1:19', 69), ('0:20', 57), ('0:26', 50), ('1:5', 40)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: jungle_shard_of_focus, treasure_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Marcella: jungle_shard_of_focus, treasure_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Ryth: prospector_shard_of_health, treasure_shard_of_health, jungle_shard_of_health, capture_shard_of_focus; Tavi: prospector_shard_of_strength, hunter_shard_of_strength, monster_shard_of_strength, jungle_shard_of_strength; Vendetta: monster_shard_of_strength, jungle_shard_of_strength, power_shard_of_strength, power_shard_of_strength; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength |
| Game endings | {'gems': 31, 'tiebreak_gems': 16, 'tiebreak_gold': 8}; winning-side gems lost to champions median 21 |
| v65 self-play / existing top-team duel record | not on fixed plan / no duel evidence |

## 02the-pond

| Measure | Observed evidence |
|---|---|
| Coverage | 49 crawl games, 17 opening replays |
| Drafts (wins/appearances) | Marcella/Vendetta/Ryth 8/8; Prism/Vesper/Heart 10/14; Marcella/Heart/Vesper 5/7 |
| Modal opening attack route by hero | Cassi: 9→6→4→6; Heart: 9→6→4→6; Issac: 9→2; Marcella: 9→6→4; Prism: 9→6→4→9→6; Ryth: 9→6; Tavi: 7→8→7; Varg: 9→6→9; Vendetta: 8→7→5→8; Vesper: 9→6→4 |
| Crew by group (median attackers) | 0:1, 1:1, 2:1, 3:1, 4:2, 5:3, 6:3, 7:3, 8:3, 9:3 |
| First fight | median R97; most common tile [((5, 8), 4)] |
| Banking | 443 submissions; median bag 15, R960; altar tiles [((3, 7), 242), ((26, 22), 201)] |
| Denial evidence in opening | contested groups [(5, 2), (2, 1), (3, 1), (7, 1)]; empty-tile occupation team:group→rounds [('1:6', 193), ('0:7', 137), ('0:3', 39), ('0:5', 29)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: hunter_shard_of_health, jungle_shard_of_focus, bruiser_shard_of_health, bruiser_shard_of_health; Marcella: prospector_shard_of_health, treasure_shard_of_strength, jungle_shard_of_health, monster_shard_of_strength; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ryth: prospector_shard_of_health, treasure_shard_of_health, jungle_shard_of_health, monster_shard_of_focus; Tavi: jungle_shard_of_strength, treasure_shard_of_strength, bruiser_shard_of_strength, durability_shard_of_health; Vendetta: prospector_shard_of_health, treasure_shard_of_strength, jungle_shard_of_health, monster_shard_of_strength; Vesper Vale: treasure_shard_of_strength, prospector_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_health |
| Game endings | {'gems': 43, 'tiebreak_gems': 6}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 2/4 / 0/2 |

## 02treasure-box

| Measure | Observed evidence |
|---|---|
| Coverage | 52 crawl games, 25 opening replays |
| Drafts (wins/appearances) | Marcella/Vesper/Vendetta/Tavi/Heart 4/4; Vesper/Vendetta/Heart/Cassi+Issac/Marcella 6/7; Heart/Ren/Ryth/Vesper/Marcella 5/6 |
| Modal opening attack route by hero | Cassi: 20→16→20; Heart: 16; Issac: 16; Marcella: 16→25→27; Prism: 16→28→26→28→16→20; Ren: 16; Ryth: 20; Tavi: 19→21→23; Varg: 16→27→30; Vendetta: 26→28→16; Vesper: 16; Willow: 16→26→28→16 |
| Crew by group (median attackers) | 0:1, 1:1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1, 10:1, 11:1, 12:1, 13:1, 14:1, 15:1, 16:4, 17:1, 18:1, 19:1, 20:1, 21:1, 22:1, 23:1, 24:1, 25:3, 26:4, 27:4, 28:4, 30:1, 31:4, 32:2 |
| First fight | median R4; most common tile [((19, 29), 4)] |
| Banking | 477 submissions; median bag 7, R449; altar tiles [((17, 17), 477)] |
| Denial evidence in opening | contested groups [(16, 17), (19, 3), (20, 2), (23, 2)]; empty-tile occupation team:group→rounds [('0:27', 65), ('0:25', 54), ('0:21', 35), ('0:16', 35)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: prospector_shard_of_focus, durability_shard_of_health, monster_shard_of_focus, capture_shard_of_health; Heart of Ruin: jungle_shard_of_focus, treasure_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Issac: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Marcella: jungle_shard_of_focus, treasure_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Prism: monster_shard_of_focus, bruiser_shard_of_focus; Ren: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Ryth: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Tavi: treasure_shard_of_focus, bruiser_shard_of_health, durability_shard_of_focus, bruiser_shard_of_health; Varg: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Vendetta: prospector_shard_of_health, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength; Vesper Vale: treasure_shard_of_strength, jungle_shard_of_strength, durability_shard_of_health, monster_shard_of_strength |
| Game endings | {'gems': 52}; winning-side gems lost to champions median 2.0 |
| v65 self-play / existing top-team duel record | 5/10 / 2/5 |

## 02uncharted-lands

| Measure | Observed evidence |
|---|---|
| Coverage | 43 crawl games, 15 opening replays |
| Drafts (wins/appearances) | Marcella/Vendetta/Ryth/Vesper/Heart 12/14; Marcella/Heart/Vesper/Ryth/Varg 5/7; Vesper/Vendetta/Heart/Cassi+Issac/Marcella 4/6 |
| Modal opening attack route by hero | Cassi: 2→14→16→1→14→2→16; Heart: 15→12; Issac: 2→14→16→1→14→2→16; Marcella: 15→9→15; Prism: 8→6→16→14→6; Ren: 7→17→15→12→3→9; Ryth: 15→5→9; Tavi: 1→5; Varg: 17→3→15→4→3; Vendetta: 6→8→16→2→1→16; Vesper: 6→14→5→16→2→14; Willow: 6→14→16→2→1 |
| Crew by group (median attackers) | 0:2, 1:2.5, 2:3.5, 3:3, 4:1, 5:1, 6:2, 7:2, 8:1, 9:1, 10:1, 11:1, 12:1, 13:1, 14:3, 15:4, 16:3, 17:2, 18:1 |
| First fight | median R82; most common tile [((27, 11), 1)] |
| Banking | 169 submissions; median bag 18, R450; altar tiles [((10, 29), 67), ((30, 18), 43)] |
| Denial evidence in opening | contested groups [(5, 2), (16, 1), (13, 1), (11, 1)]; empty-tile occupation team:group→rounds [('0:14', 58), ('1:9', 46), ('1:17', 44), ('1:3', 41)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: prospector_shard_of_health; Marcella: prospector_shard_of_strength, jungle_shard_of_strength, bruiser_shard_of_strength, bruiser_shard_of_strength; Prism: monster_shard_of_focus, jungle_shard_of_health, bruiser_shard_of_focus, bruiser_shard_of_focus; Ryth: prospector_shard_of_health; Vendetta: prospector_shard_of_health; Vesper Vale: prospector_shard_of_strength, treasure_shard_of_strength, jungle_shard_of_strength; Willow: power_shard_of_strength |
| Game endings | {'gems': 43}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 1/2 / 0/1 |

## adgato-gemcombat1

| Measure | Observed evidence |
|---|---|
| Coverage | 37 crawl games, 9 opening replays |
| Drafts (wins/appearances) | Prism/Marcella/Heart 7/8; Marcella/Vendetta/Heart 5/7; Vesper/Heart/Marcella 5/7 |
| Modal opening attack route by hero | Heart: 3; Issac: 2; Marcella: 4→1; Prism: 4→0→4; Ryth: 1→2→1→5→2; Tavi: 5→1; Vendetta: 1→5→2; Vesper: 1→5→2→0→1→5→2→1 |
| Crew by group (median attackers) | 0:2, 1:1, 2:1, 3:1, 4:1, 5:1 |
| First fight | median R34; most common tile [((13, 16), 1)] |
| Banking | 144 submissions; median bag 21, R620; altar tiles [((15, 15), 144)] |
| Denial evidence in opening | contested groups [(3, 5), (2, 4), (1, 2), (0, 1)]; empty-tile occupation team:group→rounds [('0:0', 61), ('1:1', 60), ('0:4', 30), ('1:5', 27)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: jungle_shard_of_focus, bruiser_shard_of_health; Marcella: bruiser_shard_of_strength, bruiser_shard_of_health, bruiser_shard_of_focus, bruiser_shard_of_strength; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Vendetta: hunter_shard_of_strength, jungle_shard_of_strength, durability_shard_of_health, bruiser_shard_of_strength |
| Game endings | {'gems': 37}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 2/2 / 0/1 |

## adgato-gemcombat2

| Measure | Observed evidence |
|---|---|
| Coverage | 52 crawl games, 17 opening replays |
| Drafts (wins/appearances) | Prism/Marcella/Ryth/Heart 9/9; Vesper/Vendetta/Heart/Cassi+Issac 10/14; Vesper/Vendetta/Heart/Ryth 3/4 |
| Modal opening attack route by hero | Cassi: 0→5; Heart: 6→0→6; Issac: 0→5; Marcella: 0; Prism: 7→0→6→4→0→7; Ryth: 0; Stellar: 7→0→7→5; Tavi: 8→0→6; Varg: 4→0; Vendetta: 5→0; Vesper: 6→0 |
| Crew by group (median attackers) | 0:3, 1:1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:1, 8:1 |
| First fight | median R26; most common tile [((23, 9), 2)] |
| Banking | 149 submissions; median bag 49, R442; altar tiles [((25, 26), 149)] |
| Denial evidence in opening | contested groups [(0, 17), (3, 2), (1, 1), (8, 1)]; empty-tile occupation team:group→rounds [('0:0', 108), ('1:0', 94), ('1:6', 52), ('0:5', 49)]; altar locks unmeasured |
| Winning-side opening item milestones | Cassi: treasure_shard_of_focus; Heart of Ruin: treasure_shard_of_health, jungle_shard_of_focus, durability_shard_of_health, bruiser_shard_of_focus; Issac: treasure_shard_of_strength; Marcella: treasure_shard_of_strength, bruiser_shard_of_health, durability_shard_of_health; Prism: durability_shard_of_health, monster_shard_of_health; Ryth: treasure_shard_of_health, jungle_shard_of_strength; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, power_shard_of_strength, durability_shard_of_health |
| Game endings | {'gems': 52}; winning-side gems lost to champions median 14 |
| v65 self-play / existing top-team duel record | not on fixed plan / no duel evidence |

## adgato-gemcombat3

| Measure | Observed evidence |
|---|---|
| Coverage | 41 crawl games, 10 opening replays |
| Drafts (wins/appearances) | Prism/Marcella/Ryth/Heart 7/7; Vesper/Heart/Vendetta/Varg 3/4; Heart/Marcella/Vendetta/Vesper 5/9 |
| Modal opening attack route by hero | Cassi: 2→9; Heart: 0→9→8; Issac: 0→9→2; Marcella: 9→8; Prism: 1→5→9; Ren: 5→9; Ryth: 3; Varg: 4; Vendetta: 1→9→5; Vesper: 5→8→9→8 |
| Crew by group (median attackers) | 0:2, 1:1, 2:1, 3:1, 4:1.5, 5:1, 6:1, 7:1, 8:2, 9:1 |
| First fight | median R50; most common tile [((28, 27), 2)] |
| Banking | 104 submissions; median bag 42, R402; altar tiles [((30, 25), 104)] |
| Denial evidence in opening | contested groups [(9, 7), (5, 1), (2, 1)]; empty-tile occupation team:group→rounds [('1:1', 40), ('0:0', 24), ('1:9', 23), ('0:2', 19)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: jungle_shard_of_focus, bruiser_shard_of_health; Marcella: bruiser_shard_of_strength, bruiser_shard_of_health; Prism: durability_shard_of_health; Ryth: jungle_shard_of_strength, bruiser_shard_of_health; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, monster_shard_of_strength, durability_shard_of_health; Vesper Vale: treasure_shard_of_strength |
| Game endings | {'gems': 41}; winning-side gems lost to champions median 31.5 |
| v65 self-play / existing top-team duel record | 2/2 / 0/1 |

## adgato-gemcombat4

| Measure | Observed evidence |
|---|---|
| Coverage | 57 crawl games, 18 opening replays |
| Drafts (wins/appearances) | Prism/Vendetta/Marcella/Tavi/Heart 8/9; Vesper/Vendetta/Heart/Varg/Marcella 8/11; Marcella/Vendetta/Ryth/Vesper/Ren 7/10 |
| Modal opening attack route by hero | Cassi: 4→6; Heart: 5→3; Issac: 4→2→0→4→6→2→0→6; Marcella: 4; Prism: 3→5→7→5; Ren: 3→5; Ryth: 3; Tavi: 4→6; Varg: 6→2; Vendetta: 5→3→7; Vesper: 4; Willow: 3→5 |
| Crew by group (median attackers) | 0:1, 1:1, 2:2, 3:2, 4:1, 5:2, 6:1, 7:2 |
| First fight | median R44; most common tile [((14, 27), 3)] |
| Banking | 129 submissions; median bag 42, R403; altar tiles [((20, 30), 129)] |
| Denial evidence in opening | contested groups [(5, 2), (4, 1), (3, 1)]; empty-tile occupation team:group→rounds [('1:5', 71), ('1:3', 68), ('0:4', 60), ('0:2', 52)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: treasure_shard_of_focus; Issac: treasure_shard_of_strength; Marcella: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength, bruiser_shard_of_health; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ryth: prospector_shard_of_focus; Vendetta: treasure_shard_of_health, jungle_shard_of_strength, durability_shard_of_strength; Vesper Vale: jungle_shard_of_strength |
| Game endings | {'gems': 57}; winning-side gems lost to champions median 0 |
| v65 self-play / existing top-team duel record | 2/4 / 0/2 |

## adgato-gemcombat5

| Measure | Observed evidence |
|---|---|
| Coverage | 45 crawl games, 19 opening replays |
| Drafts (wins/appearances) | Prism/Marcella/Ryth/Heart/Vesper 7/7; Marcella/Heart/Vesper/Ryth/Varg 6/6; Prism/Vendetta/Marcella/Tavi/Heart 5/6 |
| Modal opening attack route by hero | Cassi: 2; Heart: 0; Issac: 2; Marcella: 0; Prism: 0; Ren: 16→4; Ryth: 0; Tavi: 1; Varg: 0; Vendetta: 0; Vesper: 0; Willow: 1→0 |
| Crew by group (median attackers) | 0:2, 1:1, 2:1, 3:1, 4:1, 6:1, 7:1, 8:1, 9:1, 10:1, 11:1, 12:1, 13:1, 14:1, 15:1, 16:1, 17:1, 18:1, 19:1, 20:1 |
| First fight | median R15; most common tile [((49, 43), 2)] |
| Banking | 114 submissions; median bag 63, R406; altar tiles [((49, 51), 114)] |
| Denial evidence in opening | contested groups [(17, 1), (1, 1)]; empty-tile occupation team:group→rounds [('1:0', 42), ('0:1', 22), ('1:2', 20), ('0:0', 19)]; altar locks unmeasured |
| Winning-side opening item milestones | Heart of Ruin: treasure_shard_of_health; Marcella: prospector_shard_of_health, treasure_shard_of_strength, bruiser_shard_of_focus, bruiser_shard_of_health; Prism: durability_shard_of_health, monster_shard_of_health, jungle_shard_of_health, home_shard_of_health; Ryth: jungle_shard_of_strength, bruiser_shard_of_health; Tavi: treasure_shard_of_health, treasure_shard_of_strength; Vendetta: treasure_shard_of_health; Vesper Vale: prospector_shard_of_strength |
| Game endings | {'gems': 45}; winning-side gems lost to champions median 0.0 |
| v65 self-play / existing top-team duel record | 1/2 / 0/1 |

