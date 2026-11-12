# B1: expected-exchange engagement (DZ_EE3), 2026-11-01 — parked

Two contact models: `ee_model.h` (V-M2: this body dies within 4 rounds) and `ee_enemy_model.h` (PROVISIONAL:
the same features from the enemy's side, fitted on 56 v76 games; Brier 0.00448 vs baseline 0.00460, interval
not yet below 0; enemy deaths are rare, 0.6% of samples). Engage the target with the best
P(kill) x (carried gems + gold_weight x kill_gold + tempo) - P(death) x (bag + tempo), tempo = 0.25 x respawn_time.

Paired against the selected release (140 cells each):

| Run | Δ banked (SE) | Δ margin | deaths | fuel-outs |
|---|---|---|---|---|
| `dz-ee3-v76-01` v1 (also overrides retreat, keeps working below P 0.15) | −12.8 | | 21.1 vs 19.0 | 406 |
| `dz-ee3-v65-01` v1 | −35.6 | | 20.2 vs 18.1 | 337 |
| `dz-ee3v2-v76-01` v2 (only adds positive-EV engagements) | −5.5 (10.9) | +10.7 | 19.4 vs 19.0 | 404 |
| `dz-ee3v2-v65-01` v2 | −23.6 (12.9) | −37.6 | 18.2 vs 18.1 | 676 |

Findings:
- Overriding the incumbent retreat loses bodies (v1, as EE2 did): the conservative retreat is protective.
- Extra engagements don't pay even when priced by calibrated models; v76 margin improved slightly (denial), v65 lost.
- The fuel-outs (00dunes rounds 0-200, 00vault, 02treasure-box) come from the Fight executor: each Fight goal
  builds a whole-map field around the target (actions.cpp), and EE3 chooses Fight far more often. Any future
  engagement rule needs a bounded local Fight path first.
Next combat work (B2/B3) should change *how* contacts are fought (focus, abilities, kiting), not how often.
