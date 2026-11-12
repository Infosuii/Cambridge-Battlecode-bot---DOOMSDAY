# v72 (2026-10-28)

Same design as `bots/v71` (v70 + `V71_MAP_KNOBS`), with the per-map profile table reselected from four seeds per
opponent instead of two: seeds 1/2/5/6 against v65, v61, v58 and the proxy (`research/v71/round2.ps1`). 37 maps carry a
profile (`research/v71/knob_table_r2.json`; in-sample +129 gems per game over v70).

Fresh validation against v71 (seeds 17/18, paired, 280 distinct games each, gems per game, 95% CI):

| Opponent | Margin difference | Deaths | Gold |
|---|---:|---:|---:|
| v65 | +66 [+6, +138] | −0.7 | +209 |
| v61 | +5 [−50, +58] | −0.3 | −60 |
| v58 | +61 [+8, +117] | −0.3 | +171 |
| proxy | +20 [−31, +73] | −0.1 | +154 |

Absolute on seeds 17/18: vs v65 176/280 wins, +179 per game; vs v61 173/280, +186; vs v58 190/280, +250; vs proxy
221/280, +402. Not submitted (the user's bar is a dramatic gain).
