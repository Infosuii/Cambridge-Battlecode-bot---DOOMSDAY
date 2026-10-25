# V54 build log: actor-level loss explanation, mechanisms, experiments

Claude Code, 2026-10-25. Implementation authorised by the user's v54 build request (the analysis-only wording in
`V54_PLAN.md` applied to the preceding Codex session). Base: frozen `bots/v53` (unchanged). Candidate: `bots/v54`.
Opponent for every bench below: `bots/v53` (live platform version 53). No credentials entered; nothing submitted.

All replay analysis is offline and omniscient (pinned engine wasm via `tools/replay/engine.mjs`); none of it feeds
a bot input.

## 1. Representative losses explained at actor level

Tools (committed): `tools/replay/actor_ledger.mjs` (per-champion time allocation, capture income, shared captures,
purchases, emblem rounds), `ledger_report.py` (cohorts → `V54_ACTOR_LEDGER.md/json`), `still_runs.mjs` +
`still_report.py` (stationary no-attack stretches by context), `death_context.mjs`, `spawn_hold.mjs`,
`ledger_bench.py` (the same ledger over a local bench), `extract_local.py`. Inputs: the 136 decoded v52/v53/reference
replays in `artifacts/local-only/v53-review/replays` (local-only).

### 1a. The economy is lost before contact, through time use and yield

v53 losses (39 games), medians of per-game team values, us / opponent:

| R250 | Us | Opponent |
|---|---:|---:|
| camp-attack share of alive champion-rounds | 0.20 | 0.25 |
| moving without attacking | 0.49 | 0.43 |
| stationary off-spawn without attacking | 0.19 | 0.15 |
| capture gold per actor | 144 | 267 |
| capture gold per attack/cast round | 2.93 | 3.46 |
| actors with a Treasure emblem (R500) | 0 | 4 |
| median first purchase round | 147 | 107 |

Against the targeted cohort (meow, Hidden Altar Keepers) at R500 the capture-gold rate is 69 vs 158 per 100 alive
champion-rounds: about half from time attacking (0.19 vs 0.29) and half from gold per attack round (2.97 vs 5.24).
Yield is equal at R100 (2.64 vs 2.77) and diverges with items: opponents first buy at R72 (Treasure), we at R148.
The seven "pure economy" losses (no deaths on either side by R250) show the same gap: 120 vs 285 capture gold per
actor at R250, stationary share 0.29 vs 0.15.

Shared-capture fraction is 0.00 for us: redundant capture occupancy is **not** our problem (the plan's hypothesis
was checked and rejected).

### 1b. Where the stationary time goes, and the large groups we never take

Stationary no-attack champion-rounds by R500, all v53 games (us / opponent): respawn waits beside a dead camp
12,770 / 4,041 — three times the opponents'. Big captures separate wins from losses: in losses opponents bank 196
gems/game from 20+-gem rewards by R500 against our 110 (small rewards are equal); in our wins we out-capture them
(249 vs 200).

Logged reproduction (`artifacts/tmp/v53log`, diagnostic only) on 00fragment and 01concentrated-wealth:

* fragment has six groups: two 4-camp centre groups (26 gems, 150 gold) needing two champions, four 2-camp wolf
  groups (4 gems). Our three champions scored only their two home wolf groups and the centre group as an
  initiating job, and waited for the wolves to respawn; the winner took the centre with all three actors at R6-7.
* concentrated-wealth's centre group (21 camps, 71 gems, 330 gold) was never attacked by R300. At R2 all five
  champions claimed it and staged; all five gave up at R8, 40 tiles out, "present 1" each. 38 such lapses by R500.

**Root cause (correctness bug):** the staging clock in `fight_camps` started when a champion began walking to a
multi-champion job, not when it arrived. Any job farther than the 7-turn timeout lapsed before anyone arrived,
banned the group for 60 rounds and set a call cooldown. Presence was also judged by personal vision only, and
teammates behind bushes/walls were invisible.

### 1c. Early-contact spirals (elkring, swirl)

Opponents' winning actors carry Treasure + Jungle + Durability emblems and Bruiser stacks; ours carry Jungle +
Durability + Power. On swirl against Hidden Altar Keepers, R500 equipment 480 vs 5400 after 13 vs 2 deaths. The local
mirror reproduces the low yield. The decisive local change on swirl came from the item milestones (section 2, M2:
12/12, worst +78 on swirl with M1-M4).

### 1d. Logistics

Winning teams use teleport crystals on exactly our weak maps (626 hops in 45 of 136 replays; e.g. one winner's
Marcella 53 hops on concentrated-wealth, meow/HAK actors ~150 on swirl). They reuse a few fixed 3-tile terrain
shortcuts (concentrated-wealth (12,23)→(15,25), swirl (17,23)→(14,26)). v53 never bought or used a crystal.

