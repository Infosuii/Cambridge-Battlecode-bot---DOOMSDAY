# Brawl-map PvP survival: findings (v55 research, 2026-10-25)

Target set by the user: PvP survival on brawl maps (hooks, eight, quadrants, gold-rush). Development maps used:
eight, quadrants, gold-rush, rows, rushbait-v2. **hooks is a release-holdout map**; it was used here at the user's
request and can no longer serve as unseen evidence. Nothing was submitted; v54 stays frozen and unchanged.

## 1. New ladder data

180 games were played after the last snapshot (13:30-15:30 UTC, all platform v53): ranked 24/55, unranked 61/125.
All 95 losses were downloaded and decoded (local-only, `artifacts/local-only/v53-after`); the listing is
`data/ladder/v53_after_snapshot_20261025.json` (`tools/replay/fetch_since.py`).

## 2. Why we die in fights (ladder losses, us vs the winners)

| Measure (tool) | Us | Winners |
|---|---:|---:|
| contact champion-rounds per game, brawl maps (`contact_cohesion.mjs`) | 1235 | 1197 |
| allies within 4 at contact / alone / outnumbered | 1.11 / 0.35 / 0.20 | 1.06 / 0.34 / 0.22 |
| P(die within 5 rounds), alone / supported | 0.067 / 0.046 | 0.030 / 0.021 |
| mean hp fraction in contact | 0.72 | 0.80 |
| contact time below 50% hp | 22% | 13% |
| P(die within 5) at hp ≥ 75% | 0.021 | 0.002 |
| hurt-contact episodes (hp < 50%) (`hurt_contact.mjs`) | 3010 | 1955 |
| once hurt: died within 5 / escaped / hit back | 0.14 / 0.31 / 0.33 | 0.14 / 0.33 / 0.32 |
| rounds with PvP attacks; distinct targets per such round (`focus_fire.mjs`) | 9489; 1.03 | 6565; 1.02 |
| enemy hp lost per contact round | 42 | 57 |

Positioning, cohesion, focus fire and behaviour once hurt are at parity. From equal contact we get hurt 54% more
often because each of our attacks does roughly half the damage. The ladder PvP gap is **power** (equipment and
damage), the economy problem v54 targets, not a separate tactical deficit. Local benches against our own lineage
cannot reproduce that gear gap.

Bot death logs (`APEX_DEATHLOG`, `tools/deathlog_report.py`) on the four maps: 82% of our deaths happen in flee mode
(hp 0.45 four turns earlier), for v53 as well (79%).

## 3. Why v54 is weak on brawl maps locally

Ablations on the six-map brawl set, seeds 1-6, 72 games each vs v53 (`tools/bench_deaths.py`):

| Build | Win rate | Margin | Deaths us/v53 |
|---|---:|---:|---:|
| v54 | 0.36 | −135.9 | 18.0 / 14.2 |
| without M1 | 0.46 | −3.1 | 16.1 / 17.4 |
| without M2 | 0.49 | −29.4 | 16.2 / 16.7 |
| without M4 (teleports) | 0.53 | +121.8 | 14.5 / 17.0 |

On hooks no champion of either team ever teleports, yet carrying the crystal bought at the first shop matters:
buy-but-never-use 10/24 (−208.5), check-but-never-buy 20/24 (+535.8), seeds 1-12. By R500 the two variants are
behaviourally indistinguishable (dead share 0.30 both, similar spending), so the path is a long-horizon divergence
on a winner-takes-all map; the mechanism is not identified.

## 4. Candidates tested (paired against v54 on the same 12-seed, 672-game dev set vs v53 unless noted)

| Variant | Brawl set | Full dev, paired vs v54 | Verdict |
|---|---|---|---|
| v55a: buy a crystal only after a worthwhile hop was seen | 0.46, −11.4 | 410 vs 424 wins, −28.6 (644 games) | rejected: mobility maps lose their first hop (stampede 19→13/24) |
| A2_THREAT (hurt or carrying ≥20 avoid contested camps) | 0.47, +69.2 | 306 vs 327, −28.1 (504 games) | rejected |
| APEX_THREAT_RETREAT 0.55 | 0.39, −58.7 | - | rejected at screen |
| A2_DANGERMAP | 0.35, −162.3 | - | rejected at screen |
| A2_TEAM hold | 0.40, −138.0 | - | rejected at screen |
| hp-only readiness at 70% (A2_THREAT, carrier trigger off) | dev brawl 52 vs 52 wins, +69.8 | 423 vs 443, −14.6 | rejected |
| **hp-only readiness at 50%** | dev brawl 59 vs 52 wins, +79.1 (naive s.e. 44) | 443 vs 443, +0.2 | neutral overall; brawl gain about 1.8 s.e.; hooks 12/24, −27 |

The 50% readiness variant did not reduce the share of our contact time below 50% hp (0.206 vs 0.205), the mechanism
it was meant to act on; its brawl gain is therefore not attributed to readiness. It is recorded as an option, not a
candidate.

The four screened levers were already in the code and switched off; they were re-tested because the v54 economy
and the new ladder evidence changed the context, and all but readiness failed again.

## 5. Harness fix

`tools/bot_match.py` imported `nfs.policy` (CUDA torch) in every shard to locate the default baseline; with 48
parallel shards Windows ran out of paging file (WinError 1455) and dropped 28-168 games per 672-game run. The
import is now lazy. Runs after the fix completed all 672 games.

## 6. Conclusions and next steps

1. The ladder PvP deficit is a damage/equipment deficit; v54's economy is the relevant fix. Only ladder games can
   test whether it closes the gap (v54 is not submitted).
2. v54's local brawl weakness is tied to teleport-crystal behaviour (strongly on hooks, where no hop occurs).
   Neither gating the purchase nor any readiness rule removed it without costing elsewhere.
3. A tactical survival mechanism that wins locally would have to win the damage exchange at equal gear. Positioning,
   focus and retreat behaviour are not where the measured differences are.
