# v73 (2026-10-28)

`bots/v72` plus round-3 knob profiles on maps v72 left alone: 8 of the 33 uncovered maps gain a second-generation
profile (hunt2, ranged2, search2, huntranged, bankhunt, softcaut, softaggr, decisive, patient or teamfight;
`tools/v67/c_profiles.py`). Table: `research/v71/knob_table_v73.json` (45 maps). Built from `bots/v70` with
`tools/v67/c_v71_knobs.py`; run log `research/v71/round3.txt`.

Fresh validation against v72 (seeds 19/20, paired, 280 distinct games each, gems per game, 95% CI):

| Opponent | Margin difference | Deaths |
|---|---:|---:|
| v65 | +33 [+1, +71] | −0.3 |
| v61 | +6 [−13, +29] | −0.3 |
| v58 | +1 [−33, +26] | +0.3 |
| proxy | +8 [−15, +31] | −0.3 |

Absolute on seeds 19/20: vs v65 169/280 wins, +150 per game; v61 164/280, +138; v58 196/280, +267; proxy 223/280, +367.
Knob profiles are reaching diminishing returns. Not submitted.
