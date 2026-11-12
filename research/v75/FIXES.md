# Direct fixes for the ladder-loss problems (2026-10-28)

Each fix is a switch in `bots/v78` (= v76 + the v75 switches ported, all off; v78 with everything off reproduces v76 game
for game). Checked against v76 on seeds 24/25, 280 paired games per opponent (`tools/v67/c_paired.py`), gems per game;
gated-map fixes on 01boss-battle and 02guardians only (seeds 23-30, 32 games per opponent).

| Problem | Fix (switch) | v65 | v61 | v58 | proxy | Verdict |
|---|---|---:|---:|---:|---:|---|
| Lone dives | no lone fight vs 2x health (V75_LONE 2 + ALL) | +13 | -54 | +32 | +4 | ladder: -91 vs v74 |
| Damage races we lose | in danger, only a race we win (V75_RACE 1) | -60 | | | +11 | off |
| Big-bag carriers dive | no fights at 120+ gems (V75_BAG 120) | -55 | -21 | -29 | -22 | off |
| | no fights at 300+ gems (V75_BAG 300) | -7 | -35 | -22 | -14 | off |
| Hunting without numbers | numbers check in hunt() (V78_HUNT_GUARD) | 0 | 0 | 0 | 0 | no effect: hunting is off in every map class (APEX_C*_HUNT 0) |
| Fleeing away from allies | flee toward a healthy ally (APEX_FLEE_ALLY 2) | -70 | -21 | +35 | +22 | off |
| Ally left alone in a fight | join a nearby ally's fight (A2_TEAM 2) | -47 | -35 | -24 | -12 | off |
| Dying while fleeing | stand and fight when cornered (APEX_STAND 7) | -523 | | | -529 | off |
| | melee caught: fight (APEX_STAND2 3) | -425 | | | -347 | off |
| Staging deadlock (monolith ring empty) | ring 2 tiles past camp reach (V78_STAGE_RING) | -61 | -70 | +11 | +26 | off |
| Siege never times out | siege only if spells finish in 40 / 80 turns (V78_SIEGE_CAP) | -16 / -36 | -20 / -5 | +20 / +30 | -5 / -2 | off |
| Gate opened late (gated maps) | whole team, no gathering, from 150/300/450 (V75_GATE) | | | | | -950 to -1,780 |
| | gather 3, from 400 / 600 (A2_GATE_JOB + V78_GATE_NEED 3 + ring) | -987 / -715 | -1,270 / -944 | -1,344 / -1,199 | -1,227 / -734 | off |

Per-map knob rounds: round 5 (12 maps, v76) +27 to +44 on fresh seeds; round 6 (35 maps, v77) no gain (-48 to +29).

What the numbers say: every rule that removes a failure also removes what that behaviour was earning (kills, map
control, banking pace). The ladder agreed for the one rule tested there. Changes that did raise results were per-map
strategy (v70-v76) and fixes for champions frozen in place (v68/v69); v74's ladder gain over v67 came from economy
(top-12 losses: deaths unchanged at 14.6 per game, shards at round 800 up from 24 to 30).
