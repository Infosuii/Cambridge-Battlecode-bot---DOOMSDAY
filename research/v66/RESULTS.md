# v66: results (2026-10-27)

**Decision: v66 is not released.** Neither candidate beat v65 against the top 12 (v66a -23 +/- 46, v66b -17 +/- 54 gems
per game, paired). v65 (platform 65) is re-pinned as the live version.

Inputs: `research/v62/BIG_STRATEGIES.md` and `research/top-losses-20261026/README.md` (the 502-loss audit).
Base: **v65** (platform 65). It is v58 plus a 48-value `A2_KNOBS` vector (`bots/v65/CHANGES.md`), not v61 as its file
name suggests. A first v66 built on v61 was discarded (kept at `artifacts/tmp/v66-on-v61`).

## v65 is the best version measured against the top 12

Same 24 match groups (`research/v59/duel_top1.json`: 12 top teams x 2 groups x 5 maps, fixed maps and sides):

| Arm | Platform | Wins / 120 | Mean gem margin |
|---|---:|---:|---:|
| v60 | 59 | 15 | -465 |
| v61 | 60 | 21 | -462 |
| v62c | 63 | 15 | -494 |
| **v65** | 65 | **24** | **-386** |
| v66a | 66 | 20 | -409 |
| v66b | 67 | 23 | -403 |

v65 minus v61, paired: +76 +/- 52 gems. Against the top 12, v65 dies 14.9 times per game against their 5.1 and kills
3.6 against 13.6. Gold is 3,564 against 6,511 (45 cached summaries).

## What was built, mapped to the audit's six steps

| Audit step | v66 switch | Local, vs v65 (560 games) | Ladder |
|---|---|---:|---|
| 1. Earlier useful stats | `V66_ITEMS 1`: the winners' engine-2 opening per hero, then Bruiser stacks | **+33** | in v66a/v66b |
| 1. (meta compiler) | `V66_ITEMS 2`: same, read from the generated `meta_tables.h` | -81 (and -20 vs v66a) | not sent |
| 2. Fight admission | `V66_LEAVE 1`: leave a losing fight at 0.75/0.5/0.3 health (outnumbered/even/ahead) | -70 | |
| 2. | `V66_LEAVE` at 0.6/0.35/0.2 | -18 | v66b: -17 +/- 54 vs v65 |
| 2. | `V66_ENGAGE 1`: walk in only above 0.8 health with equal numbers | **-262** (rejected) | |
| 3. Progress watchdog | `V66_WATCHDOG 1` | -126 vs v61, with `V59_ALONE` (rejected; off) | |
| 5. Target selection | `V66_TARGET 1`: closest enemy, lowest health on ties | **+52** (with items) | v66a: -23 +/- 46 vs v65 |
| 4, 6 | gate/bank plans; camp-death, late-race and fuel review | not started | |

v66a = items + closest target. v66b = v66a + the softer leave rule. Local runs:
`artifacts/evaluations/gauntlet-r2-*`; ablation builds come from `tools/make_variant.py` with the switches above.

**The local gain did not transfer:** v66a was +52 locally and -23 +/- 46 against v65 on the ladder. The local bench plays
our own bots, whose fighting is the weakness, so fight changes are judged against the wrong opponent. That is the
same failure as v58 (+153 locally, nothing on the ladder).

## Meta compiler (BIG_STRATEGIES option A), first working slice

- `tools/meta/crawl.py`: the current top 12, their ranked games of the last 24 hours, kept when both sides are
  top 12; native summaries downloaded. The first crawl found **3,378 top-vs-top games**; 600 summaries were downloaded
  (`artifacts/local-only/meta/20261027`).
- `tools/meta/compile.py`: writes `bots/v66/src/meta_tables.h` (per-hero winning opening and stack ratio; draft games
  and wins), plus the report `research/v66/META_TABLES.md`.
- Finding: in top-vs-top games **Cassi & Issac win 62%** (878 games). Every other pick is 39-51%.
- The generated item table lost locally to the hand-written one. Before it can replace the hand table, it needs
  stack proportions by role (it reduced most heroes to 1:1 health) and a check that each opening fits the inventory.

## What this says about the next step

Single heuristic switches in a 7,000-line bot have now been tried across v59-v66 without moving the top-12 margin by
more than its noise (about +/-50). Two things limit progress:

1. **No local opponent that fights like a top team.** Every local verdict on a fight rule is unreliable, and the
   ladder gives one 120-game verdict per hour. Building a local proxy opponent is the highest-leverage fix. One way:
   imitate top-team decisions (engage, target, leave) from the decoded replays the meta crawler now fetches. Then
   check the proxy's ladder ranking before trusting it.
2. **The fight controller itself.** We lose 13.6 kills to 3.6. BIG_STRATEGIES section 7 (one controller scoring
   tile x action x target from game constants, with the rulebook on top) has not been built. It is a multi-day
   rewrite and needs (1) to be tuned against something other than ourselves.
