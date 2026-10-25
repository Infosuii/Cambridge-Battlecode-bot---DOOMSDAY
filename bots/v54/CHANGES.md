# v54: coordinated economy (crew jobs, item milestones, lead lock, teleport logistics)

Built 2026-10-25 by Claude Code from frozen `bots/v53` (live platform version 53; its files are verified unchanged).
**Not submitted.** Full audit trail: `artifacts/claude_ops/V54_BUILD_LOG.md`; hashes, gate and research numbers:
`artifacts/claude_ops/V54_RELEASE.json`. Source SHA-256 (sorted name + bytes of `src/`):
`b8a7b7b58dd03c25684af915aff68fd877d98289c656461e93ded97cdd1d24b9`.

## Why (actor-level evidence, 136 decoded ladder replays)

* In v53 losses our champions attack camps 20% of alive rounds against the winners' 25%, sit beside dead camps
  waiting for respawns three times as much (12,770 vs 4,041 champion-rounds by R500 over the v53 games), and earn
  144 vs 267 capture gold per champion by R250. The gap opens before any deaths.
* The large multi-champion groups that decide those maps were almost never taken: opponents bank 196 gems/game from
  20+-gem rewards by R500, we 110. Cause, found by logging: the staging clock for a job that needs helpers started
  when the walk began, so every job beyond ~7 tiles lapsed before helpers arrived and was banned for 60 rounds
  (concentrated-wealth: all five champions gave up the centre group at R8, 40 tiles out; 38 lapses by R500).
  Presence was also counted only from personal vision.
* Every winning lineup buys a Treasure emblem first and stacks Bruiser emblems; v53 never bought Treasure (first
  purchase R148 vs R72). Winners also reuse fixed 3-tile teleport shortcuts; v53 never bought a crystal.
* Redundant capture occupancy, a planning hypothesis, is not a problem for us (shared-capture fraction 0).

## Mechanisms (each switchable in `src/common.h`)

1. **Crew jobs (M1)** `V54_STAGE_ARRIVE`, `V54_STAGE_WALK` 60, `V54_ONSITE`, `V54_STAGE_HELPED` 20. Staging starts at
   the ring; on-site claim codes (64 + group, maps ≤ 48 groups) let hidden teammates count as present; a call that
   enough teammates have claimed gets the walk and a 20-turn wait, an unanswered call lapses as before. Claims are
   decoded once per shared-memory change into a cache.
2. **Item milestones (M2)** `V54_ITEMS` 3. Treasure as the first emblem (same stats as any emblem; its passive adds 20%
   to all later gold), then Jungle and Durability, then Bruiser stacks (7 shards of stats per 150 gold) instead of
   Power (6). Role variants for Vesper, Prism, Heart of Ruin and casters.
3. **Lead lock (M3)** `V54_HOLD`, `V54_HOLD_LEAD` 160. On sole-gem maps, with a banked lead of one cycle, one
   empty-bag champion holds a spawn tile of the sole gem group, which delays its respawn (engine-checked: 120 vs 65
   rounds); teammates wait beside it.
4. **Teleport logistics (M4)** `V54_TP`, `V54_TP_GAIN` 8. Carry one 10-gold crystal; where a legal hop within 3 tiles
   saves at least 8 turns of walking net of the 3-turn channel, take it (no visible enemy, outside awake-camp reach).

All new logic runs once per call/turn or in cold paths; none is inside per-group or per-camp loops.

## Measured against v53 (bench2: 28 development maps × both sides × NOVA_SEED; zero faults in every run)

| Test | Games | Record | Win rate | Mean gem margin | Fuel-exhausted turns (v54 / v53) |
|---|---:|---:|---:|---:|---:|
| Development, seeds 1-3 (gate run) | 168 | 109-59 | 0.649 | +149.0 | 259 / 278 |
| Development, seeds 1-12 (research) | 672 | 443-229 | 0.659 | +187.1 | 955 / 1018 |
| v53 opponent built with seeds 2-7 (v54 seed 1) | 336 | 216-120 | 0.643 | +173.6 | |
| **Release holdout, 12 final maps, seeds 1-3 (one pass, after freezing)** | 72 | 41-31 | 0.569 | +30.8 | 20 / 18 |

Opponent portfolio, 28 maps × 2 sides, seed 1: v48 41-15 (+265.6), v50 40-16 (+272.5), v51 38-18 (+207.1), v52 34-22
(+149.6), heuristic-v1 40-16 (+199.3); total 193/280 (68.9%). The same lineage is not a diverse league.

