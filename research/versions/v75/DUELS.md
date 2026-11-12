# Ladder duels against the top 12 (2026-10-28)

Plan `research/v59/duel_top1.json`: 12 top teams x 2 match groups x 5 games (fixed maps and sides), 120 games per arm,
played back to back with `tools/replay/ladder_duel.py` (the arm's version is live while its groups play). Ten of the
twelve plan teams are still in the current top 12. Approved by the user on 2026-10-28.

| Arm | Platform | Wins / 120 | Mean gem margin | Paired vs v67-1028 |
|---|---:|---:|---:|---|
| v67-1028 (live v66b, re-measured) | 67 | 17 | -444 | |
| v74 | 68 | 30 | -302 | +142 +/- 54 gems; 19 games only v74 won, 6 only v67 (sign z = +2.60) |
| v75 (v74 + V75_LONE 2 + V75_LONE_ALL 1) | 69 | 21 | -393 | +49 +/- 55; **vs v74: -91 +/- 54** (v74 only 16, v75 only 7; z = -1.88) |

The caution rule that keeps lone champions out of fights against twice their health loses on the ladder as it did locally
(neutral there): fewer dives is not the lever, against top teams either. v74 (platform 68) was re-pinned as the live
version at 2026-10-28 ~10:05 UTC.

Earlier arms on the same plan (2026-10-26/27, opponents' bots older): v65 24/120 (-386), v66b 23/120 (-403).

Per opponent (v67 -> v74, of 10): Ad Astra 0->1, Claudus 3->5, Intercontinental Fish 0->0, Mite 0->0, NEETCoders 3->4,
Sponge 3->5, Trzy Kwaterki 3->4, Univardisty 2->7, hello 0->0, print dont int 0->0, prism best girl 1->2,
willow best girl 2->2.

v74 is the first version whose local gains (per-map drafts and knob profiles, vault/island/capture fixes) carried
over to the top teams. Four teams still win every game against both versions.
