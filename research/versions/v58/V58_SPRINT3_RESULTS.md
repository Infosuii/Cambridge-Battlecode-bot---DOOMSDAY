# v58 Sprint3 combined package

All runs use official CLI/SDK4.0.0, engine2.0.0 and default fuel. Frozen v57 is rebuilt with the same SDK. No bot source was changed during or after the final checks.

| Run | Games | Wins | Margin | Candidate fuel/game |
|---|---:|---:|---:|---:|
| core | 224 | 125 (55.8%) | +77.9 | 2.478 |
| economy | 224 | 135 (60.3%) | +116.9 | 2.094 |
| economy-confirm | 672 | 410 (61.0%) | +136.3 | 2.247 |
| fastgroups | 224 | 147 (65.6%) | +186.6 | 0.853 |
| fastgroups-confirm | 672 | 430 (64.0%) | +153.0 | 0.999 |
| holdout12 | 96 | 67 (69.8%) | +152.0 | 0.240 |
| fresh15 | 120 | 69 (57.5%) | +127.1 | 0.000 |
| new02 | 120 | 73 (60.8%) | +79.5 | 1.867 |

Final map-cluster95%[+107.5,+202.8]; Bayes mean+202.5, P(gain)=1.0000. All native faults0 on both teams. All three final pools exceed50% wins/nonnegative margin, with candidate fuel<=2/game.

The fast camp-contact path was checked against the original calculation on every observation of six diagnostic games, with zero assertion faults. A separate profiling build and a discarded optimization for an inactive belief feature are excluded from strength evidence. Four smoke games are also excluded.

2352 competitive games were played, with1904 distinct configuration/map/side/seed slots. Screening and confirmation overlap. Reused old fresh maps have historical exposure; the new02 pool had recent-loss analysis exposure. These are local lineage comparisons, not a claim of rank25 or measured superiority to Claudus.

Mechanism audit:56 seed1 games, all28 development maps/both sides. R250 capture gold711.9 vs689.7, elk captures2.79, carry share27.5%. Full672-game deaths down13.3%. Original900/3.5/40%/30% targets remain unmet and explained in CHANGES.md; no proxy qualifies.

Native672-game R250 income948.8 vs878.8, including kills/bonuses; do not label this capture income. Prospector is acquired in every candidate game; Capture in618 games and Greed in387. Timing is conditional on acquisition.

Clean source-only build matches benchmark seed1 byte for byte. Official bundle has33 source files,279034 bytes, exact per-file source identity. Full proof and hashes are in results/v58-s3-clean-build.json.
