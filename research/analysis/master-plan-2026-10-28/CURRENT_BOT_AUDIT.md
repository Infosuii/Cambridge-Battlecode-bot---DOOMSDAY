# Current bot audit: v76 (frozen `bots/v76/src`, about 16.5k lines)

Sources:
- the source code
- saved runs `artifacts/evaluations/v67/SA-*` (seed 71, 140 paired games each)
- the earlier evidence register `research/algorithmic-plan-2026-10-28/FINAL_DEEP_ANALYSIS.md` (E1–E28)
- the deep analysis @ 19109c4

No new games were run for this audit.

## 1. The decision pipeline, end to end

Each subsystem is checked against eight questions:
1. decides what
2. executed?
3. overridden by
4. conflicts
5. fuel
6. mechanically valid
7. demonstrably useful
8. replaceable

| Stage | v76 implementation | 1–2 Decides / executed | 3–4 Overrides, conflicts | 5 Fuel | 6 Valid | 7 Useful (evidence) | 8 Verdict |
|---|---|---|---|---|---|---|---|
| Draft | `draft.cpp`: V70 table (30 maps) → ML draft (53×64 MLP, non-table maps) → map-class lineup → preset | Lineup; executed | Header to draft memory | ~1% of a draft turn | Valid; ignores Prospector/Capture economics | V70 transferred to ladder (+142 with knobs); ML net −116/−112 on changed drafts (n.s.) | Keep the table; re-select on the final controller; optional deterministic draft for unseen maps |
| Map interpretation | `read_facts`, brain map class, V71 per-map rows keyed on exact map identity | Knob profiles per map | Overwrites global knobs | negligible | Exact-identity keys don't generalise (E6) | Map knobs −100/−171 when removed (in-sample) | Keep for pool maps; generalise only if held-out LOMO > 0 |
| Strategic objective | None as a team object. Implicit via per-champion farm, hunt, join-fight, rush | — | Each layer early-returns | — | — | — | **Missing**: add team objectives (TEP) |
| Champion assignment | `score_groups` (value/cost, claims, belief divisor) + campnet re-rank (≤40-round commit) | Group per champion; executed | Claims (7-bit) only | **~32%** of fuel | Ignores crew composition, respawn arrival, follow-up, Prospector/Capture | Campnet −58/−91 removed (n.s.) | Replace with TEP (crews, timing, contest, items) |
| Movement | `walk_toward(bitboard)`, per-group distance fields built incrementally, flee field | Executed | — | Part of world update (27%) | Valid | Proven infrastructure | **Keep** |
| Combat | `handle_enemies`: 5 verdict writers (base TTK/TTD formula, burst, tactical_decide, knob-41 engage, team numbers) + 6 early-return owners + 5 executors | Fight or flee and action; executed | Last writer wins; objective-blind; per champion | 7% + tdecide 3% | Partly: phantom-free, no objective value; `worth += 0.5` for recalling enemies (exploitable, see TOP_TEAM M-E) | Deaths 2× in losses; step-away 28% vs 8%; local fight changes never helped | Replace the verdict with EE; keep executors |
| Farming / clear | `farm()` → `fight_camps`, staging, need counts, stage timeout | Executed | Pre-empted by combat | in farm 45% | Valid | Proven | Keep as executor under TEP roles |
| Capture | `capture_stand`, finish-before-reset, single-capturer leave (v58 R3) | Executed | Early return in combat | small | Valid; Capture emblem time read at runtime | Proven | Keep; TEP chooses who captures |
| Shopping | `build_for` (V58_ITEM_PLAN): Prospector → Jungle → Durability → Monster → Capture → Collectors → Greed stacks | Executed on spawn or death | — | small | **Prospector valued nowhere in camp choice** (`prospector_bonus` computed, unused); fixed order regardless of role | Sprint-3 item package +136..+153 vs v57 locally | Rework: marginal-value gear planner (ALGO §7) |
| Banking | `tribute_if_needed`, carry threshold (`kTributeCarry` from brain/knobs), stale-bag altar avoidance, win-now, `deny_tribute`, altar locks | Executed | Recall-cancel conflict (M1 bug) | small | **M1: winning-bag recall restarts while banking is disabled** (confirmed by trace) | Conversion 63% vs 88% in losses | Fix M1 now; hazard-based BANK (ALGO §4) |
| Victory | win-now tribute; no explicit race model | Executed | — | — | No time-to-1000 race estimate; no endgame lock policy | — | Add a race controller (ALGO §8) |

## 2. Combat authority (finished investigation)

Resolving all compile flags and constants (`common.h`) gives the active order in `handle_enemies`
(`bot.cpp:3162–4219`):

1. **Early-return owners, which run before any verdict exists:**
   - `camp_contact`
   - `capture_stand` (V58 = 2)
   - `deny_capture`
   - `bush_ambush`
2. **Verdict 1, the base formula:**
   - `winning = ttk·risk·ci < min(ttd,8)·aggression`
   - `in_danger = ttd < kDangerTtd·… ∨ hp < kDangerHp`

   Aggression and danger are rescaled every turn by `brain::adapt`, A2_LAB knobs 0–3, 22–23, 43–44, and the V71 row.
