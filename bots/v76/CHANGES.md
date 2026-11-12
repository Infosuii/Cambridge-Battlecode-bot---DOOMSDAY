# v76 (2026-10-28)

`bots/v74` (ladder-best: top-12 duel 30/120, +142 over v67) with 12 more per-map knob profiles from round 5
(`research/v75/round5*.sh`): nine new profiles over knobs earlier rounds never varied, aimed at the time the v67
ladder-loss review found wasted (`research/v75/LOSSES.md`): `spread` / `solo` (need pool, cohesion, stage timeout),
`wait` / `nowait` (respawn waiting), `shopmore` / `shopless`, `calm` (danger ttd), `needplus`, `nohunt`
(`tools/v67/c_profiles.py`). Selected per map on seeds 1/2/5/6 against v65, v61, v58 and the proxy (gain > 100, no
opponent below -250): 00collision shopmore, 00corners solo, 00eight shopmore, 00quadrants solo, 00reverse-spiral spread,
00the-line wait, 00vault wait, 01concentrated-wealth spread, 01gold-rush calm, 01hooks solo, 02famine wait, 02tangle
nowait. Five of them combine with the map's existing profile. Table `research/v75/knob_table_v76.json` (52 maps),
built with `tools/v67/c_v71_knobs.py --replace`.

Fresh validation against v74 (seeds 24/25, 280 paired games each): v65 +44 [+10, +89], v61 +42 [+3, +87], v58 +33
[+3, +82], proxy +27 [-9, +72] gems per game.
