# Which opening leads transfer across layouts?

Use the three x3mf opponent pools and only the events up to round 150. Split by layout so both sides and all opponents of a layout stay together. Train a small ridge logistic model on 43 maps and evaluate the other 43, then swap folds. No model inputs use end-of-match information.

| Signal | AUC, first held-out fold | AUC, second held-out fold |
| --- | ---: | ---: |
| Completed emblems | 0.677 | 0.655 |
| Champion kills | 0.680 | 0.607 |
| Champion deaths | 0.674 | 0.619 |
| Camp gems | 0.577 | 0.592 |
| Banked gems | 0.575 | 0.554 |
| All nine counters | 0.731 | 0.671 |

The emblem lead is the most stable individual predictor across these folds. It can reflect a stronger opening economy or earlier fight wins, so the association alone does not justify shopping more often. A narrow intervention is to take a short detour only when the inventory and available gold already complete an opening emblem. Preserve expensive return trips and active camp work.
