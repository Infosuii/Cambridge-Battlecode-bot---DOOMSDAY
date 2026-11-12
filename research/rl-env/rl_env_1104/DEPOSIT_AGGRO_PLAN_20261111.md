# Deposit and aggression plan (11 Nov 2026): an add-on for an existing bot

Separate from `BUILD_PLAN_20261110.md`. It appends to any bot of the v139 / v220 family. Line numbers are for
**v221** (`artifacts/tmp/rl_env_1104/v221/src`, unpacked from `v221_v220_fake_recall_engine5.zip`); every step
also gives the anchor text, which I checked exists once in v221, v141 (`rl_env_1104/v141src/src`), v139
(`rl_env_1104/v139src/src`) and `upload_final/src` unless a step says otherwise.

**Status.** Steps S1-S5, S7 and G1-G3 are also available as one script:
`python tools/rl_env_1104/v130/depaggro_patch.py <bot>/src`. It applies and compiles on v221 and on v141, and the
v221 build played 500 rounds against v141 with no errors in its logs. That is a build check only: **no step has a
game result yet**, and the knob steps S6, S8 and G4 are not in the script. The script handles both code
generations (old channel guard / `channel_danger`) and Windows line endings (v221's files use them).

## 1. What the games show

265 decoded ranked games from 10 Nov (v137-v141); "current" = the 75 games of v140/v141, the v220-based bots.
Tool: `tools/rl_env_1104/deposit_fights.py`.

**Deposit mechanics (13,000 deposits):**
- A deposit takes about one round per 10 gems: 1-10 gems 1 round, 20-30 gems 3, 30-45 gems 4, 60-90 gems 7.5,
  90-150 gems 11, 150+ gems 23.
- **Damage does not interrupt a deposit.** 833 of 1,218 deposits during which the depositor lost health still
  completed. Only death or a stun ends one.
- Once started, a deposit is safe: with an enemy within 6 tiles at the start, ours complete 87-89% and the
  depositor dies in 1%.

**We do not start them.** A carrier (20+ gems) arriving within 8 tiles of an altar, next 40 rounds:

| Situation | Who | Deposits | Walks away | Dies |
|---|---|---|---|---|
| no enemy within 8 | us / opponents | 63% / 65% | 26% / 21% | 2% / 2% |
| enemy within 8, we have fewer or equal bodies | us | **24%** (current 31%) | **43%** | 13% (current 15%) |
| the same | opponents | **44%** (current 56%) | 29% (24%) | 12% (9%) |
| enemy within 8, we have more bodies | us | **39%** (current 45%) | 34% | 5% |
| the same | opponents | **54%** (current 64%) | 25% (21%) | 6% |

Walking away is not safer: we deposit half as often and die slightly more often.

**Carriers die near altars while not depositing.** Deaths with 20+ gems within 10 tiles of an altar: us 1.10 a
game, opponents 0.89 (current 1.11 v 0.77), mean bag 100 gems (current 44). Only 7-8% of ours were depositing at
the time; 37-41% had no teammate within 6 tiles.

**An enemy arriving during our deposit:** 75-83% still complete, 16-24% are cancelled, 1-2% die.

**Numbers are not converted, by either side.** Champion-rounds with an enemy within 6 tiles in which the champion
attacks a champion:

| Our bodies there v theirs | Us | Opponents |
|---|---|---|
| +2 or more | 16% (current 18%) | 12% (11%) |
| +1 | 20% | 18% |
| level | 24% | 21% |
| behind | 30% | 27% |

So with two or three on one we attack in fewer than one round in five. Opponents do no better, so this is unused
upside and not a gap to them: a kill before round 300 pays the killers 76 gold and 6 gems on average, and with a
body more the attacker's side loses the first champion only 15-26% of the time (`BUILD_PLAN_20261110.md`, section 1).

## 2. Why the code does this (v221)

1. **Fight-or-flee runs before banking.** `Bot::play_turn` calls `handle_enemies()` first (line 8330); only when it
   returns false does the chain reach `tribute_if_needed()` (line 8381). A carrier standing in altar range that
   sees an enemy within 8 tiles flees, although a 30-gem deposit takes 3 rounds and damage cannot stop it.
2. **Carriers get a flee multiplier.** `handle_enemies`, line 3378:
   `const float risk = gems >= 60 ? 2.0f : gems >= 25 ? 1.4f : 1.0f;` makes `winning` harder and `in_danger` easier.
3. **The banking route avoids every recent sighting.** `tribute_if_needed`, line 5116: with 15+ gems all tiles
   within 4 of an enemy seen in the last 10 rounds are blocked; the carrier detours or turns back.
4. **A carrier that makes no progress for 20 turns stops banking for 80 rounds** (line 5201).
5. **The helpers are bag-limited.** `a2_join_fight` (line 1363) needs `gems < 20` and health 60%+;
   `press_isolated` (line 3263) needs `gems < 20`, health 65%+ and no second enemy within 7.
6. **Targets end at range + 4** (line 3391): an enemy 6-8 tiles away is nobody's target.
7. **Off switches:** `APEX_SNIPE 0` (attack an enemy that is depositing), `APEX_DISTRESS 0` (call for help).

## 3. Switches (`common.h`, directly after the line `#define A2_KITFIX 31`)

```cpp
#define CL_DEPOSIT 1      // S1-S7
#define CL_DEP_MIN 10     // smallest bag that deposits before the fight-or-flee logic
#define CL_DEP_SAFE 0.8f  // share of our health the wait may cost
#define CL_DEP_PUSH 6     // steps from the altar ring within which a carrier walks in
#define CL_DEP_GUARD 10   // teammates this close guard a depositing ally
#define CL_AGGRO 1        // G1-G3
#define CL_AGG_HP 0.45f   // health share needed to stand with a body advantage
#define CL_AGG_BAG 100    // carriers above this never stand
#define CL_GANG_BAG 40    // carriers above this do not walk into a fight
#define CL_GANG_TURNS 6   // rounds a walk-in may last
```

## 4. Smart deposit

### S1. Two helpers (everything below uses them)
- **`bot.h`**, inside `class Bot` next to `bool tribute_if_needed();`:
  ```cpp
  int deposit_rounds(int bag) const;
  float standing_damage(int rounds) const;
  bool guard_depositor();
  bool gang_up();
  bool dep_push = false;
  int gang_since = -100, gang_pause_until = 0;
  ```
- **`bot.cpp`**, directly above `bool Bot::tribute_if_needed() {`:
  ```cpp
  // CL_DEPOSIT: rounds a deposit of this bag takes (the engine's rule; about one round per 10 gems).
  int Bot::deposit_rounds(int bag) const {
      return std::max(bc::constants::submit_gem_minimum_duration,
          bc::constants::submit_gem_base_duration +
              static_cast<int>(std::ceil(static_cast<double>(bag) * bc::constants::submit_gem_duration_multiplier)));
  }
  // Damage the visible enemies can do to us over the next `rounds` rounds if we stay here. An enemy `gap` tiles
  // outside its reach needs `gap` rounds to arrive (one tile of slack for a dash) and then hits every round.
  float Bot::standing_damage(int rounds) const {
      float dmg = 0.0f;
      for (const auto& e : w.enemies) {
          if (e.hp <= 0 || e.tributing() || e.real_recall()) continue;
          const int gap = std::max(0, cheb(e.pos, pos) - e.range - 1);
          const int hits = rounds + 1 - gap;
          if (hits > 0) dmg += enemy_dps(e) * static_cast<float>(hits);
      }
      return dmg;
  }
  ```
  `enemy_dps` is the free function at line 2070. `real_recall()` exists only in v221; on other bases write
  `e.recalling()` (or apply `tools/rl_env_1104/v130/frc_patch.py` first, which makes `recalling()` mean the same).
- **Limit:** a stun also ends a deposit and this does not model it. The deposit then simply restarts on the next
  turn through S3 (the data has 266 such restarts).

### S2. One timing rule for starting, retrying and cancelling
Without this the new start rule (S3) and the old cancel rule disagree and the champion starts and cancels in turn.
- **Cancel guard** (`play_turn`, line 8078). Anchor in v221 / v139:
  `if (incoming * static_cast<float>(left + 1) * tune::kChannelGuard < hp) return;`
  Replace with:
  ```cpp
  if (CL_DEPOSIT && state.contains(bc::champion_state::submitting_gems)) {
      if (standing_damage(left) < hp) return; // CL: we finish before they kill us: keep channelling
  } else if (incoming * static_cast<float>(left + 1) * tune::kChannelGuard < hp) return;
  ```
  In v141 / `upload_final` the anchor is `if (!channel_danger(channel, left)) return;`; replace with
  `if (CL_DEPOSIT && channel == ChannelRetry::submit ? standing_damage(left) < hp : !channel_danger(channel, left)) return;`
- **Retry rule** (`Bot::retry_channel`, line 5040). Anchor in v221 / v139:
  `bool unsafe = tune::kChannelGuard > 0.0f && incoming * static_cast<float>(duration + 1) * tune::kChannelGuard >= hp;`
  Add on the next line:
  ```cpp
  if (CL_DEPOSIT && kind == ChannelRetry::submit) unsafe = standing_damage(duration) >= hp * CL_DEP_SAFE;
  ```
  (v141 / `upload_final`: the line is `bool unsafe = channel_danger(kind, duration);`, add the same line after it.)

### S3. Deposit first: in altar range, start before fight-or-flee
- **`play_turn`**, directly above the line `    const bool fought =` (line 8323):
  ```cpp
  // CL_DEPOSIT S3/S4: a carrier at an altar, or a few steps from one, deposits before the fight-or-flee logic
  // when the deposit ends before the visible enemies can kill it. Damage does not interrupt a deposit.
  bool dep_first = false;
  if (CL_DEPOSIT && gems >= CL_DEP_MIN && !w.enemies.empty() && !w.no_bank) {
      w.ensure_altar_field();
      const int da = fdist(w.altar_field, pos);
      if (da != kUnreach && da <= CL_DEP_PUSH && standing_damage(da + deposit_rounds(gems)) < hp * CL_DEP_SAFE) {
          force_tribute = true;
          dep_push = true;
          dep_first = tribute_if_needed();
          dep_push = false;
          if (dep_first) mode = da == 0 ? "tribute-first" : "tribute-push";
      }
  }
  ```
- Same statement, last operand: change `        handle_enemies();` to `        (!dep_first && handle_enemies());`.
  (In v221 the two operands above it are compiled out. If `V58_SURVIVE` or `V58_ACT & 2` is on in your base, wrap
  the whole right-hand side: `!dep_first && ( ... )`.)
- A few lines below, change `    if (fought) {` to:
  ```cpp
      if (dep_first) {
      } else if (fought) {
  ```
- `force_tribute` is reset at the top of every turn (line 7936), so nothing has to be restored. `da == 0` means
  the champion stands on the altar ring; `tribute_if_needed` then starts the submission itself and already handles
  an enemy altar lock.

### S4. Push through: walk the last steps on the direct route
S3 already calls `tribute_if_needed` from up to `CL_DEP_PUSH` steps away. One more change stops that call from
detouring around sightings.
- **`tribute_if_needed`**, anchor `    if (gems >= 15) {` (line 5116): change to `    if (gems >= 15 && !dep_push) {`.
- **Values to test:** `CL_DEP_PUSH` 6 (default), 4, 8; `CL_DEP_SAFE` 0.8, 0.6.

### S5. No 80-round banking freeze for a real bag
- Anchor `            tribute_off_until = round + 80;` (line 5201; not present in `upload_final`, which already has
  this): change to `            tribute_off_until = round + (CL_DEPOSIT && gems >= 30 ? 15 : 80);`

### S6. Call an escort (optional; uses a switch that is off today)
- `common.h`: `#define APEX_DISTRESS 0` -> `1`. This also turns on the existing call by fleeing champions and the
  `rescue` branch in `Bot::hunt` (healthy teammates with fewer than 40 gems within 14 tiles walk to the caller).
- **`play_turn`**, inside the new `if (dep_first) {` branch of S3:
  ```cpp
          if (tune::kDistress && gems >= 40) share_sighting(true); // CL: a big bag is going in, cover me
  ```
- Test this step alone: the switch was off in every recent version and I do not know why.

### S7. Guard a depositing teammate
- **`bot.cpp`**, directly above `bool Bot::tribute_if_needed() {`:
  ```cpp
  // CL_DEPOSIT S7: a teammate within CL_DEP_GUARD tiles is depositing and an enemy is within 8 tiles of it:
  // close to our range of that enemy and hit it.
  bool Bot::guard_depositor() {
      if (!CL_DEPOSIT || w.enemies.empty() || hp < max_hp * 0.5f || gems >= CL_GANG_BAG) return false;
      FlagScope combat{combat_move};
      for (const auto& a : w.allies) {
          if (cheb(a.pos, pos) > CL_DEP_GUARD || !a.unit.state().contains(bc::champion_state::submitting_gems)) continue;
          const EnemyRec* threat = nullptr;
          for (const auto& e : w.enemies)
              if (e.hp > 0 && cheb(e.pos, a.pos) <= 8 && (!threat || cheb(e.pos, a.pos) < cheb(threat->pos, a.pos))) threat = &e;
          if (!threat) continue;
          mode = "guard";
          if (cheb(threat->pos, pos) > range) {
              bc::bitboard goal;
              goal.clear();
              goal.draw_chebyshev(threat->pos, static_cast<float>(range));
              walk_toward(goal);
          }
          if (cheb(threat->pos, pos) <= range) {
              cast_on_enemy(*threat);
              attack_unit(threat->unit, threat->pos);
          }
          return true;
      }
      return false;
  }
  ```
- **Chain** (`play_turn`): directly above `    } else if (home_siege()) {` add `    } else if (guard_depositor()) {`.
- When the guard itself has an enemy within 8 tiles, `handle_enemies` decides first; G1 below makes it stand in
  that case.

### S8. Smaller bags when the altar is contested (optional knob)
- **Why:** a 100-gem bag is 10-11 rounds of standing still; a 40-gem bag is 4. The mean bag we lose near an altar
  is 44-100 gems.
- **`play_turn`**, directly after the anchor line
  `tune::kTributeCarry = std::min(tune::kTributeCarry, tune::kEarlyCarry);`:
  ```cpp
  if (CL_DEPOSIT && w.altar_ready) { // CL S8: an enemy was near an altar in the last 40 rounds: bank at 40
      bool contested = false;
      for (const auto& s : w.sightings)
          if (round - s.round <= 40)
              for (vec2 a : w.altars) contested = contested || cheb(a, s.pos) <= 8;
      if (contested) tune::kTributeCarry = std::min(tune::kTributeCarry, 40);
  }
  ```
  Check how long `w.sightings` keeps entries in your base before relying on the 40 rounds; if it keeps fewer, keep
  your own `last_altar_enemy_round` and set it in this loop.

## 5. Aggression

### G1. With a body more than they have, stand and fight
- **`handle_enemies`**, directly above the line `    if (tune::kTribDeny & 2) {` (line 4285). All names used are
  locals of the function at that point (`target`, `ttd`, `winning`, `in_danger`):
  ```cpp
  // CL_AGGRO G1: one body more than they have here (or level while a teammate deposits beside us): stand and
  // fight, carriers too. Never on their spawn, in a camp's reach or at a target in a bush.
  if (CL_AGGRO && target) {
      int friends = 1, foes = 0;
      bool guarding = false;
      for (const auto& a : w.allies) {
          if (cheb(a.pos, pos) > 6 || a.hp < 0.4f * a.max_hp) continue;
          if (a.unit.state().contains(bc::champion_state::submitting_gems)) guarding = true; // cannot fight
          else ++friends;
      }
      for (const auto& e : w.enemies) {
          if (e.hp <= 0) continue;
          const int d = cheb(e.pos, pos);
          if (d > 7 || (bit(w.enemy_spawn, e.pos) && d > e.range + 2)) continue;
          ++foes;
      }
  #if A2_BELIEF
      foes += a2_hidden_near(8, 0);
  #endif
      if (foes > 0 && (friends >= foes + 1 || (guarding && friends >= foes)) && hp >= CL_AGG_HP * max_hp &&
          gems < CL_AGG_BAG && ttd > 2.0f && !bit(w.enemy_spawn_zone, target->pos) && !bit(w.hot_zone, pos) &&
          !bit(w.bushes, target->pos)) {
          winning = true;
          in_danger = false;
      }
  }
  ```
- **What changes:** today the same idea exists only as `A3_BACKOFF`, which still applies the carrier multiplier,
  needs `gems < 60` and a won damage race. This drops those three conditions when we have the bodies.
- **Values to test:** `CL_AGG_HP` 0.45, 0.6; `CL_AGG_BAG` 100, 60.
- On v139 `a2_hidden_near` may not exist: delete those three lines there.

### G2. Walk in on an outnumbered enemy
`handle_enemies` only targets enemies within range + 4 and returns false when it is not yet "engaging". This picks
up the rest.
- **`bot.cpp`**, directly above `bool Bot::tribute_if_needed() {`:
  ```cpp
  // CL_AGGRO G2: a visible enemy with fewer bodies around it than we have around it: walk in and hit it.
  bool Bot::gang_up() {
      if (!CL_AGGRO || w.enemies.empty() || hp < max_hp * 0.55f || gems >= CL_GANG_BAG || heading_home ||
          round < gang_pause_until) return false;
      const EnemyRec* best = nullptr;
      for (const auto& t : w.enemies) {
          if (t.hp <= 0 || cheb(t.pos, pos) > 7 || bit(w.enemy_spawn_zone, t.pos) || bit(w.bushes, t.pos)) continue;
          int foes = 0, friends = 1;
          for (const auto& e : w.enemies) foes += e.hp > 0 && cheb(e.pos, t.pos) <= 6;
          for (const auto& a : w.allies) friends += cheb(a.pos, t.pos) <= 6 && a.hp >= 0.5f * a.max_hp;
          if (foes > 2 || friends < foes + 1) continue;
          if (!best || t.hp / std::max(1.0f, t.max_hp) < best->hp / std::max(1.0f, best->max_hp)) best = &t;
      }
      if (!best) return false;
      if (round - gang_since > CL_GANG_TURNS + 2) gang_since = round;          // a new walk-in
      if (round - gang_since >= CL_GANG_TURNS) { gang_pause_until = round + 20; return false; } // it got away
      FlagScope combat{combat_move};
      mode = "gang";
      if (cheb(best->pos, pos) > range) {
          bc::bitboard goal;
          goal.clear();
          goal.draw_chebyshev(best->pos, static_cast<float>(range));
          walk_toward(goal);
      }
      if (cheb(best->pos, pos) <= range) {
          cast_on_enemy(*best);
          attack_unit(best->unit, best->pos);
      }
      return true;
  }
  ```
- **Chain** (`play_turn`): directly above `    } else if (home_siege()) {`, after the `guard_depositor()` line of
  S7, add `    } else if (gang_up()) {`.
- It runs only when `handle_enemies` returned false, so it never overrides a flee.

### G3. Let carriers of small bags help
- `Bot::a2_join_fight` (line 1364), anchor
  `    if (hp < max_hp * 0.6f || gems >= 20 || !bc::self().can_move()) return false;`:
  change `0.6f` to `0.5f` and `gems >= 20` to `gems >= CL_GANG_BAG`.
- `Bot::press_isolated` (line 3267), anchor `gems >= 20 || heading_home ||`: change `gems >= 20` to
  `gems >= CL_GANG_BAG`.

### G4. Attack an enemy that is depositing (existing switch, off)
- `common.h`: `#define APEX_SNIPE 0` -> `3` (walk up to 3 tiles to an enemy channelling a deposit of 20+ gems when
  we arrive before it ends; the code is at the top of `Bot::hunt`).
- **Why:** opponents start 6-7 deposits a game with one of ours within 6 tiles and 84-90% complete (mean bag
  29-58). Damage does not stop them, so only a kill, a stun or an altar lock counts: the snipe is worth it against
  bags of 40+ (4+ rounds). Test alone.

### Guard rails already in the code above
Never: on the enemy's spawn zone, inside a camp's reach (`hot_zone`), at a target standing in a bush, below 45%
health (G1) or 55% (G2), with 100+ gems (G1) or 40+ (G2, S7), against more than two enemies (G2), or for more
than six rounds at a time (G2, then a 20-round pause).

## 6. Order, checks and measurement

1. **Order:** S1 + S2 + S3 + S4 together (they depend on each other), then S5, then G1, then G2 + G3, then S7.
   S6, S8 and G4 are knobs: each alone, last.
2. **Compile and crash check:** `cambc build <dir> --release --output x.wasm`, then
   `cambc run <dir> artifacts/tmp/rl_env_1104/v141src --map artifacts/tmp/ladderpool_maps/03colosseum.map26a --rounds 400 --release -o <out>`.
3. **Behaviour check in a debug build:** print `round, my_id, mode, gems` when `mode` is `tribute-first`,
   `tribute-push`, `guard` or `gang`, and when G1 fires. Expect: `tribute-first` on the altar ring with an enemy
   in sight; no start-cancel-start on the same tile; `gang` ending within six rounds.
4. **Interaction with `BUILD_PLAN_20261110.md`:** steps A1 and B1 there stop level and losing fights before round
   300; G1 and G2 start fights only with a body more. Both use the body count, so they do not conflict.
5. **The local test opponents do not contest altars or skirmish like ladder teams**, so local scores will show
   little. Use them for "not worse" only (`tools/rl_env_1104/eval/seq.sh`, see the other plan) and measure on the
   ladder after 20+ ranked games:
   ```
   python -I tools/rl_env_1104/ladder_pull.py --since <upload time> --window vNEW=<upload time> --cache artifacts/tmp/ladder_1110
   python -I tools/rl_env_1104/ladder_decode.py --cache artifacts/tmp/ladder_1110 --versions vNEW --workers 3
   python -I tools/rl_env_1104/deposit_fights.py artifacts/tmp/ladder_1110 vNEW --only vNEW
   ```
   Targets, against v140/v141 today:

   | Measure | Today | Target |
   |---|---|---|
   | Carrier near an altar, enemy within 8, fewer or equal bodies: deposits | 31% | 50%+ (opponents 56%) |
   | The same, more bodies: deposits | 45% | 60%+ (opponents 64%) |
   | The same two cases: walks away | 43% / 33% | under 25% |
   | Deaths with 20+ gems within 10 tiles of an altar | 1.11 a game | under 0.8 |
   | Attacks a champion with +2 bodies | 18% of rounds | 30%+ |
   | Deaths in rounds 150-800 (`time_budget.py`) | 6.6 a game in losses | not higher |

   If deaths near altars rise instead of falling, lower `CL_DEP_SAFE` to 0.6 and `CL_DEP_PUSH` to 4 before
   removing anything.
