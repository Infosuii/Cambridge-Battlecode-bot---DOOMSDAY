# CAMBC bot: code efficiency under the fuel budget, and the evidence on best strategy / near-perfect play

Sources are local files; links are relative to `C:\Users\Iniya\Videos\Default Project 2\` unless they start with `memory/`
(= `C:\Users\Iniya\.claude\projects\C--Users-Iniya-Videos-Default-Project-2\memory\`). Nothing was built or run; all
numbers are quoted from the project's own logs. "Pts" = percentage points of win rate. Current best bot: v61
(`v4/bots/v61`); newest experimental source: p64 (`v4/bots/p64/src`, = p63sc + V59_ITEMS 5 + A2_SQUAD 1).

## A1. Where does the bot spend fuel per turn, and are decisions cut short by fuel?

### Takeaway
Fuel almost never binds in play: the bot uses roughly a quarter to a half of its 100k per-turn budget, overruns are
~3 turns in 43,000, and since v32 the work is capped by fixed *deterministic counts* (16 camp groups scored, a
predicted 70k fight-search budget, 2 distance fields per calm turn), not by the fuel left. What *is* cut short is the
fight search's scope: a 4-unit relevance snapshot, one opponent model, and a 2-3 round horizon, set by those caps.

### Cited Findings
- Budgets (cambc 4.0.0, measured with A2_FUELPROBE): draft turn 1 = 9.99M fuel; draft turns 2-5 = 100k each; champion
  turn 1 = 185k; later turns 100k — [EXPERIMENTS E62](agent2/EXPERIMENTS.md). Rules: C++ gets 100k/turn, 10x on the
  first draft turn, 2x on the first play turn, unused fuel does not carry over; a bot that runs out is suspended and
  resumes next round — [GameRules](v3/GameRules.md) (Fuel section).
- Exhausting a turn is costly per event: execution suspends mid-instruction, actions already taken land in the old
  round, and the stale code then spends the *next* round's allowances, so the champion loses its fresh decision —
  [FINDINGS.md §1](agent2/FINDINGS.md).
- Platform games on 4.0.0 (our bot, 11 losses): draft turn 1 uses 88-118k of 10M (1%); champion turn 1 uses 80-181k
  of ~185-200k (181k on a 5v5 map with 51 camp groups, near the cap); later turns average 23-59k of 100k; turns at
  >= 99k: 3 in ~43,000. "Overruns are not losing us games"; ~40-75k per turn unused —
  [MATCH_ANALYSIS_E63 §6](agent2/MATCH_ANALYSIS_E63.md).
- Earlier ladder (v32 era): median 15-26k of 100k per turn; first turn ~100k of 200k; draft ~20k of 1M —
  [FINDINGS_2026-10-18 "Fuel"](FINDINGS_2026-10-18.md). v34 (route depth 2): median 36.5k, p90 72k, p99 87k —
  [FINDINGS_2026-10-18 "v34 packaged"](FINDINGS_2026-10-18.md).
- Deterministic budgets (APEX_DET=1): "work is bounded by counts and predicted costs instead of the fuel left, so
  decisions depend on the game state only (fuel checks remain as safety floors that should almost never bind).
  Otherwise any code change shifts fuel use, flips threshold decisions and moves strength by +-20-40 Elo" — code
  comment, [common.h ~L1993](v4/bots/p64/src/common.h). Defaults: APEX_DET_SAFETY 12000 (floor for optional work),
  APEX_DET_SCORE_N 16 groups per farm decision, APEX_DET_UNIT_COST 2200 fuel per unit per simulated round,
  APEX_DET_FIELDS 2 distance fields per calm turn (4x on dead turns); the shipped override is
  APEX_DET_TS_BUDGET 70000 (default 45000) — [common.h L172, L1997-2017](v4/bots/p64/src/common.h); same in
  [v61 common.h L151](v4/bots/v61/src/common.h).
- Group scoring loop: under APEX_DET it breaks once 16 groups are evaluated *or* fuel < kDetSafety (12k); the old
  non-deterministic path broke below kScoreFloor = 25,000 — [bot.cpp L5617-5622](v4/bots/p64/src/bot.cpp),
  [common.h L1611-1614](v4/bots/p64/src/common.h) (kLowFuel 60k: keep current target instead of rescoring;
  kMinMoveFuel 15k: skip path searches).
- Fight-search admission (tactical_decide): predicted cost = 2200 x units x (rounds+1) per playout; with two plans
  (fight, run) per enemy model, it drops from 2 models to 1, then shortens the horizon to 2, else returns no verdict —
  [tsearch.cpp L917-930](v4/bots/p64/src/tsearch.cpp). With the 70k budget and APEX_TS_DECIDE_ROUNDS 3 this means
  (my arithmetic from that code): 2 units -> 1 model, 3 rounds (two models need 70,400 > 70,000); 3 units -> 1 model, 3
  rounds; 4 units -> 1 model, 2 rounds; 6 units would need 79,200 > 70,000 -> no verdict ("Six-unit comparison 79,200 >
  70,000: yes, exactly; 5 units fit" — [IMPROVEMENT_PLAN_v34 appendix](IMPROVEMENT_PLAN_v34.md)).
- "The two-enemy-model comparison never runs: even n=2, h=3 needs 4 x 17,600 = 70,400 > 70,000. Every verdict uses one
  model." Scene sizes (v34, official mirror): 2-4 units 63% of calls (verdict 45-54%), 5 units 17% (verdict 18%,
  incomplete for fuel), 6+ units 17% (verdict 0-3%) — [FINDINGS.md §4](agent2/FINDINGS.md).
- The snapshot is now capped at 4 relevance-ranked units (A2_SNAP=4): verdict rate 39.3% -> 46.8%; a 5-unit cap makes
  verdicts at scene >= 5 collapse to ~3% ("a 5-unit pair needs 78k at entry") — [EXPERIMENTS E9/E10](agent2/EXPERIMENTS.md).
- Real playout cost vs the 2,200 estimate (thousands, median/p90/p99/max): n=3,h=3 14/22/27/34 [est. 26.4]; n=4,h=2
  15/22/29/37 [26.4]; n=5,h=2 19/27/35/42 [33.0] — the estimate is ~1.7x the median but below the tail —
  [FINDINGS.md §4](agent2/FINDINGS.md). Playout cost scales ~0.7-1k x units^2 (15k with 4 units, 42-49k with 8) —
  code comment, [tsearch.cpp L901](v4/bots/p64/src/tsearch.cpp).
- In the pre-fix v34, the turns that ran out were in counter_ambush() (35-61% of suspensions; median 72-80k per call,
  up to 729 bush_cluster lookups at ~100 fuel each), ward_reveal() (first-use bush labelling ~800 fuel per tile, 112k for
  100-149 tiles), the action after the fight search (caster micro / stand, 19-20%) and route search (1-20%) —
  [FINDINGS.md §3](agent2/FINDINGS.md). The "fuel package" (A2_BUSH_FAST, A2_FAST_AMBUSH, A2_CMICRO_FAST, A2_GOV, all
  =1 in p64) cut exhaustion entries from 2.94/2.38/3.12 to 0.18/0.53/0.08 per team-game —
  [EXPERIMENTS E6, E13](agent2/EXPERIMENTS.md), [common.h L153-156](v4/bots/p64/src/common.h).
- The opening schedule (A2_SCHED) uses the 10M draft turn: up to 48 rollouts + 1,500 local moves, stopping at a 2.5M
  floor (it hits the floor on big-world and yellow-brick-road) — [EXPERIMENTS E62](agent2/EXPERIMENTS.md).

### Inferences
- The binding limits on decision quality are design caps (snapshot of 4 units, one opponent model, 2-3 round horizon,
  16 groups, route depth 2), chosen so that fuel never binds — not fuel exhaustion itself.
- The only places where fuel is genuinely tight are the first champion turn on big maps (181k of ~185k) and big
  multi-unit fights (5+ units cannot be searched at all).

### Gaps
- No per-stage fuel breakdown (PROF scopes exist in bot.cpp: shop, move, escape, enemies, score, route, plan, farm,
  field, world) was found for the current v61/p64 build on engine 2.0.0; the stage attribution in FINDINGS.md is for
  v34 on cambc 2.2.5.
- How much fuel each SDK host call (bitboard ops, distance fields) is charged on 4.0.0 is only partly measured (see A2).

## A2. Which data structures dominate, and what concrete optimisations are possible?

### Takeaway
The heavy primitives are SDK host calls — bitboards (every op and every temporary is a host call plus an aligned heap
allocation) and host-computed distance fields (3k-33k fuel each) — plus the hand-written fight simulator
(cost ~ units^2). Caching already exists (per-champion World persists across turns; group fields built incrementally),
so the remaining optimisations (field reuse from the draft turn, fewer bitboard temporaries, cheaper playouts,
compiler/wasm-opt) are real but would mostly free fuel that is already unused.

### Cited Findings
- Each champion has its own bot instance; the team shares only 8 bytes of memory all game plus 1,024 bytes written
  in the draft — [GameRules, Shared memory](v3/GameRules.md); `shared_memory_bytes` = 8 and fully used by claims —
  [memory/cambc-team-assignment.md](memory/cambc-team-assignment.md).
- `main()` constructs one `Bot` and loops forever (each turn wrapped in try/catch, then `end_turn()`), so World state
  persists across turns within a champion's instance — [main.cpp](v4/bots/p64/src/main.cpp).
- World caches: `altar_field`, `spawn_field`, `enemy_field`, `std::vector<bc::distance_field> group_dist` with
  `field_order` and `build_next_group_field(budget)`, `pair_rows` (group-to-group distances) —
  [world.h L101-166](v4/bots/p64/src/world.h). Fields are built 2 per calm turn (4x when dead) —
  [common.h APEX_DET_FIELDS](v4/bots/p64/src/common.h); building is gated by
  `kFieldBuildReserve + (w+h+40) x field_chunks()` — [bot.cpp L6656-6663](v4/bots/p64/src/bot.cpp).
- SDK bitboards: constructor does `::operator new(raw_buffer_size(), align 16)`; `count()`, `&=`, `shift_right_into`,
  `draw_chebyshev`, `shadow_cast`, `reachable_tiles` are all host imports (`sdk_Bitboard_*`) —
  [cambc.h L749-1150](v4/sdk/cpp/cambc.h). `distance_field::compute_to` is a host search —
  [cambc.h L1340-1360](v4/sdk/cpp/cambc.h). Engine search cost model: (levels + 16) x chunks + 3,000 fuel ("measured to
  0.3%") — [runtime_budget.h](v4/bots/p64/src/runtime_budget.h).
- Measured costs: one walking-distance field 3k-33k fuel; fields from every camp group 96k-549k (1-6% of the draft
  turn) — [EXPERIMENTS E60](agent2/EXPERIMENTS.md); a 100x100 field ~32k; one opening-planner job evaluation ~1.5-3k;
  wasm printf ~10-20k fuel per call — [memory/cambc-opening-schedule.md](memory/cambc-opening-schedule.md). Per-call
  printf and dense dumps in a telemetry build inflated exhaustion from ~2.5 to ~35 per team-game ("printing and even
  plain array scans are expensive under a ~1-fuel-per-instruction budget") — [FINDINGS.md §3](agent2/FINDINGS.md).
  v34's first turn on lanes (90x30, 42 groups) spent ~73k on initialisation, 36k of it on camp-group loading —
  [FINDINGS.md §2](agent2/FINDINGS.md).
- Code counts in p64 (my grep): 63 local `bc::bitboard` declarations in bot.cpp, 30 in world.cpp; 20 `std::vector<`
  declarations in bot.cpp; ~62 `try {` blocks in bot.cpp (around SDK calls that can throw); the belief update shifts
  per-enemy reach bitboards by host calls each round — [world.cpp L626-690](v4/bots/p64/src/world.cpp).
- Fight simulator state is a fixed-size struct (`Unit u[kMaxUnits]`, kMaxUnits = 8), no heap in the playout —
  [tsearch.h L39-75](v4/bots/p64/src/tsearch.h).
- Build: C++20, `-msimd128 -mbulk-memory -mbulk-memory-opt -fwasm-exceptions`, link `--no-wasm-opt` ("older Binaryen
  cannot parse this SDK's output"); no explicit -O level in the CMake file —
  [v4/cmake/CMakeLists.txt](v4/cmake/CMakeLists.txt).
- Draft precompute (A2_MAPPRE) computes walking fields from both spawns and every group on draft turn 1 but can pass
  only a summary to champions (draft memory 600-991: cluster, rush, altar, 4 bytes per group) —
  [EXPERIMENTS E61](agent2/EXPERIMENTS.md). Using it all game (A2_MP_LATE) replayed exactly at setting 0 and lost or was
  neutral when switched on — [EXPERIMENTS E66 (first)](agent2/EXPERIMENTS.md),
  [memory/cambc-precompute-late.md](memory/cambc-precompute-late.md). The earlier plan expected draft-turn tables to let
  champions "skip rebuilding fields ... and spend the saved fuel on a deeper fight search" —
  [PLAN_v4.md](agent2/PLAN_v4.md).
- Release fuel tools cannot be bypassed: fuel_pause/resume/adjust exist only under CAMBC_DEBUG and a release bot
  importing them is trapped — [EXPERIMENTS E59](agent2/EXPERIMENTS.md).
- Gating expensive model calls matters: a location-risk model run for every scored camp every turn "starved turns of
  fuel (18-22% vs v34 even at weight 0.001) until it ran only near enemies" —
  [IMPROVEMENT_PLAN_v34 §9](IMPROVEMENT_PLAN_v34.md).

### Inferences
- Concrete optimisation options, in rough order of fuel saved: (1) a cheaper playout (the units^2 cost model, ~15k for a
  4-unit 2-round pair) — e.g. precomputed per-unit threat/reach tables per turn, early termination when a side is dead
  or out of reach, incremental evaluation; this is the only change that could widen the search to 5-8 units;
  (2) reuse of distance fields: walking fields are cheap per field but are rebuilt per champion instance because only
  4 bytes per group cross the draft-memory boundary — a compressed group-to-group / group-to-altar table in the
  1,024 draft bytes removes most field builds; (3) fewer bitboard temporaries (each is a host call + aligned new) by
  reusing scratch boards held in World; (4) avoiding throw paths (SDK `get` throws outside the map) inside loops;
  (5) trying wasm-opt -O3 with a newer Binaryen (currently disabled) — gain unknown.
- Because turns already end with 40-75k unused, these would make the bot faster, not stronger, unless the freed fuel is
  spent on something that has been shown to improve decisions (see A3).

### Gaps
- Fuel charged per host call on engine 2.0.0 (e.g. a bitboard intersect, a shadow cast) was not found in the logs.
- The -O level the cambc CLI passes (CMAKE_BUILD_TYPE) is not visible in the project files.
- No measurement of how many fields each champion rebuilds per game after the precompute exists.

## A3. Has fuel ever been shown to limit results, and how large would an optimisation gain be?

### Takeaway
Spending more fuel helped twice early on (fight-search budget 45k -> 70k, about +1.7 pts in the pool; route depth 2,
about +2 pts but only on official maps), and then saturated: 85k search budget, 10x search, full-candidate search,
fixing exhaustion and raising every cap were neutral or negative. The fight verdict itself is not where games are lost.
Expected gain from code optimisation alone: small (0-2 pts), unless paired with a better evaluator.

### Cited Findings
- Fight-search budget 70k on bundle A: pool 58.9% -> 60.6% (unseen 60.9%); farming/precompute caps (40 groups, 6
  fields): 57.2% (rejected) — [FINDINGS_2026-10-18 v32/v33](FINDINGS_2026-10-18.md). Route depth 2 on v33: 60.6% ->
  62.7%, but it hurt short generated suites and was limited to official maps (v34c) —
  [FINDINGS_2026-10-18 "Fuel uses", "v34c"](FINDINGS_2026-10-18.md).
- Raising all caps at once (TS 80k, cheaper estimate, 40 groups, 6 fields, unlimited first turn): p99 91k per turn, 66
  exhausted turns vs 8, 3/12 wins — rejected — [FINDINGS_2026-10-18 "Fuel"](FINDINGS_2026-10-18.md).
- Fixing exhaustion (-80 to -98% events) was strength-neutral: a2fix -0.9 +- 1.1, a2gov -0.1 +- 1.2 pts over 1,904
  paired games — [EXPERIMENTS E8](agent2/EXPERIMENTS.md). Side effect: faster bush labelling let bush-hiding run on
  stampede, which *lost* games there (62.5% -> 51.8%) — [EXPERIMENTS E28](agent2/EXPERIMENTS.md).
- APEX_DET_TS_BUDGET 85000 (E64): 48.0 vs control 45.0 (100 games), 51.2 vs 50.5 (280 official games); against an
  opponent boosted +0.25 gold/turn 17.9 vs 20.0 — "None beats the control" —
  [EXPERIMENTS E64, E65](agent2/EXPERIMENTS.md).
- Search vs no search: fight/run verdict by rules only (APEX_TS_DECIDE=0) 48.7% +- 4.1 vs the combo — "the search
  verdict adds nothing measurable" — [EXPERIMENTS E39](agent2/EXPERIMENTS.md). Own search with vision + full action
  search at 10x fuel: 32/100 ("more search exploits the simulator's errors") — [E28](agent2/EXPERIMENTS.md). Full
  candidate list, no fuel limit (A2_TSFULL): worse in the duel lab (43% vs 59% within 0.5 of best) —
  [E33](agent2/EXPERIMENTS.md).
- Engine-branched fight states: engine prefers a side in only 12% of states; where it does, the simulator verdict agrees
  95.5%, regret ~0.01 value per state — "the fight/run verdict is not where games are lost" — [E24](agent2/EXPERIMENTS.md).
  Simulator rules reproduce 95.2% of recorded turns exactly; the limit is behaviour modelling (move-ranking agreement
  0.42 vs a 0.90 ceiling) — [E33, E35](agent2/EXPERIMENTS.md).
- Snapshot size *did* matter for deaths: A2_SNAP=4 + A2_TD_AUTH cut deaths 0.73/game on both seed halves (score +1.1 +-
  1.5) — [E12, E13](agent2/EXPERIMENTS.md).
- Lab vs real: the lab's `fuel_remaining()` always reports a full budget, yet over 100 replayed real games the lab win
  rate (57/100) matched the real engine (56/100), though only 53/100 had the same winner —
  [EXPERIMENTS E56](agent2/EXPERIMENTS.md). Real-engine comparison vs t58: "Fuel is not the cause (fuel log: 0-4
  overruns a game for both)" — [E53](agent2/EXPERIMENTS.md). Platform losses: "Fuel: not a cause" —
  [MATCH_ANALYSIS_E63 §6](agent2/MATCH_ANALYSIS_E63.md).
- 100k fuel per turn rules out large networks in play — [RESEARCH_REVIEW_2026-10-18](RESEARCH_REVIEW_2026-10-18.md).

### Inferences
- Optimisation would bring a *small* gain on its own. The strongest argument: a lab with effectively unlimited fuel
  reproduces the real engine's aggregate win rate, and doubling-to-10x search budget did not help. The ~50k spare per
  turn is already available today without any optimisation.
- Where efficiency could matter: (a) letting the fight search see 5-8 units (bigger snapshots reduced deaths before,
  and platform losses are 3v3-6v6 team fights against packs); (b) a learned value/death model or opponent-power
  estimate evaluated every turn near enemies; (c) the first champion turn on large maps. Each needs a better evaluator
  first; more search on the current simulator has repeatedly been neutral or harmful.
- Any optimisation also changes which fuel-gated branches fire (APEX_DET exists because fuel-dependent cut-offs moved
  strength +-20-40 Elo), so it must be parity-checked game-by-game.

### Gaps
- No experiment tested a widened snapshot (5-8 units) with a cheaper playout on engine 2.0.0.
- No test of search depth against platform-style (stat-stacking, grouped) opponents; the lab stand-ins do not
  reproduce them (A3/B gaps).

## B1. What wins games? Strongest quantitative findings

### Takeaway
Games are decided by an income/power snowball: whoever converts gold into combat stats faster wins fights, dies less,
farms faster and banks safely. On the ladder, fewer deaths (86%) and more gems by round 200 (83%) predict the winner;
a +0.25 gold/turn edge turns 50% into ~18%; our platform losses show 0 stat shards vs 56-402, 5-41 deaths vs 0-9, a
spread-out team, unbanked bags and no altar locks.

### Cited Findings
- Win condition: first to tribute 1,000 gems wins; at round 2,000 compare tributed gems, then lifetime gold earned,
  then kills — [GameRules "How to win"](v3/GameRules.md). Gems only count once tributed; carried gems go to the killer
  on death (lost if a camp kills you); death = 60 rounds out + 100 gold to the killer; tribute channel =
  ceil(gems/10) turn ends, broken by stun, death or an altar lock (not damage); locks cost 10 gold, block enemy
  tributes, need 5 hits — [GameRules](v3/GameRules.md).
- 87 ladder games: the team with fewer deaths wins 86%; more gems collected by round 200 wins 83% —
  [FINDINGS_2026-10-18 §4](FINDINGS_2026-10-18.md).
- Income snowball: giving the opponent +0.25 sandbox gold per turn turns 50% into ~18% either way round —
  [EXPERIMENTS E65](agent2/EXPERIMENTS.md).
- Platform losses (11 games, 0 wins; opponent A): our economy emblems vs stat emblems — us 0 stat shards in 8 of 11
  games, them 56-402; their Vesper ends with 19-26 Bruiser strength emblems (str 580-760), our Vesper str 75 / hp 1000
  after 983 rounds; power gap visible by round 200 (their Vesper 130 str / 2,100 hp vs ours 45 / 1,000) —
  [MATCH_ANALYSIS_E63 §1](agent2/MATCH_ANALYSIS_E63.md). Damage traded is even to round 300, then they out-damage us
  2-17x — [EXPERIMENTS E65](agent2/EXPERIMENTS.md).
- Deaths: ours 5-41 (median 10) vs theirs 0-9 (median 2); many "alone" (no ally within 4) — e.g. 22/41 in g10, 21/30
  in g03; mostly in our own third or the middle (g03 26/30, g10 33/41) — [MATCH_ANALYSIS_E63 §2](agent2/MATCH_ANALYSIS_E63.md).
  Across all 11 games: 184 deaths vs 49 — [E65](agent2/EXPERIMENTS.md).
- Spacing: mean distance to nearest living ally us 5.0-11.5 tiles vs them 3.2-7.9 (g04 11.5 vs 5.8, g03 8.6 vs 4.1) —
  [MATCH_ANALYSIS_E63 §2](agent2/MATCH_ANALYSIS_E63.md). Earlier ladder profile: nearest teammate rounds 20-300 top-12
  6.0 tiles vs us 8.2; deaths with no teammate within 6: 39% vs 49%; deaths/kills per game 6.0/6.7 vs 9.0/7.3 —
  [FINDINGS_2026-10-18 "Behaviour profile"](FINDINGS_2026-10-18.md). Top teams have ~35% more teammates within 4 tiles
  in fights — [memory/cambc-replay-learning.md](memory/cambc-replay-learning.md).
- Flee deaths: the last mode before 75% of our deaths is "flee"; flight starts at median 30% health (quartile 17%),
  median 1 enemy and 0 allies within 5 (alone in 54%), median walk home 24 tiles, death after a median 5 turns of
  fleeing — [EXPERIMENTS E65](agent2/EXPERIMENTS.md). Earlier: "87% of our deaths happened while fleeing" — code
  comment on APEX_STAND, [common.h ~L1604](v4/bots/p64/src/common.h).
- Value of a death: -91 +- 8 team gems 100 rounds later with an empty bag, -177 +- 24 carrying 40+; half a health bar
  -21; +20 carried gems +12 — [EXPERIMENTS E26](agent2/EXPERIMENTS.md). From real games: a death costs 76 gems
  (rounds 0-200), 37 (200-400), 47 (400-700) — [FINDINGS_2026-10-18 §10](FINDINGS_2026-10-18.md).
- But avoiding deaths by leaving early costs about as much as the death: "no response beats the control" (E38); escape
  retreat + squad farming cut deaths 27% (382 -> 279) yet gave no more wins in the lab (E66); a cohesion camp penalty
  cut deaths 19% but lost 4 pts (race maps -11 to -16) — [EXPERIMENTS E38, E66](agent2/EXPERIMENTS.md),
  [IMPROVEMENT_PLAN_v34 "Not to redo"](IMPROVEMENT_PLAN_v34.md).
- Banking: gems carried into death up to 270 per game; on road-of-riches we carried 33-177 gems at rounds 100-400 and
  banked 0 all game (every carrier died before reaching an altar) — [MATCH_ANALYSIS_E63 §3](agent2/MATCH_ANALYSIS_E63.md);
  the long spiral walk to central altars makes carriers hold 300-480-gem bags — [E67](agent2/EXPERIMENTS.md).
  Top teams bank first much earlier (rows r56 vs our r99, collision r74 vs r220) — [FINDINGS_2026-10-18 §4](FINDINGS_2026-10-18.md).
  Bank timing within a 30-round window does not move the margin (hold 20+ bag: -1.1 +- 7.8) — [E27](agent2/EXPERIMENTS.md).
- Altar locks: the opponent kept locks on our altars 764/849 rounds on contest, 747/1,068 on anvil, 578/1,469 on
  reverse-spiral; our locks: 0 rounds in all 11 games; our carriers spent 10-68 champion-turns next to an enemy-locked
  altar — [MATCH_ANALYSIS_E63 §4](agent2/MATCH_ANALYSIS_E63.md).
- Economy/farming: top teams first capture r28 vs our 41, gold by r300 1,988 vs 1,732, emblems by r300 9.9 vs 8.0 —
  [FINDINGS_2026-10-18 "Behaviour profile"](FINDINGS_2026-10-18.md); their ranged champions avoid camp hits (camp damage
  taken per damage dealt 0.16 vs our 0.33) because a melee partner tanks; every emblem type worth about the same (16-28
  banked gems), converting gold into emblems is what counts; unspent gold ~6 gems per 100 —
  [FINDINGS_2026-10-18 §11](FINDINGS_2026-10-18.md). v34 harvests only 21% (official) / 19% (unseen) of the maps' gem
  regrowth; travel is 48-49% of turns — [FINDINGS_2026-10-18 "Critique check"](FINDINGS_2026-10-18.md).
- Turn use vs opponent B: both move 55% / stand 35-37%; "Opponent B does not use its turns better; it gets more per turn
  (stats -> faster camp kills) and survives fights"; dead 11% vs 8% of champion-rounds (vs opponent A: 24% vs 6%) —
  [EXPERIMENTS E68](agent2/EXPERIMENTS.md). Opponent B: deaths about even but they out-farm us from round ~400 with
  stat stacks after 2-4 emblems — [E67](agent2/EXPERIMENTS.md).
- Middle camps: the black-box search that produced v61 moved the middle-camp weight knob k40 from 0 to 0.63 (x exp(0.3k)
  = ~x1.21) as its largest change; v61 vs t58 in the real engine 57% over 200 games —
  [EXPERIMENTS E54](agent2/EXPERIMENTS.md), [KNOBS.md slot 40](agent2/KNOBS.md). Lanes (all camps in the shared middle):
  we take 19 captures by r300 vs top teams' 25 — [FINDINGS_2026-10-18](FINDINGS_2026-10-18.md).
- Draft: our draft net is worth ~+8 pts in the lab (E48); no fixed lineup beats it in the lab; on the platform both
  opponents always field Vesper (+33% gold) and Heart; we pick Vendetta first every game —
  [EXPERIMENTS E48](agent2/EXPERIMENTS.md), [MATCH_ANALYSIS_E63 §5](agent2/MATCH_ANALYSIS_E63.md). Counter-picking is
  noise once per-size champion values are fitted — [memory/cambc-draft-fit.md](memory/cambc-draft-fit.md).
- Items in the lab vs the platform conflict: against our own bot family, Prospector-first economy build won (v59 vs v57
  67/100 real engine, E52), and power-curve builds (V59_ITEMS 1/3/4/5) tested neutral or negative (E64, E67) —
  [EXPERIMENTS](agent2/EXPERIMENTS.md); against platform opponents the same economy-first build loses every fight —
  [MATCH_ANALYSIS_E63 §1](agent2/MATCH_ANALYSIS_E63.md) ("our reference opponents ... buy the same economy-first build,
  so economy-first looked best in closed-loop tuning").
- Macro choices are locally flat: barring the current camp -8.6 +- 8.0, ridge chooser over forbid/bank/hold/regroup/home
  +0.1 +- 0.3 gems per decision — [EXPERIMENTS E27, E44](agent2/EXPERIMENTS.md). Learned fight/flee/regroup from
  engine counterfactuals: held-out correlation -0.07 to +0.02 — [E69](agent2/EXPERIMENTS.md).
- Exploits tried and not winning: carrier hunter 50.0%, altar ambusher 36.7%, early pressure 34.7%, counter-draft
  44.0% (E40); camp pull 44 vs 46 (E55); capture-bank fires 0-1 times a game (E51) — [EXPERIMENTS](agent2/EXPERIMENTS.md).

### Inferences
- The causal chain on the platform is: economy-first items -> no stat growth -> lost even fights from ~round 200-300 ->
  deaths (often alone, while fleeing late) -> gems lost and 60-round absences -> slower farming and no banking ->
  opponent snowballs. Fixing any single link inside a lab of look-alike bots shows nothing, because those bots share
  the same weakness.
- Spacing numbers in the brief ("7.5 vs 11.3 tiles") were not found; the closest documented figures are 6.0 vs 8.2
  (ladder top-12 vs us) and 3.2-7.9 vs 5.0-11.5 (platform E63).

### Gaps
- The exact passives of the 4.0.0 emblem families (Tribute, Capture, Prospector, Hunter, Skirmish, Greed, Collectors)
  are not documented locally (SDK enum only; GameRules (10) is stale per E50); only probe results exist (Tribute emblem
  helps bags >= 31; Capture caps the timer at 3; Hunter = 150 gold per kill).
- No controlled test of any fix against a platform-like opponent: the stand-in op1 (copying their build and draft)
  loses to our bot 41.4% (E65), so it does not reproduce them.
- No figure for a "middle-camp gem edge" beyond the k40 knob move and lanes capture counts.

## B2. What would near-perfect play look like, and what does the current bot do / not do?

### Takeaway
Near-perfect play is a power-curve economy run as a pack: farm efficiently with melee tanking and minimal travel,
convert gold into stats after a short economy opening so the team is stronger at every contact, move and fight in
2-3 champion groups that only engage with local superiority and leave early, bank small bags often at safe altars
while denying the enemy's banking with locks and stuns, and race-manage the endgame. The bot does the farming
machinery and per-turn micro well, but buys economy instead of stats, farms alone, flees late, never places or reads
altar locks, and drafts away from the platform meta.

### Cited Findings (rules and evidence each element rests on)
- Economy ceiling: gem regrowth (sum of gems / respawn) — a perfect harvester would need ~97 (official) / ~50
  (unseen) rounds to 1,000; v34 took 476 / 330 median; travel is the largest turn bucket —
  [FINDINGS_2026-10-18 "Critique check"](FINDINGS_2026-10-18.md). Top teams re-take wolf packs every 52-58 rounds
  (respawn 40 + quick kill) vs our 70-85 — [FINDINGS_2026-10-18 §4](FINDINGS_2026-10-18.md). Camps attack the nearest
  champion in range and stop after 2 rounds without damage; Jungle = 30% less camp damage —
  [GameRules](v3/GameRules.md). Rewards split among allies present (more allies do not speed capture) —
  [GameRules](v3/GameRules.md).
- Power curve: stats are permanent shards (30 gold each), emblems at 5; Bruiser/Power give extra stats; winners run
  2-3 economy emblems then main-stat Bruiser/Power stacks, casters focus —
  [MATCH_ANALYSIS_E63 §1, "What to change" 1](agent2/MATCH_ANALYSIS_E63.md), [E67](agent2/EXPERIMENTS.md).
- Pack movement and fight selection: top teams keep closer spacing and hit back when outnumbered (70-74% of turns vs
  our 38-63%) — [memory/cambc-replay-learning.md](memory/cambc-replay-learning.md); top teams recall at 63-67% health vs
  our 47%; our champions spend 4.1% of off-spawn rounds near enemies below 30% health vs top-vs-top 0.6-1.3% —
  [FINDINGS_2026-10-18 §4](FINDINGS_2026-10-18.md).
- Banking and denial: tribute duration uses the starting bag but completes the whole bag; stun (not damage) breaks it;
  a placed lock cancels channels at that altar; captures resolve before channels (capture-bank) —
  [GameRules](v3/GameRules.md), [PLAN_v4 "Exploits"](agent2/PLAN_v4.md), [E51](agent2/EXPERIMENTS.md).
- Respawn/capture denial: "any occupied spawn tile delays the entire group"; "admitting an enemy resets progress" —
  [GameRules](v3/GameRules.md), [PLAN_v4](agent2/PLAN_v4.md).
- Endgame: lifetime gold breaks ties at round 2,000 — [GameRules](v3/GameRules.md). A learned win-probability posture
  (A2_RACE=2) gave pool +5.2 +- 3.6 but 46.7% head-to-head — [E42](agent2/EXPERIMENTS.md).
- What the bot does: learned draft net (+8 in lab, E48); per-champion greedy camp scoring with 7-bit claims, route depth
  2, respawn waits (16 groups scored, 2 fields/turn) — [common.h](v4/bots/p64/src/common.h); fight/run simulation over
  a 4-unit snapshot + caster micro + flee-hit — [E12-E13](agent2/EXPERIMENTS.md); wards ahead (NOVA_WARD_AHEAD 6), Ryth
  tribute denial, big-camp rush — [common.h L163-166](v4/bots/p64/src/common.h); knob-tuned middle-camp weight (v61, E54);
  opening schedule on draft turn (A2_SCHED, off by default, +1.5 not clear, E62).
- What it does not do: buys 0 stat shards in 8/11 platform games (six economy emblems first); places 0 altar locks (its
  prelock/deny code never fires against them); does not read enemy locks (A2_LOCKAWARE written, off); farms solo far
  from allies (A2_SQUAD off in v61; on in p64 = bit 1); flees at ~30% health alone over ~24 tiles; drafts Vendetta first
  every game; no team-level plan beyond 8 shared bytes; fight decisions use health, not a power comparison —
  [MATCH_ANALYSIS_E63](agent2/MATCH_ANALYSIS_E63.md), [E61, E65, E66](agent2/EXPERIMENTS.md),
  [p64 common.h L1-17](v4/bots/p64/src/common.h).

### Inferences
- A concrete "near-perfect" policy, assembled from the rules and the winners' observed behaviour:
  1. Draft for income and team-fight power on the map (the platform winners always take Vesper's +33% gold and Heart;
     our lab's draft net disagrees, so this needs platform testing).
  2. Opening (rounds 0-150): use the 10M draft turn to plan routes on walking distances; first captures by ~r25 with a
     melee tanking each camp for a ranged partner; one or two economy emblems (Jungle; Prospector/Treasure).
  3. Mid game: buy main-stat Bruiser/Power stacks (health every 2-3; casters focus) so power at round 200-300 is at
     least equal; keep pairs/trios within ~4-6 tiles; farm our half and the contested middle as a group; wards on
     approach routes; a lock always in stock.
  4. Fights: engage when locally ahead in numbers *and* power; leave at a health/power threshold early enough that the
     walk home is survivable (time-to-death vs walking distance), and retreat toward allies; focus stuns on channelers.
  5. Banking: bank small bags often at the nearest safe altar, escort carriers on contested routes, never carry
     100+ through enemy space; lock the altar the enemy uses when they channel; clear locks on our altar as a group.
  6. Endgame: project both teams' finish; when ahead, play safe and deny; when behind, contest altars and carriers;
     near round 2,000 farm gold for the tiebreak.
- The bot's architecture (independent per-champion instances, 8 bytes of shared state, no shared vision) makes 3-5
  hard: coordination must be emergent from deterministic shared rules (claims, draft-memory plans) rather than messages.

### Gaps
- No local evidence that the full near-perfect package wins: every element was tested only against our own bot family
  (where it was neutral) or observed in opponents' replays.
- Top-vs-top behaviour on engine 2.0.0 (the current patch) is only seen through two opponents (A and B).

## B3. Largest remaining bot weaknesses, ranked

### Takeaway
1) items / power curve, 2) deaths from solo farming and late, lone flight, 3) carrier losses and the altar-lock war,
4) draft vs the platform meta, 5) farming efficiency, 6) fight micro and search depth, 7) fuel/code efficiency.
Over all of them sits a methodology gap: the lab bench (our own bot family) cannot see the platform opponents'
strengths, so fixes for 1-4 all test neutral locally.

### Cited Findings
- Items called "the biggest single cause" of platform losses (0 stat shards in 8/11 games; power gap by r200) —
  [MATCH_ANALYSIS_E63 §1](agent2/MATCH_ANALYSIS_E63.md); a small income/power edge decides games (E65 gold boost
  50% -> 18%) — [EXPERIMENTS E65](agent2/EXPERIMENTS.md).
- Deaths: 184 vs 49 over 11 games; flee mode before 75% of deaths; median flight from 30% health, alone, 24 tiles from
  home — [E65](agent2/EXPERIMENTS.md); death value ~-91 gems (-177 with a bag) — [E26](agent2/EXPERIMENTS.md); lab fixes
  cut deaths 27% but not losses vs own family — [E66](agent2/EXPERIMENTS.md).
- Banking/locks: up to 270 gems lost on death per game, 0 banked on two maps, enemy locks 37-90% of rounds, our locks 0
  — [MATCH_ANALYSIS_E63 §3-4](agent2/MATCH_ANALYSIS_E63.md); A2_LOCKAWARE almost never fires in the lab (48.0 vs 49.1)
  — [E61](agent2/EXPERIMENTS.md).
- Draft: Vendetta first in all 11 games; opponents always Vesper + Heart; V60_VESPER_FIRST tested 53.0 (100) / 48.2
  (280) / 16.4 vs 20.0 (boosted) in the lab — [E64, E65](agent2/EXPERIMENTS.md).
- Farming: harvest 21% of regrowth; first capture 40 vs 28; per-turn turn use equals opponent B's, but each turn
  yields less because of lower stats — [FINDINGS_2026-10-18](FINDINGS_2026-10-18.md), [E68](agent2/EXPERIMENTS.md).
  Farm-speed knob search: held-out 1,088 -> 1,075 rounds (noise) — [E68](agent2/EXPERIMENTS.md).
- Fight micro: bot within 0.5 of the engine's best 1v1 move 59% (2v2 22%); fixes and learned scorers did not beat it;
  in-game effect of better isolated fight turns ~1 pt — [E26, E31-E33](agent2/EXPERIMENTS.md). Per-turn fight choices
  match top teams' (47.9% network accuracy for both); "the gap is positioning, not per-turn choices" —
  [memory/cambc-replay-learning.md](memory/cambc-replay-learning.md).
- Fuel: "not a cause"; 85k budget neutral — [MATCH_ANALYSIS_E63 §6](agent2/MATCH_ANALYSIS_E63.md), [E64](agent2/EXPERIMENTS.md).
- Methodology: "the lab bench (our own bot family, with or without the gold handicap) cannot show gains against
  platform-style opponents; every change aimed at them tests neutral or negative here" (E67); "no setting, switch, item
  plan or knob search beats m62 / v61 in our lab by more than noise; the bot is at a local optimum for its design" (E68);
  self-play does not predict the ladder (proxy r 0.00-0.26; weighted old pool ~0.65) —
  [EXPERIMENTS E67-E68](agent2/EXPERIMENTS.md), [memory/cambc-platform-data.md](memory/cambc-platform-data.md),
  [memory/cambc-sparring-pool.md](memory/cambc-sparring-pool.md). Candidates packaged for platform tests but not
  submitted: p64_engine4.zip, p63sq3_engine4.zip, p63sq1_engine4.zip — [E67](agent2/EXPERIMENTS.md).

### Inferences
- Ranking by expected gain on the platform (my judgement from the cited sizes): items/power curve (large; root of the
  snowball) > grouping + earlier retreat (large in deaths, but costs farming; pairs naturally with stats) > carrier /
  lock play (medium; decisive on altar-centric maps like contest, anvil, road-of-riches) > draft (medium, uncertain) >
  farm routing (small-medium) > fight micro/search depth (small, ~1-2 pts) > code/fuel efficiency (smallest; only as an
  enabler for a bigger fight snapshot or a learned evaluator).
- The next real step is not an optimisation but a measurement: a sparring opponent that stacks stats, moves as a pack
  and locks altars (or platform match groups with the packaged candidates), since local self-play rewarded the very
  build that loses on the platform.

### Gaps
- Platform test results for p64 / p63sq* candidates do not exist yet (not submitted).
- Opponent names / ratings for the E63 and E67 match groups were not recorded (`cambc login` not done for that pass).
