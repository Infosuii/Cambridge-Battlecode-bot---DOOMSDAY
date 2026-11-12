# Engine conformance suite: eliminating surprises before strategy code depends on them

**Purpose.** Every OPEN item in GAME_MECHANICS_AND_WIN_CONDITIONS.md, and every assumption the design makes about the
engine, is checked by a small **diagnostic bot** in scripted local games.
- **When.** Day 1–2 of implementation, after approval. Not run during planning.
- **Where.** Diagnostic bots live under `artifacts/tmp/dz-conformance/` and are never competition candidates.
- **Re-runs.** The suite is re-run automatically **on every new cambc CLI or engine version**. Releases have shipped
  every 3–5 days this season.
- **How.**
  - Diagnostics use `cambc run --release`, matching the platform. They print through stdout and summarise with a
    Python checker.
  - Instrumented diagnostics are never used for strength claims.
  - Expected values come from §§1–12 of the reference; any mismatch updates the reference and the bot's runtime
    tables.

**Already verified in planning (no test needed):**
- **Fuel budgets:** 10M first draft turn, 100k later draft turns, 200k first play turn, then 100k.
- **Treasure** +10% on all gold; Vesper +33%; Vesper with Treasure +43%.
- **Capture emblem:** capture time 3.
- **Prospector:** +25% gems from gem clusters.
- **Camps don't regenerate** while unattended.
- **Item metadata** and **champion stats** (engine probe).

## Test list

| ID | Question | Method (diagnostic bot on a chosen map) | Expected / hypothesis | If different, the bot adapts by |
|---|---|---|---|---|
| CT-1 | Fuel cost of each host primitive | `fuel_remaining()` before and after 100 repetitions, release build: `distance_field::compute` on 30², 60², 100² maps, `compute_to`, `reachable_tiles`, `shadow_cast`, `visible_tiles_from`, `move_towards`, `champions()`, `camps()`, `camp_groups()`, `champion.state()`, `damage_amount(t)`, shared-memory read/write, bitboard ops | Host work mostly free; a fixed cost per call | Updating `FUEL_TABLE` in `dz_config.h`; budgets in FUEL_AND_PERFORMANCE §2 recomputed |
| CT-2 | Fuel-out suspension and resumption semantics | Burn fuel to suspension at a marked point; record `round_number()` and the next action's acceptance after resume | Resumes mid-code next turn; round advanced | The kernel's stale-decision guard (MASTER §3) is mandatory either way |
| CT-3 | Initial budgets | `fuel_remaining()` at the start of draft turn 1, draft turn 2, play turn 1, play turn 2 | 10M, 100k, 200k, 100k | Draft and initialisation budgets |
| CT-4 | Effect of an uncaught exception | Throwaway diagnostic: throw once at round 50 | Bot fault; champion inactive afterwards | Confirms the catch-all policy (already mandatory) |
| CT-5 | Shared-memory semantics | Ally A writes a counter; ally B reads it in the same round and the next | Immediate visibility within the round | Protocol freshness rules |
| CT-6 | Exact turn interleaving and `set_priority` timing | Each champion appends (round, slot) to shared memory; vary priorities | Teams alternate, starting team swaps each round; priority applies next round | Crew-leader ordering and "acts before enemy" micro rule |
| CT-7 | Movement edge cases | `move_towards` into an unseen bush occupant; ranged move-then-attack (should throw); exclusive spell after move; dash over a hole; landing restrictions | As in SDK docs | Movement executor checks |
| CT-8 | Can enemy cooldowns, channel time, gems and items be read when visible? | Query a visible enemy with `abilities()[s].cooldown()` / `sdk_champion_cooldown`, `remaining_channel_time()`, `gem_count()`, `item_count()` | Cooldowns and channel time yes; gems and items: verify | EnemyBelief fields fall back to estimates if a query throws |
| CT-9 | `is_alive()` for hidden enemies; teammate respawn timer query | Query hidden enemies' `is_alive()`; query a dead ally's respawn timer | Unknown | Death tracking from observations if hidden |
| CT-10 | Camp-group visibility and `capture_state` | Stand so only one spawn tile of a group is in vision; read `state()` and `capture_state()` | Visible if any spawn tile is in vision | Ledger update rules |
| CT-11 | Camp attack cadence and targeting | Single champion vs one elk: log HP per round | Cooldown 2 suggests a hit every 2 rounds; nearest target | ObjModel damage-taken rate (D_taken) |
| CT-12 | Tribute emblem 0.33 | Bank 40 gems with and without a Tribute emblem; compare channel length, banked gems and gold | Unknown (tribute speed?) | Gear planner value for Tribute |
| CT-13 | Prospector on non-cluster groups and splits | Capture a golem group and a mixed group with Prospector, alone and split | Clusters only (hypothesis) | Gear planner and ObjModel rewards |
| CT-14 | Hunter kill gold | Kill an enemy dummy with Hunter (diagnostic-vs-diagnostic game) | +50 | λ_gold kill value |
| CT-15 | Skirmish and Collectors | Damage logs against a dummy with and without | +5% champion damage; +1% per family | EE damage model |
| CT-16 | Recall rules | Recall with Home; recall interrupted by camp damage; recall started on spawn | 3 turn ends with Home; interrupted by damage | BANK and recall planning |
| CT-17 | Tribute and lock interactions | Tribute 25 gems; lock placed mid-tribute; tribute attempt into lock; lock placement at distance 2 vs 3 | As per rules | Banking executor and lock usage |
| CT-18 | Teleport crystal and dash | Teleport reservation visibility to enemies; dash path legality over holes | As per rules | Mobility planning (optional) |
| CT-19 | Cassi & Issac | Two instances? Linked death? Order of their turns? Same slot order? | Two instances; linked death | Slot mapping in the protocol |
| CT-20 | Draft mechanics | Number of draft rounds, when enemy picks become visible, fuel per draft turn, behaviour on a missed pick | One pick per round, simultaneous | Draft engine |
| CT-21 | `team_size()` | Compare with picks and bodies on C&I maps | Picks | Slot count |
| CT-22 | Spawn heal and respawn blocking | Damaged champion on spawn; Health purchase on spawn; respawn with a spawn tile occupied | Full heal per round; Health purchase heals | Recovery planning |
| CT-23 | Vision details | Bush cluster in and out; ward vision; `in_vision` with ward | As per rules | Belief and ward planner |
| CT-24 | Reward split and contest | Two allies capture together; enemy enters during capture | Even split, remainder to lowest ID; contested resets | Single-capturer rule |
| CT-25 | Kill credit | Two attackers kill a target; who is credited (last hit?) | Last hit (hypothesis) | Focus fire, Vendetta resets, Hunter |
| CT-26 | Vendetta camp-kill reset | Vendetta last-hits a camp member | Cooldowns reset | Clear executor spell timing |
| CT-27 | Version fingerprint | Hash of all constants, designs and items at startup, printed in diagnostics | Equal to the recorded hash | Re-run the whole suite and update the reference if it changes |

## Acceptance

- The suite produces `research/dz/CONFORMANCE.md`: each test with observed values, verdict and the resulting change.
- **No strategy module may rely on an OPEN item until its CT is resolved.** Until then, modules use the conservative
  default listed in ALGORITHM_SPECIFICATIONS.md.
