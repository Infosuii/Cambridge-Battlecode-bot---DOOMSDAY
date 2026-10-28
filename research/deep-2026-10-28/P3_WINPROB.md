# Win probability model

**Predictive association.** The model uses 385 examined games only: 231 train,77 calibration,77 internal test. Each game has equal total weight; snapshots never cross folds. The external 165 hands-off games remain untouched.

The feature plan and game split were committed before fitting (871a933). A symmetric logistic regression has no intercept and uses ten fixed-scale team-difference features. L2 strength was selected from {0.01,0.1,1,10} using calibration log-loss; a positive scalar temperature was fitted on those same calibration games. Test games were used once for the following evaluation.

| Partition | Games | Snapshots | Model log-loss | Brier | ECE (10 bins) | Bank-only log-loss | 0.5 log-loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| train | 231 | 161121 | 0.3951 | 0.1292 | 0.0599 | 0.4987 | 0.6931 |
| calibration | 77 | 55982 | 0.4622 | 0.1493 | 0.0380 | 0.5290 | 0.6931 |
| test | 77 | 55220 | 0.4243 | 0.1400 | 0.0490 | 0.5318 | 0.6931 |

Test model-minus-bank log-loss, complete-game bootstrap95% (2,000 draws,77 games): [-0.16613388338741406, -0.04282774980115906]. Lower is better. This interval does not model shared-map/opponent dependence.

## Test calibration

| Prediction band | Game-weighted mass | Mean prediction | Observed win fraction |
|---|---:|---:|---:|
| 0.0–0.1 | 0.150 | 0.024 | 0.000 |
| 0.1–0.2 | 0.055 | 0.150 | 0.005 |
| 0.2–0.3 | 0.054 | 0.253 | 0.146 |
| 0.3–0.4 | 0.088 | 0.353 | 0.242 |
| 0.4–0.5 | 0.147 | 0.457 | 0.486 |
| 0.5–0.6 | 0.139 | 0.544 | 0.585 |
| 0.6–0.7 | 0.089 | 0.649 | 0.709 |
| 0.7–0.8 | 0.064 | 0.750 | 0.769 |
| 0.8–0.9 | 0.063 | 0.852 | 0.883 |
| 0.9–1.0 | 0.152 | 0.970 | 0.948 |

## Test timing slices

| Rounds | Games | Snapshots | Model log-loss | Brier | Bank-only log-loss |
|---|---:|---:|---:|---:|---:|
| 0_100 | 77 | 7777 | 0.6581 | 0.2341 | 0.6935 |
| 101_250 | 77 | 11550 | 0.5588 | 0.1898 | 0.6725 |
| 251_500 | 77 | 11993 | 0.4415 | 0.1440 | 0.5933 |
| 501_plus | 76 | 23900 | 0.2482 | 0.0761 | 0.3356 |

## Interpretation and limits

WINPROB_MODEL.json includes scales, coefficients, lambda scores, temperature and every calibration table. Coefficients are conditional on correlated features: a small negative middle-income or vision coefficient does not establish that either hurts winning. Inventory purchase cost is not combat power; unspent gold is omitted under the registered feature plan, so a shop visit can create a sharp prediction change.

The internal split shares maps and opponents across folds. This is not an unseen-map performance estimate. Calibration reuses 77 games for lambda and temperature, and early-game predictions remain weak. R0 is included with its actual state; terminal rows are excluded. Last-50 income uses the last retained row at/before the start of that window (up to four extra rounds after R300).

Four scientific checks pass: neutral probability/calibration-bin accounting, exact team-exchange complement, no future-resource access in an earlier feature, and invariance to duplicated snapshots when per-game weights are preserved.

moments.json records the five largest disjoint positive approximately ten-round drops per examined DOOMSDAY loss. Nonterminal states are used at both ends. Feature changes are apportioned by integrating the logistic derivative along the observed segment; the components sum to the model change but are not causal credit. Single events, cards, shares and later fix priorities require that distinction.

MOMENT_SAMPLE.json fixes 105 cards: 90 loss moments from 65 losses (20 Learn,30 Climb,15 Other) and 15 distinct control wins (2 Learn,9 Climb,4 Other). Actor-own pre-window observations and rule-based expectations are frozen separately before subsequent actions are exposed. The focus actor is selected from the pre-window state by largest bag, then lower HP fraction, then physical ID. This can omit a different victim in a team-level swing.
