# Data structures, module contracts and the communication protocol

These are interface sketches, not production code. Names are the proposed C++ identifiers in `bots/v86/src/occ_*`.

## 1. Modules and files

| Module | Files | Depends on | Flag |
|---|---|---|---|
| M0 World (v76) | `world.*`, `bot.*` (unchanged except hooks) | SDK | — |
| M1 TeamLedger + EnemyBelief | `occ_ledger.{h,cpp}` | M0, M5 decode | `OCC_LEDGER` |
| M2 ObjModel | `occ_model.{h,cpp}` | M0, M1, M6 stats | (inside TEP) |
| M3 TEP | `occ_tep.{h,cpp}` | M1, M2, M10 | `OCC_TEP` 0/1/2/3 |
| M4 EE | `occ_ee.{h,cpp}` | M0, M1, M3 | `OCC_EE` 0..4 |
| M5 Crew protocol | `occ_proto.{h,cpp}` | — | `OCC_CREW` |
| M6 Gear planner | `occ_gear.{h,cpp}` | M2 stats | `OCC_GEAR` |
| M7 Draft optimiser | `occ_draft.{h,cpp}` | SDK draft calls | `OCC_DRAFT` |
| M8 Fuel governor | `occ_gov.h` | SDK | `OCC_GOV` |
| M9 Opening schedule | `occ_open.{h,cpp}` | M2, M3 (rollout) | `OCC_OPEN` |
| M10 Race controller | `occ_race.{h,cpp}` | M1 | `OCC_RACE` |
| M11 Micro scorer (optional) | `occ_micro.{h,cpp}` | M4 | `OCC_MICRO` |
| Fixes | in `bot.cpp` under flags | — | `OCC_FIX_RECALL`, `OCC_FIX_TARGET` |
| Trace (never in a release) | `occ_trace.h` | all | `OCC_TRACE` |

**Rule.** Every flag at 0 gives a Wasm byte-identical to v76 (`42071fa6…`). Proven before any experiment.

## 2. Core data structures

```cpp
// M1
enum class GState : uint8_t { Alive, Partial, Reward, Respawning, Unknown };
struct GroupBelief {            // ~16 B; G ≤ 112
  GState  state; uint8_t kind;  // kind: DamageBound | CaptureBound (static, from member types)
  int16_t respawn_round, last_seen;
  float   hp_left;              // known or full HP
  int8_t  ally_claim_slot;      // −1 none
  float   pressure;             // cached per turn when needed
  int16_t avoid_until; uint8_t fail_count;
};
struct EnemyBelief {            // ≤5
  uint32_t id; int16_t last_round; vec2 last_pos; float hp, maxhp; int16_t bag;
  int16_t dead_until; uint8_t channel_kind, channel_age; uint8_t items_seen;
  float dps_est, burst_est;
};
struct TeamLedger { GroupBelief g[112]; EnemyBelief e[5]; int ng, ne; int banked_us, banked_them;
                    float gem_income_us, gem_income_them; void sync(const World&, uint64_t word, int round);
                    float pressure(vec2 p, int tau) const; };

// M2/M3
enum class Role : uint8_t { MoveTo, WaitRespawn, Clear, Capture, ClusterRun, Bank, Shop, Escort, Defend, Idle };
struct Pred { int16_t t_ready, t_clear, t_cap; float d_taken, reward_ge, p_ok, cost, rate; bool feasible; };
struct Assignment { int16_t group; uint8_t crew_mask; Role role; int16_t start, milestone_due; float rate, v_obj, progress; };

// M4
enum class Stance : uint8_t { Fight, Hold, Kite, Disengage, Retreat, Continue };
struct Unit { vec2 p; float hp, maxhp, str, rng, dps, burst; uint8_t team, stun_ready:1, dash_ready:1, stun_immune:1, cid; int16_t bag; };
struct Scene { Unit u[16]; int n; int me; float phantom_w; };
struct Decision { Stance s; uint32_t target; vec2 goal; float v[7]; };
struct StanceMemory { Stance s; int16_t since; uint32_t target; };

// M8
enum class Tier : uint8_t { Full, Lean, Fallback };
struct Governor { Tier tier; uint64_t start; bool allow(uint32_t est) const; void start_turn(); };
```

## 3. Module contracts

| Module | Input | Output | Invariants |
|---|---|---|---|
| Ledger | World, shared word, round | beliefs | Pure function of its own history plus inputs; own vision overrides; never assumes an unseen enemy is absent |
| ObjModel | crew, group, round, stats | `Pred` | Deterministic; no SDK actions; fields missing → low-confidence flag |
| TEP | me, ledger, model, claims, mode, governor | `Assignment`, claim write | Commits only my own job; hysteresis; contract check every turn; replan only in tier FULL |
| EE | scene, assignment, crew stance, governor | `Decision` | Single verdict owner; ≤12k fuel; returns CONTINUE if the scene is empty of threats within the horizon |
| Executors | Decision or Role | SDK actions | Only module that calls action APIs; legal-action checks as in v76 |
| Gear | stats, gold, location | purchases | Only on spawn or dead (Tavi: shards anywhere) |
| Protocol | the word | decoded claims, beacon / new word | Never overwrites a fresher higher-priority beacon; claim codes identical to v76 |
| Governor | `fuel_remaining()` | tier, allow | Hard reserve 12k after any OCC module |

