# Map categories (tools/mapatlas/categorise.py)

k-means on 12 standardised atlas features chose k=4 (silhouette 0.159);
a depth-3 decision tree turns the clusters into readable rules (agrees with the clusters on 86% of maps).
The rules define the categories, so an unseen map is categorised from its features alone.

## C1 (12 maps)

Rule: log_area <= 7.8242 and walls <= 0.1089 and near30 <= 0.763

Typical: log_area=7.44, team=4.17, contested=0.42, centre=0.44, top3=0.54, log_density=3.23, groups_per_champ=3.11, harmless=0.23, log_maze=0.55, walls=0.06, unreachable=0.07, near30=0.40

Maps: 00breadcrumbs, 00collision, 00gem-fields, 00monolith, 00quadrants, 00rows, 00split, 00swirl, 01boss-battle, 01the-farm, 02the-pond, 03one-gem

## C2 (25 maps)

Rule: log_area <= 7.8242 and walls <= 0.1089 and near30 > 0.763

Typical: log_area=7.21, team=4.16, contested=0.58, centre=0.57, top3=0.64, log_density=2.85, groups_per_champ=1.87, harmless=0.20, log_maze=0.07, walls=0.04, unreachable=0.00, near30=0.94

Maps: 00contest, 00eight, 00elkring, 00fragment, 00gemfight, 00interlock, 00oasis, 00packs, 00quarry, 00rushbait-v2, 00the-line, 01elk-arena, 01gold-rush, 01hooks, 01starfish, 01yellow-brick-road, 02arena, 02gift-wrapping, 02the-pack, 02uncharted-lands, 03ambush-field, 03membrane, 03shrines, adgato-gemcombat1, adgato-gemcombat2

## C3 (13 maps)

Rule: log_area <= 7.8242 and walls > 0.1089 and top3 <= 0.802

Typical: log_area=7.28, team=4.31, contested=0.72, centre=0.31, top3=0.50, log_density=4.00, groups_per_champ=3.16, harmless=0.23, log_maze=0.38, walls=0.17, unreachable=0.00, near30=0.54

Maps: 00great-wall, 00lost-world, 00reverse-spiral, 00road-of-riches, 01broken-curve, 01corridors, 01shortcut, 02guardians, 02stalactites, 02treasure-box, 03fan, 03honeycomb, 03showdown

## C4 (3 maps)

Rule: log_area <= 7.8242 and walls > 0.1089 and top3 > 0.802

Typical: log_area=7.03, team=3.33, contested=0.58, centre=0.37, top3=0.97, log_density=3.78, groups_per_champ=2.57, harmless=0.37, log_maze=0.25, walls=0.12, unreachable=0.00, near30=0.83

Maps: 00anvil, 00vault, 03homonoliths

## C5 (24 maps)

Rule: log_area > 7.8242 and near30 <= 0.6285 and unreachable <= 0.1355

Typical: log_area=8.61, team=4.96, contested=0.42, centre=0.40, top3=0.58, log_density=2.21, groups_per_champ=2.12, harmless=0.16, log_maze=0.42, walls=0.07, unreachable=0.01, near30=0.10

Maps: 00ambush, 00dunes, 00expanse, 00galaxy, 00lanes, 00pilgrimage, 00ribs, 00stampede, 01big-world, 01concentrated-wealth, 01fracture, 01starvation, 02cuts, 02famine, 02fields, 02geodes, 02harvest, 02tangle, 03contours, 03reef, 03riverbed, 03twisty, adgato-gemcombat3, adgato-gemcombat5

## C6 (3 maps)

Rule: log_area > 7.8242 and near30 <= 0.6285 and unreachable > 0.1355

Typical: log_area=8.17, team=4.33, contested=0.10, centre=0.18, top3=0.44, log_density=1.95, groups_per_champ=2.13, harmless=0.60, log_maze=0.17, walls=0.01, unreachable=0.39, near30=0.29

Maps: 01islands, 03ultrastarvation, adgato-gemcombat4

## C7 (3 maps)

Rule: log_area > 7.8242 and near30 > 0.6285 and log_area <= 8.0262

Typical: log_area=7.85, team=5.00, contested=0.39, centre=0.52, top3=0.27, log_density=3.34, groups_per_champ=3.80, harmless=0.31, log_maze=-0.04, walls=0.07, unreachable=0.00, near30=0.86

Maps: 02crossing, 03colosseum, 03the-front

## C8 (3 maps)

Rule: log_area > 7.8242 and near30 > 0.6285 and log_area > 8.0262

Typical: log_area=8.31, team=5.00, contested=0.60, centre=0.48, top3=0.53, log_density=2.42, groups_per_champ=1.93, harmless=0.00, log_maze=-0.07, walls=0.06, unreachable=0.00, near30=0.88

Maps: 00corners, 00crater, 00happy-halloween
