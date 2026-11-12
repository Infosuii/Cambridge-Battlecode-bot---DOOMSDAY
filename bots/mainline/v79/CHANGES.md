# v79 (2026-10-28)

`bots/v76` (per-map knob profiles; v74 + round 5) with the v75/v78 switches ported (all off) and the team-fight system
`V79_TF` (`src/common.h`, `src/bot.cpp` handle_enemies / tf_ratio / tf_join). With `V79_TF 0` v79 plays v76 game for
game. Analysis and every local result: `research/v75/TEAMFIGHT.md`.

Why: in the v74 ladder duel against the top 12, focus fire (86% both), starting numbers and grouping match the top
teams; what differs is how contact rounds are spent. Our champions step away without hitting in 28% of contact rounds
(top teams 8%), reverse direction 2.6 times per contact episode (1.7), and beside a teammate one hits while the other
leaves in 21.8% of grouped contact rounds (13.7%).

`V79_TF` bits:
- 1: team power at the contact point (summed health x summed damage, champions weighted by how soon they can hit there,
  same view for every teammate). A commitment to fight holds while the ratio stays at 0.8 (`V79_TF_STAY`); only health
  below 25% (`V79_TF_EXIT_HP`, 40% for 60+ gem carriers) or a lethal burst next turn break it. A commitment to leave
  holds 4 rounds (`V79_TF_LEAVE`) while the ratio stays below 0.8.
- 8 (with 1, the default 9): the bot's own verdict opens the commitment, so the change is in flip-flopping, not in which
  fights are taken. Without 8, the ratio opens it (engage at `V79_TF_ENGAGE` 1.3, leave at `V79_TF_AVOID` 0.7 with an
  enemy in reach).
- 2: team focus target. 4: retreat toward a healthy ally. 16: join an ally's fight within 12. 32 (with 8): beside a
  healthy teammate the ratio alone opens the fight. All negative or neutral locally; off.

Default `V79_TF 9`. Local check against v76 (= v78), seed 24, 140 paired games each: v65 -72 [-202, +55], v61 -107
[-214, +4], v58 -82 [-184, +18], proxy -24 [-129, +68] gems per game; deaths -0.3 to -1.2 a game
(`research/v75/v79_paired.txt`). Not a release candidate on local evidence. The local league is our own lineage, so
only a ladder arm beside v76 on the same match groups can show whether top teams punish the old flip-flopping more;
the one fight rule tested there before (v75 lone guard) kept its local sign (neutral locally, -91 on the ladder).