**Error handling.**
- Every OCC entry point catches exceptions. On error it returns "not handled", so the v76 path runs this turn, and
  increments `err[module]`.
- At 3 errors the module is disabled for the game.
- No exception crosses into v76 code.

## 4. Shared-word protocol (64 bits)

### 4.1 Layout

| Bits | Field |
|---|---|
| 0–41 | 6 claim slots × 7 bits (unchanged v76 codes: group 0–111, on-site 64+g when G ≤ 48, 112–118 reserved, 126 dead, 127 idle) |
| 42–43 | Beacon type |
| 44–63 | Beacon payload (20 bits) |

| Type | Payload (20 bits) | Writer | Freshness |
|---|---|---|---|
| 00 SIGHTING | sector x 6 (tile/2), sector y 6, round mod 32 (5), distress 1, count−1 (2) | any champion seeing enemies | 4 rounds |
| 01 CAMP_EVENT | group 7, respawn round mod 256 (8), event kind 2 (captured / cleared / enemy-held), spare 3 | observer | until superseded |
| 10 CREW_STANCE | leader slot 3, stance 3, enemy idx 3 (7 = none), rally sector x 5 (tile/4), rally sector y 5 (tile/4), round parity 1 | crew leader in contact | 2 rounds (parity check) |
| 11 TEAM_MODE | mode 3, target group 7, round mod 64 (6), spare 4 | lowest alive slot | 8 rounds |

Sectors: tile/2 covers 128 tiles in 6 bits (maps are ≤100); tile/4 covers 128 tiles in 5 bits. This is the
sector-encoding lesson from [B6].

### 4.2 Pre-emption

CREW_STANCE > SIGHTING with distress (fresh) > TEAM_MODE change > CAMP_EVENT > SIGHTING without distress.

- A writer may overwrite only a lower-priority beacon or a stale one (past its freshness window).
- Within one turn, read the word, apply this champion's writes, and write once: the buffer-pool lesson [B6].

### 4.3 Sufficiency argument

What the design needs teammates to know, and how each fact is represented:

1. **Who owns which objective.** Claims, 7 bits per champion, persistent and updated at least every replan. Up to 6
   champions; teams have 3–5, and C&I count as 2 bodies with 2 slots.
2. **Who is on site.** On-site codes (G ≤ 48), or CAMP_EVENT for larger maps.
3. **Group state changes others cannot see.** CAMP_EVENT carries the group and its respawn round. Respawn timing is
   then deterministic for everyone.
4. **Enemy presence for pressure and reinforcement.** SIGHTING carries sector, count and distress. One message per
   ≤4 rounds suffices, because pressure decays smoothly (reach ramp).
5. **Fight commitment.** CREW_STANCE carries stance, target and rally point. A crew has one leader, and at most one
   active fight per crew is assumed; two simultaneous crews in contact alternate through freshness.
6. **Team mode.** TEAM_MODE is deterministic from shared inputs, so it can be recomputed locally. The beacon is a
   consistency hint only.

**Contention bound.** At most one fight-leader message (2 rounds) and one sighting (4 rounds) compete at a time. When
both are needed, CREW_STANCE wins, and members already in the crew can see the enemies themselves. A sighting delayed
by ≤2 rounds affects only non-crew champions' pressure estimates, which use a ramp tolerant of a 2-round delay.

### 4.4 Missing, delayed or stale data

| Situation | Behaviour |
|---|---|
| Claim stale (>3 rounds, no on-site) | Weight 0.5 in TEP's residual (probably still assigned) |
| Claim names a group out of range | Ignore (as v76) |
| Leader stance absent or stale | Decide alone with π + 0.2 (pessimistic) |
| Sighting stale | Ignore; EnemyBelief ramp continues |
| Team mode stale | Recompute locally (deterministic) |

## 5. Draft memory layout (1024 bytes)

| Bytes | Content |
|---|---|
| 0–7 | v76 brain header (size, max gems, flags), unchanged |
| 8–39 | Opening schedule: per slot ×5, 3 jobs × (group 7 + role 2 + start 8) = 17 bits each, packed |
| 40–71 | Map summary: altar ranks, contested index, cluster-circuit flag, gap flags |
| 72–1023 | Free |

## 6. Configuration

- **Compile-time constants** in `occ_config.h`: default scalars; per-map rows keyed like V71 (w, h, groups, gems).
- **Parameter sets** for style adaptation: 3 rows.
- No runtime file I/O; everything is compiled in.

## 7. Testing hooks

- **`OCC_TRACE=1` builds** print one compact line per decision: stance values `v[7]`, the chosen assignment and its
  rate, and the fuel at module entry and exit. Never used for strength or fuel-out claims, because logging changes
  turns (deep analysis).
- **Pure-function cores** (ObjModel predict, EE evaluate, the protocol codec) take plain structs, so a **host-side
  unit test harness** can call them. The same C++ is compiled natively under `sdk/cpp/tests` style CMake, with no
  engine.
- **Puppet takeover harness** (deep-analysis `tools/replay/puppet/*`, `tests/loss_cases/*`): warm-state regression
  cases, where the baseline fails and the candidate passes.
