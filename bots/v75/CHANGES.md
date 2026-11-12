# v75 (2026-10-28) — rejected on the ladder

**Ladder duel (top 12, 120 games): 21/120, -393 per game; v74 30/120, -302; v75 - v74 = -91 +/- 54.** Not used;
v74 (platform 68) stays live. The switches below remain available but off in later bots.

`bots/v74` plus one fight-admission rule from the v67 ladder-loss analysis (`research/v75/LOSSES.md`):

- `V75_LONE 2.0` + `V75_LONE_ALL 1` (bot.cpp, handle_enemies): with no healthy ally within 4, visible enemies within 6
  holding at least twice our health are not engaged unless this turn kills, and when one can reach us within two steps we
  leave now, before contact. Applies whether the verdict layers said fight or neither (farming on toward a stronger
  group). Ladder losses: 5.1 deaths per game walking into enemies that outnumber us (winners 1.7); the enemies around our
  deaths hold 3x our shards.

Switches present but off (each tested on seed 23 against v65 / v61 / v58 / proxy, 140 games each, vs v74):

| Switch | Margin vs v74 (gems per game) | Deaths | Verdict |
|---|---|---|---|
| `V75_LONE 2` + `V75_LONE_ALL 1` (shipped) | v65 +13, v61 −54, v58 +32, proxy +4 | −0.5 to −1.7 | neutral locally; ladder test |
| `V75_LONE 2` (fight verdict only) | v65 −33, proxy +31 | −0.8 to −1.3 | not chosen |
| `V75_RACE 1.0` (in danger, only a race we win) | v65 −60, proxy +11 | −1.3 to −1.8 | off |
| `V75_BAG 120` (big-bag carriers take no fights) | v65 −55 (CI below 0), v61 −21, v58 −29, proxy −22 | ±0 | off |
| race + lone2 + bag | v65 −48, v61 −165, v58 +47, proxy −44 | −0.6 to −2.6 | off |
| `APEX_STAND 7` (existing; stand when cornered) | v65 −523, proxy −529 | +7 to +9 | off |
| `APEX_STAND2 3` (existing; melee caught) | v65 −425, proxy −347 | +6 | off |

Local play cannot reward the caution rules: every league opponent is our own lineage and dives the same way. The
ladder duel (top 12, `research/v59/duel_top1.json`) is the judge; results in `research/v75/DUELS.md`.