Gate (ops/HANDOFF.md §4): (a) declared target maps, seeds 1-3, both sides: concentrated-wealth 6/6 (worst +679),
fragment 6/6 (+502), stampede 6/6 (+200), swirl 6/6 (+439), big-world 6/6 (+103) — pass; (b) 0.649 ≥ 0.47 and +149.0
≥ −30 — pass; (c) holdout aggregate 41/72, +30.8 (v53's release check against v52: 39/72, +5.3) — pass on the
aggregate interpretation used for v52 and v53.

Development per map, seeds 1-3 (A side, B side): wins on fragment, stampede, swirl, big-world, concentrated-wealth
(all 6/6); 5/6 great-wall, islands, broken-curve, yellow-brick-road; losses to disclose: gem-fields 1/6, quadrants
2/6, rushbait-v2 2/6, gold-rush 2/6, boss-battle 3/6 (side B 0/3), contest, eight, elkring, lost-world, rows,
starfish, starvation 3/6. Full strings: `artifacts/claude_ops/results/v54final-dev.txt`; 12-seed table
`results/v54h-tp8-maps.txt`.

Holdout per map (seeds 1-3, A/B): ambush 5/6, the-farm 5/6, packs 5/6, elk-arena 4/6, pilgrimage 4/6, interlock 3/6,
corners 3/6, monolith 3/6, expanse 3/6, lanes 3/6, fracture 2/6, **hooks 1/6** (five losses by 968-1012: v54 loses
25-31 champions by R1000 there against v53's 12-20; v53 itself was 2/6 on hooks against v52 with ±1012 swings).

Economy over the 168 gate games, by R500 (v54 / v53 means): capture gold per champion 341 / 311, gems from 20+-gem
captures 149 / 135, respawn-wait champion-rounds 133 / 147, deaths 5.4 / 5.4. boss_battle now banks: in the gate
run v54 banked 49-758 gems in its three side-A wins; the M1-M4 build with hop gain 5 banked in 8 of 12 games over
seeds 1-6 (up to 1,383), where M1-only and v53-era games were mostly 0-0 tiebreaks.

## Ablations (336 games each vs v53, seeds 1-6)

M1 only +72.3 (191-145); M1 + M2 +148.1 (206-130); M1 + Treasure only +54.8; M1 + Bruiser only +64.2; M2 without M1
+82.8; M1-M3 +154.5; M1-M4 with hop gain 5 +192.9 (12 seeds: +176.1), without teleports over 12 seeds +149.3,
gain 8 over 12 seeds +187.1. Treasure and Bruiser help only together; crew coordination adds about +65 on top.

## Research targets (V54_PLAN §8), honestly

* ≥60% development wins and ≥+100 mean gems against v53: **met** (64.9%/+149 gate run; 65.9%/+187 over 12 seeds).
* Useful boss_battle banking: **partly met** — real banking in most games, but seeds 1-3 side B lost all three.
* Equipment ratios ≥0.9 against meow / Hidden Altar Keepers: **not measurable** locally (no opponent source);
  unverified until ladder games.
* Less unproductive time: respawn waits −10%; most of the 3× gap to the winners **remains**.
* Robustness across race/brawl/denial/mobility/control opponents: **not met** — only our own lineage is available;
  brawl/death-spiral maps (hooks, eight, quadrants, gold-rush) are v54's weakest.
* Compute: fewer fuel-exhausted turns than v53 and zero faults; no tail-fuel profile (the engine's `.fuel` file
  format is undocumented and was not used).

## Rejected / not pursued

Naive spawn hold (idle holder lost 0-640; mechanic confirmed only). Crew fix without on-site presence (v54a) and with
unconditional long staging (v54b) — superseded. Teleport hop gain 5 — replaced by 8. Re-enabling squads, zones,
gold funnel or lower wait weights — previously rejected levers, not retried. See the build log for the full ledger.

## Risks and release recommendation

Risks: (1) all evidence is against our own lineage; the ladder field may punish the Treasure-first opening early
(PvP strength is unchanged in stats, but Durability's damage reduction arrives one emblem later); (2) PvP death
spirals on brawl maps (hooks holdout 1/6); (3) per-map results swing by up to ±4/12 from trajectory divergence, so
single-map claims are weak; (4) the 12 holdout maps were exposed in earlier releases.

**Recommendation: release v54** as the next platform version after the user's go-ahead. It passes the original gate,
meets the main development research target by a wide margin on 672 paired games and 336 cross-seed games, beats
every lineage opponent, and does not regress the holdout aggregate. After submission, track ranked/unranked
results and queue groups against meow and Hidden Altar Keepers on concentrated-wealth, fragment, swirl, elkring and
boss-battle; the next development target is PvP survival on brawl maps.

## Reproduce

```bash
export PY="<python 3.12>"; R="$PWD"   # repo root, with the environment from ops/SETUP.md
bash artifacts/claude_ops/bench2.sh "$R/bots/v54" "$R/bots/v53" "$R/artifacts/evaluations/v54final-dev"
HOLDOUT=1 MAPS_OVERRIDE="00ambush 00corners 00expanse 00interlock 00lanes 00monolith 00packs 00pilgrimage 01elk-arena 01fracture 01hooks 01the-farm" \
  bash artifacts/claude_ops/bench2.sh "$R/bots/v54" "$R/bots/v53" "$R/artifacts/evaluations/v54final-holdout"
python tools/bench_maps.py artifacts/evaluations/v54final-dev        # per-map table
python tools/replay/ledger_bench.py artifacts/evaluations/v54final-dev  # economy ledger
```
