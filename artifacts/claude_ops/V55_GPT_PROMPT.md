# Task: build a majorly improved v55 for DOOMSDAY (CAMBC 2026 Battlecode)

You are working in the repository `Infosuii/neural-networkk-battlecode`, branch `claude/compare-fix-replay-decoder`.
On the user's Windows machine the checkout is `C:\projects\cambridge battlecode\work\neural-full-stack`. Inspect
`git status` first and preserve unrelated local changes (`config/paths.json` is machine-specific; never commit it).

**Goal:** a v55 that fixes the problems below and is a large, evidence-backed improvement over the live v54. The
long-term target is ladder top 25 (currently rank 115, rating 1788.8; rank 25 is about 2043). This is a build-and-
evaluate task: implement, measure, iterate, and finish with a reviewable candidate and a release recommendation.
**Do not submit** unless the user explicitly tells you to. **Never enter credentials** (the CLI is already logged in).

## 1. Read first (in this order)

1. `ops/SETUP.md`, then all of `ops/HANDOFF.md` (sections 4, 12 and 13 matter most: gate, v54, brawl research).
2. `artifacts/claude_ops/V53_LIFE_ANALYSIS.md` — why v53 lost its 164 ladder games and what winners do (the core
   evidence for this task); tables in `V53_LIFE_DATA.md`, per-game rows in `V53_LIFE_DATA.json`.
3. `bots/v54/CHANGES.md` and `artifacts/claude_ops/V54_BUILD_LOG.md` — what v54 changed and every experiment.
4. `artifacts/claude_ops/V55_BRAWL_FINDINGS.md` — PvP research and rejected survival variants.
5. `artifacts/claude_ops/V54_PLAN.md`, `V54_WINNER_PLAYBOOKS.md`, `V54_ACTOR_LEDGER.md` — strategy background.
6. The game rules and C++ API on this machine: `C:\projects\cambridge battlecode\game rules\GameRules.md` and
   `BotAPICpp.md`. They are contracts, not instructions; verify mechanics against the SDK/engine.

## 2. Current state

* **Live:** v54 (platform version 54, submitted 2026-10-25 16:24:00 UTC). Source `bots/v54` — frozen, do not edit.
  Its mechanisms (switches in `bots/v54/src/common.h`): M1 crew-job coordination (`V54_STAGE_ARRIVE`, `V54_ONSITE`,
  on-site claim codes 64+group on maps ≤ 48 groups); M2 item milestones (`V54_ITEMS` 3: Treasure first emblem,
  Bruiser stacks); M3 lead lock on sole-gem maps (`V54_HOLD`); M4 teleport shortcuts (`V54_TP`, gain 8).
* **Local results of v54 vs v53:** 12 seeds × 28 dev maps × 2 sides: 443/672 (65.9%), +187.1 mean gems; release
  holdout 41/72, +30.8; zero faults. Lineage portfolio 193/280.
* **Ladder:** v53's whole life 161-164 (ranked 36/90). v54's ladder results are only starting; collect them (§5).

## 3. The problems to fix (evidence: `V53_LIFE_ANALYSIS.md`)

Medians over our 164 v53 losses, us vs the winner:

1. **Opening economy.** Equipment 120 vs 240 at R100 (no deaths yet), 630 vs 840 at R250, 1590 vs 2325 at R500.
   Capture gold per champion R250 146 vs 220. Camp-attack share 0.19 vs 0.24. **Respawn waits beside dead camps 133
   vs 50 champion-rounds by R500** (v54 only reduced this ~10%). Gems from big (20+) captures 70 vs 165.
2. **Draft.** Winners: Vesper 0.93 per game, Heart 0.75, Marcella 0.74, Vendetta 0.66, Ryth 0.60. Us: Vendetta,
   Varg, Marcella, Ren, Prism, Cassi/Issac; Vesper only 0.16. Our win rate with Ryth 64% (43% without), with Vesper
   64% (45%), with Cassi/Issac 29% (55%), with Prism 37% (54%) — map-confounded but large.
