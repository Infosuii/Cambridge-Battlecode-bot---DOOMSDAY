# Algorithmic DOOMSDAY blueprint: OCC (Objective–Crew–Combat) controller on v76 infrastructure

This is the implementation blueprint for Architecture B (ARCHITECTURE_COMPARISON.md). It is meant to be complete
enough that an implementation agent makes **no architectural decisions**: only engineering ones, within the stated
budgets and contracts.

The detailed algorithms live in:
- DRAFT_AND_ECONOMY_DESIGN.md: ledger, ObjModel, TEP, banking, shopping, opening, draft
- COMBAT_AND_COORDINATION_DESIGN.md: EE, survival rules, crew protocol
- COMPUTATIONAL_DESIGN.md: budgets

E-numbers refer to FINAL_DEEP_ANALYSIS.md.

**Not implemented. No source has been written. Implementation requires the user's explicit approval.**

---

## 1. Overall architecture

```
                 ┌──────────────────────────── per champion instance, every turn ─────────────────────────────┐
 draft phase ──► │ M7 Draft (V70 table → ML draft → [OCC_DRAFT optimiser] → presets)                           │
 (10x fuel)      │ M9 Opening schedule [OCC_OPEN] → draft memory bytes 8..39                                  │
                 └────────────────────────────────────────────────────────────────────────────────────────────┘
 play turn:
   M8 FuelGovernor.start()                     budget tiers: FULL / LEAN / FALLBACK (v76 path)
   M0 World.update()        (v76, reused)       own vision, camps, fields (incremental), allies, enemies
   M1 TeamLedger.sync()     [OCC_LEDGER]        group beliefs, timers, claims, beacon decode, EnemyBelief
   v76 knob layer           (unchanged)         brain::adapt, V71 rows, A2_LAB (they keep acting on v76 code paths)
   channel guard            (v76 + S7 fix)      never cancel a winning-bag recall while banking is disabled
   ┌─ threat present? (enemy ≤10 or hidden pressure > θ) ─────────────────────────────────────────────────────┐
   │ yes → M4 EE.decide(scene, role, V_obj, crew_stance)  [OCC_EE ≥2]   else v76 handle_enemies                  │
   │        stance ∈ {FIGHT(t), HOLD(o), KITE(t), DISENGAGE, RETREAT, CONTINUE}                                │
   │        non-CONTINUE → executors (v76) + free-action rule → M5 publish → return                           │
   └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
   win-now / BANK priority (v76 win_now + §A.4 hazard rule)
   M3 TEP.role()            [OCC_TEP ≥2]   else v76 farm()/score_groups/campnet
        role ∈ {CLEAR g, CAPTURE g, ESCORT a, BANK altar, SHOP, DEFEND a, MOVE_TO g (respawn arrival)}
        → objective executor (v76 farm internals: walk_toward, fight_camps, capture, tribute, shop/build_for)
   opportunistic (ward, lock, pre-lock): only if budget tier == FULL
   M5 CrewProtocol.publish()  claims (unchanged codes) + typed beacon [OCC_CREW]
```

**Decision ownership (strict):**

| Decision | Owner | May be overridden by |
|---|---|---|
| Channel continue/cancel | channel guard (v76 + S7 fix) | EE RETREAT only, and only if P_die_next > 0.5 |
| Fight/flee/hold/kite when a threat is present | **EE (single authority)** | nothing; the personal-danger override lives inside EE |
| Which objective / crew / role | **TEP** | EE (temporarily, while a non-CONTINUE stance is active) |
| Bank now | TEP BANK objective, win-now rule | EE (a threat on the path delays it) |
| What to buy | v76 `build_for` (S6 later) | — |
| Draft | M7 chain | — |
| Low-level move/attack/cast legality | v76 executors | — |

**Override rules.**
1. EE output is final for the turn when its stance is not CONTINUE.
2. TEP runs only when EE returns CONTINUE or no threat is present.
3. No module writes `winning` / `in_danger` except EE stage 2's mapping layer. The other verdict writers are bypassed
   when OCC_EE ≥ 2: base formula, burst, tactical_decide, knob-41 engage.
