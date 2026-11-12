# Map categories (tools/mapatlas/categorise.py)

k-means on 14 standardised atlas features chose k=8 (silhouette 0.156);
a depth-3 decision tree turns the clusters into readable rules (agrees with the clusters on 81% of maps).
The rules define the categories, so an unseen map is categorised from its features alone.

## C1 (18 maps)

Rule: log_area <= 7.8823 and log_mean_dist <= 3.1377 and harmless <= 0.623

Typical: log_area=7.12, team=4.44, contested=0.45, top3=0.63, log_density=2.94, groups_per_champ=1.91, harmless=0.11, strong=0.16, blocked=0.13, unreachable=0.02, near15=0.49, near30=0.94, log_mean_dist=2.81, log_hp_per_gem=4.94

Maps: 00anvil, 00eight, 00elkring, 00fragment, 00oasis, 00packs, 00quarry, 01broken-curve, 01corridors, 01elk-arena, 01hooks, 01yellow-brick-road, 02arena, 02gift-wrapping, 02the-pack, 03membrane, 03showdown, 03shrines

## C2 (4 maps)

Rule: log_area <= 7.8823 and log_mean_dist <= 3.1377 and harmless > 0.623

Typical: log_area=6.88, team=4.00, contested=0.71, top3=0.77, log_density=3.29, groups_per_champ=1.16, harmless=0.93, strong=0.00, blocked=0.13, unreachable=0.00, near15=0.65, near30=0.96, log_mean_dist=2.78, log_hp_per_gem=3.68

Maps: 00the-line, 00vault, 02stalactites, adgato-gemcombat1

## C3 (24 maps)

Rule: log_area <= 7.8823 and log_mean_dist > 3.1377 and harmless <= 0.1725

Typical: log_area=7.55, team=4.79, contested=0.50, top3=0.59, log_density=3.52, groups_per_champ=2.41, harmless=0.03, strong=0.48, blocked=0.16, unreachable=0.00, near15=0.08, near30=0.51, log_mean_dist=3.53, log_hp_per_gem=4.75

Maps: 00collision, 00contest, 00great-wall, 00interlock, 00monolith, 00quadrants, 00reverse-spiral, 00rows, 00rushbait-v2, 00split, 00swirl, 01boss-battle, 01gold-rush, 01shortcut, 01starfish, 01the-farm, 02crossing, 02fields, 02guardians, 02uncharted-lands, 03ambush-field, 03homonoliths, 03honeycomb, 03the-front

## C4 (13 maps)

Rule: log_area <= 7.8823 and log_mean_dist > 3.1377 and harmless > 0.1725

Typical: log_area=7.34, team=4.92, contested=0.31, top3=0.45, log_density=2.87, groups_per_champ=2.75, harmless=0.64, strong=0.09, blocked=0.23, unreachable=0.01, near15=0.13, near30=0.51, log_mean_dist=3.52, log_hp_per_gem=4.33

Maps: 00breadcrumbs, 00gem-fields, 00gemfight, 00lost-world, 00road-of-riches, 02the-pond, 02treasure-box, 03colosseum, 03fan, 03one-gem, adgato-gemcombat2, adgato-gemcombat3, adgato-gemcombat4

## C5 (21 maps)

Rule: log_area > 7.8823 and harmless <= 0.459 and near30 <= 0.578

Typical: log_area=8.63, team=5.67, contested=0.31, top3=0.59, log_density=2.11, groups_per_champ=1.93, harmless=0.03, strong=0.32, blocked=0.14, unreachable=0.01, near15=0.02, near30=0.09, log_mean_dist=4.18, log_hp_per_gem=4.78

Maps: 00ambush, 00corners, 00dunes, 00expanse, 00lanes, 00pilgrimage, 00ribs, 00stampede, 01big-world, 01concentrated-wealth, 01fracture, 01starvation, 02cuts, 02famine, 02geodes, 02harvest, 02tangle, 03contours, 03reef, 03riverbed, 03twisty

## C6 (3 maps)

Rule: log_area > 7.8823 and harmless <= 0.459 and near30 > 0.578

Typical: log_area=8.20, team=5.67, contested=0.34, top3=0.56, log_density=2.57, groups_per_champ=2.01, harmless=0.01, strong=0.36, blocked=0.20, unreachable=0.00, near15=0.01, near30=0.81, log_mean_dist=3.33, log_hp_per_gem=4.75

Maps: 00crater, 00happy-halloween, 01islands

## C7 (3 maps)

Rule: log_area > 7.8823 and harmless > 0.459

Typical: log_area=8.92, team=4.67, contested=0.27, top3=0.54, log_density=1.18, groups_per_champ=1.30, harmless=0.90, strong=0.00, blocked=0.39, unreachable=0.03, near15=0.10, near30=0.15, log_mean_dist=3.94, log_hp_per_gem=3.73

Maps: 00galaxy, 03ultrastarvation, adgato-gemcombat5
