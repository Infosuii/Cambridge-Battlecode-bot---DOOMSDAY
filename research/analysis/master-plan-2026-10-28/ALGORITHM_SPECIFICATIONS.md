# Algorithm specifications

Notation:
- `t` is the round; `c` a champion; `C` a crew; `g` a camp group.
- `d_g(p)` is the walking distance from tile p to group g (v76 distance field).
- `F` is the number of free champions (≤5); `G` the number of groups (≤112); `E` the visible enemies.
- `GE` is gem-equivalents.

Engine values are read at runtime (GAME_MECHANICS §3–6). The constants shown here are defaults, to be calibrated.

---

## 1. Shared quantities, recomputed each turn (≤1k ops)

```
income_us(t)   = EMA_50( team collected gems/round + λ_gold·gold/round )   // from own timelines: bags+banked deltas (own team only)
T_end(t)       = min(2000, t + min(T_us, T_them))                          // race horizon
T_us           = max(0, 1000 − banked_us − 0.7·Σ ally bags) / max(ε, gem_income_us)
T_them         = max(0, 1000 − banked_them − 0.7·Σ seen enemy bags) / max(ε, gem_income_them_est)
R(t)           = T_end(t) − t                                              // remaining productive rounds
ρ̄(c,t)        = EMA_50 of champion c's GE income per alive round (floor 0.2, cap 1.5)
```

Two sources:
- `banked_*` comes from the SDK team scores.
- `gem_income_them_est` comes from the change in enemy banked score over the last 100 rounds, plus seen bags.

## 2. Exchange rates (no arbitrary weights)

**Gold to GE.**
- A purchase of 30 gold raises champion c's income rate by `δ_c` GE/round for the remaining `R(t)` rounds, so
  `λ_gold(t) = E_c[δ_c] · R(t) / 30`.
- In closed form for a damage stat: `δ_c ≈ ρ̄(c) · s_c · f_dmg`, where:
  - `s_c` = the relative DPS gain of one shard (growth / current stat)
  - `f_dmg` = the fraction of the champion's cycle time spent clearing (from ObjModel, typically 0.3–0.5)
- **Calibration** (offline, existing replays, no new games):
  1. Regress per-champion income over the next 100 rounds on equipment cost at round t, from SA-* local timelines.
  2. Fit `λ_gold(t) = a · R(t)`.
  3. Parity check: at R50 the value should be close to v76's effective gold weight (≈0.18–0.31 GE/gold, logged on
     Day 2). If the regression is noisy, set `a` by parity.
- **Floor and cap.** `λ_gold ∈ [0.02, 0.6]`. Near the end, gold only matters for the round-2000 tiebreak:
  `λ_gold ≥ 0.02` when `T_end = 2000`.

**Death cost and kill value:**
```
DeathCost(c,t) = bag_c + λ_gold(t)·(kill_gold + hunter_bonus_enemy) + λ_tempo·T_respawn·ρ̄(c,t) + V_obj_lost(c)
KillValue(e,t) = bag_e + λ_gold(t)·(kill_gold + hunter_bonus_us)   + λ_tempo·T_respawn·ρ̄_enemy(t)
```
- `T_respawn` = 60.
- `ρ̄_enemy` is estimated from enemy gem income per alive enemy.
- `λ_tempo` defaults to 1. It is fit in V-T1.

**Objective value.** `V_obj(g) = Reward_GE(g, capturer) · progress(g)`. Progress is the share of total HP removed,
or the capture-timer fraction plus the HP share, so it lies between 0 and 1.

## 3. Economy: ObjModel and Team Economy Planner

### 3.1 ObjModel (validated before use: VALIDATION V-M1)

**Camp DPS of a champion against a camp:**
```
DPS_camp(c) = str_c · hit_rate_c · (1+0.15·monster_c) · (1+collectors_c)                      // hit_rate 1 melee; ranged 1 if standing
            + Σ_s dmg_s(c)/cd_s                          // nukes: focus·mult/8, AoE counts n_targets in r1
            + reset_c · str_c / 8 + splash_varg(g) + vendetta_reset_bonus(g)
```

