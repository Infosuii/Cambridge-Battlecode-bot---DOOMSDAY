# v76: v75 with ext's V68/V69 fixes off (v74h + V70 draft table + V71 map knobs)

Ablation on the 120-map suite, both sides, seeds 1-3 (720 games each), overall win rate vs v74h:

| variant | win rate (95% CI) | gem margin |
|---|---|---|
| v75 (fixes + tables) | 52.9% (49.0-56.7) | +42.0 |
| fixes only (V68_SIEGE_FIX, V69_ISLAND, V69_CAPTURE_STALL) | 46.7% (43.8-49.6) | -37.7 |
| tables only = v76 | 53.9% (51.4-56.4) | +56.6 |

Only change from bots/v75: `V68_SIEGE_FIX 0`, `V69_ISLAND 0`, `V69_CAPTURE_STALL 0` in src/common.h.
Not kept (v75 base, 720 games each): A3_ONE_OWNER 49.9%, A3_ITEMS 40.0%, A3_FOCUS 51.4% then 51.1% on seeds 4-6.