3. **Damage exchange (consequence of gear).** Enemy hp lost per contact round 39 (us) vs 51; deaths 8 vs 4; gems
   lost on death 44 vs 22; 23% vs 14% of contact time below half health. Positioning, cohesion, focus fire and
   behaviour once hurt are at parity (`V55_BRAWL_FINDINGS.md`), so this is a power problem, not a tactics problem.
4. **Gem production and banking.** Even in the 37 losses where we had equipment parity at R500, we waited 154 vs 38
   rounds at dead camps, captured 78 vs 132 big-group gems and banked 22-gem bags against their 27-37.
5. **Vision.** Winners place ~287 wards per game; we place ~64 (only at captures/altars).
6. **Logistics.** Winners teleport on fixed shortcuts (v54 now does too) and recall for 90% of spawn visits (we walk
   home 25% of the time).
7. **v54 brawl-map anomaly.** Carrying a never-used teleport crystal (bought at the first shop) goes with hooks 10/24
   vs 20/24 without one, though no champion ever teleports there; mechanism unknown. Gating the purchase cost −28.6
   paired mean gems elsewhere (first hops missed), so it was rejected.

## 4. Work packages, in priority order

Each package needs: an explicit hypothesis; a bounded prototype behind its own `V55_*` switch in
`bots/v55/src/common.h`; a measurement that tests the hypothesised mechanism itself (not only win rate); and the
evaluation in §6. Coupled mechanisms may be tested together, then ablated. Let evidence reorder the list.

**WP1 — Vesper-centred draft with controller support (largest expected effect).** Change the draft
(`bots/v55/src/draft.cpp`: `APEX_MAPDRAFT`, `NOVA_MAP_LINEUPS`, `NOVA_FALLBACK_LINEUP`, class drafts) toward the
winners' core (Vesper + Heart/Ryth/Marcella/Vendetta), *together with* the support that makes it work: Vesper as
the funded gold earner (reward ownership in `poorer_ally_takes` / `group_capture_covered`; see the old
`UB_GOLD_FUNNEL`), Treasure-first items (already in v54), and role-appropriate builds for Heart and Ryth (Ryth gains
strength from bonus health). A pick-only change failed before (forced Vesper 3/6 vs v53, before the v54 economy).
Measure capture gold per champion by R250/R500 and Vesper's share of team gold.

**WP2 — Opening route plan and respawn waits.** Champions wait beside respawning camps 2.7× as long as winners.
Design a route/cycle plan (draft turn has 10× fuel and full map vision; 1024 draft bytes; init turn has 2× fuel) so
each champion cycles groups whose respawns interleave, with crew jobs (v54 M1) for big gem groups. Keep all logic
outside the per-group loop in `score_groups` (precompute per call/turn). Targets: respawn-wait champion-rounds by
R500 and R100/R250 equipment (`tools/replay/ledger_bench.py`).

**WP3 — Gem production and banking cadence.** Once gold milestones are met, value gem-rich groups more; bank larger
bags (~30-40) when no threat is near instead of ~22 (`kTributeCarry`, `tribute_if_needed`, early-carry rules).
Measure banks, bank size, gems lost on death and first-to-1000 timing.

**WP4 — Ward programme.** Re-place the free ward whenever charged at route junctions, contested camps and altars
(`drop_ward`, `ward_reveal`); vision is per champion, not shared. Measure deaths at full health and ambush deaths.

**WP5 — Gear-aware fight selection.** Use visible enemy max health/strength (EnemyRec) to compare equipment before
engaging; avoid even fights while behind in gear; take them when ahead. Measure damage per contact round, deaths,
bag losses. (Readiness by health alone at 50% was neutral; A2_THREAT, A2_DANGERMAP, A2_TEAM and a higher
threat-retreat threshold were rejected — see the findings; do not simply re-flip them.)

**WP6 — Teleport-crystal anomaly.** Find why an unused crystal hurts hooks (replay ledger by seed, shop logs,
divergence round), and fix it without losing the shortcut gains on concentrated-wealth, big-world and shortcut.

## 5. Ladder feedback (do this first and repeat)