**Team prediction for crew C on group g, starting at round t:**
```
T_arr(c)    = d_g(pos_c)                              // walking; dash not credited
T_ready     = max( max_c T_arr(c), respawn_g − t )
T_clear     = κ_g · HP_g / Σ_{c∈C} DPS_camp(c)        // κ_g fitted per camp type (1.0 single, ~1.1 multi-camp)
D_taken     = Σ_m str_m · alive_m(T_clear) · (1−0.3·jungle)·(1−0.1·durability)   // focused on the nearest champion
T_cap       = capture_time(capturer)                  // 5, or 3 with Capture emblem
Reward_GE   = gems_g·(1 + 0.25·[cluster ∧ prospector(cap)]) + λ_gold·gold_g·(1 + 0.33·[cap=Vesper] + 0.10·[cap has Treasure])
Feasible    = D_taken ≤ Σ_c (hp_c − 0.25·maxhp_c)  or  heal plan (add recall: 5+1 rounds, or 3+1 with Home)
Cost(C,g)   = Σ_c (T_arr(c) + (T_ready − T_arr(c))) + |C|·T_clear + T_cap   [champion-rounds]
```

**Capture-bound groups** (clusters): `T_clear ≈ 1` and `|C| = 1`.

**Validation thresholds** (replays of SA-IDLE-v76, decoded with `tools/replay/camp_clear.mjs`):
- clear time: median |error| ≤ 20%, bias ≤ 10%
- arrival: ≤ 3 rounds for d ≤ 30
- damage bias ≤ 20%

### 3.2 Contest probability

```
S(X)       = (Σ_{x∈X} hp_x) · (Σ_{x∈X} dps_x)                                  // Lanchester-square strength
pressure_g = Σ_e P(e can reach g within T_ready + T_clear + T_cap)              // EnemyBelief ramp (§9)
S_enemy_g  = pressure_g · mean visible enemy (hp·dps)  (default: our mean)
P_ok(C,g)  = 1 / (1 + exp(−α·(ln S(C) − ln(β·S_enemy_g + ε))))   with α=2, β=1   // = 1 when pressure ≈ 0
```

### 3.3 Rate and assignment (sequential auction through claims)

Each champion runs this for the team and commits only its own result.
```
ρ(C,g) = P_ok(C,g) · Reward_GE(C,g) / Cost(C,g)

TEP.replan(me):
  fixed  = {allies a : claim(a) fresh (≤3 rounds) ∧ contract ok}                // keep their jobs
  free   = all alive allies \ fixed  (me ∈ free)
  cand   = top-M groups by single rate ρ({c},g) per free c  (M=8; prune d_g > 45 or static value rank > 25)
           ∪ {BANK(c), SHOP(c)} ∪ respawn-arrival variants (respawn within 25 rounds)
  for each candidate g: residual reward if a fixed ally already holds g → skip (unless crew size < need_g)
  assignments = ∅
  while free ≠ ∅:
     for each g in cand: C_g = grow crew from nearest free champions while Δteam > 0:
           Δteam(C+c) = ρ(C+c,g)·|C+c| − ρ(C,g)·|C| − ρ_alt(c)       // ρ_alt = c's best solo alternative
           clusters: |C| = 1
     choose (g*, C*) maximising  Σ_{c∈C} ρ(C,g)  −  regret,  regret = Σ_c (ρ_alt2(c) − ρ_alt(c))_+ · 0.5
     add follow-up value: + γ · max_{g'} ρ({c}, g' | start at g*, t + T_g*)   (γ=0.5)
     assignments += (g*, C*, roles: capturer = member with farthest next objective; Vesper only if Δ≤3 rounds)
     free −= C*, cand −= g*
  my = assignments[me];  if ρ(my) < 1.15·ρ(current) and current valid: keep current        // hysteresis
  write claim(my.g)
```

Triggers:
- **Events:** own completion or invalidation, death, respawn, new group state seen, contact start or end, a
  crew-mate's claim changes.
- **Periodic:** every 8 rounds.
- **Skipped** if `gov.tier != FULL` (the cached assignment is kept).

**Progress contract.**
- Expected milestones: `d_g(pos)` falls by ≥1 every 2 rounds while moving, or the group's HP falls, or the capture
  timer advances.
- No progress for 6 rounds: release, `avoid[g] = t + 15` (40 after the second failure), replan.

