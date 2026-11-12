# Data structures, module contracts and communication protocol (DOOMSDAY Zero)

These are interface sketches, not production code. Everything lives in `bots/dz/src/`. No file is copied from a
previous bot.

## 1. Files and modules

| File | Module | Depends on |
|---|---|---|
| `main.cpp` | K0 entry, draft or champion dispatch, exception boundary | all |
| `kernel.{h,cpp}` | TurnContext, Governor (K1), Actuator (K2), error counters, StaleTurn | SDK |
| `config.h` | Compile-time defaults, fuel table, per-map rows, parameter sets, flags (`DZ_*`) | — |
| `static_world.{h,cpp}` | N1: terrain, groups, designs, fields (lazy), regions | SDK |
| `observation.{h,cpp}` | N2: this turn's visible state | SDK |
| `memory.{h,cpp}` | N3: GroupLedger, EnemyBelief, AllyBelief, Stats | N1, N2, protocol |
| `protocol.{h,cpp}` | C1: shared-word codec, pre-emption, freshness | — |
| `crew.{h,cpp}` | C2: crews, leader, stance adoption | protocol, memory |
| `race.{h,cpp}` | S1: TEAM_MODE | memory |
| `objmodel.{h,cpp}` | Pure prediction functions | N1 |
| `economy.{h,cpp}` | S2 auction, roles, contracts, bank rule | objmodel, memory, crew, race |
| `gear.{h,cpp}` | S4 gear planner | memory |
| `threat.{h,cpp}` | T1 scene | observation, memory |
| `engage.{h,cpp}` | T2 EE (pure evaluate plus glue) | threat, objmodel |
| `actions.{h,cpp}` | T3 action scorer and spell policy | engage, economy, kernel |
| `safemode.{h,cpp}` | Fallback behaviour | N1, N2, kernel |
| `draft.{h,cpp}` | Draft engine and opening planner (draft instance) | SDK, objmodel |
| `trace.h` | `DZ_TRACE` diagnostics (never in a release) | — |

Pure-function cores (`objmodel`, the `engage` evaluate, the `protocol` codec, the `draft` utility) take plain structs,
so they compile natively for **host unit tests** (`tests/dz/host/`) without the engine.

## 2. Core structures

```cpp
struct TurnContext { uint32_t round; uint64_t fuel0; Tier tier; bool first_turn; };
enum class Tier : uint8_t { Full, Lean, Fallback };

// N1
enum class GKind : uint8_t { DamageBound, CaptureBound };
struct GroupStatic { uint16_t id; GKind kind; uint8_t n_members; uint8_t types_mask; vec2 centroid;
                     bitboard* spawn_tiles; uint32_t gold, gems; int16_t respawn; float hp_max; uint8_t region; };
struct StaticWorld { int w,h; symmetry sym; bitboard walls, holes, bushes, altars_mask, spawn_us, spawn_them;
                     std::vector<vec2> altars; std::vector<GroupStatic> groups; Designs designs;
                     distance_field F_spawn; std::vector<distance_field> F_altar; std::vector<int16_t> field_slot; /* lazy F_group */ };

// N3
enum class GState : uint8_t { Alive, Partial, Reward, Respawning, Unknown };
struct GroupBelief { GState s; float hp_left; int16_t respawn_round, last_seen; int8_t ally_slot; bool enemy_held;
                     int16_t avoid_until; uint8_t fails; };
struct EnemyBelief { uint32_t handle; champion_type type; vec2 last_pos; int16_t last_round; float hp, maxhp;
                     int16_t bag, dead_until; uint8_t channel_kind, channel_age; int8_t cd[2]; uint8_t recall_pattern; float dps, burst; };
struct AllyBelief  { uint8_t slot; uint8_t objective; bool onsite, dead; int16_t updated; };
struct Stats { float income_ema, gem_income_them, hazard, capture_rate, cluster_rate, kill_rate, gold_rate, dmg_rate, recall_rate; };

// S2
enum class Role : uint8_t { MoveTo, WaitRespawn, Clear, Capture, ClusterRun, Bank, Shop, Escort, Defend, Deny, Idle };
struct Pred { int16_t t_ready, t_clear, t_cap; float d_taken, reward, p_ok, cost, rate; bool feasible, low_conf; };
struct Assignment { uint8_t objective; uint8_t crew_mask; Role role; int16_t start, milestone_due; float rate, v_obj, progress; uint32_t round_computed; };

// T
enum class Stance : uint8_t { Fight, Hold, Kite, Disengage, Retreat, Continue };
struct Unit { vec2 p; float hp, maxhp, str, rng, dps, burst; uint8_t team, cid; bool stun_ready, dash_ready, stun_immune, linked; int16_t bag; };
struct Scene { Unit u[16]; uint8_t n, me; float phantom_n; bool threat; };
struct Decision { Stance s; uint32_t target; vec2 goal; float v[7]; bool keep_channel; };
struct ActionPlan { std::optional<vec2> move; std::optional<uint32_t> attack; std::optional<std::pair<int, Target>> cast;
                    std::optional<Consumable> use; std::optional<vec2> ward; ChannelOp channel; Order order; };
```

## 3. Module contracts