4. Early-return owners (capture_stand, camp_contact, deny_capture, bush_ambush, deny_tribute) run unchanged at stage
   2. At stage 3 they become EE stance options.

## 2. State representation

| State | Owner | Lifetime | Invalidation |
|---|---|---|---|
| World `w` (v76) | M0 | per turn | rebuilt each turn |
| Distance fields per group, spawn, altars | M0 (v76 `build_fields`) | game | static terrain; built incrementally under budget |
| `GroupBelief[G]` | M1 | game, per champion | own vision overrides; claims and beacon events; deterministic respawn timers; UNKNOWN after 2× respawn time unseen |
| `EnemyBelief[≤5]` (pos, round seen, hp, bag, items, dead_until) | M1 | game | on sight; death known via kill events/claims (`dead_until = round + 60`) |
| `Assignment` {objective, crew mask, role, start, milestone, ρ} | M3 | until complete or released | progress contract (6 rounds), replan triggers, EE non-CONTINUE |
| `StanceMemory` {last stance, round, target id} | M4 | 1–6 rounds | expires 2 rounds after contact ends |
| Crew stance (from beacon) | M5 | 2 rounds | type and round check |
| Opening schedule | M9 → draft memory | R0–R120 | dropped on first ledger mismatch |
| Calibrated scalars (EE ×8, TEP ×6, λ_gold, λ_tempo) | constants (+ per-map rows later) | build | — |

**Hidden information.**
- Enemies: EnemyBelief with a reachability ramp gives the pressure.
- Unseen camps: ledger timers plus claims.
- Ally positions: own vision, else claimed objective position.
- No module may treat an unseen enemy as absent: phantom weights apply (COMBAT_AND_COORDINATION_DESIGN §C.2).

## 3. Algorithms (summaries; the detail documents are normative)

### 3.1 Draft (M7)

The chain is unchanged from v76: V70 table → ML draft → class/preset. `OCC_DRAFT=1` inserts the exhaustive utility
optimiser *before* the ML draft on non-table maps. It may only be enabled after it wins V-D1. Draft memory layout:
DRAFT_AND_ECONOMY_DESIGN §B.3.

### 3.2 Economy (M1–M3, M9)

- **Value scale.** Gem-equivalents, `GE = gems + λ_gold·gold`. λ_gold starts at v76's effective per-map gold weight,
  logged on Day 2, for parity.
- **ObjModel** (validated first):
  - `T_ready = max(max_c field_g(c), respawn_g − t)`
  - `T_clear = HP_g / Σ DPS_camp · κ`
  - `D_taken`, `T_cap = 5`
  - `Reward = gems + λ·gold·capturer multiplier`
- **Rate.** `ρ = P_ok · Reward / champion-rounds`.
- **TEP.**
  - Each champion solves the team assignment from its belief and commits its own job by claim. Later movers solve the
    residual.
  - Regret-2 greedy crews (size 1–3), single capturer, follow-up lookahead γ = 0.5.
  - Progress contract: 6 rounds, then release and avoid for 15/40.
  - Replans on events or every 8 rounds; 15% hysteresis.
- **BANK.** Hazard rule `bag·h·T > T_trip·ρ̄·η`, the win-now guard (S7) and altar avoidance under pressure.
- **SHOP.** Free when dead or on spawn; piggy-backed on trips; emblem completion priority.
- **Opening (optional).** A TEP rollout at draft time, used as a ×1.3 prior that is dropped on mismatch.

### 3.3 Combat (M4)

- Scene ≤11 units, phantom enemies from the belief.
- Stances: FIGHT(top-2 targets), HOLD, KITE, DISENGAGE, RETREAT, CONTINUE.
- 4-round focused exchange simulation, optimistic and pessimistic, mixed by π.
- `V = Σ KillValue − Σ DeathCost + V_obj·P_obj − V_obj_lost − ρ̄·rounds_lost`.
- Hysteresis margin `m_commit = 0.15·DeathCost(me)`; personal override `P_die_next > 0.5`.
- Free-action rule.
- Executors are v76's. Staged rollout 0 → 4 (COMBAT_AND_COORDINATION_DESIGN §C.6).

### 3.4 Coordination (M5)