**Complexity.** Single rates O(F·G′), with G′ ≤ 25 after pruning, at about 60 ops each. Crew growth
O(M·F²) ≈ 200. Follow-up O(M·G′). **≤12k ops** for a replan; ≤500 per turn for the contract check.

### 3.4 Cluster circuits (CLUSTER_RUN role)

- **Eligibility.** The map has ≥4 clusters within a 25-tile tour, and the champion owns Capture or Prospector, or the
  gear planner has scheduled them.
- **The runner's next cluster:** `argmax 7·(1 + 0.25·P) / (max(d, respawn − t) + 1 + T_cap)`.
- The circuit is re-evaluated at each capture.
- The runner is excluded from crews unless DEFEND/ESCORT fires.

### 3.5 Respawn denial (optional)

Standing on an enemy-side group's tile delays its respawn. Only consider it as a TEP objective "DENY(g)" with value
`λ_deny · enemy_expected_reward_g` when the champion is idle (no positive ρ elsewhere). Off by default.

## 4. Banking (BANK objective)

The burglar-problem cutoff:
```
h(c,t)     = h0 · (1 + κ_p·pressure(pos_c)) · (1 + κ_hp·(1 − hp/maxhp))            // per-round loss hazard
             h0 = observed own death rate per alive champion-round (EMA; prior 0.002)
T_next     = rounds until the next natural bank opportunity (altar within 4 of planned path, else full trip)
C_trip     = (d_altar(pos) + ceil(0.1·bag) − detour_saved) · ρ̄(c)
Bank now   ⇔  bag · h · T_next ≥ C_trip · η          (η = 1 default; V-T1)
           ∨  TEAM_MODE == ENDGAME_RACE ∧ bag ≥ 1
           ∨  banked_us + bag ≥ 1000 (win-now; respect tribute_off_until: M1 rule)
```
- **Bank-on-route:** if an altar lies within +4 rounds of the current path and `bag ≥ 10`, insert BANK before the
  objective.
- **Altar choice:** `argmin d_altar + 5·pressure(altar) + 50·[enemy lock seen]`.
- **Marcella:** her C_trip is reduced by `λ_gold·2·bag` (tribute gold).
- **Locks:** buy and carry an altar lock (10 gold) when gold ≥ 40. Place it on the enemy's nearest altar when a
  visible enemy carrier with `bag ≥ 60` is within 6 of it, or in ENDGAME_RACE when `T_them ≤ 150`.

## 5. Engagement Evaluator

### 5.1 Scene

- Allies within 10 (including me), enemies within 10 (each with cooldowns via `sdk_champion_cooldown`), and awake
  camps within 5 (damage sources only). At most 11 units.
- **Phantoms:** `n_hidden = max(0, pressure(pos,5) − n_visible_near)` units at the mean visible enemy stats, with
  weight w_h (default 0.5).
- C&I count as one fate unit: `hp = min(hp_C, hp_I)`.

### 5.2 Candidate stances

- **FIGHT(t1), FIGHT(t2).** The two best targets by `key = ttk / worth`. Worth = KillValue, and the v76 terms are
  replaced by §2. The recalling-enemy bonus applies only if the channel age is ≥ 2.
- **HOLD(o)** if I am on or adjacent to my objective's tiles.
- **KITE(t)** if I am ranged and t is melee.
- **DISENGAGE** toward the crew centroid or the objective's safe side.
- **RETREAT** home.
- **CONTINUE.**

### 5.3 Attrition model (deterministic, H = 4)

```
contact x = t.pos (FIGHT), objective tile (HOLD), my pos (others)
join(u)   = max(0, cheb(u,x) − range_u − 2·dash_ready_u)            // rounds until u can hit at x
for τ = 1..H:
   for side in {us, them}:
      dmg_side(τ) = Σ_{u joined, not stunned} (str_u·hit_rate_u) + Σ_{u joined, spell ready & unused} burst_u
      apply dmg to the side's focus target: us → t (FIGHT) else lowest EHP; them → lowest EHP in reach (ties → bigger bag)
      stuns: our ready stun removes the highest-dps enemy's next τ; theirs likewise (Marcella immune)
      Ren retaliation: 0.2·focus per hit received; Heart: +0.5·missing% damage; Varg splash on adjacent
   remove dead (C&I together)
outcome: killed sets K_us, K_them; hp lost; whether my objective's holders survive to completion
```

