# Z14c (2026-11-01): exact table with the fuel set, EE3 and per-map switches

41 configs (Z14b set, EE3 variants, 7 per-map mid-game switch rows) as uniform 70-row tables under
DZ_PLAN_TABLE + DZ_FAST_FIGHT + DZ_LATE_FIELD_GATE + DZ_FIELD_METER, snapshot `source`; selected on v76+v65
(margin 100; 53 of 56 development maps get a row: dv7 5, int1b 4, fightgs 4, ee3 3, dv5 3, ...).

| Table | vs v74 Δ banked (SE) | dev Δ margin | vs v81hl Δ banked (SE) | dev Δ margin | fuel-outs |
|---|---|---|---|---|---|
| Z14c | **+102.1 (14.8)** | +140.7 (18.0) | +9.3 (10.7) | +6.8 (16.4) | 0 |
| Z14b | +78.4 (15.3) | +114.8 (27.4) | +26.7 (11.2) | +25.1 (19.0) | 0 |

Both transfer strongly to v74 (close to the v76/v65 line) and weakly to v81hl. Next, Z14d: add v74 to the
selection (v76+v65+v74) and confirm on v81hl and v85, both unseen (`tools/dz_z14d.sh`).
