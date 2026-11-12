# x1 macro layer: case-based plan selection over influence maps (architecture and test cases, 2 Nov 2026)

Brief (Rishik, adapted to CAMBC): a multi-agent bot that **remembers, retrieves and executes macro strategies by
topological state similarity** (case-based reasoning), uses **influence maps** to evaluate terrain on novel maps (choke
points, high-value zones), and adapts retrieved cases to the current map and game in real time. Sources: Weber &
Mateas, *Case-Based Reasoning for Build Order in RTS Games* (AIIDE 2009); Sugandh, Ontañón & Ram, *On-Line
Case-Based Plan Adaptation for RTS Games* (AAAI 2008); Hagelbäck thesis (dead-end filling, choke clearing,
section 4.11 of PAPERS_BATCH2_NOTES.md); Tribes / EA notes (one module behind a switch).

## 1. Why CBR here, and what changes from the papers

| Paper element | Their setting | Ours |
|---|---|---|
| Case = (game state, behaviour) from expert or scripted traces | Wargus build orders; ~1,500 cases from 36 traces of winning scripts | (map topology + game state at round r, team plan p) **with an exact measured outcome**: the J005 branch farm replays every game with each plan switched in at r = 150/250/350 (12,000 branches, prefix-exact). No guessing which action "caused" the win. |
| Retrieval: conceptual neighbourhoods (exact match on a feature subset; generalise features with edit-distance costs; weighted random choice) | beat nearest neighbour under fog (66% vs 50%) and kept improving with more traces | same, deterministic: weighted mean of measured gains, highest wins, ties to plan 0; switch only if the evidence clears a safety margin (safe exploitation) |
| Map properties as case features (direct path; distance close/medium/far) | 2 hand-coded properties | computed by **influence maps** on any map: corridor length, choke count / min width, value split home / contested / enemy, dead ends, size, team size |
| Behaviours with preconditions, **alive conditions**, success conditions; on-line adaptation | Darmok plan trees | each team plan has an alive condition checked every round; violation -> fall back to plan 0 and re-retrieve at the next checkpoint |
| Parameter adaptation (coordinates bound to the current map) | units / positions | plan spatial parameters (home zone, choke tile, contested zone) bound to this map's influence map |
| Agents communicate through a blackboard (ABL working memory) | one process | 8-byte shared memory: slot 0 decides, writes plan id + round in 6 bits; every champion reads it |

What we do **not** copy: learning from human demonstrations (we have exact counterfactuals instead), random case
selection (games are deterministic, so selection must be too), and per-action plan trees (x1's per-champion logic
stays; plans steer it through knobs, the proven hook).

## 2. Architecture

```
            draft turn (10M fuel)                       champion turns (200k first, then 100k)
  +---------------------------------+      +------------------------------------------------------------+
  | Draft (unchanged x1)            |      | World (x1): camps, groups, fields, sightings                |
  +---------------------------------+      |   |                                                         |
                                           |   v                                                         |
                                           | [IM] Influence-map builder (X1_IM)   -- lazily, 2-4 turns    |
                                           |   corridor, chokes, value zones,      -> MapDescriptor (8 B) |
                                           |   dead ends, zone membership bitboards                       |
                                           |   |                                                         |
                                           |   v                                                         |
                                           | [SA] Situation assessor (every checkpoint r in {150,250,350})|
                                           |   our/their banked, team deaths, kills, team gold (SDK),     |
                                           |   carried gems -> StateDescriptor                            |
                                           |   |                                                         |
                                           |   v                                                         |
                                           | [CR] Case retrieval (X1_CBR), slot 0 only                    |
                                           |   conceptual neighbourhoods over the compiled CaseTable      |
                                           |   -> plan id p*, confidence                                  |
                                           |   |  shared memory: 3 bits plan + 3 bits checkpoint          |
                                           |   v                                                         |
                                           | [EX] Plan executor = X1_PLAN hook, plan id now runtime       |
                                           |   knob overrides (territory, aggression, carry, hunt)        |
                                           |   + spatial binding from IM (home zone, choke tile)          |
                                           |   |                                                         |
                                           |   v                                                         |
                                           | [AD] Adaptation monitor (every round)                        |
                                           |   alive condition of p*; violated -> plan 0 until next r     |
                                           +------------------------------------------------------------+
  offline (5060):  J005 rows + harvested MapDescriptors  ->  case library builder  ->  CaseTable (C++ header)
```