**Variants.** Optimistic: phantom weight 0, and enemy spells ready only if observed ready. Pessimistic: phantom
weight 1, and all enemy spells ready. They are combined as `V = (1−π)V_opt + πV_pess`, with
`π = 0.5 + 0.3·[bag ≥ 40] + 0.2·[respawned < 25 rounds ago]`.

### 5.4 Value

```
V(s) = Σ_{e∈K_them} KillValue(e) − Σ_{a∈K_us} DeathCost(a) + V_obj·P_obj(s) − V_obj_lost(s) − ρ̄(me)·rounds_diverted(s)
P_obj(HOLD)   = 1 if holders survive to capture completion else 0 (soft: fraction of rounds held)
P_obj(FIGHT)  = P_obj(HOLD) if fight point within objective region else 0.5·P_obj(HOLD)
P_obj(DISENGAGE/RETREAT) = 0;  V_obj_lost = progress lost (capture timer resets; camps may sleep/heal: ENG-1)
```

**Escape model** for DISENGAGE and RETREAT: walk the flee-field path to the safe point (an ally cluster of ≥2 within
3, or spawn). Pursuit rounds `n_e` are the rounds in which enemy e's reach covers the path position.
`D = Σ_e dps_e·n_e + bursts`; `P_die = clip((D − hp)/(0.25·D) + 0.5, 0, 1)`; `V = −P_die·DeathCost(me) − ρ̄·rounds`.

### 5.5 Decision

```
s* = argmax V(s)
if last stance ∈ {FIGHT, HOLD} (mine or crew leader's) and still feasible:
    switch to DISENGAGE/RETREAT only if V(new) > V(old) + m,  m = 0.15·DeathCost(me)
if P_die_next_round(me) > 0.5: allow any switch (personal override)
symmetric margin for re-engaging after DISENGAGE
free-action rule: before/after the stance move, take any legal basic attack / ready damaging spell on an enemy in range
    that does not consume an allowance the stance needs this turn (ranged: only if stance needs no move this turn)
```

**Calibration (V-M2).** On recorded contact turns, the Python port must beat v76's `in_danger` flag on 4-round death
Brier score. Fit at most 8 scalars on training maps only: w_h, π terms, m, α, the σ_D factor, λ_tempo and the join
weight.

**Cost.** Up to 7 stances × 2 variants × H=4 × n≤11 ≈ 616 unit-steps at about 15 ops each, so **≈9–12k fuel**. In
the LEAN tier, run only the optimistic variant and 4 stances.

## 6. Micro scorer (M11, optional executor)

For each legal candidate a = (move m ∈ mask ∪ {stay}, attack target ∈ in-range ∪ {∅}, spell ∈ ready ∪ {∅}), subject
to the rules (ranged: m ≠ stay excludes attack and excludes-walking spells):
```
score(a) = dmg_now(a)·(1 + kill_bonus·[kills]) + stun_value(a)
         − κ_r · threat(m)                  // Σ_e dps_e·[cheb(m,e) ≤ range_e+1(+2 dash ready)] + ready bursts in reach
         − κ_g · d_stance_goal(m)            // FIGHT: d to target ≤ range; DISENGAGE: toward safe point
         + κ_a · [ally within 2 of m]
```
The κ weights come from EE's stance (FIGHT: κ_r small; DISENGAGE: κ_r large). At most 9 × 4 × 4 = 144 candidates,
pruned to ≤60, about 6k ops.

## 7. Gear planner (M6)

