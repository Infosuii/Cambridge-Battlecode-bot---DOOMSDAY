# v68c (2026-10-28; first named v68)

Base: `bots/v66a` = platform v65 + `V66_ITEMS 1` (the winners' engine-2 item openings, then Bruiser stacks) +
`V66_TARGET 1` (closest enemy). v66a measured even with v65 against the top 12 (−23 ± 46 gems, paired).

v68 switches on the coordinated carry economy that v58 built and then rejected on the local self-play bench only. It
was never played against the top teams. Every switch is in `src/common.h`; setting it to 0 gives back v66a.

| Switch | What it does | Top-team evidence |
|---|---|---|
| `V58_DIRECTOR 1` | Early team clearing jobs, replanned outside the greedy camp loop, so several champions take elk-size groups together | Claudus clears 4.0 elk-size groups by R250 with 3-4 champions, first at R21; we clear 2.3, first at R36 |
| `V58_ROUTE 1` | Rewards are handed to a designated nearby capturer (the carry) without leaving them unattended | Claudus Vesper takes 44-49% of team capture gold |
| `V58_CARRY_SHOP 1` | Short shopping trips complete the carry's Treasure milestone early | Claudus Vesper has Treasure at R88 |
| `V58_DRAFT 1` | Carry composition: Vesper, Heart of Ruin, Vendetta, Ryth/Marcella (only with the three switches above) | Every top-12 team drafts Vesper, Heart, Vendetta and Marcella in 80-100% of games |

Local check (artifacts/evaluations/v67/d01, d02; vs v65, seeds 21/22, 240 games, zero faults):
Vesper earns 364 gold by R250 (v66a 160; Claudus 466). Win count 93/240 against v66a's 123/240. Self-play has not
predicted the ladder in either direction (v58 +153 locally, flat on the ladder; v66a +52 locally, −23 on the ladder),
so the top-12 ladder duel is the deciding test.

**Superseded (2026-10-28):** on the full-pool platform-faithful test (research/v68/LOCAL_TESTING.md) this loses to v66a by 176 gems per game (95% CI -262 to -93), 600 less gold per game. Both carry builds now also carry an earlier (non-incremental) siege fix. Not a release candidate.