### 2.1 Influence-map builder (IM)

Inputs already in x1's World: passable tiles (`~w.static_blocked`), our spawn distance field, the enemy spawn field
(`ensure_enemy_field`), camp groups with gems, gold, respawn time and position, `group_margin`.

| Layer | Definition | Cost |
|---|---|---|
| Corridor | tiles with `d_own + d_enemy <= D + s` (D = spawn-to-spawn distance, s = 4): the near-shortest routes between the bases | O(tiles), two existing fields |
| Width profile / chokes | for each distance level k = d_own on the corridor, width w(k) = number of corridor tiles at that level; a choke is a level with w(k) <= 3 that has wider levels on both sides; its tile = the level's middle tile | O(tiles) |
| Dead ends (thesis 4.11) | passable tile with walls within 5 in >= 9 of 16 directions; marked unsafe for retreat | bounded: 16 rays x 5 per tile, built over 2-3 turns |
| Value zones | per group rate v = (gems + g_w * gold) / respawn; zone = home (margin >= +4), contested (\|margin\| < 4), enemy (<= -4) | O(groups) |
| Influence | value field: sum of v / (1 + d) over groups (d by path distance); threat field: decaying enemy sightings (A2_BELIEF style) | value: once; threat: per turn, local window only |

**MapDescriptor** (8 bytes; also printed once as `X1IM ...` with `X1_IM_LOG` for offline harvesting): D class
(close < 30, medium < 55, far), choke count on the corridor (0, 1, 2+), min corridor width class, value share
home / contested / enemy (3 x 4 bits), team size, area class, dead-end share class.

### 2.2 Situation assessor (SA)

At each checkpoint r: banked gap (ours - theirs, from `global_submitted_gems`), team deaths so far (alive->dead
transitions, as X1_ANTIFEED), kills (`team_kills_seen`), team gold and carried gems (`sdk_champion_gold/gems` over
`num_handles[0]`). **StateDescriptor**: r, banked-gap class (<-50, -50..50, >50), deaths class (0-2, 3-5, 6+),
kills-minus-deaths sign, gold-gap class where knowable (own gold only under fog: own-gold class).

### 2.3 Case library and retrieval (CR)

**Case** = (MapDescriptor, StateDescriptor, plan p, outcome): built offline from J005 rows, one case per (map, side,
opponent, r, p) with outcome = exact branch result vs its baseline (win flip +1 / -1 / 0 and margin delta).
Aggregated into the **CaseTable**: for each (exact key, plan) the count, mean margin delta and net flips, plus the
generalisable features' values; compiled into the bot as a constant table (size target < 16 KB).

**Retrieval (conceptual neighbourhoods, deterministic):**
1. *Exact features* (must match): checkpoint r, team size, D class.
2. *Generalisation methods* in order of cost, each relaxing one feature and adding its edit cost: choke class (1),
   value-share bins (1 each, by bin distance), deaths class (2), banked-gap class (2), area class (1), dead ends (1).
   Up to G = 3 generalisations.
3. *Recall*: all cases matching the remaining features; weight = 1 / (1 + total edit cost).
4. *Evaluate*: for each plan, weighted mean margin delta and weighted net flips; candidate = best plan by net flips
   per case, margin delta as tie-break.
5. *Safety*: switch only if candidate's weighted support >= N_min and its lower bound (mean - k * stderr) > 0;
   otherwise plan 0. This is the "safe exploitation" rule from the strategy synthesis.

### 2.4 Plan executor and spatial binding (EX)

The X1_PLAN hook's plan id becomes a runtime value (set by CR via shared memory; volatile reads stay for the farm).
Spatial binding from the IM: *turtle* (4) and *early-contact answer* (6) use the IM home zone instead of the fixed
territory value; a new *choke hold* behaviour (plan 9, after the first CBR gate) farms home and parks one healthy
champion on the corridor's nearest choke tile when enemies are sighted beyond it; *full map* (1) and *push* (8)
weight contested-zone value up.

### 2.5 Adaptation monitor (AD), Darmok alive conditions

| Plan | Alive while | On violation |
|---|---|---|
| 4 turtle / 6 early-contact | our home-zone camps are not being taken (enemy sightings in our home zone < 3 in 50 rounds) and banked gap is not worsening by > 100 per 100 rounds | plan 0 until the next checkpoint |
| 3 fight harder / 8 push | kills - deaths since the switch >= -1 | plan 4 until the next checkpoint |
| 2 hoard / 7 fast bank | no carried bag lost since the switch | plan 0 |