For each purchasable candidate i (the next shard toward an emblem, or a new family's first shard if fewer than 2
families are in progress; consumables separately):
```
ΔGE_i = Σ effects over remaining horizon R(t):
  stat shard: Δρ = ρ̄(c)·(growth_i/stat_c)·f_dmg (str/focus) ;  health: ΔDeathRisk·DeathCost·rounds  ≈ ρ̄·0.5·(growth/maxhp)·f_contact
  emblem completion (5th shard) adds passive:
     Monster: ρ̄·0.15·f_clear·R
     Jungle: (recall rounds saved/round)·ρ̄·R   from D_taken model
     Treasure: λ_gold·0.10·gold_rate_c·R
     Prospector: 0.25·7·cluster_captures_rate_c·R
     Capture: 2·capture_rate_c·ρ̄·R
     Home: 2·recall_rate_c·ρ̄·R
     Hunter: λ_gold·50·kill_rate_c·R
     Durability: 0.10·damage_taken_rate·(DeathCost/maxhp)·R
choose argmax ΔGE_i / cost_i ; commit: once ≥2 shards of a family bought, finish it unless another option ≥1.5× better
consumables: altar lock when gold ≥ 40 and (ENDGAME or enemy carrier seen); TP crystal only on maps with value behind gaps (v76 rule)
```
The rates come from the champion's last 100 rounds: captures, clusters, kills, damage taken, recalls. Prior is the
role average from idle runs.

## 8. Race controller (M10)

From §1, TEAM_MODE is set by the table in MASTER §6. ENDGAME_RACE also sets:
- EE π = 0.8 for carriers
- TEP priority: BANK > ESCORT > lock enemy altars > farming

## 9. Opponent modelling

- **EnemyBelief[e]:** last position and round, HP, bag, items count, `dead_until`, channel kind and age.
- **Reach ramp.** `P(e within r of p in τ) = clip((r + τ + k_unseen − cheb(last_e, p)) / (k_unseen + τ + 1), 0, 1)`,
  with k_unseen = rounds since seen. A dead enemy contributes 0 until `dead_until`.
- **Symmetry prior** (before the first sighting): mirror our spawn to theirs (the map is known). Expected early
  enemy objectives are the mirror images of our top-3 TEP objectives at the same rounds.
- **Style classifier at R100** (optional):
  - perma-recall share: enemy recall channels started and cancelled within 1 turn, ≥ 50% of observations
  - contact rate: rounds with an enemy within 8 of any ally
  - middle presence

  These map to the parameter sets {default, cautious, aggressive}. With fewer than 20 observations, use default.

## 10. Draft (M7)

**Chain:**
1. V70 table (known pool maps).
2. On other maps: if OCC_DRAFT=1 and it passed V-D1, the utility optimiser; else the ML draft.
3. Map-class lineup.
4. Preset.

**Utility optimiser** (draft turn 1, with ≤250k ops):
```
U(L | map, E_revealed) = w1·ClearPower(L,camp mix) + w2·Sustain(L,camp damage) + w3·FightPower(L,E)
                       + w4·Mobility(L,gap value) + w5·Econ(L | our controller: Vesper gold share, Marcella banking, Prospector clusters)
                       + Σ synergy(i,j) − RoleViolations(L)
pick = argmax_{champ x ∉ ours} max_{completion ⊇ ours+x} U          // exhaustive: ≤ C(12,k) ≤ 792
before enemy picks: E prior = top-team modal drafts (Vesper, Heart, Vendetta, Marcella, C&I) weighted by frequency
```
Fit `w` by pairwise ranking on v70 league per-map gains. **Accept only if the LOMO held-out gain beats the ML net**
(the coarse-feature kNN gave only +17 [−13, +52] against an oracle of +134).

## 11. Opening schedule (M9)

On the last draft turn, run the TEP rollout without enemies for 120 rounds, with the ObjModel, from spawn. Hill-climb
over the first 2 objectives per crew (swap and resize; ≤200 rollouts). Encode per champion the first 3 jobs
(7-bit group, 2-bit role, 8-bit start round): ≤32 bytes. At runtime it is a ×1.3 prior on those (g, start) pairs,
dropped on the first mismatch (group not ALIVE when expected, pressure > 0.5, or a crew-mate missing).

## 12. World and pathfinding

- **Keep v76 distance fields:**
  - per group, plus spawn and altars
  - built incrementally under a per-turn budget
  - before a group has a field, ObjModel uses `1.3·cheb`, flagged as low-confidence (no long commitments)
- **Local danger window.** 17×17 around me, computed only on threat turns:
  `danger[tile] = Σ_e dps_e·[cheb(tile,e) ≤ range_e+1(+2 dash ready)]`, about 289 × E ops, ≤3k.
- **Hot-zone update** (17% of fuel today). Recompute only when the visible enemy set or awake camps change, using a
  hash of positions. Expected saving 3–5k per turn.
