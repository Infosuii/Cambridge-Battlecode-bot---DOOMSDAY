# Resource race and openings

**Measured identities; paired associations.** 360 examined DOOMSDAY games (191 losses,169 wins); 25 top-v-top references are separately available for the model/matched controls. Hands-off use: zero.

All 385 replay timelines pass native resource clocks and gem conservation. Gold sources use exact capture-phase deltas and native kill/bank cursor deltas; unmatched earned gold remains residual.

`banked margin = collected margin + (enemy lost − our lost) + (enemy carried − our carried)` is an exact accounting identity. It is not a counterfactual: killed bags can enter the other team’s collected income.

| Cohort/outcome | n | Mean banked margin | Collected margin | Loss preservation | End carried margin |
|---|---:|---:|---:|---:|---:|
| all/loss | 191 | -579.3 | -448.7 | -103.0 | -27.5 |
| all/win | 169 | 631.7 | 632.2 | 36.5 | -37.0 |
| Climb/loss | 83 | -512.5 | -382.0 | -81.6 | -48.9 |
| Climb/win | 119 | 625.0 | 613.0 | 26.7 | -14.7 |
| Learn/loss | 53 | -672.8 | -566.2 | -125.0 | 18.4 |
| Learn/win | 7 | 520.0 | 541.7 | 68.6 | -90.3 |
| Other/loss | 55 | -589.8 | -436.2 | -114.3 | -39.3 |
| Other/win | 43 | 668.3 | 700.0 | 58.3 | -90.0 |

## Paired opening equipment gaps

Our current inventory cost minus the opponent’s at the same round. Cost is not combat power. Intervals resample maps or opponents, preserving paired games; these are descriptive and unadjusted for draft/roster differences.

| Cohort/outcome | R100 n/mean | R250 n/mean | R100 map 95% | R100 opponent 95% |
|---|---:|---:|---|---|
| all/loss | 191/-86.7 | 191/-276.8 | [-122.7890216253924, -49.34358256697322] | [-117.36294327369961, -53.56487667009253] |
| all/win | 169/+90.5 | 169/+340.3 | [44.24901315789474, 138.665191053122] | [46.756878557874764, 138.4275074478649] |
| Climb/loss | 83/-91.8 | 83/-193.7 | [-121.00384615384615, -61.23205479452055] | [-124.66666666666667, -78.60759493670886] |
| Climb/win | 119/+84.2 | 119/+337.1 | [37.42668669318827, 138.81822033898302] | [-30.0, 89.20124234172906] |
| Learn/loss | 53/-120.6 | 53/-462.5 | [-167.40136363636364, -72.66578947368421] | [-161.02941176470588, -51.81818181818182] |
| Learn/win | 7/+222.9 | 7/+548.6 | [60.0, 313.3333333333333] | [-60.0, 285.0] |
| Other/loss | 55/-46.4 | 55/-223.1 | [-136.91089193825042, 36.79245283018868] | [-113.4054255319149, 13.398214285714213] |
| Other/win | 43/+86.5 | 43/+315.3 | [8.997972972972972, 163.4701530612245] | [28.53369704749679, 165.40736704446383] |

## Scope of opening evidence

TIMELINE_DATA.json records both rosters, each physical champion’s first three observed camp targets, first later team gem receipt for each target, first purchase, observed large-reward timing and pre-receipt team spread. A receipt is not proof that the initial targeter captured the camp. Gold-only captures, rejected calls, hidden targets and policy intentions are outside those opening labels.

Exact R50/R100/R250/R500 resource, equipment, vision and time-proxy paired means and per-game rows are in TIMELINE_DATA.json. Games ending before a mark are omitted at that mark, with coverage reported. Middle uses minimum distance over every original camp tile to each team’s initial spawn positions, as in camp_clear.mjs.

Vision is the union of official per-champion vision buffers; visible-enemy summaries are the union of those observations. Decision cards require the acting champion’s own view. Travel and stationary time must not be equated with wasted time. Model and cards follow separately.
