# What was wrong with the production process, and what changed (v59, 2026-10-26)

Evidence is in `V59_LOSS_ANALYSIS.md`. In short: the gate measured "beats our own previous version on 28 old maps",
and that number does not predict ladder results.

## Findings

1. **The gate's opponent is ourselves.** Every gate compared a candidate with its parent. v58 cleared it at +153
   gems (64%), and it beats every older sibling by +200 locally. On the ladder, opponent-adjusted, v58 is not better
   than v57 (residual -0.001 ± 0.051 vs +0.047 ± 0.027). Self-play games are brawls (both sides die 16 times);
   the ladder teams that beat us die 7 times.
2. **Discipline gets punished in self-play.** Retreat, burst-danger, threat-aware travel, team-hold and v58's
   survive package were built from ladder evidence and each switched off after a self-play screen. A reckless mirror
   keeps farming while we back off, so careful play costs tempo in self-play but not on the ladder.
3. **The bench does not play the ladder's maps.** Development used 28 maps; the ladder rotates 67. 80 of v58's 127
   ladder losses were on maps the development set never contains (galaxy, the_pond, dunes, the_line, guardians,
   adgato_gemcombat5 and others). The other 39 local maps were reserved as once-only holdouts.
4. **One change at a time cannot see real effects.** A 224-game screen has a map-clustered interval of about ±100
   gems. In v58, 20 screens and 13 incremental steps all ended with intervals spanning zero, and most were discarded.
   Changes that only work together (gear plus disengage plus banking) were never tested together.
5. **There was no feedback from the ladder into the gate.** Nothing compared what the bench predicted with what a
   release actually did, so the miscalibration went unnoticed across releases.

## Fixes

| Problem | Fix | Tool |
|---|---|---|
| Gate opponent is one sibling | Pooled gauntlet against v58, v57, v55 and v54; report the pooled margin and the worst opponent | `tools/gauntlet.sh`, `tools/gauntlet_report.py` |
| 28 old maps | The gauntlet plays all 70 maps in `maps/local-benchmarks` by default (`MAPS28=1` for the old set) | `tools/gauntlet.sh` |
| Mechanism blindness | Every gauntlet line reports deaths, kills, gems lost on death and gold for both sides, the quantities that separate ladder wins from losses | `tools/gauntlet_report.py` |
| No ladder feedback | Opponent-adjusted ladder residual per live version; run it after every release | `tools/replay/ladder_calibration.py` |
| Local bench is not the truth | Paired ladder A/B: replay the 24 match-group sets other teams ran against v58 (same opponent bot via `--source-group`, same maps and sides) and compare with v58's 149/225 on them | `tools/replay/ladder_ab.py`, `V59_LADDER_AB_PLAN.json` |
| Loss analysis by hand | One-command reviews from summaries and replays | `tools/replay/fetch_v59_review.py`, `v59_loss_review.py`, `fight_review.mjs`, `fight_report.py` |
| One knob at a time | Variants are built with `tools/make_variant.py` and screened as packages; a package is kept when the pooled gauntlet does not regress and its mechanism moves the right way | `tools/make_variant.py` |

## New release rule

1. **Local safety net.** The full-pool gauntlet must show no faults, fuel within 10% of the parent, a pooled
   margin no worse than the parent's minus 30, and no opponent worse than -100. This catches breakage; it is not
   evidence of ladder strength.
2. **Mechanism.** The change must move the ladder-loss quantity it targets (deaths, gems lost on death, gold) in
   the right direction locally.
3. **Ladder A/B.** After submission (the user's decision), queue the paired sets (`ladder_ab.py queue --yes`, about
   45 groups for 225 games). Keep the version only if it is at least as good as v58 on the same sets. Revert with
   `cambc submissions activate <previous>` otherwise.
4. **Calibrate.** After a day live, run `ladder_calibration.py` and record the residual next to the local prediction.