3. **Verdict 2, burst danger** (NOVA_BURST_K 1.0): ready nukes plus basic hits in reach ≥ HP, so danger is set.
4. **Verdict 3, `tactical_decide`** (APEX_TS_DECIDE 1, A2_TD_AUTH 1): a search with learned exchange rates. A fight
   verdict is ignored when the risk is unmodelled.
5. **Verdict 4, lab knob 41 team-fight engage:** a local strength ratio ≥ 2.38 forces fight.
6. **Then:**
   - `deny_tribute` (early return)
   - bush recall
   - `caster_micro` for casters
   - NOVA_FLEE_HIT (melee hits before leaving)
   - `escape_or_stand`
   - flee, kite, fight or gap-dash executors

Inactive (compiled or tuned off): outnumbered, BURST2, C&I-outnumbered, side-HP, commit-retreat, team fight
commander, neural policy, fight sim, FIGHT2 gate, ASSESS, DISENGAGE, burst-hold, tactical *search*.

**Findings:**
- The verdict is two booleans overwritten in sequence; no layer sees why an earlier one wrote.
- Objective value (capture timer, camp progress, ally bags) never enters the verdict.
- There is no shared team stance: the team fight commander is off, and fight-order claim codes 112–118 are unused.

**Evidence for redesign:**
- the step-away and reversal statistics
- 26% of local deaths come from `winning` overriding `in_danger`
- dive deaths 5.1 vs 1.7

**Evidence against redesign:**
- every incremental fight change has been neutral or negative
- the tuned knob layers are load-bearing (§4)

## 3. Computation (verified against saved evidence)

- **Engine fuel traces (SA-P-base):** mean 40–44k per turn, p50 ≈41k, p90 ≈67k, p99 ≈82k, 0.49 fuel-outs per game.
- **Instrumented profile (behaviour-altering, so shares only):**

  | Section | Share |
  |---|---|
  | farm | 45% (score_groups 32%) |
  | world update | 27% (hot zones 17%) |
  | handle_enemies | 7% |
  | tactical_decide | 3% |
  | campnet | 1.3% (567 fuel per turn) |
- **Conclusion confirmed.** Camp scoring and world updates dominate; neural inference is cheap. Fuel is **not binding
  at the median (≈59k headroom) but is tight at the tail (≈18k at p99)**.
- **Fuel-outs suspend the bot.** Tactical search on: 16 fuel-outs per game and −366 gems.

## 4. Learned and tuned components: matched ablations

140 paired games each, seed 71, 70 maps × 2 sides. Effect of removing (or, for tactical search, enabling) each
component:

| Change | vs proxy | vs v65 | Verdict |
|---|---|---|---|
| Campnet off | −58 [−174, +48] | −91 [−225, +41] | Undecided; replaced by TEP if TEP passes |
| ML draft off (changed drafts only) | −116 [−258, +25] | −112 [−298, +79] | Retain provisionally |
| V71 map knobs off | **−100 [−200, −9]** | **−171 [−283, −54]** | Retain (in-sample by map) |
| A2_LAB + map knobs off | **−148 [−256, −44]** | **−197 [−305, −93]** | Retain |
| APEX_TSEARCH on | **−366 [−470, −263]** | **−325 [−453, −204]** | Remove |
| `tactical_decide` | not ablated | — | Replace with EE; first measure it (V-C0) |
| Compiled-out nets (policy, assess, enemy net, move, tile, ML plan, TS local net, learner) | inactive | — | Exclude from design; keep source |

Leave-one-map-out test on the v70 draft league:
- per-map oracle +134 in-sample
- feature-predicted only +17 [−13, +52] out of map

**Per-map value is real but does not generalise by coarse features.**

## 5. Strategic failures, in order of measured impact

1. **Contest losses.**
   - Deaths: 2× dead champion-rounds in losses.
   - Retention: we keep 62–66% of our uncontested income, opponents keep 93–96%.
   - Equipment: we trail by 871 gold at R500.
2. **Opening economy against top teams.** Fish 483 vs our 278 gold at R100; R250 1444 vs 739.
3. **Item economics not modelled.** Prospector and Capture make clusters high-rate solo objectives, but camp choice
   ignores them.
4. **Banking conversion and the M1 bug.**
5. **No team objective or stance.** Per-champion greedy with 7-bit claims.
6. **Exploitable target valuation.** `worth += 0.5` for recalling enemies, against perma-recall teams.

## 6. Reusable infrastructure (verified useful; keep)

- **Engine interface:** SDK wrappers, the `World` update, claims I/O, NOVA_SEED, the draft memory header.
- **Spatial:** distance fields (incremental `build_fields`), `walk_toward`, the flee field.
- **Combat executors:** `kite_step`, `caster_micro`, `position_and_attack`, gap-dash, `escape_or_stand`, flee-hit.
- **Objectives:** capture and staging executors, `fight_camps`; tribute, recall and altar-lock execution; `build_for`
  purchase execution.
- **Tuning assets:** the V70 draft table, the V71/A2 knob tables (still acting on retained v76 paths), and the
  `APEX_PROFILE` instrumentation pattern.
