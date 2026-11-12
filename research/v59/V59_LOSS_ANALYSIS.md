# Why v58 loses on the ladder, and why our process did not catch it (v59 research, 2026-10-26)

## Data

- Every match since v58 (platform 57) went live at 13:31 UTC: 320 games, ranked 44/95, unranked 149/225
  (`data/ladder/v58_since_live.json`, `tools/replay/fetch_since.py`).
- Native summaries and replays for all 126 losses plus 42 wins, local-only in `artifacts/local-only/v58-ladder`
  (`tools/replay/fetch_v59_review.py`, manifest `V59_LADDER_MANIFEST.json`).
- Summary review: `tools/replay/v59_loss_review.py` -> `V59_LOSS_REVIEW.json`.
- Replay fight review (engine 2 decoder): `tools/replay/fight_review.mjs` + `fight_report.py`.
- Ladder calibration: `tools/replay/ladder_calibration.py` (ladder snapshot `data/ladder/ladder_20261026_p*.json`).

## 1. The production process is miscalibrated

Opponent-adjusted ranked results (Elo-expected score against the same opponents at our current rating 1943):

| Live version | Ranked | Expected | Residual |
|---|---:|---:|---:|
| v57 (platform 56) | 172/330 = 0.521 | 0.474 | **+0.047 ± 0.027** |
| v58 (platform 57) | 44/95 = 0.463 | 0.464 | **-0.001 ± 0.051** |

Locally, v58 beat v57 430/672 (64%, +153 gems) and passed every gate. On the ladder it is no better than v57 and
probably worse. The local gauntlet shows why: v58 beats every older sibling by +200 (v57 68.5%, v55 67.3%,
v54 66.1%). Every local opponent is our own lineage, and v58 was tuned against them.

The local games do not look like ladder games:

| Per game | Local v58 vs v57 | Ladder losses: us | Ladder losses: winner |
|---|---:|---:|---:|
| deaths | 15.8 / 16.2 | 14.0 | 6.9 |
| gems lost on death | 236 / 284 | 214 | 117 |
| contact time outnumbered | 0.14 / 0.17 | 0.21 | 0.11 |

Self-play is a brawl between two reckless copies, where both sides die 16 times. The teams that beat us die
seven times. A change that makes us disciplined (retreat when outnumbered, bank before a fight) gets punished in
self-play, because a reckless mirror keeps farming while we back off. On the ladder that discipline is exactly what
winners have. The code shows the pattern: the outnumbered retreat (`APEX_OUTNUMBERED`), two-turn burst danger
(`A2_BURST2`), threat-aware travel (`A2_THREAT`), team hold (`A2_TEAM`), out-of-sight memory (`A2_BELIEF`) and
v58's survive/locks/vision packages were each written from ladder evidence and then switched off after a
self-play screen.

Testing one mechanism at a time adds a second problem. A 224-game screen has a map-clustered interval of about
±100 gems, so a real +30 effect cannot be separated from noise. Most v58 screens (d1-d14) ended with intervals
spanning zero and were discarded. Changes that work together (gear plus disengage plus banking) never got
tested together.

## 2. Why we lose (126 losses vs the same games' winners)

| Per game | Us | Winner |
|---|---:|---:|
| deaths | 14.0 | 6.9 |
| kills | 5.8 | 11.8 |
| champion damage dealt | 24.5k | 39.2k |
| earned gold | 4,428 | 6,932 |
| gems collected by R200 | 100 | 134 |
| gems lost on death | 214 | 117 |

From the replays (95 losses): equal contact time (1,079 vs 1,142 champion-rounds) and equal action rate in contact
(0.27 vs 0.27), but we are outnumbered in 21% of contact time against 11%, alone in 48% against 36%, and we
take 31.7 hp per contact round against 22.9. 40% of our deaths happen outnumbered (theirs 24%), 34% with no
ally within 8, and the enemies around a dying champion have 1.84x the max health of its allies.

**Gear is the largest single gap.** The same heroes on the two sides of our losses:

| Hero | Gold earned us / them | Champion damage us / them | Their top purchase |
|---|---:|---:|---|
| Vesper Vale | 870 / 2,738 | 4.0k / 13.4k | 43 Bruiser Strength shards |
| Marcella | 875 / 2,220 | 7.1k / 13.0k | Bruiser Focus 24, Strength 16, Health 11 |
| Vendetta | 1,087 / 1,277 | 6.7k / 7.3k | Bruiser Strength 15, Health 8 |
| Heart of Ruin | 621 / 1,002 | 3.4k / 6.0k | Bruiser Focus 8, Health 8 |

The winners open with Treasure, Jungle, Bruiser Health and Durability, then stack Bruiser (7 shards of stats per
150 gold). v58 buys six passive emblems first (Prospector, Jungle, Durability, Monster, Capture, Collectors:
900 gold), then Greed in 25-shard (750-gold) steps. Our champions earn 600-1,250 gold each in a loss, so they
rarely complete a Greed emblem and fight on plain 1.0x shard stats. Our most-bought item in losses is Greed
Strength.

**Banking is not the problem.** Winners bank bigger bags than we do (mean 68 vs 41 gems per tribute). They can
carry because they do not die.

**Draft.** Ranked opponents take Marcella (86/95), Vesper (80/95), Heart (77/95) and Vendetta (71/95). We take
Vendetta (94), Marcella (79), Varg (67) and Ren (44), and Vesper in only 33. A Claudus-style draft copy lost
locally because our bot does not play Vesper as a gold carry, so the draft is left for a later version.

**Why we die.** From the replays, our champions are dead 14.6% of the game in losses against 7.6% for the
winners. Idle time is the same (about 19%). Before round 300, 42% of our deaths are outnumbered (theirs 20%), when
gear is still equal. Later, the gold gap compounds: kills pay 100 gold, and dead champions don't farm. In losses,
their Marcella (3.8 per game), Vesper (3.2) and Vendetta (2.4) do the killing.

## 3. What v59 changes

v59 changes two things. Bruiser stat stacks replace v58's Greed milestones. And the existing outnumbered retreat is
switched on at margin 2 (`APEX_OUTNUMBERED 2`). See `bots/v59/CHANGES.md` and `V59_RESULTS.md`. Process changes
are in `V59_PROCESS_FIXES.md`. The decisive test is the paired ladder A/B in `V59_LADDER_AB_PLAN.json`.