### 1e. Gated altar (boss_battle)

v53 (and M1 alone) produced 0-0 tiebreak games. With the item milestones, crews kill the gate and bank (section 3).

## 2. Mechanisms implemented (each behind its own switch in `bots/v54/src/common.h`)

| Id | Switch | Mechanism | Hot-path cost |
|---|---|---|---|
| M1 | `V54_STAGE_ARRIVE`, `V54_STAGE_WALK` 60, `V54_ONSITE`, `V54_STAGE_HELPED` 20 | Crew jobs: staging clock starts at the staging ring; on-site claim codes (64+g on maps ≤48 groups) so hidden teammates count as present; only calls enough teammates have answered get the walk and the 20-turn wait; unanswered calls lapse after the old timeout. Claims decoded once per change into a cache (`claim_of` became an array load). | cheaper (claim cache); staging logic only in the stage branch |
| M2 | `V54_ITEMS` 3 | Item milestones: Treasure first emblem (bit 1), Bruiser stat stacks instead of Power (bit 2); camp emblems (Jungle, Durability) keep their place; role variants for Vesper, Prism, Heart, casters. | none (cold shop path) |
| M3 | `V54_HOLD`, `V54_HOLD_LEAD` 160 | Lead lock on sole-gem maps: with a banked lead of one cycle, one empty-bag champion holds a spawn tile of the sole gem group (engine-checked: occupation delays the whole group's respawn), marked on site; teammates wait beside it. | once per farm call on the respawning branch |
| M4 | `V54_TP`, `V54_TP_GAIN` 5 | Teleport shortcuts: carry one 10-gold crystal; in `walk_toward`, which already has the walking field to the goal, hop to the legal tile within 3 that saves ≥5 turns net of the channel, only with no visible enemy and outside awake-camp reach. | one cached count check per walk while no crystal is held |

New logic is outside per-group/per-camp loops. Fuel-exhausted turns over the 336-game dev bench: 431 for v54 vs 529
for v53. Zero faults in every bench.

## 3. Experiment ledger (bench2 vs v53; seeds are NOVA_SEED policy perturbations; 168 games per 3 seeds)

| Run | Change | Games | Record | Win rate | Mean margin | Verdict |
|---|---|---:|---:|---:|---:|---|
| v54a smoke | staging clock on arrival only | 4 | concentrated-wealth 0/2 | | | crews gather, but presence unseen: 92-172 turns of 250 in "stage" |
| v54b | + on-site claims | 168 | 90-78 | 0.536 | +54.8 | rows/contest/broken-curve regress: unanswered calls walk 60 rounds |
| v54b target | concentrated-wealth + fragment | 12 | 9-3 | 0.750 | +282.5 | |
| v54c | + long staging only for answered calls (= M1) | 168+168 | 95-73, 96-72 | 0.568 | +84.3, +60.3 | retained |
| v54c ledger | | 168 | | | | gems from 20+-gem captures 166 vs 139; respawn waits unchanged 146 vs 148 |
| v54d probe | UB_PROXY item table | 168 | 107-61 | 0.637 | +193.5 | motivates M2 |
| v54e | M1 + M2 (V54_ITEMS 3) | 336 | 206-130 | 0.613 | +148.1 | retained |
| ablation | M1 + Treasure only | 336 | 184-152 | 0.548 | +54.8 | components interact |
| ablation | M1 + Bruiser only | 336 | 187-149 | 0.557 | +64.2 | |
| ablation | M2 without M1 | 336 | 189-147 | 0.562 | +82.8 | M1 adds ~+65 on top of M2 |
| lab | naive spawn hold (holder idles) | 1 | 0-640 | | | mechanic confirmed (respawn 120 vs 65 rounds); strategy as written useless |
| v54f stampede | + M3 lead lock | 12 | 7-5 | 0.583 | +257.8 | hold engaged in 5/12 games, all after a lead, all wins |
| v54f | M1-M3 | 336 | 207-129 | 0.616 | +154.5 | aggregate neutral, retained for stampede |
| v54g | M1-M4 | 336 | 223-113 | 0.664 | +192.9 | retained |

Noise: an inert change (M3 is inactive on all but one map) moved single-map means by up to ±100 gems and one map
from 9/12 to 5/12 (elkring, which used zero teleports in v54g). Read per-map results with that in mind; aggregates
over hundreds of paired games are the evidence.

## 4. Rejected or not pursued

* Forced role/route plan for crews (draft-time itineraries): not needed once job coordination worked; untested.
* Lowering the respawn-wait weight or re-enabling squads/zones: threshold tweaks of previously rejected levers; not
  retried. M1 did not reduce respawn waits (146 vs 148 champion-rounds by R500); this remains open.
* Naive spawn hold (idle holder): confirms the mechanic, loses the game (0-640).
