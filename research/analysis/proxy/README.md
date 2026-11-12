# Proxy opponent: a local stand-in for the top teams (2026-10-27)

Goal: a local opponent built from the top teams' own games, so a change to our bot can be judged against something
that plays like them instead of against our own lineage (self-play has repeatedly failed to predict the ladder: v58
+153 locally and nothing on the ladder; v66a +52 locally and -23 +/- 46 against v65 on the ladder).

**Status: built and measured; it does not predict the ladder better than self-play.** It copies what can be copied
exactly (draft, items, the recall trick) but fights and farms with v65's code, so v65 beats it by 250 gems while the
real top teams beat v65 by 386. See "Validation" and "Limits". Use it as a second opinion next to self-play, never
as a release gate.

## What it is

`bots/proxy` (see `bots/proxy/CHANGES.md`) is v65's code (via `bots/v66` with all v66 rules off) that imitates one
top team at a time, `PROXY_TEAM` = the team's row in the generated `src/proxy_tables.h`:

| Imitated | Source | Fidelity checked |
|---|---|---|
| Draft: the team's lineup on each map | 8,470 engine-2 games of the 12 duel-plan teams (meta crawl + their games against us); maps identified in-bot by a hash of size, draft size and camp layout (`research/proxy/map_keys.json`: 70 pool maps, all distinct, both sides agree) | 119 of 120 duel games: the proxy drafts exactly the lineup the real team used there |
| Items: the team's purchase milestones per hero | 1,470 native summaries | 356 of 356 hero openings follow the table (the teams themselves vary: the real team's first four milestones were reproduced in 175 of 343) |
| Perma-recall (Mite, NEETCoders, Trzy Kwaterki, willow best girl, print dont int start a recall at the end of 89-97% of their turns and cancel it next turn) | replay step kinds 16 (cancel) / 11 (recall) / 8 (end turn) | Locally it changes v65's margin by -33 +/- 40 against those teams: not what makes them strong |
| Fight knobs | fitted (below) | |

Everything else (farming, banking, movement, fight search) is v65's.

## How the top teams fight (same 120 ladder games, them vs v65)

From `tools/proxy/fight_style.mjs` (per champion round in contact) and `style_report.py`; full table in
`style_ladder.json`.

| Measure | Top teams vs v65 | v65 vs top teams | Top vs top |
|---|---:|---:|---:|
| Deaths per game | 6.6 | 14.3 | 9.5 |
| Back off in contact (step away, enemy within 5) | 0.263 | 0.389 | 0.325 |
| Walk in (enemy 2-6 away, none in range) | 0.380 | 0.301 | 0.354 |
| Another ally hit the same enemy (focus) | 0.319 | 0.249 | 0.281 |
| Alone (no ally within 8) in contact | 0.184 | 0.232 | 0.212 |
| Contact entry with more friends than foes | 0.64 | 0.55 | 0.61 |
| Off spawn below 50% health | 0.086 | 0.139 | 0.094 |
| Health when arriving home | 0.63 | 0.57 | 0.63 |
| Target choice (lowest health fraction / closest, 2+ enemies in reach) | 0.60 / 0.85 | 0.64 / 0.85 | 0.63 / 0.87 |

Economy in the same games (native summaries): they collect 1,110 gems a game against our 785, bank 911 against 525
(82% of what they collect against our 67%), earn 6,794 gold against 4,303 and deal 110k camp damage against 85k. The
gap is fighting and farming, and the proxy imitates neither farming nor fight execution.

## Fit (tools/proxy/fit_style.py)

Coordinate search over five knobs; each candidate plays the 120 duel games against v65 and is scored on how close
its play against v65 is to the top teams' play against v65 (margin, both sides' deaths, back-off, walk-in, alone,
focus, deaths after contact). Log: `artifacts/evaluations/proxy-fit/f1/fit_log.jsonl` (23 candidates).

| Candidate | v65 margin vs proxy* | Proxy deaths | Back off | Alone | Focus | Loss |
|---|---:|---:|---:|---:|---:|---:|
| Target: top teams vs v65 | -386 | 6.6 | 0.263 | 0.184 | 0.319 | 0 |
| P0 (draft, items, recall; v65 fight) | +300 | 15.3 | 0.310 | 0.296 | 0.257 | 148 |
| + `APEX_COHESION 0.5`, `APEX_RETREAT_HP 0.25` | +254 | 13.7 | 0.308 | 0.243 | 0.267 | 115 |
| **F1**: + `NOVA_TD_LIFE1 15` (now the default in `bots/proxy`) | **+221** | 13.5 | 0.307 | 0.246 | 0.268 | **105** |
| `NOVA_FIGHT2` 6 or 7 (strength gate / regroup) | +367 to +449 | 15.5-16.5 | | | | 160-200 |