## 3. Workload split (usage-aware)

| Who | Work | Why there |
|---|---|---|
| PC (this session) | this design; IM builder + `X1IM` log line (X1_IM); runtime plan id + shared-memory broadcast; retrieval + adaptation code (X1_CBR); host tests T1-T5, T7 | code lives here, single writer of bots/x1; small compute |
| 5060 | J011 harvest MapDescriptors on all 120 maps (+ maze); J012 build the case library from J005 rows + descriptors, leave-one-map-out evaluation (T6) vs nearest neighbour and fixed plans; gates T8 | game volume and the farm rows are there |
| 5070 Ti | none (its 1.5 h are K001-K003) | |

## 4. Algorithmic test cases

| ID | Tests | Method | Pass |
|---|---|---|---|
| T1 | IM determinism and side symmetry | every champion of both teams logs X1IM on the same map | identical descriptors within a team; mirrored zones swap home / enemy on symmetric maps |
| T2 | Choke detection | synthetic maps: open field, one 1-wide corridor, two corridors, a 3-wide neck | open: 0 chokes; corridor: 1 choke at the neck level; two corridors: no choke (width sums); 3-wide: 1 choke |
| T3 | Value zones | sum of zone values = total group value; mirror maps: home = enemy share | exact equality; symmetric shares within one bin |
| T4 | Fuel | IM build on the largest map (80x80, 166 camps) spread over first turns; full games | zero added fuel-outs vs base (gate rule) |
| T5 | Retrieval correctness | query = a stored case's exact key -> its best plan; adding generalisations increases edit cost monotonically; ties -> plan 0 | all pass; deterministic across runs |
| T6 | **Generalisation to novel maps** (the point of topology features) | leave-one-map-out on J005 rows: library without map m picks the plan for m's positions; score = realised net flips of the chosen branch (exact, from the rows) | CBR > always-plan-0, > always-best-single-plan (plan 4), > nearest neighbour on raw counts; reported per map kind; maze maps held out entirely |
| T7 | Adaptation | scripted state sequences: alive condition violated at round t -> plan 0 from t+1; no plan flapping (one change per checkpoint) | exact |
| T8 | Whole-game gate | X1_CBR vs base on ladder + styled + maze, x2 and x2-s2 | gate rule (RETRY_QUEUE R1) |
| T9 | Multi-agent consistency | log each champion's executed plan id per round | all champions of a team agree every round after the broadcast |
| T10 | Spatial adaptation | plan 9 choke hold on maps with 0 / 1 / 2+ chokes | falls back to plan 4 when the map has no choke; the parked champion's tile is the corridor choke tile |

## 5. Order

1. PC: X1_IM + X1IM log line, T1-T4 locally (this step).
2. 5060: J011 harvest; J012 library + T6 (needs J005 complete).
3. PC: X1_CBR (retrieval, broadcast, adaptation), T5, T7, T9; CaseTable header generated from J012.
4. 5060: T8 gates; T10 after plan 9.
5. Retry protocol applies: a negative T8 is retried with the library rebuilt on more rows (J005 seeds 2-3) and other
   safety margins before anything is rejected.

## 6. First data check (2 Nov, PC): map topology does not predict the plan-4 gain

716 paired games (5060 gates: ladder, styled, maze A + B; x2 and x2-s2), bp vs bp + plan 4 from R100 / R150, with
map features computed offline (area, team, groups, spawn distance D, wall / bush share, home / contested value share,
min corridor width, chokes) and own state at R100 (deaths, gold). Script: tools-free scratch, rows reproducible from
the 5060 run records.

| | always plan 4 | correlation of per-game gain with any feature | leave-one-map-out best single-feature rule |
|---|---:|---|---:|
| plan 4 R100 | +22 | all within +-0.08 | +25 |
| plan 4 R150 | +25 | all within +-0.07 | -11 (overfits) |

So plan 4 helps about evenly across map types; a selector on map topology has nothing to learn here, and the
in-game state we log (own deaths / gold at R100) carries no signal either. Decision: ship plan 4 as a fixed plan;
the CBR selector is parked until there is opponent-aware state (banked gap from global_submitted_gems, enemy
sightings) in the farm rows, which J005 does not record. PC moves to the team camp planner (TOPTW) next.
