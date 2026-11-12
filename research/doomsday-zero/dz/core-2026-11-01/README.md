# Experiments on the candidate core (2026-11-01); pairs dz-mastery-<opp>-01 (core binary 24d36aa56b12)

| Flag | v81hl | v85 | v76 | v65 | mean Δ margin |
|---|---|---|---|---|---|
| DZ_CLEAR_BOLD (clear margin 1.1x + 5%) | +17.6 (11.7) | -36.1 (16.4) | -24.8 (13.4) | -29.7 (9.9) | **-18.3**, deaths up |
| DZ_FOCUS (target x(1+0.75 helpers)) | +12.9 (11.4) | -24.7 (14.6) | -13.9 (5.4) | +9.0 (4.5) | **-4.2** |

Both parked. Next: mastery variant 2 (Vendetta last).

## Ports from v81hl and the pure mastery draft (pairs: core dz-mastery-*, and release+fuel dz-fastboot-*)

| Build | v81hl | v85 | v76 | v65 | mean vs core | mean vs release+fuel |
|---|---|---|---|---|---|---|
| DZ_DRAFT_NET (v81hl's draft net) | -30.7 | -90.3 | -57.8 | -62.3 | **-60.3** | -13.5 |
| DZ_DRAFT_MASTERY=3 (mastery order on every map/size) | +43.8 (13.9) | -5.2 (16.0) | +20.8 (12.2) | +34.9 (10.8) | **+23.6** | **+70.4** |
| DZ_DRAFT_MASTERY=2 (Vendetta last) | worse on all four | | | | parked | |

m3 vs the release with the fuel set: v81hl +79.7 (18.5), v85 +60.0 (27.1), v76 +65.0 (21.6), v65 +77.0 (17.8);
0 fuel-outs. G5 (+50, lower bounds > -30) passes on every opponent. New core = m3 (DZ_DRAFT_MASTERY=3 +
survive/prospect gear + fuel set + fast boot). v81hl's draft net picks for the lab bots' play, not DZ's: parked
(retrain on DZ games before reuse).