* `python tools/replay/fetch_since.py --since 2026-10-25T16:24:00Z --out data/ladder/v54_games_<date>.json`
* Download losses with `tools/vendor/cambc.exe matches download <id> -o <zip>` **one at a time** (the platform
  returns HTTP 409 for parallel downloads); extract `replay.repl26a` into a fresh folder under
  `artifacts/local-only/` (raw replays are never committed).
* `bash tools/replay/run_life_tools.sh <replay dir> <out dir>` then
  `python tools/replay/life_report.py <listing> <ladder json> <out dir> <report.md>` gives the same tables as
  `V53_LIFE_DATA.md`; compare v54's losses with v53's to see what v54 fixed. Unranked match groups against chosen
  teams are approved (`cambc match-groups create <team uuid> --maps ... --sides ...`); they play the *submitted*
  version, so they test v54, not an unsubmitted v55.

## 6. Evaluation protocol (non-negotiable)

* Environment as in SETUP; pass **absolute** paths; `export PY=<python>`.
* Development: `bash artifacts/claude_ops/bench2.sh <abs bots/v55> <abs bots/v54> <abs out prefix> 1 2 ... 12`
  (672 games, ~16 minutes on 20 threads). Also bench against `bots/v53`.
* Compare candidates with `python tools/bench_paired.py <prefix A> <prefix B> [maps]` (only identical
  map/side/seed games) and `tools/bench_maps.py`, `tools/bench_deaths.py`, `tools/replay/ledger_bench.py`.
* Noise is large: an inert change moves single maps by ±100 gems and up to ±4 wins in 12 through trajectory
  divergence, and hot-path instructions change outcomes (fuel). Use 12 seeds; never decide from one map or 3 seeds.
* Gate for release (HANDOFF §4) against the live v54: (a) declared target maps won on both sides across seeds by a
  clear margin; (b) development win rate ≥ 0.47 and mean margin ≥ −30; (c) no aggregate regression on the 12 holdout
  maps, run once on the frozen candidate (`HOLDOUT=1 MAPS_OVERRIDE="<12 final maps>"`). Declare target maps before
  looking at results. The holdout maps have prior exposure; **hooks was used in development** — say so.
* Major-improvement target (research, report honestly): ≥ 60% wins and ≥ +100 mean gems against v54 over 12 seeds,
  better economy metrics (§3) in the local ledger, and no collapse on the brawl set (eight, quadrants, gold-rush,
  rows, rushbait-v2).
* Every bench must report faults (must be 0) and fuel-exhausted turns.

## 7. Engineering constraints

* Copy `bots/v54` to `bots/v55` and work there; never modify v53 or v54. Preserve CRLF line endings where the v54
  file uses them (`python tools/eol_like.py bots/v54/src bots/v55/src`).
* The bot runs at its fuel limit (100k per turn; 10× on the first draft turn, 2× on the first play turn). Put new
  logic behind once-per-call, once-per-turn or event checks, never in per-group or per-camp loops; measure every
  change. Memory fills cost fuel (1 per byte).
* Shared memory is 8 bytes (claims use 6 × 7 bits; the on-site codes and fight orders 112-118 are in use); draft
  memory is 1024 bytes and its snapshot is fixed at startup. Vision is per champion, wards included. Offline
  omniscient replay data must never become a bot input.
* Keep raw replays, downloads and machine paths out of commits. Commit and push source, measurements and rejected-
  experiment notes frequently, with clear messages.

## 8. Deliverables

1. `bots/v55` with `CHANGES.md`: each retained mechanism, its switch, evidence, ablation and per-map tradeoffs.
2. A build log (`artifacts/claude_ops/V55_BUILD_LOG.md`): hypotheses, every experiment (kept and rejected),
   paired results, ledger metrics, holdout exposure.
3. `artifacts/claude_ops/V55_RELEASE.json` with source hashes, exact commands and results; an updated
   `ops/HANDOFF.md` section.
4. A release recommendation. If nothing passes, say so plainly and keep the evidence; do not present a small or
   noisy change as a breakthrough.