- Claims are unchanged: 6 × 7 bits.
- The beacon becomes 2 type bits + 20 payload bits: SIGHTING / CAMP_EVENT / CREW_STANCE / TEAM_MODE, with
  pre-emption.
- Crew leader = lowest slot in the crew. Use `set_priority` so the leader acts first.
- DEFEND objectives from distress, joined only with an arrival-in-time check. ESCORT for big bags under path
  pressure.
- No `need = team_size`.

### 3.5 Pathfinding and movement

- No new path search on the hot path.
- Use the v76 group, spawn and altar distance fields and the flee field, the SDK movement mask, and
  `walk_toward(bitboard)`.
- ObjModel uses walking distance only; dashes are a bonus and are not counted.
- Field construction stays incremental (v76 `build_fields`). Groups without a field fall back to Chebyshev × 1.3 in
  ObjModel, flagged so TEP does not commit long trips to unknown-distance groups.

## 4. Module interfaces (contracts, not code)

```
// M1
struct TeamLedger {
  void sync(const World&, uint64 shared_word, int round);          // ≤ 2k fuel; pure function of inputs + own history
  const GroupBelief& group(int g) const;
  float pressure(vec2 p, int tau) const;                            // expected enemies near p within tau rounds
  const EnemyBelief& enemy(int idx) const;
};
// M2
struct ObjModel {
  Pred predict(const Crew&, int g, int round) const;                // {T_ready, T_clear, D_taken, reward, feasible, P_ok}
  float champion_rate(const Champ&, int g) const;                   // single-champion ρ, cached per turn
};
// M3
struct Assignment { Objective obj; uint8 crew_mask; Role role; int start, milestone_due; float rho, v_obj, progress; };
struct TEP {
  const Assignment& role(const Champ& me, const TeamLedger&, const ObjModel&, const Claims&, FuelGovernor&);
  void on_event(Event);                                              // completion, death, respawn, contact start/end
};
// M4
enum Stance { FIGHT, HOLD, KITE, DISENGAGE, RETREAT, CONTINUE };
struct Decision { Stance s; EnemyId target; vec2 goal; float v[6]; };   // v[] logged in trace builds only
struct EE { Decision decide(const Scene&, const Assignment&, const CrewStance&, FuelGovernor&); };
// M5
struct CrewProtocol { CrewStance read(uint64) const; uint64 write_stance(uint64, ...) const; uint64 write_mode(...) const; };
// M8
struct FuelGovernor { Tier tier() const; bool allow(uint32 est_cost) const; void start(); };   // reserve R_hard = 12k
```

**Contracts:**
- Every module is deterministic given its inputs and NOVA_SEED.
- No module calls another module's internals.
- EE and TEP never call SDK actions. Only executors act.
- Every module has a v76 fallback path selected by `FuelGovernor::allow` or by its flag.

## 5. Runtime (summary; detail in COMPUTATIONAL_DESIGN.md)

| Item | Budget |
|---|---|
| Mean turn | ≤ 48k (v76: 41k) |
| p99 turn | ≤ 88k (v76: 82k) |
| Fuel-outs | ≤ 0.6 / game (v76: 0.49) |
| Hard reserve | 12k (FALLBACK tier below 25k remaining) |
| EE | ≤ 12k, contact turns only |
| TEP replan / check | ≤ 8k (cap 15k) / ≤ 1k |
| Ledger | ≤ 2k |
| Draft optimiser + opening | ≤ 850k on draft turn 1 (of 1M) |
| Shared memory | 64 bits (claims 42 + typed beacon 22) |
| Draft memory | ≤ 72 of 1024 bytes |

## 6. Integration plan

**Location.** New bot `bots/v86` = a copy of frozen `bots/v76/src` plus new files:
- `occ_ledger.{h,cpp}`
- `occ_model.{h,cpp}`
- `occ_tep.{h,cpp}`
- `occ_ee.{h,cpp}`
- `occ_crew.{h,cpp}`
- `occ_gov.h`
- `occ_trace.h` (trace builds only)

The frozen `bots/v76` is never edited.

