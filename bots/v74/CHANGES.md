# v74 (2026-10-28) — current best

`bots/v69` (v65 + 00vault siege fix + island escape + capture stall breaker) with:
- `V70_DRAFT_TABLE`: per-map draft lineups, 30 maps (`research/v71/draft_table_v74.json` = v70's 29-map table with two
  entries re-chosen and one added on top of the knob profiles, round 4);
- `V71_MAP_KNOBS`: per-map strategy profiles, 45 maps (`research/v71/knob_table_v73.json`).

Built with `tools/v67/c_v70_draft.py` then `tools/v67/c_v71_knobs.py`; run log `research/v71/round4.txt`.

Fresh validation against v73 (seeds 21/22, paired, 280 distinct games each): v65 +13 [0, +37], v61 +7 [0, +22],
v58 +7 [−4, +26], proxy +10 [0, +27] gems per game. Only two maps differ from v73.

## How far the line has come (fresh seeds only; paired steps)

| Step | v65 | v61 | v58 | proxy |
|---|---:|---:|---:|---:|
| v70 vs v69 (seeds 13/14) | +169 | +63 | +75 | +15 |
| v71 vs v70 (15/16) | +20 | +56 | 0 | +58 |
| v72 vs v71 (17/18) | +66 | +5 | +61 | +20 |
| v73 vs v72 (19/20) | +33 | +6 | +1 | +8 |
| v74 vs v73 (21/22) | +13 | +7 | +7 | +10 |

Absolute on seeds 21/22: vs v65 160/280 wins (+160 per game), v61 181/280 (+189). v69 against v65 on fresh seeds was
about even (135-140/280, −36 to −48 per game). Not submitted: the user's bar is a dramatic gain, and every opponent in
the league is our own lineage or the proxy, so the ladder effect is unmeasured.
