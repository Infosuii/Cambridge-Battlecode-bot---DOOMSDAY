# A2: DZ plan-switch branches and a learned switch policy (2026-11-01)

Branch hook: `DZ_SWITCH_ROUND`/`DZ_SWITCH_BITS` (table builds; volatile non-zero initialisers, so branch binaries
differ only in data, checked). Screens from snapshot `source` with the uniform base table: switch the whole team
to HOME / FIGHT / TURTLE / HOARD at R = 100, 250, 500, vs v76 and v65 (`tools/dz_overnight.sh`; 23 of 24 runs,
hoard@100 vs v76 timed out in build under load).

Mean margin change vs `dz-a2-base-*` (140 cells): early switches hurt (home@100 -17 / -22, turtle@100 -14 / -14);
the best fixed switch is fight@500 (+6.1 v76, +11.9 v65). Oracle choice per map (best of 11, both sides): +86.5 /
+98.8 margin, an optimistic upper bound on deterministic games. Per-map switch rows are now table candidates
(PlanRow switch_round/switch_bits; Z14c configs s250*/s500*/s100hoard).

Learned policy (`tools/dz_a2_model.py`, map-grouped 5-fold CV, ridge per (R, plan) on the position at R for both
teams: banked, carried, gold, kills, deaths, collected): `model_RESULTS.json`.

| R | CV policy margin change (95% CI) | best fixed plan |
|---|---|---|
| 100 | -8.3 (-27.1, +9.9) | hoard -4.0 |
| 250 | -4.4 (-16.4, +6.6) | fight +4.5 |
| 500 | +9.6 (-4.9, +26.3) | fight +9.5 |

Exit (CV gain > 0 with interval above 0) not met: the position at R does not say which plan helps beyond the best
fixed switch. More opponents and positions (the branch farm) are needed before a distilled selector.