\* seed 1; positive = v65 wins. `APEX_AGGRESSION` 1.2 / 1.6 / 2.2 gave identical games: the knob is dead in v65's
path (the search verdict decides). The fit closes about 80 of the 686 gems between the proxy and the top teams and
moves the fight style only slightly: these knobs cannot make v65's code fight like them.

## Validation (tools/proxy/compare.py)

Every arm of the ladder duel (`research/proxy/ladder_arms.json`: v60, v61, v62c, v65, v66a, v66b, 120 games each
against the top 12) replays the same schedule locally (`tools/proxy/local_duel.py`), against the proxy (each game
against the proxy of the team it met) and, as the control, against v65 (self-play).

Seeds: F1 two, P0 and self-play one (`research/proxy/VALIDATION.md` has every arm, team and pair).

| Opponent | Team difficulty r (12 teams) | Arm rank corr. | Arm pairs agreeing with the ladder | Per-game r |
|---|---:|---:|---:|---:|
| Proxy F1 (fitted) | +0.01 | +0.37 | 10/15 | +0.07 |
| Proxy P0 (unfitted) | -0.09 | +0.54 | 11/15 | -0.03 |
| Self-play against v65 | -0.44 | +0.43 | 9/15 | -0.01 |

**No opponent tells the arms apart better than the others; all are within noise.** The decisive questions go the wrong
way for F1 and self-play alike: both put v66a and v66b above v65 (+44, +33; ladder -23, -17) and v65 below v61
(ladder +76). P0 got those signs right, but on 1 seed and with the same overall agreement. None of them knows which
teams are hard: on the ladder Fish (-732) and prism best girl (-631) are the hardest; locally the hardest proxies are
hello and willow best girl.

One game per run is pathological on every opponent: 00vault with our side b, where one side runs out of fuel almost
every turn (also v65 against itself): a v65-lineage fuel problem on that map, not a proxy artefact.

## Limits

- The ladder ground truth is weak: one game per (arm, group, slot), and the six arms differ by at most ~110 gems
  with paired SEs of ~50; only 1 of 15 arm pairs is decided at 2 SE. No proxy can be shown to agree much better
  than another with these data.
- A single local game's margin moves with SD ~470 between seeds (the bots' only randomness), about as much as
  on the ladder, so per-game agreement is capped near 0.3 even for a perfect proxy.
- The proxy is v65 underneath: it is far weaker than the teams it imitates (v65 beats it; the real teams beat v65 by
  386) and it does not know what makes Fish or prism best girl harder than the others (team-difficulty r about 0).
  A proxy that matched them in strength would itself be a top-team-strength bot.

## Next steps

1. Ground truth with power: predict, then measure, one new version on the ladder (an out-of-sample test), or
   duel fewer arms with more groups each. Each ladder arm means about an hour with that version live.
2. Farming is half the gap and the proxy copies none of it: decode the top teams' camp routes and banking from the
   same replays (who farms which group when, carry sizes) before more fight work.
3. Cohesion and earlier retreat made the proxy ~80 gems stronger against v65 (fit). They are candidate changes for our
   own bot; test them against the proxy and self-play together.

## Reproduce

```
python tools/meta/crawl.py --out artifacts/local-only/meta/<stamp>
python tools/meta/crawl.py --team d559d741-ac53-411e-bc4e-36b8f3d12d5a --hours 48 --out artifacts/local-only/meta/<stamp>-printdontint
python tools/proxy/fetch.py arms --plan research/v59/duel_top1.json --out research/proxy/ladder_arms.json
python tools/proxy/fetch.py replays --arms research/proxy/ladder_arms.json --arm v65 --crawl <crawl> --out artifacts/local-only/proxy/replays
NFS_REPLAY_ENGINE=2.0.0 node tools/proxy/fight_style.mjs artifacts/local-only/proxy/style-ladder.jsonl artifacts/local-only/proxy/replays
python tools/proxy/style_report.py --style artifacts/local-only/proxy/style-ladder.jsonl --index artifacts/local-only/proxy/replays/index.json --json research/proxy/style_ladder.json
python tools/proxy/compile_proxy.py mapkeys --out research/proxy/map_keys.json
python tools/proxy/compile_proxy.py tables --crawl <crawl> <crawl>-printdontint --arms research/proxy/ladder_arms.json --keys research/proxy/map_keys.json --out bots/proxy/src/proxy_tables.h --report research/proxy/TABLES.md
python tools/proxy/fit_style.py --space research/proxy/fit_space.json --out artifacts/evaluations/proxy-fit/<run>
python tools/proxy/local_duel.py --plan research/v59/duel_top1.json --bot bots/<arm> --name <arm> --proxy bots/proxy --per-team --seeds 1 2 --out artifacts/evaluations/proxy-duel/<run>-<arm>
python tools/proxy/compare.py --ladder research/proxy/ladder_arms.json --run proxy=<dirs> --run self-play=<dirs>
```
Maps: `maps/local-benchmarks` is byte-identical to the current platform pool (all 70 checked on 2026-10-27).