| Module | Contract |
|---|---|
| Kernel / Actuator | The only caller of SDK actions. Checks the round, allowances and restrictions. Catches `cambc::error`, marks the allowance used, returns the result. Never throws upward |
| Observation | Reads each live quantity at most once per turn |
| Memory | Pure update from (previous memory, observation, decoded word). Own vision overrides. Never treats an unseen enemy as absent |
| ObjModel, EE evaluate, draft utility | Deterministic and side-effect free; no SDK calls; host-testable |
| Economy | Commits only its own slot. Hysteresis. Contract check every turn. Replans only in tier FULL |
| EE | ≤12k fuel. Returns CONTINUE when there is no threat within its horizon |
| Action scorer | Legality first, then score. Order sub-actions (attack/move/cast) per SDK rules |
| Protocol | One read-modify-write per turn. Respects pre-emption and freshness |
| SafeMode | Uses only N1/N2 plus the kernel. ≤5k fuel. Cannot fail on missing memory |

**Errors.** Each module entry is wrapped. On an exception: count it, return "not handled", and SafeMode covers the
turn. At 3 errors the module is disabled for the game.

## 4. Shared-word protocol (64 bits; designed fresh)

### 4.1 Layout

| Bits | Field |
|---|---|
| 0–47 | Slot records 0–5, 8 bits each: `obj` (7 bits) + `onsite` (1 bit) |
| 48–49 | Team message type |
| 50–63 | Team message payload (14 bits) |

**Objective codes (7 bits):**

| Code | Meaning |
|---|---|
| 0–111 | camp group id. Maps with more than 112 groups: groups ≥112 are published as 111 = "other" |
| 112–119 | altar index 0–7 (BANK). More than 8 altars: index modulo 8, disambiguated by distance |
| 120 | SHOP / home |
| 121 | RETREAT |
| 122 | DEFEND (target in the team message) |
| 123 | ESCORT |
| 124 | CLUSTER circuit (between clusters) |
| 125 | reserved |
| 126 | DEAD |
| 127 | IDLE / unknown |

**Team message types:**

| Type | Payload (14 bits) | Writer | Freshness |
|---|---|---|---|
| 00 SIGHTING | sector x 5 (tile/4), sector y 5 (tile/4), count−1 2, distress 1, round parity 1 | anyone seeing enemies | 2 rounds (parity) |
| 01 CAMP_EVENT | group 7, (event round mod 128) 7 | observer of a capture or clear | 4 rounds |
| 10 CREW_STANCE | leader slot 3, stance 3, target enemy index 3 (7 = none), ttl 2, spare 3 | crew leader in contact | ttl rounds (≤3) |
| 11 TEAM_MODE | mode 3, target group 7, round mod 16 4 | lowest alive slot | 8 rounds |

- **Enemy index:** position in `champions(team::enemy)` sorted by handle.
- **Respawn round from a CAMP_EVENT:** event round + `max_respawn_timer(g)`, which is static.

### 4.2 Pre-emption and write discipline

- **Priority order:** CREW_STANCE > SIGHTING with distress > TEAM_MODE change > CAMP_EVENT > SIGHTING without
  distress.
- **Overwriting:** a writer may overwrite only a lower-priority or stale message.
- **One write per turn:** read the word once, modify the own slot plus at most one message, then write once.

### 4.3 Sufficiency

What teammates must know, and how each is represented:

1. **Who owns which objective, and whether they are on site.** Slot records: every body, every turn, any group count
   up to 112.
2. **Respawn timing others cannot see.** CAMP_EVENT. The respawn is deterministic from the static timer.
3. **Enemy presence and distress.** SIGHTING, at 4×4-tile sectors. The 2-round freshness matches the reach ramp's
   tolerance.
4. **Fight commitment.** CREW_STANCE (leader, stance, target). The rally point is implicit: the leader's slot
   objective position.
5. **Team mode.** TEAM_MODE. It is deterministic from shared inputs, so it is recomputable locally; the message is a
   consistency hint.
6. **Contention.** At most one active fight and one sighting compete. CREW_STANCE wins; crew members already see the
   enemies. A sighting delayed by ≤2 rounds only affects pressure estimates of non-crew champions.

### 4.4 Stale or missing data

| Case | Behaviour |
|---|---|
| Slot not updated for 3 rounds | Half weight in the auction residual |
| Slot DEAD | Ally excluded until its respawn (`dead_until` = its death round + 60) |
| Stance missing or stale | Decide alone with π + 0.2 |
| Sighting stale | Ignore it; the belief ramp continues |
| Team mode stale | Recompute locally |

## 5. Draft memory layout (1024 bytes)

| Bytes | Content |
|---|---|
| 0–3 | Magic and version |
| 4–11 | Lineup intent: slot roles per pick |
| 12–43 | Opening plan: per slot, 3 jobs × 17 bits |
| 44–107 | Map summary: altar ranks, contested index, cluster-circuit flag, gap flags, group classes (bitset) |
| 108–1023 | Free |

## 6. Configuration and flags

- **`config.h`** holds defaults for all `[default]` constants, the fuel table (filled from CT-1), per-map rows
  (filled by the league after Day 9), and 3 parameter sets for style adaptation.
- **Flags:**

  | Flag | Values |
  |---|---|
  | `DZ_EE` | 0 = SafeMode combat, 1 = EE |
  | `DZ_ECON` | 0 = SafeMode farming, 1 = auction |
  | `DZ_CREW` | 0/1 |
  | `DZ_GEAR` | 0 = fixed build, 1 = planner |
  | `DZ_OPEN` | 0/1 |
  | `DZ_STYLE` | 0/1 |
  | `DZ_TRACE` | 0/1 (never in a release) |

  Flags let each module be A/B tested inside DZ.