**Hooks in v86 `bot.cpp`.** Each is guarded by `#if OCC_*`; the `#else` branch is v76's line, unchanged.
1. `play_turn` start: `gov.start()` and `ledger.sync()`.
2. The channel guard: S7 fix (`OCC_FIX_RECALL`).
3. `handle_enemies()` entry:
   - stage ≥ 2: EE first
   - stage 2: map to flags and continue into v76 execution with the other verdict writers skipped
   - stage ≥ 3: own execution
4. `score_groups()` entry: return TEP's assignment. The pattern already exists for `A2_SOLE_GEM` and
   `V58_DIRECTOR economy_assignment` (`bot.cpp` ≈5430).
5. `farm()` capture branch: the single-capturer leave rule (TEP role CLEAR, after the last kill).
6. `publish`: the beacon typing.

**Flags** (all default 0, so the build is byte-identical to v76 at all zeros):

| Flag | Values |
|---|---|
| `OCC_FIX_RECALL` | 0/1 (S7) |
| `OCC_GOV` | 0/1 |
| `OCC_LEDGER` | 0/1 (1 = maintain and log only) |
| `OCC_TEP` | 0 / 1 shadow / 2 owns farming / 3 + BANK·SHOP objectives |
| `OCC_EE` | 0 / 1 shadow / 2 verdict / 3 stances / 4 crew |
| `OCC_CREW` | 0/1 |
| `OCC_OPEN` | 0/1 |
| `OCC_DRAFT` | 0/1 |
| `OCC_TRACE` | 0/1 (never in a release) |

**Byte-identity proof.** Build v86 with all flags 0 and compare the Wasm SHA-256 with v76's (`42071fa6…`, as
recorded for v81–v83). This is required before any experiment.

## 7. Testing (summary; VALIDATION_PLAN.md is normative)

1. **Unit / host tests.**
   - ObjModel and the EE exchange model ported to Python, checked against replay-extracted cases.
   - Shared-word encode/decode round-trip.
   - Ledger timer arithmetic.
2. **Offline model gates.**
   - ObjModel against SA-IDLE-v76 replays.
   - EE death-Brier against the v76 `in_danger` flag on recorded contacts.
3. **Shadow builds** (OCC_* = 1): fuel and disagreement logs on idle and contested runs.
4. **Mechanism gates (idle):** TEP non-inferiority, opening, shop.
5. **Scenario gates (puppet takeovers on the 12 reproduced ladder games, examined set only).**
   - EE stance sanity.
   - The S7 recall loop.
   - Split-engagement windows.
6. **Contested league:** v65, v61, v58, proxy and v76; 140 games each; fresh seeds 101+; plus a held-out map set.
7. **Ladder duel:** only with the user's explicit approval, because it activates arms.

## 8. How OCC avoids the V81–V85 (and earlier) failures

| Past failure | Cause | OCC countermeasure |
|---|---|---|
| v81 action sequences −532 | Immediate damage as the objective; approximate response; fuel overrun | EE values deaths, kills, objectives and tempo; calibrated offline; ≤12k budget with fallback; v76 executors kept |
| v82 coalition scheduler −89..−115 uncontested | Unvalidated travel/clear model; job held without progress (02arena) | ObjModel replay gate before TEP; progress contract; idle gate first |
| v83 learned intent −65 vs proxy | Imitation labels without fight value or coordination | Value-based stance (no imitation); crew stances |
| v84 denial −886 | Starved own economy | No fixed guards; contest only as a valued objective with crew strength |
| v85 rendezvous −231 | Harvest gain without gear or bank follow-through; unbounded geometry loops | TEP follow-up lookahead, BANK / SHOP objectives; all loops budgeted |
| v58 director (0/20), A2_DPLAN −217 | Stale plans, team schedules without a live check | Per-turn validation, event replans, advisory opening only |
| v79 team fight −24..−107 | Added verdict layers on top of the stack; long leave locks stopped farming | Replaces the verdict stack (single authority); stances expire; TEP resumes immediately |
| tsearch −366 | Unbounded search, fuel-outs (16/game) | Analytic O(n·H) model, governor tiers, hard reserve |
| Funnel / meta draft / carry | Copying surface choices | Single capturer only within the crew; drafts stay league-selected |
| Seed- and lineage-overfit "wins" | Self-play on reused seeds | Fresh-seed ledger (101+), held-out maps, scenario replays from ladder losses, ladder duels |
